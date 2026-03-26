# Running a Local AI Coding Assistant with Aider and Ollama

A guide to setting up a fully local, free AI coding assistant — no API subscription required. You run the models yourself on hardware you control.

## Contents

- [Why bother?](#why-bother)
- [Is this better than copy-pasting into ChatGPT or Gemini?](#is-this-better-than-copy-pasting-into-chatgpt-or-gemini)
- [How it works](#how-it-works)
- [What you need](#what-you-need)
- [Part 1: Server Setup](#part-1-server-setup)
  - [Install Ollama](#install-ollama)
  - [Expose Ollama on your local network](#expose-ollama-on-your-local-network)
  - [Choose and download models](#choose-and-download-models)
  - [Find your server's IP address](#find-your-servers-ip-address)
- [Part 2: Client Setup (Mac)](#part-2-client-setup-mac)
  - [Install Aider](#install-aider)
  - [Configure Aider](#configure-aider)
  - [Create a global instructions file](#create-a-global-instructions-file)
  - [Add a shell alias](#add-a-shell-alias)
- [Alternative Client: Claude Code via Ollama](#alternative-client-claude-code-via-ollama)
  - [Install](#install)
  - [Launch](#launch)
  - [Recommended: create qwen3-fast before launching](#recommended-create-qwen3-fast-before-launching)
  - [Known limitations](#known-limitations)
  - [Note: conflict with existing Claude Code setups](#note-conflict-with-existing-claude-code-setups)
- [Part 3: Usage](#part-3-usage)
  - [Aider](#aider)
  - [Claude Code](#claude-code)
- [Part 4: Choosing the Right Models](#part-4-choosing-the-right-models)
  - [Local vs paid: the honest comparison](#local-vs-paid-the-honest-comparison)
  - [The key local tradeoff](#the-key-local-tradeoff)
  - [On thinking mode](#on-thinking-mode)
  - [On model size](#on-model-size)
- [Part 5: Troubleshooting](#part-5-troubleshooting)

---

## Why bother?

Paid AI APIs (Claude, GPT-4, etc.) are powerful but cost money and send your code to external servers. This setup lets you:

- Run models for free on your own hardware
- Keep your code entirely local
- Use a more powerful machine (desktop, gaming PC, old workstation) as the AI server while coding on a laptop
- Learn how local AI actually works

**The tradeoff:** Local models are generally slower and less capable than frontier models like Claude Sonnet. For routine coding tasks the difference is small. For complex logic you'll want to review the output carefully.

## Is this better than copy-pasting into ChatGPT or Gemini?

It depends on the size of the codebase you're working in.

For a small script or a one-off question, copy-pasting into a capable frontier model (GPT-4o, Gemini) is perfectly fine — and those models are arguably stronger than what you can run locally. You might not gain much from this setup in that case.

Where this approach pulls ahead is when you're working in a larger, real codebase:

- The tool reads the files it needs automatically — you don't have to decide what to include
- It understands existing patterns without you having to explain them
- It can write changes directly, run tests, and react to the results
- Context that would be tedious to copy manually is already there

The model quality is lower than frontier models, but the tooling advantage becomes significant once the project has more than a handful of files. If you're regularly working in the same codebase, the integration pays off more than the model quality difference costs you.

---

## How it works

[Aider](https://aider.chat) is an open-source AI coding assistant that runs in your terminal. It works with any OpenAI-compatible API — including [Ollama](https://ollama.com), which lets you run LLMs locally.

```
[ Your laptop ]  ──── local network ────  [ GPU machine ]
  aider (terminal)                          ollama
  edits your code                           runs the AI models
  no GPU needed                             port 11434
```

**Single machine:** Works just as well if you run both on the same computer — just use `http://localhost:11434/v1` as the API base.

---

## What you need

**Server (the machine running the models):**
- A GPU with enough VRAM to hold the model (see model guide below)
- Or a machine with a lot of RAM if you don't have a GPU (much slower)
- Windows, macOS, or Linux

**Client (where you write code):**
- Any machine — no GPU needed
- macOS (this guide), but aider works on Linux and Windows too

---

# Part 1: Server Setup

## Install Ollama

Ollama documentation: [ollama.com](https://ollama.com) · [Model library](https://ollama.com/library)

**Windows:** Download from [ollama.com/download/windows](https://ollama.com/download/windows) — installs as a background service.

**macOS:**
```bash
brew install ollama
brew services start ollama   # run automatically on login
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

---

## Expose Ollama on your local network

By default Ollama only listens on `localhost` — other devices on your network can't reach it. Skip this if you're running everything on one machine.

**Windows:**
1. Open **Start** → search "Environment Variables" → **Edit the system environment variables**
2. **Environment Variables...** → under **System variables** → **New**
   - Name: `OLLAMA_HOST`
   - Value: `0.0.0.0`
3. Restart Ollama via Task Manager

Verify:
```powershell
netstat -an | findstr 11434
# Should show: TCP  0.0.0.0:11434  LISTENING
```

**Windows Firewall:** Allow port 11434:
1. **Windows Defender Firewall with Advanced Security** → **Inbound Rules** → **New Rule**
2. Port → TCP → `11434` → Allow the connection

**macOS:**
```bash
# Either run manually:
OLLAMA_HOST=0.0.0.0 ollama serve

# Or set it permanently for the Homebrew service:
# Edit ~/Library/LaunchAgents/homebrew.mxcl.ollama.plist
# Add inside <dict>:
#   <key>EnvironmentVariables</key>
#   <dict>
#     <key>OLLAMA_HOST</key>
#     <string>0.0.0.0</string>
#   </dict>
brew services restart ollama
```

macOS usually doesn't need firewall changes for LAN traffic.

---

## Choose and download models

Aider's architect mode uses two models:
- **Architect** — reasons about the problem and proposes a plan
- **Editor** — writes the actual code based on the plan

You can use the same model for both, or different ones. The models below are good starting points.

**How much VRAM do you need?**
A Q4_K_M quantized model needs roughly 1 GB per billion parameters. A 14B model needs ~9 GB of VRAM to run fully on GPU. If it doesn't fit, it falls back to CPU which is much slower.

**Recommended starting point (fits in 10 GB VRAM):**
```bash
ollama pull deepseek-r1:14b    # good architect/reasoning model (~9 GB)
ollama pull qwen3:14b          # fast, capable editor (~9 GB)
```

> Note: both models won't fit in VRAM simultaneously. Ollama loads them on demand and evicts the previous one. This is fine — architect runs first, then editor.

**Other models worth considering:**

| Model | Size | Good for |
|---|---|---|
| `phi4:14b` | ~9 GB | Higher quality output than qwen3:14b, slower |
| `qwen2.5-coder:14b` | ~9 GB | Code-specialized, fast first-token |
| `qwen3:8b` | ~5 GB | Less VRAM, decent quality |
| `qwen3:32b` | ~19 GB | Best local quality, but very slow (~6 min) |
| `llama3.2:3b` | ~2 GB | Tiny, fast, weaker quality |

**Pull models:**
```bash
ollama pull <model-name>
```

**Verify what's installed:**
```bash
ollama list
# Or from another machine:
curl http://YOUR_SERVER_IP:11434/api/tags
```

---

## Find your server's IP address

**Windows:**
```powershell
ipconfig
# Look for IPv4 Address, e.g. 192.168.1.103
```

**macOS:**
```bash
ipconfig getifaddr en0   # Wi-Fi
ipconfig getifaddr en1   # Ethernet
```

Note this IP — you'll use it in the client config.

---

# Part 2: Client Setup (Mac)

## Install Aider

Aider documentation: [aider.chat](https://aider.chat) · [Configuration reference](https://aider.chat/docs/config/aider_conf.html)

```bash
brew install aider
aider --version   # verify
```

---

## Configure Aider

Create `~/.aider.conf.yml`:

```yaml
# --- Connection ---
# Point to your Ollama server. Use localhost if running on same machine.
openai-api-base: http://YOUR_SERVER_IP:11434/v1
openai-api-key: ollama   # any string works, Ollama ignores it

# --- Models ---
# The openai/ prefix is required when using Ollama's OpenAI-compatible API
model: openai/deepseek-r1:14b        # architect: plans and reasons
editor-model: openai/qwen3:14b       # editor: writes the code

# --- Flow ---
architect: true              # enable dual-model architect/editor workflow
auto-accept-architect: false # pause after plan, wait for your approval
auto-commits: false          # don't commit automatically
map-tokens: 2048             # how much of the repo structure to include
cache-prompts: true
read: [ ~/.aider.instructions.md ]   # global instructions for the AI

# --- UI ---
dark-mode: true
pretty: true
stream: true
show-model-warnings: false
```

**Key settings explained:**
- `auto-accept-architect: false` — aider will show the plan and wait for `y` before the editor writes anything. This is important — without it, code is written immediately without your review.
- `auto-commits: false` — you decide when to commit.
- `openai/` prefix — required for Ollama's OpenAI-compatible endpoint.

---

## Create a global instructions file

This file is loaded into every aider session and tells the AI how you want it to behave. Adapt it to your stack and preferences.

Create `~/.aider.instructions.md`:

```md
# AI Coding Assistant Instructions

## Workflow
- You work as a dual-model team: the Architect plans, the Editor implements.
- Always present a step-by-step plan before modifying any files.
- Wait for explicit approval ("y", "go", "proceed") before writing to disk.

## Code style
- Write clean, idiomatic code that matches existing patterns in the project.
- Prefer simple solutions over clever ones.
- Follow the conventions already present in the codebase.

## Git
- Write concise, descriptive commit messages.
- Never push — all git operations stay local unless I say otherwise.

## Communication
- Be concise and technical.
- If a request conflicts with existing architecture, say so before proceeding.
- Break complex tasks into smaller steps.
```

Adjust the content to match your tech stack, team conventions, and preferences.

---

## Add a shell alias

Add to `~/.zshrc` (or `~/.bashrc`):

```bash
alias aider-local='echo "Loading source files..." && aider $([ -d src ] && echo src/ || echo .)'
```

Reload:
```bash
source ~/.zshrc
```

This loads `src/` automatically if it exists, otherwise the entire project root — so you don't have to manually add files every session.

---

# Alternative Client: Claude Code via Ollama

Claude Code documentation: [code.claude.com/docs](https://code.claude.com/docs) · [Installation guide](https://code.claude.com/docs/en/getting-started) · [ollama launch blog post](https://ollama.com/blog/launch)

Since January 2026, Ollama implements Anthropic's Messages API. This means you can run Claude Code — Anthropic's official CLI — backed by local models instead of paid API access.

**What you get:** The full Claude Code experience (file editing, bash commands, multi-file context, tool use) running on free local models.

**What you need:** The Ollama CLI installed on the client machine. It doesn't need to run models locally — it just acts as a launcher that configures Claude Code to talk to your server.

## Install

**Claude Code:**
```bash
# macOS / Linux / WSL (recommended — auto-updates)
curl -fsSL https://claude.ai/install.sh | bash

# macOS via Homebrew (does not auto-update)
brew install --cask claude-code

# Windows PowerShell
irm https://claude.ai/install.ps1 | iex

# Windows via WinGet (does not auto-update)
winget install Anthropic.ClaudeCode
```

> Note: `npm install -g @anthropic-ai/claude-code` also works but is deprecated — use the native installer above.

**Ollama CLI** (used only as a launcher — does not need to run models locally):
```bash
# Mac
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# Download from ollama.com/download/windows
```

You do **not** need to start the Ollama service locally — it's only used as a CLI tool to configure and launch Claude Code.

## Launch

```bash
OLLAMA_HOST=http://YOUR_SERVER_IP:11434 ollama launch claude
```

This command:
- Connects to your Ollama server
- Shows available models to choose from
- Configures Claude Code to use Ollama's Anthropic-compatible API
- Starts Claude Code — no manual environment variables or config files needed

When prompted, select a model. See the note below about creating a `qwen3-fast` variant before launching.

## Recommended: create qwen3-fast before launching

`qwen3:14b` defaults to thinking mode — it reasons internally before responding, which adds minutes of latency even for simple questions. Create a custom variant with thinking disabled on the server before using it with Claude Code:

```bash
ollama create qwen3-fast -f - <<'EOF'
FROM qwen3:14b
PARAMETER think false
EOF
```

Then launch Claude Code with that model:

```bash
OLLAMA_HOST=http://YOUR_SERVER_IP:11434 ollama launch claude --model qwen3-fast
```

`phi4:14b` is the better choice for complex coding tasks (see Part 4), but doesn't require this workaround.

## Known limitations

Not all Claude Code features work with every local model. `/init` (which generates a CLAUDE.md file by analyzing your project) is known to fail or produce poor results with some models — it depends on the model's ability to follow structured output formats. If a command behaves unexpectedly, try a different model before assuming it's a configuration issue.

## Note: conflict with existing Claude Code setups

If you already have Claude Code configured to use a paid API (Anthropic or Vertex AI), those settings may override what `ollama launch` sets up. On a fresh machine with no prior Claude Code configuration, it works without any extra steps.

If you have an existing setup and want to override it temporarily, create `~/.claude/settings.local.json`:

```json
{
  "env": {
    "CLAUDE_CODE_USE_VERTEX": "",
    "ANTHROPIC_VERTEX_PROJECT_ID": "",
    "ANTHROPIC_BASE_URL": "http://YOUR_SERVER_IP:11434",
    "ANTHROPIC_AUTH_TOKEN": "ollama"
  }
}
```

Then run `ollama launch claude` as normal. Delete `settings.local.json` when you want to switch back.

---

# Part 3: Usage

## Aider

### Starting a session

```bash
cd your-project
aider-local
```

All source files are loaded. You can start describing what you want to build or fix.

### The workflow

1. Describe your task
2. **Architect** (DeepSeek-R1) thinks through the problem and presents a plan
3. You review — type `y` to approve or ask for changes
4. **Editor** (Qwen3) writes the code
5. Aider asks if you want to commit — your choice

### Useful commands inside aider

| Command | What it does |
|---|---|
| `/add <file>` | Add a file to the context |
| `/drop <file>` | Remove a file from the context |
| `/clear` | Clear chat history (keeps files loaded) |
| `/diff` | Show what was changed |
| `/undo` | Undo the last code change |
| `/model <name>` | Switch model mid-session |
| `/exit` | Quit |

---

## Claude Code

### Starting a session

```bash
cd your-project
OLLAMA_HOST=http://YOUR_SERVER_IP:11434 ollama launch claude
```

Claude Code starts with the model you selected. It automatically maps your project directory and can read, edit, and create files.

### The workflow

Claude Code works differently from Aider — there's no separate architect/editor split. Instead:

1. Describe what you want to build or fix
2. Claude Code reads the relevant files and proposes changes
3. You review and approve each edit before it's applied
4. Run tests or commands directly from the chat if needed

### Useful commands inside Claude Code

| Command | What it does |
|---|---|
| `/init` | Generate a CLAUDE.md with project instructions (may not work on all models) |
| `/clear` | Clear conversation history |
| `/diff` | Show pending changes |
| `/undo` | Revert the last change |
| `/model` | Switch model |
| `/exit` | Quit |

---

# Part 4: Choosing the Right Models

## Local vs paid: the honest comparison

The core question: **what do you actually give up by going local instead of paying for Claude?**

Testing used real Kotlin Spring Boot code across three task complexity levels. The results were more nuanced than expected.

### On simple and medium tasks: no meaningful difference

Adding a field, renaming something, writing a small utility function, following an existing pattern — all tested models produced correct, idiomatic code. If this is most of your work, the free local setup is a genuine replacement.

### On complex tasks: quality gaps appear

Complex business logic with multiple interacting requirements (error handling across layers, bulk DB operations, conditional branching based on external API state) exposed clear differences.

| Model | Speed (first token) | Quality on complex tasks |
|---|---|---|
| Claude Sonnet 4.6 (paid) | ~1–5 s | Consistently correct |
| `phi4:14b` (free, local) | ~10–60 s | Consistently correct |
| `qwen3:14b` (free, local) | ~0.2–3 s | Subtle logic bugs |
| `qwen2.5-coder:14b` (free, local) | ~4–60 s | Type errors on complex calls |
| `gemma3:12b` (free, local) | variable | Scoping bugs, not recommended |
| `qwen3:32b` (free, local) | ~6 min | Correct, but impractically slow |
| `qwen3:14b` (think=on) | ~5 min | No quality improvement |

> Speed numbers vary when models share VRAM. These are from isolated runs.

### The actual tradeoff

| | Claude Sonnet 4.6 (paid) | `phi4:14b` (free, local) | `qwen3:14b` (free, local) |
|---|---|---|---|
| Cost | Subscription / API charges | Free | Free |
| Privacy | Code sent to Anthropic servers | Stays on your hardware | Stays on your hardware |
| First token | ~1–5 s (network-bound) | ~10–60 s | ~0.2–3 s |
| Simple tasks | Correct | Correct | Correct |
| Complex logic | Consistently correct | Consistently correct | Occasional bugs |
| Setup effort | None | Significant (this guide) | Significant (this guide) |

**What you give up by going local:**
- You need to invest time in setup (hours, not minutes)
- `phi4:14b` is slower to start responding than Claude (though total generation time is similar)
- `qwen3:14b` produces subtle bugs on complex logic — easy to miss in a quick review
- No fallback if the server is unavailable

**What you gain:**
- No cost
- Code never leaves your hardware
- No dependency on external services or rate limits
- You can use a more powerful machine as the AI server while coding on a laptop

**Bottom line:** `phi4:14b` matches Claude's quality on the tasks tested here. If you're willing to do the setup and live with slower initial response times, the output quality is equivalent. For fast iteration on routine changes, `qwen3:14b` is the better local choice — just review complex output carefully.

---

## The key local tradeoff

Between the two strongest local options:

| | `qwen3:14b` (think=off) | `phi4:14b` |
|---|---|---|
| First token | ~200ms best case | ~10s best case |
| Routine tasks | Correct | Correct |
| Complex logic | Occasional bugs | Consistently correct |
| Best for | Fast iteration, small changes | Complex business logic |

**Recommendation:** Start with `qwen3:14b` as your editor. If you find yourself catching subtle bugs in complex code, switch to `phi4:14b`.

## On thinking mode

Qwen3 models support a `think=on` mode where the model reasons internally before responding. Testing showed this adds 5–13 minutes of latency with **no measurable quality improvement** for coding tasks. Stick to `think=off` for the editor role.

## On model size

Bigger isn't always better in practice:
- `qwen3:32b` produced correct code but took ~6 minutes — too slow for interactive use
- `phi4:14b` at ~9 GB outperformed it on quality at a fraction of the wait time
- The sweet spot for a coding editor is 8–14B parameters with thinking disabled

---

# Part 5: Troubleshooting

**Aider can't connect to Ollama:**
```bash
curl http://YOUR_SERVER_IP:11434/api/tags
# If this fails, Ollama isn't reachable — check OLLAMA_HOST and firewall settings
```

**Models are very slow:**
- Check if the model fits in VRAM. On Windows, open Task Manager → Performance → GPU → look at the "Compute_0" engine (not "3D") for actual AI workload
- If GPU utilization is low or zero, the model may be running on CPU — check VRAM size vs model size

**Aider applies code without asking:**
Make sure `auto-accept-architect: false` is set in `~/.aider.conf.yml`.

**Aider commits without asking:**
Make sure `auto-commits: false` is set.

**Model name not found:**
Use `ollama list` on the server to see exact model names. The `openai/` prefix in the config is for aider, not for Ollama — the part after `openai/` must match the Ollama model name exactly.
