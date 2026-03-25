# LOCAL AI DEPLOYMENT SETUP (AIDER + OLLAMA)

This document serves as the single point of truth for configuring a local AI development environment using Aider and Ollama — without needing a paid API subscription.

The primary goal is to let you run AI models on a more powerful machine (a desktop, gaming PC, or Mac Mini with enough RAM) while keeping your development workflow on your everyday laptop. This way the laptop's resources are left untouched while the heavy lifting happens elsewhere.

**That said, this works just as well on a single machine.** If you want to run both Ollama and Aider on the same computer, simply point `openai-api-base` to `http://localhost:11434/v1` instead of a remote IP.

---

## ARCHITECTURE OVERVIEW

```
[ Mac Client (laptop) ]  ──── local network ────  [ GPU Server (Windows or Mac Mini) ]
  aider                                              ollama + models
  ~/.aider.conf.yml                                  port 11434 exposed on LAN
  lightweight, no GPU needed                         does all the AI computation


[ Single machine setup (optional) ]
  aider + ollama running on the same computer
  openai-api-base: http://localhost:11434/v1
```

---

# PART 1: SERVER SETUP

## Option A: Windows Server

### 1. Install Ollama
Download and install from: `https://ollama.com/download/windows`

The installer sets up Ollama as a background service that starts automatically.

### 2. Expose Ollama on the local network
By default Ollama only listens on `127.0.0.1` (localhost). To make it reachable from other devices on the LAN, set the environment variable `OLLAMA_HOST`:

1. Open **Start** → search for "Environment Variables" → click **"Edit the system environment variables"**
2. Click **Environment Variables...**
3. Under **System variables**, click **New**
   - Name: `OLLAMA_HOST`
   - Value: `0.0.0.0`
4. Click OK and close all dialogs
5. Restart Ollama: open Task Manager → find **Ollama** → End Task → relaunch from Start menu

Verify it's listening:
```powershell
netstat -an | findstr 11434
# Should show: TCP  0.0.0.0:11434  ...  LISTENING
```

### 3. Open Windows Firewall for port 11434
1. Open **Windows Defender Firewall with Advanced Security**
2. Click **Inbound Rules** → **New Rule...**
3. Select **Port** → Next
4. Select **TCP**, enter `11434` → Next
5. Select **Allow the connection** → Next
6. Leave all profiles checked → Next
7. Name it `Ollama LAN` → Finish

### 4. Pull the models
Open PowerShell or Command Prompt:
```powershell
ollama pull deepseek-r1:14b
ollama pull qwen3:32b
```

These are large downloads (~8 GB and ~19 GB). Both will be stored in `%USERPROFILE%\.ollama\models`.

### 5. Find the server's IP address
```powershell
ipconfig
# Look for IPv4 Address under your LAN adapter, e.g. 192.168.1.100
```

Note this IP — you'll use it in the client config.

### 6. Verify from another device
From your Mac (or any device on the same network):
```bash
curl http://<server-ip>:11434/api/tags
```
You should get a JSON response listing the installed models.

---

## Option B: Mac Mini Server

### 1. Install Ollama
```bash
brew install ollama
```

### 2. Expose Ollama on the local network
Set `OLLAMA_HOST` so it binds to all interfaces instead of just localhost:

```bash
# Set it permanently via launchctl (survives reboots)
launchctl setenv OLLAMA_HOST "0.0.0.0"
```

If running Ollama as a Homebrew service:
```bash
brew services stop ollama

# Edit the launchd plist to add the environment variable
# File: ~/Library/LaunchAgents/homebrew.mxcl.ollama.plist
# Add inside the <dict> block:
# <key>EnvironmentVariables</key>
# <dict>
#   <key>OLLAMA_HOST</key>
#   <string>0.0.0.0</string>
# </dict>

brew services start ollama
```

Or run it manually in a terminal session:
```bash
OLLAMA_HOST=0.0.0.0 ollama serve
```

### 3. macOS Firewall
macOS usually allows incoming connections on the LAN without extra configuration. If you have the firewall enabled:

1. Open **System Settings** → **Network** → **Firewall**
2. Click **Options...**
3. Add Ollama to the allowed apps, or temporarily disable the firewall for testing

### 4. Pull the models
```bash
ollama pull deepseek-r1:14b
ollama pull qwen3:32b
```

Models are stored in `~/.ollama/models`.

### 5. Find the Mac Mini's IP address
```bash
ipconfig getifaddr en0      # Wi-Fi
ipconfig getifaddr en1      # Ethernet (adjust interface as needed)
```

Or check **System Settings** → **Network**.

### 6. Run as a persistent background service
```bash
brew services start ollama
# Ollama will now start automatically on login
```

---

## Example server details

Replace `YOUR_SERVER_IP` with the actual IP address of your server throughout this document.

| Setting | Value |
|---|---|
| OS | Windows or Mac Mini |
| IP address | `YOUR_SERVER_IP` |
| Port | `11434` (Ollama default) |
| Models | `deepseek-r1:14b`, `qwen3:14b`, `qwen3:32b` |

Verify models are available from client:
```bash
curl -s http://YOUR_SERVER_IP:11434/api/tags | python3 -m json.tool
```

> **Note:** `qwen3:32b` is kept on the server for deep analysis tasks but is not used by aider.
> To use it manually: `ollama run qwen3:32b` directly on the server.

| Model | Role | Size | Quantization |
|---|---|---|---|
| `deepseek-r1:14b` | Architect (plans logic) | ~8.4 GB | Q4_K_M |
| `qwen3:14b` | Editor (writes code) | ~9 GB | Q4_K_M |
| `qwen3:32b` | Deep analysis (manual use) | ~18.8 GB | Q4_K_M |

---

## Benchmarks

> **Note:** These are simple benchmarks meant to give a rough sense of speed and output style — not a comprehensive evaluation. Results will vary depending on GPU, network, and prompt complexity. Three progressively harder tasks were tested across multiple model variants.

### Setup
- **Date:** 2026-03-25
- **Client:** MacBook Pro (Apple Silicon), running aider locally
- **Server:** Windows PC with dedicated GPU (~19 GB VRAM used), Ollama on LAN
- **Claude:** Sonnet 4.6 via Vertex AI (GCP, europe-west1)
- **Script:** `benchmark.py` in this repo (sends same prompt to all models in parallel)

---

### Test 1 — Simple (basic function)
**Task:** Write a Kotlin function that partitions a list of integers into even/odd sums.

| | Time to first token | Total time | Output tokens |
|---|---|---|---|
| Claude Sonnet 4.6 (Vertex AI) | 2 443 ms | 14 716 ms | ~950 |
| qwen3:14b (think=off) | **304 ms** | 15 849 ms | ~190 |

**Quality:** Both correct. qwen3:14b was more concise (5 lines). Claude more thorough with edge cases and explanation.

---

### Test 2 — Medium (pattern matching in existing class)
**Task:** Add a `deactivateById()` method to an existing Spring Boot repository, following existing patterns.

| | Time to first token | Total time | Output tokens |
|---|---|---|---|
| Claude Sonnet 4.6 (Vertex AI) | 1 441 ms | **2 072 ms** | ~76 |
| qwen3:8b (think=on) | 26 342 ms | 28 139 ms | ~57 |
| qwen3:14b (think=off) | 2 930 ms | 30 464 ms | ~57 |

**Quality:** All three produced identical, correct code. No meaningful difference.

---

### Test 3 — Complex (business logic with error handling)
**Task:** Implement `syncDealerOffers()` — fetches from DB and external API, handles partial failures, uses bulk DB updates, returns a structured result.

#### Round 1 — qwen3 variants
| | Time to first token | Total time | Output tokens |
|---|---|---|---|
| Claude Sonnet 4.6 (Vertex AI) | **1 377 ms** | **6 299 ms** | ~531 |
| qwen3:14b (think=off) | 2 930 ms | 30 464 ms | ~326 |
| qwen3:14b (think=on) | 302 007 ms | 336 652 ms | ~370 |
| qwen3:32b (think=off) | 349 556 ms | 483 339 ms | ~484 |
| qwen3:8b (think=on) | 789 631 ms | 803 790 ms | ~367 |

**Quality:**
| | Correct logic | Bulk updates | `skipped` correct | Bug-free |
|---|---|---|---|---|
| Claude Sonnet 4.6 | Yes | Yes | Yes | Yes |
| qwen3:14b (think=off) | Almost | Yes | Yes | No — compile error in groupBy |
| qwen3:14b (think=on) | Yes | Yes | No | Yes |
| qwen3:32b (think=off) | Yes | Yes | Yes | Yes |
| qwen3:8b (think=on) | Yes | Yes | No | Yes |

#### Round 2 — qwen2.5-coder:14b vs qwen3:14b
> Note: qwen3:14b was slower than usual in this run, likely due to VRAM contention from a parallel model download on the server.

| | Time to first token | Total time | Output tokens |
|---|---|---|---|
| Claude Sonnet 4.6 (Vertex AI) | 4 861 ms | **9 443 ms** | ~527 |
| **qwen2.5-coder:14b (think=off)** | **4 169 ms** | 44 505 ms | ~344 |
| qwen3:14b (think=off) | 53 781 ms | 88 066 ms | ~382 |

**Quality — qwen2.5-coder:14b:**
- Correct overall structure and error handling flow
- Bug 1: `bulkUpdateStatus()` called with `List<OfferStatus>` instead of a single `OfferStatus` — type error, does not compile
- Bug 2: `synced` count calculation is mathematically wrong — can exceed total offer count

**Observation:** `qwen2.5-coder:14b` matched Claude's first-token latency (~4s) despite running locally. Purpose-built code models have less reasoning overhead and respond faster to code prompts.

---

### Overall conclusions

**Speed:**
- `qwen2.5-coder:14b` and `qwen3:14b` (both think=off) are the fastest local options
- `qwen2.5-coder:14b` is particularly fast to first token on code tasks — matched Claude's latency in testing
- `think=on` adds no meaningful quality improvement but multiplies latency by 10-100x regardless of model size
- Claude's first-token latency (~1-5s) reflects network roundtrip to Vertex AI (europe-west1) and varies with load

**Quality:**
- For simple and medium tasks: all models produce correct, idiomatic code — no meaningful difference
- For complex tasks with multiple interacting requirements: only Claude and qwen3:32b were consistently bug-free across all runs
- Local 14b models reliably produce plausible-looking code with subtle bugs (wrong types, off-by-one counts) on complex tasks
- `think=on` did not eliminate bugs — it only increased latency

**Practical recommendation for aider:**
- `qwen3:14b think=off` or `qwen2.5-coder:14b` as editor — both work well for routine tasks (adding fields, small methods, refactors)
- `qwen2.5-coder:14b` may be preferable for pure code tasks due to faster first-token response
- On complex business logic, always review the output — local models can produce plausible-looking code with subtle bugs
- `qwen3:32b` is too slow for interactive use; keep it for one-off deep analysis outside aider
- More models being evaluated (phi4:14b, gemma3:12b, mistral-nemo:12b) — conclusions may be updated

---

# PART 2: CLIENT SETUP (MAC)

## 1. Install Aider
```bash
brew install aider
```

Verify:
```bash
aider --version
```

## 2. Global instructions file
**File:** `~/.aider.instructions.md`
**Content:**
```md
# Global AI Agent Instructions

## 1. Context & Project Identification
- At the start of every session or when switching topics, always prefix your response with: "📂 Project: [Current Folder Name]".
- This is mandatory to ensure I know which repository you are currently operating in. If unsure, run `pwd` internally.

## 2. Workflow (Architect & Editor Mode)
- You operate in a dual-model team: DeepSeek-R1 14B (Architect) plans the logic; Qwen3 14B (Editor) implements the code.
- **Architect Phase:** Always present a clear, step-by-step implementation plan in Markdown before modifying any files.
- **Approval:** Wait for my explicit approval (e.g., "y", "go", or "proceed") before the Editor begins writing to the filesystem.

## 3. Technical Stack & Coding Style
- Primary Stack: **Kotlin** (Spring Boot) for backend, **Vue.js** (utilizing `h()` render functions) for frontend.
- Write modern, idiomatic, and type-safe Kotlin code. Avoid unnecessary boilerplate.
- **Error Handling:** Follow existing patterns found in `RouteUtils.kt` (e.g., using `sanitizeErrorMessage`).
- Keep components modular and maintainable.

## 4. Git & Security
- Provide concise, descriptive commit messages for every logical change.
- Never attempt to `git push`. All operations must remain local to this machine.
- Proactively scan for and warn about hardcoded secrets, tokens, or sensitive IP addresses.

## 5. Communication Style
- Be technical, concise, and solution-oriented.
- For complex tasks, break them down into smaller sub-tasks.
- If a requested change conflicts with existing architecture, point it out before proceeding.
```

## 3. Configuration file
**File:** `~/.aider.conf.yml`
**Content:**
```yaml
# --- Connection ---
openai-api-base: http://YOUR_SERVER_IP:11434/v1
openai-api-key: ollama

# --- Models ---
model: openai/deepseek-r1:14b
editor-model: openai/qwen3:14b

# --- Flow ---
architect: true
map-tokens: 2048
cache-prompts: true
read: [ ~/.aider.instructions.md ]

# --- UI ---
dark-mode: true
pretty: true
stream: true
show-model-warnings: false

# --- Automation ---
auto-commits: false
auto-accept-architect: false
```

**Key behavior:**
- `auto-accept-architect: false` — aider pauses after the architect's plan and waits for `y` / `n` before writing any code
- `auto-commits: false` — aider asks before committing, nothing is automatic
- `openai/` prefix on model names — required when using Ollama's OpenAI-compatible API
- Update `openai-api-base` if your server IP changes

## 4. ZSH alias
**File:** `~/.zshrc`
**Add this line:**
```bash
alias aider-local='echo "🚀 Loading all source files..." && aider $([ -d src ] && echo src/ || echo .)'
```

Then reload:
```bash
source ~/.zshrc
```

**How it works:**
- Loads `src/` automatically if it exists, otherwise loads the entire project root
- No need to manually `/add` files inside aider
- `--yes` is intentionally omitted to preserve the plan → approve → write flow

---

# PART 3: USAGE

## Starting a session
1. `cd` to your project directory
2. Run `aider-local`
3. All source files are loaded automatically

## Workflow inside aider
1. Describe what you want to build or fix
2. **DeepSeek-R1** (Architect) presents a step-by-step plan
3. Review the plan — type `y` to proceed or `n` to reject/refine
4. **Qwen3** (Editor) writes the code
5. Aider asks if you want to commit — decide yourself

## Useful aider commands inside a session
| Command | Description |
|---|---|
| `/add <file>` | Add a specific file to context |
| `/drop <file>` | Remove a file from context |
| `/clear` | Clear chat history (keeps files) |
| `/diff` | Show what was changed |
| `/undo` | Undo last code change |
| `/exit` | Quit aider |
