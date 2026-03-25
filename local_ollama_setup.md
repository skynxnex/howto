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

> **Note:** These are informal benchmarks meant to give a rough sense of speed and output quality — not a comprehensive evaluation. Models were tested across three progressively harder tasks. Speed numbers vary when models share VRAM; the quality assessment is the more reliable signal.

### Setup
- **Date:** 2026-03-25
- **Client:** MacBook Pro (Apple Silicon), running aider locally
- **Server:** Windows PC with dedicated GPU, Ollama on LAN
- **Claude:** Sonnet 4.6 via Vertex AI (GCP, europe-west1)
- **Script:** `benchmark.py` in this repo

### Models tested
| Model | Size | Notes |
|---|---|---|
| Claude Sonnet 4.6 | — | Via Vertex AI |
| qwen3:14b (think=off) | ~9 GB | Current aider editor |
| qwen2.5-coder:14b | ~9 GB | Code-specialized |
| phi4:14b | ~9 GB | Microsoft, strong reasoning |
| gemma3:12b | ~8 GB | Google |
| mistral-nemo:12b | ~7 GB | API error — could not test |
| qwen3:8b (think=on) | ~5 GB | Thinking enabled |
| qwen3:32b (think=off) | ~19 GB | Largest local model |

---

### Task 1 — Simple: write a function from scratch
**Prompt:** Partition a list of integers into even/odd sums, return as a map.

All models produced correct, idiomatic Kotlin. No meaningful quality difference. Claude was more verbose (edge cases, explanations); local models were more concise.

---

### Task 2 — Medium: add a method to an existing class
**Prompt:** Add `deactivateById(id: Long): Boolean` to an existing Spring Boot repository, following existing patterns exactly.

All tested models produced identical, correct code. No meaningful difference.

---

### Task 3 — Complex: business logic with error handling
**Prompt:** Implement `syncDealerOffers()` — fetch from DB and external API, handle partial failures per offer, use bulk DB updates, return a structured result.

#### Speed (indicative — varies with VRAM load)
| Model | Time to first token | Total time |
|---|---|---|
| Claude Sonnet 4.6 | ~1–5 s | ~6–15 s |
| qwen3:14b (think=off) | ~0.2–3 s | ~27–90 s |
| qwen2.5-coder:14b | ~4–130 s | ~44–165 s |
| phi4:14b | ~12–60 s | ~55–90 s |
| gemma3:12b | ~1–140 s | ~52–200 s |
| qwen3:14b (think=on) | ~5 min | ~6 min |
| qwen3:32b (think=off) | ~6 min | ~8 min |
| qwen3:8b (think=on) | ~13 min | ~13 min |

#### Quality
| Model | Bug-free | Notes |
|---|---|---|
| **Claude Sonnet 4.6** | **Yes** | Consistent across all runs |
| **phi4:14b** | **Yes** | Correct and clean — separate SOLD/REMOVED lists, proper bulk calls |
| qwen2.5-coder:14b | No | Passes `List<OfferStatus>` to `bulkUpdateStatus` instead of single status — type error |
| qwen3:14b (think=off) | No | Ignores `isSold` result — both branches add to same list, sets everything to SOLD |
| gemma3:12b | No | Scoping bug (`activeVehicleIds` inside try block), double updates, extra N+1 DB calls |
| qwen3:32b (think=off) | Yes | Correct but ~6 min to first token — impractical |
| qwen3:8b/14b (think=on) | Partial | Thinking mode adds no quality benefit, only extreme latency |
| mistral-nemo:12b | — | HTTP 500 from Ollama API — incompatible |

---

### Conclusions

**On thinking mode (`think=on`):**
Tested on qwen3:8b, qwen3:14b, and qwen3:32b. Adds 5–13 minutes of latency with no measurable quality improvement on these tasks. Not useful for an interactive editor role.

**On speed:**
`qwen3:14b think=off` has the lowest latency to first token when VRAM is available (~200ms in the best case). `qwen2.5-coder:14b` is consistently fast on pure code prompts. Claude is bottlenecked by network latency to Vertex AI (~1–5s) but generates output much faster once it starts.

**On quality:**
The gap between models is small on simple tasks and large on complex ones. `phi4:14b` was the only local model that produced correct, bug-free code on the complex task. The bugs in local models tend to be plausible-looking and easy to miss in a quick review.

**The speed vs quality tradeoff:**
There is a clear tradeoff between the two strongest local models:

| | qwen3:14b (think=off) | phi4:14b |
|---|---|---|
| First token | ~200ms best case | ~12s best case |
| Complex task quality | Bugs in logic | Consistently correct |
| Best for | Routine edits, fast iteration | Complex business logic |

If your workflow is mostly small, well-defined changes (adding a field, renaming, small refactors) — `qwen3:14b` is the better choice due to speed. If you frequently work on complex logic with multiple interacting requirements, `phi4:14b` is worth the extra latency.

**Practical recommendations:**
- `qwen3:14b think=off` is the current editor — fast and sufficient for routine tasks
- Switch to `phi4:14b` as editor if you work on complex business logic and catch bugs in reviews
- Always review local model output on complex tasks — bugs tend to be plausible-looking and syntactically valid
- Keep `qwen3:32b` on the server for manual deep analysis, not for aider
- `gemma3:12b` and `mistral-nemo:12b` are not recommended for this use case

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
