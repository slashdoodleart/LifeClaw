"""Pre-integrated MCP servers and default configurations.

These are baked into LifeClaw so users don't need to install anything extra.
MCP servers that use npx will auto-install on first run.
"""

# Default MCP servers — available out of the box via npx
DEFAULT_MCP_SERVERS = {
    "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "~"],
        "env": {},
        "description": "File system operations (read, write, search, move)",
    },
    "memory": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-memory"],
        "env": {},
        "description": "Persistent knowledge graph memory across sessions",
    },
    "fetch": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-fetch"],
        "env": {},
        "description": "Fetch web pages and convert to markdown",
    },
    "sequential-thinking": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
        "env": {},
        "description": "Chain-of-thought reasoning for complex problems",
    },
    "context7": {
        "command": "npx",
        "args": ["-y", "@upstash/context7-mcp"],
        "env": {},
        "description": "Up-to-date library documentation and code examples",
    },
    "playwright": {
        "command": "npx",
        "args": ["@playwright/mcp@latest"],
        "env": {},
        "description": "Browser automation, testing, and web scraping",
    },
    "figma": {
        "command": "npx",
        "args": ["-y", "figma-mcp-bridge"],
        "env": {},
        "description": "Figma design integration — inspect, export, bridge designs to code",
    },
    "brave-search": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-brave-search"],
        "env": {},
        "description": "Web search via Brave Search API",
    },
    "everything": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-everything"],
        "env": {},
        "description": "Reference MCP server with all tool types for testing",
    },
}

# Optional MCP servers (require API keys, external tools, or services)
OPTIONAL_MCP_SERVERS = {
    "github": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": ""},
        "description": "GitHub operations (repos, issues, PRs, code search)",
        "requires": "GITHUB_PERSONAL_ACCESS_TOKEN",
    },
    "puppeteer": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
        "env": {},
        "description": "Headless browser automation and screenshots",
    },
    "firebase": {
        "command": "npx",
        "args": ["-y", "firebase-tools@latest", "mcp"],
        "env": {},
        "description": "Firebase project management and deployment",
    },
    "serena": {
        "command": "uvx",
        "args": ["--from", "git+https://github.com/oraios/serena", "serena", "start-mcp-server"],
        "env": {},
        "description": "AI-powered code understanding and semantic search",
    },
}

# Tips shown randomly in the terminal
TIPS = [
    "Tip: Use /mode coder to switch to focused coding mode",
    "Tip: Use /mode researcher for thorough analysis with citations",
    "Tip: Use /research <topic> for autonomous paper generation",
    "Tip: Use /review for PR-style code review of current directory",
    "Tip: Use /skills to see all built-in skills",
    "Tip: Use /mcp to see connected MCP servers and their tools",
    "Tip: Use /theme to switch between 5 visual themes",
    "Tip: Use /model to switch models with arrow-key picker",
    "Tip: Arrow keys navigate history. Tab for completion.",
    "Tip: Use /skill frontend-design for React/Tailwind/shadcn expertise",
    "Tip: Use /skill debugging for systematic root cause analysis",
    "Tip: Use /skill tdd for test-driven development workflow",
    "Tip: Use /skill research-paper for full research pipeline",
    "Tip: MCP servers auto-install via npx on first use",
    "Tip: Run lifeclaw setup to configure providers and import MCP servers",
    "Tip: Your config lives at ~/.lifeclaw/config.json",
    "Tip: Use /clear to reset conversation context",
    "Tip: Use /save to persist your session",
    "Tip: The web dashboard runs at localhost:3120 alongside the terminal",
    "Tip: Press Ctrl+C to cancel a running operation",
    "Tip: Use lifeclaw gateway to run as a service with channels & cron",
    "Tip: Use lifeclaw research 'your topic' for autonomous paper generation",
    "Tip: Connect Telegram, Discord, Slack via channels config",
    "Tip: Set up cron jobs for recurring agent tasks",
    "Tip: Web search works out of the box with DuckDuckGo (zero config)",
    "Tip: Use /skill docx to create Word documents",
    "Tip: Use /skill pptx to create presentations",
    "Tip: Use /skill xlsx to create spreadsheets",
    "Tip: 60+ built-in skills covering coding, research, documents, and more",
]
