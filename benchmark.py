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
OLLAMA_MODEL   = "qwen3:14b"

PROMPT = """Write a Kotlin function that:
1. Takes a list of integers
2. Returns a map where keys are "even" and "odd"
3. Each key maps to the sum of numbers in that category
4. Handle empty list gracefully

Include a brief docstring and one usage example in a comment."""

# /no_think disables Qwen3's internal chain-of-thought, drastically reducing
# time to first token at the cost of less "reasoning" before answering
PROMPT_OLLAMA = PROMPT + "\n\n/no_think"

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

# ── Qwen3 via Ollama native API ────────────────────────────────────────────────
def run_ollama(result: Result):
    try:
        import urllib.request

        payload = {
            "model": OLLAMA_MODEL,
            "think": False,
            "stream": True,
            "messages": [{"role": "user", "content": PROMPT}],
        }

        req = urllib.request.Request(
            f"http://{OLLAMA_BASE.split('://')[1].split('/')[0].split(':')[0]}:11434/api/chat",
            data=__import__("json").dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )

        t_start = time.perf_counter()
        first_token = None

        with urllib.request.urlopen(req) as resp:
            for line in resp:
                chunk = __import__("json").loads(line.decode())
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

# ── Run both in parallel ───────────────────────────────────────────────────────
def main():
    claude = Result("Claude Sonnet 4.6 (Vertex AI)")
    ollama = Result(f"{OLLAMA_MODEL} (Ollama remote, think=off)")

    print("Running benchmark in parallel...")
    print(f"Prompt: {PROMPT[:80].strip()}...\n")

    t1 = threading.Thread(target=run_claude, args=(claude,))
    t2 = threading.Thread(target=run_ollama, args=(ollama,))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # ── Print summary ──────────────────────────────────────────────────────────
    print("=" * 60)
    for r in [claude, ollama]:
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
    out += f"## Prompt\n```\n{PROMPT.strip()}\n```\n\n"
    out += "## Speed Summary\n\n"
    out += "| | Time to first token | Total time | Output tokens |\n"
    out += "|---|---|---|---|\n"

    for r in [claude, ollama]:
        if r.error:
            out += f"| {r.name} | ERROR | ERROR | — |\n"
        else:
            out += f"| {r.name} | {r.first_token_ms} ms | {r.total_ms} ms | ~{r.tokens} |\n"

    out += "\n---\n\n"
    for r in [claude, ollama]:
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
