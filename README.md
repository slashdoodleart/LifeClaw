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

One tool. Every task. Local-first. 60+ built-in skills. 17 LLM providers. Zero config web search. Autonomous 23-stage research pipeline with PIVOT/REFINE loops. Real literature APIs. Multi-agent debate. Token economics tracking. Combo skills. Document creation. Scheduled tasks. Arrow-key navigation everywhere.

## Why LifeClaw

- **One CLI, every use case.** Coding, research, writing, documents, shell ops, web search, channel bots — all behind one prompt
- **Local-first.** Auto-detects Ollama. Your data stays on your machine unless you choose otherwise
- **Gateway mode.** Run LifeClaw as a service — connect Telegram, Discord, Slack bots with cron scheduling
- **60+ built-in skills.** From TDD to PDF creation to autonomous research papers. Combo skills with `+` syntax
- **Autonomous research.** 23-stage, 8-phase pipeline with PIVOT/REFINE decision loops, multi-agent debate, real academic literature from OpenAlex/Semantic Scholar/arXiv, 4-layer citation verification, LaTeX export, and self-healing
- **Token economics.** Every LLM call tracked with real cost estimates. See exactly what you spend
- **Document creation.** Create Word docs, spreadsheets, presentations, and PDFs natively
- **Web search built-in.** DuckDuckGo (zero config), Brave, Tavily, Jina, SearXNG — with automatic fallback
- **Cross-run learning.** LifeClaw extracts lessons from failures and injects them into future sessions
- **MCP native.** 9 pre-integrated MCP servers, auto-import from existing configs
- **Every provider.** 17 providers: Ollama, OpenAI, Anthropic, Gemini, OpenRouter, DeepSeek, Groq, Mistral, and more
- **Arrow-key navigation.** No commands to memorize — just arrow keys and Enter for everything
- **Live autocomplete.** Type `/` and see commands + skills instantly — no Enter needed
- **Dual interface.** Terminal CLI and web dashboard share the same agent brain via WebSocket

## Quick Start

> **Requires Python 3.11+.** On macOS, install via `brew install python@3.11` or [python.org](https://python.org).

### pip (recommended)

```bash
pip3.11 install git+https://github.com/slashdoodleart/LifeClaw.git
lifeclaw         # Arrow-key interactive menu
```

### From source

```bash
git clone https://github.com/slashdoodleart/LifeClaw.git
cd LifeClaw
python3.11 -m pip install -e .
lifeclaw
```

### Docker

```bash
docker build -t lifeclaw https://github.com/slashdoodleart/LifeClaw.git
docker run -it --network host -v ~/.lifeclaw:/root/.lifeclaw lifeclaw
```

## Features

### Terminal UI
Rich, themed terminal with streaming output, markdown, syntax highlighting, live autocomplete, and arrow-key navigation.

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
lifeclaw web                      # Web dashboard
```

### Slash Commands
| Command | Description |
|---------|-------------|
| `/` | Arrow-key command picker (mode-aware, shows relevant skills) |
| `/mode` | Switch mode (coder, general, researcher, shell) |
| `/model` | Switch model — live Ollama picker + custom entry |
| `/theme` | Switch theme with arrow-key picker |
| `/skill` | Activate a skill with arrow-key picker |
| `/skill docx+research` | Combo skills — activate multiple at once |
| `/skills` | List all 60+ available skills |
| `/research <topic>` | Start autonomous 23-stage research pipeline |
| `/review` | PR-style code review of current directory |
| `/costs` | Token economics for current session |
| `/websearch <query>` | Search the web |
| `/spawn <task>` | Run a sub-agent in parallel |
| `/learn` | View cross-run learned lessons |
| `/mcp` | List connected MCP servers and tools |
| `/channels` | View messaging integrations |
| `/cron` | View scheduled tasks |
| `/clear` | Clear conversation |
| `/save` | Save session |
| `/status` | Current status |

### Combo Skills

Activate multiple skills at once with `+` syntax:

```
/docx+research       # Document creation + research mode
/xlsx+web-research    # Spreadsheet + web research
/tdd+code-review     # Test-driven dev + code review
```

### Autonomous Research Pipeline

Full 23-stage, 8-phase pipeline:

```bash
lifeclaw research "transformer attention for long documents"
```

**Phase A: Research Scoping** — Topic decomposition, problem formalization
**Phase B: Literature Discovery** — Real papers from OpenAlex, Semantic Scholar, arXiv (no hallucinated refs)
**Phase C: Knowledge Synthesis** — Multi-agent debate for hypothesis generation
**Phase D: Experiment Design** — Hardware-aware (CUDA/MPS/CPU), gate stage
**Phase E: Experiment Execution** — Sandbox execution with self-healing
**Phase F: Analysis & Decision** — PIVOT (new direction) / REFINE (tweak params) / PROCEED loops
**Phase G: Paper Writing** — Section-by-section drafting + multi-agent peer review
**Phase H: Finalization** — Quality gate, LaTeX export, 4-layer citation verification

Output:
| File | Description |
|------|-------------|
| `paper_draft.md` | Full academic paper |
| `paper.tex` | LaTeX with conference formatting |
| `references.bib` | Real BibTeX from OpenAlex/S2/arXiv |
| `verification_report.json` | 4-layer citation verification |
| `experiments/` | Generated code + results |
| `charts/` | Visualizations with error bars |
| `knowledge_base/` | Structured KB (decisions, findings, literature) |

### Token Economics

Every LLM call is tracked with real cost estimates:

```
Cost: $0.0234 | Tokens: 12,450 | Calls: 8
```

- Cloud models: real pricing (GPT-4o, Claude, Gemini, etc.)
- Local models (Ollama): free, shows token count only
- Session summary on exit
- `/costs` command for detailed breakdown
- Historical data saved to `~/.lifeclaw/economics/`

### Cross-Run Learning

Failures become reusable lessons. When the pipeline encounters errors, it extracts structured lessons and injects them into future sessions:

```
Run N fails → Lesson extracted → Stored in ~/.lifeclaw/learning/
Run N+1 → Lessons injected → Same mistake avoided
```

Use `/learn` to view accumulated lessons and their confidence scores.

### Multi-Channel Messaging (Gateway Mode)

Connect LifeClaw to your favorite chat platforms. Run `lifeclaw gateway` to start.

| Channel | What you need |
|---------|---------------|
| **Telegram** | Bot token from @BotFather |
| **Discord** | Bot token + Message Content intent |
| **Slack** | Bot token + App-level token (Socket Mode) |
| **WebChat** | Built-in, just enable |

### Document Creation

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
├── agent/          # Agent loop, memory, tools, sub-agents, cross-run learning, economics
├── providers/      # 17 LLM providers (Ollama, OpenAI, Anthropic, Gemini, ...)
├── mcp/            # MCP client (connects to any MCP server)
├── skills/         # 60+ built-in skills + custom skill loader
├── channels/       # Multi-channel messaging (Telegram, Discord, Slack, WebChat)
├── gateway/        # Gateway server (channels + cron + agent as service)
├── cron/           # Scheduled task execution
├── websearch/      # Multi-provider web search (Brave, DDG, Jina, Tavily, SearXNG)
├── research/       # 23-stage research pipeline, real literature APIs, KB, citations
├── cli/            # Terminal UI (Rich + prompt-toolkit + questionary)
├── config/         # Configuration, setup wizard, loader
├── server/         # WebSocket + static file server for web dashboard
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
