# LOCAL AI DEPLOYMENT SETUP (AIDER + OLLAMA)

This document serves as the single point of truth for configuring a friction-free local AI development environment — a Mac client talking to a remote GPU server running Ollama.

---

## ARCHITECTURE OVERVIEW

```
[ Mac Client ]  ──── local network ────  [ GPU Server (Windows or Mac Mini) ]
  aider                                    ollama + models
  ~/.aider.conf.yml                        port 11434 exposed on LAN
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
# Look for IPv4 Address under your LAN adapter, e.g. 192.168.1.103
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

## Current server details

| Setting | Value |
|---|---|
| OS | Windows |
| IP address | `192.168.1.103` |
| Port | `11434` |
| Models | `deepseek-r1:14b`, `qwen3:32b` |

Verify models are available from client:
```bash
curl -s http://192.168.1.103:11434/api/tags | python3 -m json.tool
```

| Model | Role | Size | Quantization |
|---|---|---|---|
| `deepseek-r1:14b` | Architect (plans logic) | ~8.4 GB | Q4_K_M |
| `qwen3:32b` | Editor (writes code) | ~18.8 GB | Q4_K_M |

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
- You operate in a dual-model team: DeepSeek-R1 (Architect) plans the logic; Qwen 3 (Editor) implements the code.
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
openai-api-base: http://192.168.1.103:11434/v1
openai-api-key: ollama

# --- Models ---
model: openai/deepseek-r1:14b
editor-model: openai/qwen3:32b

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
