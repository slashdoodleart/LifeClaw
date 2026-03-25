<div align="center">
  <img src="assets/logo.png" alt="LifeClaw" width="200">
  <h1>LifeClaw</h1>
  <p><strong>The hybrid AI assistant that lives in your terminal, your browser, and your chat apps.</strong></p>
  <p>
    <img src="https://img.shields.io/badge/python-%E2%89%A53.11-blue" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
    <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey" alt="Platform">
    <img src="https://img.shields.io/badge/skills-60%2B-orange" alt="Skills">
    <img src="https://img.shields.io/badge/providers-17-purple" alt="Providers">
  </p>
</div>

---

LifeClaw is a unified AI assistant that combines a surgical code editor, autonomous researcher, document creator, and multi-channel messaging bot — all in one CLI. It runs as a terminal app, a web dashboard, or a gateway service connected to Telegram, Discord, Slack, and more.

One tool. Every task. Local-first. 60+ built-in skills. 17 LLM providers. Zero config web search. Autonomous 23-stage research pipeline. Document creation (DOCX, XLSX, PPTX, PDF). Scheduled tasks. Arrow-key navigation everywhere.

## Why LifeClaw

- **One CLI, every use case.** Coding, research, writing, documents, shell ops, web search, channel bots — all behind one prompt
- **Local-first.** Auto-detects Ollama. Your data stays on your machine unless you choose otherwise
- **Gateway mode.** Run LifeClaw as a service — connect Telegram, Discord, Slack bots with cron scheduling
- **60+ built-in skills.** From TDD to PDF creation to autonomous research papers
- **Autonomous research.** 23-stage pipeline turns an idea into a conference-ready paper with real literature, experiments, and peer review
- **Document creation.** Create Word docs, spreadsheets, presentations, and PDFs natively
- **Web search built-in.** DuckDuckGo (zero config), Brave, Tavily, Jina, SearXNG — with automatic fallback
- **MCP native.** 9 pre-integrated MCP servers, auto-import from existing configs
- **Every provider.** 17 providers: Ollama, OpenAI, Anthropic, Gemini, OpenRouter, DeepSeek, Groq, Mistral, and more
- **Arrow-key navigation.** No commands to memorize — just arrow keys and Enter for everything
- **Dual interface.** Terminal CLI and web dashboard share the same agent brain via WebSocket

## Quick Start

> **Requires Python 3.11+.** On macOS, install via `brew install python@3.11` or [python.org](https://python.org).

### pip (recommended)

```bash
pip3.11 install git+https://github.com/slashdoodleart/LifeClaw.git
lifeclaw         # Arrow-key interactive menu
```

### npm (auto-handles Python)

```bash
npm install -g github:slashdoodleart/LifeClaw
lifeclaw setup
lifeclaw chat
```

### Docker

```bash
docker build -t lifeclaw https://github.com/slashdoodleart/LifeClaw.git
docker run -it --network host -v ~/.lifeclaw:/root/.lifeclaw lifeclaw
```

### From source

```bash
git clone https://github.com/slashdoodleart/LifeClaw.git
cd LifeClaw
python3.11 -m pip install -e .
lifeclaw
```

## Features

### Terminal UI
Rich, themed terminal with streaming output, markdown, syntax highlighting, and arrow-key navigation.

```bash
lifeclaw                          # Interactive arrow-key main menu
lifeclaw chat                     # Start chat session
lifeclaw chat -c                  # Coder mode (auto-accepts edits)
lifeclaw chat --mode researcher   # Research mode
lifeclaw gateway                  # Run as service with channels & cron
lifeclaw research "your topic"    # 23-stage autonomous research pipeline
lifeclaw setup                    # Interactive setup wizard
lifeclaw channels                 # View messaging integrations
lifeclaw cron                     # View scheduled tasks
lifeclaw web                      # Web dashboard only
```

### Slash Commands
| Command | Description |
|---------|-------------|
| `/` | Arrow-key command picker (all commands + skills inline) |
| `/mode` | Switch mode (coder, general, researcher, shell) |
| `/model` | Switch model — live Ollama picker + custom entry |
| `/theme` | Switch theme with arrow-key picker |
| `/skill` | Activate a skill with arrow-key picker |
| `/skills` | List all 60+ available skills |
| `/mcp` | List connected MCP servers and tools |
| `/research <topic>` | Start autonomous 23-stage research pipeline |
| `/review` | PR-style code review of current directory |
| `/clear` | Clear conversation |
| `/save` | Save session |
| `/status` | Current status |

### Multi-Channel Messaging (Gateway Mode)

Connect LifeClaw to your favorite chat platforms. Run `lifeclaw gateway` to start.

| Channel | What you need |
|---------|---------------|
| **Telegram** | Bot token from @BotFather |
| **Discord** | Bot token + Message Content intent |
| **Slack** | Bot token + App-level token (Socket Mode) |
| **WebChat** | Built-in, just enable |

Configure in `~/.lifeclaw/config.json`:
```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "YOUR_BOT_TOKEN",
      "allowFrom": ["*"]
    }
  }
}
```

### Cron / Scheduled Tasks

Create recurring agent tasks that run on schedule:

```json
// ~/.lifeclaw/cron/jobs.json
[
  {
    "id": "abc123",
    "name": "daily-standup",
    "prompt": "Generate a standup summary from recent git commits",
    "schedule": "daily",
    "enabled": true
  }
]
```

Schedules: `5m`, `1h`, `30s`, `daily`, `hourly`, `weekly`

### Autonomous Research Pipeline

Full 23-stage pipeline from idea to conference-ready paper:

```bash
lifeclaw research "transformer attention for long documents"
```

Stages: topic refinement → hypotheses → literature search → gap analysis → methodology → experiments → code generation → execution → statistical analysis → visualization → paper writing (7 sections) → peer review → final revision

Output: `paper_draft.md`, `experiments/`, `charts/`, `references.bib` — all in `./research_output/`

### Document Creation

Create professional documents natively:

| Skill | Format | Capabilities |
|-------|--------|-------------|
| `docx` | Word (.docx) | Reports, letters, proposals, formatting, tables |
| `xlsx` | Excel (.xlsx) | Data, formulas, charts, formatting |
| `pptx` | PowerPoint (.pptx) | Slides, layouts, charts, speaker notes |
| `pdf` | PDF (.pdf) | Reports, forms, merge, split, watermarks |

### Web Search

Built-in multi-provider web search with automatic fallback:

| Provider | Config | Free |
|----------|--------|------|
| **DuckDuckGo** (default) | Zero config | Yes |
| **Brave** | API key | No |
| **Tavily** | API key | No |
| **Jina** | API key | Free tier |
| **SearXNG** | Self-hosted URL | Yes |

The agent can search the web and fetch pages using `web_search` and `web_fetch` tools — no setup required.

### Providers

| Provider | Type | Models |
|----------|------|--------|
| **Ollama** | Local | llama3, qwen2.5-coder, mistral, phi, gemma, any |
| **vLLM** | Local | Any model via vLLM server |
| **OpenAI** | Cloud | gpt-4o, gpt-4o-mini, o1, o3 |
| **Anthropic** | Cloud | claude-opus, claude-sonnet, claude-haiku |
| **Gemini** | Cloud | gemini-2.0-flash, gemini-1.5-pro |
| **OpenRouter** | Cloud | Any model on OpenRouter |
| **DeepSeek** | Cloud | deepseek-chat, deepseek-coder |
| **Groq** | Cloud | llama-3.3-70b, mixtral, gemma2 |
| **Mistral** | Cloud | mistral-large, codestral |
| **Moonshot** | Cloud | moonshot-v1 |
| **Zhipu** | Cloud | glm-4, glm-4-plus |
| **DashScope** | Cloud | qwen-turbo, qwen-max |
| **MiniMax** | Cloud | abab6.5, abab5.5 |
| **SiliconFlow** | Cloud | Various open-source |
| **Volcengine** | Cloud | Doubao models |
| **Azure OpenAI** | Cloud | Any Azure-deployed model |
| **Custom** | Any | Any OpenAI-compatible endpoint |

Model format: `provider/model` — e.g., `ollama/qwen2.5-coder`, `anthropic/claude-sonnet-4-20250514`

### MCP Integration

9 pre-integrated MCP servers (auto-install via npx on first use):

- `filesystem` — File operations
- `memory` — Persistent knowledge graph
- `fetch` — Web page fetching
- `sequential-thinking` — Chain-of-thought reasoning
- `context7` — Library documentation
- `playwright` — Browser automation
- `figma` — Design integration
- `brave-search` — Web search
- `everything` — Reference/testing server

Optional: `github`, `puppeteer`, `firebase`, `serena`

Also auto-imports MCP servers from your existing tool configurations.

### Skills (60+)

| Category | Skills |
|----------|--------|
| **Development** | coder, shell, git-expert, frontend-design, code-review, pr-review, debugging, tdd, mcp-builder, webapp-testing, feature-dev, changelog-generator, git-worktree |
| **Research** | researcher, research-paper, literature-review, autonomous-research, web-research |
| **Documents** | docx, xlsx, pptx, pdf, doc-coauthoring |
| **Writing** | writer, content-research-writer, internal-comms |
| **Business** | business-analyst, prd, domain-name-brainstormer, lead-research-assistant, meeting-insights-analyzer, market-analysis |
| **Content** | seo, twitter-algorithm-optimizer, competitive-ads-extractor |
| **Creative** | playground, canvas-design, algorithmic-art, theme-factory, slack-gif-creator |
| **Utility** | file-organizer, invoice-organizer, image-enhancer, video-downloader, raffle-winner-picker |
| **Professional** | tailored-resume-generator |
| **Workflow** | systematic-debugging, test-driven-development, brainstorming, writing-plans, executing-plans, parallel-tasks, verification, smart-explore, make-plan |
| **Automation** | cron-tasks, channel-setup, daily-routine, knowledge-assistant |
| **Meta** | skill-creator |

Custom skills: drop JSON files in `~/.lifeclaw/skills/`.

### Themes

| Theme | Palette | Vibe |
|-------|---------|------|
| **Aurora** (default) | Orange + Purple + Blue | Warm, Nordic |
| **Midnight** | Purple + Cyan + Rose | Dark, neon |
| **Forest** | Green + Violet + Gold | Earthy, calm |
| **Ocean** | Cyan + Indigo + Orange | Cool, expansive |
| **Monochrome** | White + Gray | Minimal |

## Architecture

```
lifeclaw/
├── agent/          # Agent loop, memory, built-in tools (file, shell, web, docs)
├── providers/      # 17 LLM providers (Ollama, OpenAI, Anthropic, Gemini, ...)
├── mcp/            # MCP client (connects to any MCP server)
├── skills/         # 60+ built-in skills + custom skill loader
├── channels/       # Multi-channel messaging (Telegram, Discord, Slack, WebChat)
├── gateway/        # Gateway server (channels + cron + agent as service)
├── cron/           # Scheduled task execution
├── websearch/      # Multi-provider web search (Brave, DDG, Jina, Tavily, SearXNG)
├── research/       # 23-stage autonomous research pipeline
├── cli/            # Terminal UI (Rich + prompt-toolkit + questionary)
├── config/         # Configuration, setup wizard, loader
├── server/         # WebSocket bridge to web dashboard
└── themes/         # 5 built-in themes
web/                # Vite + React + shadcn web dashboard
```

## Configuration

Config lives at `~/.lifeclaw/config.json`. Run `lifeclaw setup` for the interactive wizard.

```json
{
  "theme": "aurora",
  "agent": {
    "model": "ollama/auto",
    "provider": "auto",
    "max_tokens": 8192,
    "temperature": 0.1
  },
  "providers": {
    "ollama": { "api_base": "http://localhost:11434" },
    "openai": { "api_key": "sk-..." }
  },
  "channels": {
    "telegram": { "enabled": true, "token": "BOT_TOKEN" },
    "discord": { "enabled": false, "token": "" }
  },
  "web_search": {
    "provider": "duckduckgo",
    "max_results": 5
  },
  "web": { "enabled": true, "port": 3119 }
}
```

## Requirements

- Python >= 3.11
- Node.js >= 20 (for web dashboard, optional)
- Ollama (optional, for local models)

## License

MIT
