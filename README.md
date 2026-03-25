<div align="center">
  <img src="assets/logo.png" alt="LifeClaw" width="200">
  <h1>LifeClaw</h1>
  <p><strong>The hybrid AI assistant that lives in your terminal and your browser.</strong></p>
  <p>
    <img src="https://img.shields.io/badge/python-%E2%89%A53.11-blue" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
    <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey" alt="Platform">
  </p>
</div>

---

LifeClaw is a unified AI assistant that combines the precision of a code editor with the versatility of a general-purpose agent. It runs as a terminal CLI, a web dashboard, or both simultaneously — connected to local models via Ollama, cloud providers, or any OpenAI-compatible endpoint.

A single binary handles everything from surgical code edits to autonomous research, writing, system administration, and task automation.

## Why LifeClaw

Most AI assistants force a choice: terminal or GUI, coding or general tasks, local or cloud. LifeClaw refuses to choose.

- **One CLI, every use case.** `lifeclaw chat` gives you a coding assistant, a shell expert, a researcher, and a writer — all behind the same prompt.
- **Local-first.** Auto-detects Ollama during setup. Your data stays on your machine unless you choose otherwise.
- **MCP native.** Connects to Model Context Protocol servers for filesystem, memory, web search, GitHub, browser automation, and anything else you wire up.
- **Themeable.** Five built-in themes for terminal and web. Aurora (default) blends light orange, purple, and blue for comfortable extended sessions.
- **Dual interface.** The terminal CLI and web dashboard share the same agent brain, running simultaneously via WebSocket.
- **Every provider.** Ollama, OpenAI, Anthropic, Gemini, OpenRouter, DeepSeek, Groq, Mistral, Moonshot, Zhipu, DashScope, MiniMax, SiliconFlow, Volcengine, Azure OpenAI, vLLM, and any custom endpoint.

## Quick Start

> **Requires Python 3.11+.** On macOS, the system Python is 3.9 — install a newer version via `brew install python@3.11` or [python.org](https://python.org).

### npm (recommended — auto-handles Python)

```bash
# Install globally from GitHub (auto-finds Python 3.11+, installs deps)
npm install -g github:slashdoodleart/LifeClaw
lifeclaw setup
lifeclaw chat
```

### pip

```bash
pip3.11 install git+https://github.com/slashdoodleart/LifeClaw.git
lifeclaw setup
lifeclaw chat
```

### Shell script

```bash
# macOS / Linux / WSL (auto-finds Homebrew Python)
curl -fsSL https://raw.githubusercontent.com/slashdoodleart/LifeClaw/main/install.sh | bash

# Windows (PowerShell)
irm https://raw.githubusercontent.com/slashdoodleart/LifeClaw/main/install.ps1 | iex
```

### Docker

```bash
docker build -t lifeclaw https://github.com/slashdoodleart/LifeClaw.git
docker run -it --network host -v ~/.lifeclaw:/root/.lifeclaw lifeclaw chat
```

### From source

```bash
git clone https://github.com/slashdoodleart/LifeClaw.git
cd LifeClaw
python3.11 -m pip install -e .
lifeclaw setup && lifeclaw chat
```

## Features

### Terminal UI
Rich, themed terminal interface with streaming output, markdown rendering, syntax highlighting, and persistent history.

```
lifeclaw chat                      # Start interactive session
lifeclaw chat -c                   # Coder mode (shortcut)
lifeclaw chat --model ollama/qwen2.5-coder  # Use a specific model
lifeclaw chat --theme midnight     # Override theme
lifeclaw web                       # Start web dashboard only
lifeclaw setup                     # Interactive setup wizard
```

### Slash Commands
| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/mode` | Switch mode with arrow-key picker (coder, general, researcher, shell) |
| `/model` | Switch model — live Ollama model picker + custom entry |
| `/theme` | Switch theme with arrow-key picker |
| `/skill` | Activate a skill (coder, debugging, tdd, frontend-design, ...) |
| `/skills` | List all available skills |
| `/mcp` | List connected MCP servers and tools |
| `/research <topic>` | Start autonomous 7-stage research pipeline |
| `/review` | PR-style code review of current directory |
| `/clear` | Clear conversation |
| `/save` | Save session |
| `/status` | Show current status |

### Web Dashboard
A local Vite + React + shadcn dashboard at `localhost:3120` that mirrors the terminal experience:
- **Chat** — Same agent, browser-based with markdown rendering
- **Themes** — Visual theme switcher with live preview
- **Skills** — Browse and manage available skills
- **MCP** — Monitor connected MCP servers
- **Settings** — View and manage configuration

### Providers
| Provider | Models | Type |
|----------|--------|------|
| **Ollama** | llama3.2, qwen2.5-coder, mistral, deepseek-coder, phi, gemma, codellama, any | Local |
| **vLLM** | Any model via vLLM server | Local |
| **OpenAI** | gpt-4o, gpt-4o-mini, o1, o3 | Cloud |
| **Anthropic** | claude-opus, claude-sonnet, claude-haiku | Cloud |
| **Gemini** | gemini-2.0-flash, gemini-1.5-pro | Cloud |
| **OpenRouter** | Any model on OpenRouter | Cloud |
| **DeepSeek** | deepseek-chat, deepseek-coder | Cloud |
| **Groq** | llama-3.3-70b, mixtral, gemma2 | Cloud |
| **Mistral** | mistral-large, codestral, mistral-small | Cloud |
| **Moonshot** | moonshot-v1-8k, moonshot-v1-32k | Cloud |
| **Zhipu** | glm-4, glm-4-plus | Cloud |
| **DashScope** | qwen-turbo, qwen-max, qwen-plus | Cloud |
| **MiniMax** | abab6.5, abab5.5 | Cloud |
| **SiliconFlow** | Various open-source models | Cloud |
| **Volcengine** | Doubao models | Cloud |
| **Azure OpenAI** | Any Azure-deployed model | Cloud |
| **Custom** | Any OpenAI-compatible endpoint | Any |

Model strings use `provider/model` format: `ollama/llama3.2`, `anthropic/claude-sonnet-4-20250514`, `openai/gpt-4o`.

### MCP Integration
LifeClaw natively speaks the Model Context Protocol. Pre-integrated servers:

- `filesystem` — File operations (read, write, search, move)
- `memory` — Persistent knowledge graph memory
- `fetch` — Web page fetching and conversion
- `sequential-thinking` — Chain-of-thought reasoning
- `context7` — Up-to-date library documentation
- `playwright` — Browser automation and testing
- `github` — GitHub operations (optional, needs PAT)
- `puppeteer` — Headless browser (optional)
- Any custom MCP server

During setup, LifeClaw also imports MCP servers from your existing tool configurations.

### Skills
Skills shape the agent's behavior for specific tasks:

| Skill | Category | Description |
|-------|----------|-------------|
| `coder` | development | Expert coding — reads, writes, debugs, refactors |
| `shell` | system | System administration and automation |
| `researcher` | research | Deep analysis of files, codebases, and information |
| `writer` | writing | Technical documentation and content |
| `git-expert` | development | Git workflows, commits, branches, merge conflicts |
| `research-paper` | research | Autonomous 7-stage research pipeline |
| `literature-review` | research | Systematic literature review |
| `frontend-design` | development | React/Tailwind/shadcn interfaces |
| `code-review` | development | Comprehensive code review |
| `pr-review` | development | Pull request review |
| `debugging` | development | Systematic root cause analysis |
| `tdd` | development | Test-driven development |
| `mcp-builder` | development | Create MCP servers |
| `webapp-testing` | testing | Playwright web testing |
| `feature-dev` | development | Guided feature development |

Custom skills can be added as JSON files in `~/.lifeclaw/skills/`.

### Themes

| Theme | Palette | Vibe |
|-------|---------|------|
| **Aurora** (default) | Light orange + Light purple + Light blue | Warm, comfortable, Nordic |
| **Midnight** | Purple + Cyan + Rose | Dark, neon, focused |
| **Forest** | Green + Violet + Gold | Earthy, calm, natural |
| **Ocean** | Cyan + Indigo + Orange | Deep, cool, expansive |
| **Monochrome** | White + Gray + White | Clean, minimal, distraction-free |

Themes apply to both terminal and web dashboard simultaneously.

## Architecture

```
lifeclaw/
├── agent/          # Agent loop, memory, built-in tools
├── providers/      # LLM providers (Ollama, OpenAI, Anthropic, 15+ more)
├── mcp/            # MCP client (connects to any MCP server)
├── skills/         # 15 built-in skills + custom skill loader
├── cli/            # Terminal UI (Rich + prompt-toolkit)
├── config/         # Configuration, setup wizard, loader
├── server/         # WebSocket bridge to web dashboard
└── themes/         # 5 built-in themes (terminal + web)
web/                # Vite + React + shadcn web dashboard
```

The Python backend runs the agent brain, provider connections, MCP client, and WebSocket server. The web frontend connects via WebSocket to provide a browser-based interface. Both interfaces share the same agent state.

## Configuration

Configuration lives at `~/.lifeclaw/config.json`. Run `lifeclaw setup` for the interactive wizard, or edit directly:

```json
{
  "theme": "aurora",
  "agent": {
    "model": "ollama/llama3.2",
    "provider": "auto",
    "max_tokens": 8192,
    "temperature": 0.1
  },
  "providers": {
    "ollama": { "api_base": "http://localhost:11434" },
    "openai": { "api_key": "sk-..." },
    "anthropic": { "api_key": "sk-ant-..." }
  },
  "mcp_servers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/user"]
    }
  },
  "web": { "enabled": true, "port": 3119 }
}
```

## Web Dashboard Setup

```bash
cd web
npm install
npm run dev     # Development mode at localhost:3120
npm run build   # Production build
```

The web dashboard connects to the Python backend's WebSocket server (port 3119 by default). Start the backend first with `lifeclaw chat` or `lifeclaw web`.

## Requirements

- Python >= 3.11
- Node.js >= 20 (for web dashboard, optional)
- Ollama (optional, for local models)

## License

MIT
