#!/usr/bin/env python3
"""
Benchmark: Claude Sonnet 4.6 (Vertex AI) vs Qwen3:32b (Ollama)

Sends the same coding prompt to both, measures:
- Time to first token
- Total completion time
- Token count
Saves full responses to benchmark_results.md
"""

import time
import threading
import datetime
from openai import OpenAI

# ── Config ────────────────────────────────────────────────────────────────────
VERTEX_PROJECT = "smp-mb-engineering-dev"
VERTEX_REGION  = "europe-west1"
CLAUDE_MODEL   = "claude-sonnet-4-6"

OLLAMA_BASE    = "http://192.168.1.103:11434/v1"
OLLAMA_MODELS = [
    {"name": "qwen3:8b",  "think": True,  "label": "qwen3:8b  (think=on) "},
    {"name": "qwen3:14b", "think": False, "label": "qwen3:14b (think=off)"},
    {"name": "qwen3:14b", "think": True,  "label": "qwen3:14b (think=on) "},
    {"name": "qwen3:32b", "think": False, "label": "qwen3:32b (think=off)"},
]

PROMPT = '''You are working in an existing Kotlin Spring Boot service. Here is the relevant code:

```kotlin
// Existing domain types
data class Offer(val id: Long, val dealerId: Long, val vehicleId: Long, val status: OfferStatus)
enum class OfferStatus { ACTIVE, SOLD, REMOVED }
data class SyncResult(val synced: Int, val failed: List<Long>, val skipped: Int)

// Existing repository — use these methods, do not modify
@Repository
class OfferRepository(private val jdbcTemplate: NamedParameterJdbcTemplate) {
    fun findByDealerId(dealerId: Long): List<Offer> { ... }
    fun findById(id: Long): Offer? { ... }
    fun updateStatus(id: Long, status: OfferStatus): Boolean { ... }
    fun bulkUpdateStatus(ids: List<Long>, status: OfferStatus): Int { ... }
}

// Existing external client — use as-is
@Component
class VehicleApiClient {
    fun fetchActiveVehicleIds(dealerId: Long): Set<Long>   // throws VehicleApiException on failure
    fun isVehicleSold(vehicleId: Long): Boolean            // throws VehicleApiException on failure
}

// Existing exception types
class VehicleApiException(message: String, cause: Throwable? = null) : RuntimeException(message, cause)
class SyncException(message: String, cause: Throwable? = null) : RuntimeException(message, cause)
```

Implement a `syncDealerOffers(dealerId: Long): SyncResult` method for the following service class:

```kotlin
@Service
class OfferSyncService(
    private val offerRepository: OfferRepository,
    private val vehicleApiClient: VehicleApiClient,
    private val logger: Logger = LoggerFactory.getLogger(OfferSyncService::class.java)
) {
    // implement here
}
```

Requirements:
1. Fetch current offers for the dealer from the repository
2. Fetch active vehicle IDs from the external API — if this call fails, throw SyncException
3. For each ACTIVE offer:
   - If its vehicleId is NOT in the active set, check if the vehicle is sold via the API
   - If sold → mark offer as SOLD; if not → mark as REMOVED
   - If the API call for a single vehicle fails, log a warning and add the offer ID to `failed` — do not abort the whole sync
4. Offers already SOLD or REMOVED → count as skipped, do not touch them
5. Use bulkUpdateStatus where possible to minimize DB calls
6. Return a SyncResult with counts
7. No explanation, just the method'''

# ── Result container ───────────────────────────────────────────────────────────
class Result:
    def __init__(self, name):
        self.name = name
        self.first_token_ms = None
        self.total_ms = None
        self.tokens = 0
        self.content = ""
        self.error = None

# ── Claude via Vertex AI ───────────────────────────────────────────────────────
def run_claude(result: Result):
    try:
        import anthropic
        from anthropic import AnthropicVertex

        client = AnthropicVertex(project_id=VERTEX_PROJECT, region=VERTEX_REGION)

        t_start = time.perf_counter()
        first_token = None

        with client.messages.stream(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": PROMPT}]
        ) as stream:
            for text in stream.text_stream:
                if first_token is None:
                    first_token = time.perf_counter()
                    result.first_token_ms = round((first_token - t_start) * 1000)
                result.content += text

        t_end = time.perf_counter()
        result.total_ms = round((t_end - t_start) * 1000)
        msg = stream.get_final_message()
        result.tokens = msg.usage.output_tokens

    except Exception as e:
        result.error = str(e)

# ── Ollama via native API ───────────────────────────────────────────────────────
def run_ollama(result: Result, model: str, think: bool):
    try:
        import urllib.request, json as _json

        host = OLLAMA_BASE.split("://")[1].split("/")[0].split(":")[0]
        payload = {
            "model": model,
            "think": think,
            "stream": True,
            "messages": [{"role": "user", "content": PROMPT}],
        }

        req = urllib.request.Request(
            f"http://{host}:11434/api/chat",
            data=_json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )

        t_start = time.perf_counter()
        first_token = None

        with urllib.request.urlopen(req) as resp:
            for line in resp:
                chunk = _json.loads(line.decode())
                token = chunk.get("message", {}).get("content", "")
                if token:
                    if first_token is None:
                        first_token = time.perf_counter()
                        result.first_token_ms = round((first_token - t_start) * 1000)
                    result.content += token
                    result.tokens += 1
                if chunk.get("done"):
                    break

        t_end = time.perf_counter()
        result.total_ms = round((t_end - t_start) * 1000)

    except Exception as e:
        result.error = str(e)

# ── Run all in parallel ────────────────────────────────────────────────────────
def main():
    claude = Result("Claude Sonnet 4.6 (Vertex AI)")
    ollama_results = [Result(m["label"]) for m in OLLAMA_MODELS]

    print("Running benchmark in parallel...")
    print(f"Prompt: {PROMPT[:80].strip()}...\n")

    threads = [threading.Thread(target=run_claude, args=(claude,))]
    for result, m in zip(ollama_results, OLLAMA_MODELS):
        threads.append(threading.Thread(target=run_ollama, args=(result, m["name"], m["think"])))

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    all_results = [claude] + ollama_results

    # ── Print summary ──────────────────────────────────────────────────────────
    print("=" * 60)
    for r in all_results:
        print(f"\n{r.name}")
        if r.error:
            print(f"  ERROR: {r.error}")
        else:
            print(f"  Time to first token : {r.first_token_ms} ms")
            print(f"  Total time          : {r.total_ms} ms")
            print(f"  Output tokens (~)   : {r.tokens}")
    print()

    # ── Save full results to markdown ──────────────────────────────────────────
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    out = f"# Benchmark Results — {ts}\n\n"
    out += f"## Prompt\n```kotlin\n{PROMPT.strip()}\n```\n\n"
    out += "## Speed Summary\n\n"
    out += "| | Time to first token | Total time | Output tokens |\n"
    out += "|---|---|---|---|\n"

    for r in all_results:
        if r.error:
            out += f"| {r.name} | ERROR | ERROR | — |\n"
        else:
            out += f"| {r.name} | {r.first_token_ms} ms | {r.total_ms} ms | ~{r.tokens} |\n"

    out += "\n---\n\n"
    for r in all_results:
        out += f"## {r.name}\n\n"
        if r.error:
            out += f"**Error:** {r.error}\n\n"
        else:
            out += f"```kotlin\n{r.content.strip()}\n```\n\n"

    output_file = "/Users/pontus.alm@m10s.io/priv/howto/benchmark_results.md"
    with open(output_file, "w") as f:
        f.write(out)

    print(f"Full responses saved to: {output_file}")

if __name__ == "__main__":
    main()
