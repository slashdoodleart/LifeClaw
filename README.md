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

Built by synthesizing the best architectural patterns from open-source AI agent frameworks, LifeClaw ships a single binary that handles everything from surgical code edits to research, writing, system administration, and task automation.

## Why LifeClaw

Most AI assistants force a choice: terminal or GUI, coding or general tasks, local or cloud. LifeClaw refuses to choose.

- **One CLI, every use case.** `lifeclaw chat` gives you a coding assistant, a shell expert, a researcher, and a writer — all behind the same prompt.
- **Local-first.** Auto-detects Ollama during setup. Your data stays on your machine unless you choose otherwise.
- **MCP native.** Connects to Model Context Protocol servers for filesystem, memory, web search, GitHub, and anything else you wire up.
- **Themeable.** Five built-in themes for terminal and web. Aurora (default) blends light orange, purple, and blue for comfortable extended sessions.
- **Dual interface.** The terminal CLI and web dashboard share the same agent brain, running simultaneously via WebSocket.

## Quick Start

```bash
# Install
pip install -e .

# Setup (auto-detects Ollama, imports MCP servers from Claude Code)
lifeclaw setup

# Start chatting
lifeclaw chat
```

If you have Ollama running locally, setup will detect it and list your models. If not, it walks you through configuring a cloud provider (OpenAI, Anthropic, OpenRouter, DeepSeek, Groq).

## Features

### Terminal UI
Rich, themed terminal interface with streaming output, markdown rendering, syntax highlighting, and persistent history. Every keystroke feels responsive.

```
lifeclaw chat                      # Start interactive session
lifeclaw chat --model ollama/qwen2.5-coder  # Use a specific model
lifeclaw chat --theme midnight     # Override theme
lifeclaw web                       # Start web dashboard only
lifeclaw setup                     # Interactive setup wizard
lifeclaw themes                    # List available themes
lifeclaw skills                    # List available skills
```

### Slash Commands (in chat)
| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/model <name>` | Switch model on the fly |
| `/theme <name>` | Switch theme |
| `/skill <name>` | Activate a skill (coder, shell, researcher, writer, git-expert) |
| `/skills` | List all skills |
| `/mcp` | List connected MCP servers |
| `/clear` | Clear conversation |
| `/save` | Save session |
| `/config` | Show current configuration |

### Web Dashboard
A local Next.js + shadcn dashboard at `localhost:3120` that mirrors the terminal experience:
- **Chat** — Same agent, browser-based interface with markdown rendering
- **Themes** — Visual theme switcher with live preview
- **Skills** — Browse and manage available skills
- **MCP** — Monitor connected MCP servers
- **Settings** — View and manage configuration

### Providers
| Provider | Models | Local |
|----------|--------|-------|
| **Ollama** | llama3.2, qwen2.5-coder, mistral, deepseek-coder, phi, gemma, codellama, any | Yes |
| **OpenAI** | gpt-4o, gpt-4o-mini, o1, o3 | No |
| **Anthropic** | claude-opus, claude-sonnet, claude-haiku | No |
| **OpenRouter** | Any model on OpenRouter | No |
| **DeepSeek** | deepseek-chat, deepseek-coder | No |
| **Groq** | llama-3.3-70b, mixtral, gemma2 | No |
| **Custom** | Any OpenAI-compatible endpoint | Depends |

Model strings use `provider/model` format: `ollama/llama3.2`, `anthropic/claude-sonnet-4-20250514`, `openai/gpt-4o`.

### MCP Integration
LifeClaw natively speaks the Model Context Protocol. During setup, it automatically imports MCP servers from Claude Code (`~/.claude/mcp.json`). You can also configure servers manually in `~/.lifeclaw/config.json`.

Supported out of the box:
- `filesystem` — File operations
- `memory` — Persistent memory
- `fetch` — Web fetching
- `github` — GitHub operations
- `sequential-thinking` — Chain-of-thought reasoning
- `puppeteer` — Browser automation
- `context7` — Documentation lookup
- Any custom MCP server

### Skills
Skills shape the agent's behavior for specific tasks:

| Skill | Category | Description |
|-------|----------|-------------|
| `coder` | development | Expert coding assistant — reads, writes, debugs, refactors |
| `shell` | system | System administration and automation |
| `researcher` | research | Deep analysis of files, codebases, and information |
| `writer` | writing | Technical documentation and content |
| `git-expert` | development | Git workflows, commits, branches, merge conflicts |

Custom skills can be added as JSON files in `~/.lifeclaw/skills/`. Skills imported from Claude Code plugins are prefixed with `cc-`.

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
├── providers/      # LLM providers (Ollama, OpenAI, Anthropic, custom)
├── mcp/            # MCP client (connects to any MCP server)
├── skills/         # Skill definitions and manager
├── cli/            # Terminal UI (Rich + prompt-toolkit)
├── config/         # Configuration, setup wizard, loader
├── server/         # WebSocket bridge to web dashboard
└── themes/         # 5 built-in themes (terminal + web)
web/                # Next.js + shadcn web dashboard
```

The Python backend runs the agent brain, provider connections, MCP client, and WebSocket server. The Next.js frontend connects via WebSocket to provide a browser-based interface. Both interfaces share the same agent state.

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
- Node.js >= 20 (for web dashboard)
- Ollama (optional, for local models)

## License

MIT
