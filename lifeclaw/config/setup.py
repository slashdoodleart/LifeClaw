"""Interactive setup wizard for LifeClaw with arrow-key navigation."""

import asyncio

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from lifeclaw import LOGO
from lifeclaw.config.defaults import DEFAULT_MCP_SERVERS, OPTIONAL_MCP_SERVERS
from lifeclaw.config.loader import import_external_mcp, load_config, save_config
from lifeclaw.config.schema import Config, MCPServerConfig, ProviderConfig
from lifeclaw.providers.ollama import OllamaProvider
from lifeclaw.themes import ALL_THEMES, get_theme

console = Console()


def _ask_select(message: str, choices, **kwargs):
    """Run questionary.select synchronously (safe for asyncio.to_thread)."""
    return questionary.select(message, choices=choices, **kwargs).ask()


def _ask_checkbox(message: str, choices, **kwargs):
    return questionary.checkbox(message, choices=choices, **kwargs).ask()


def _ask_text(message: str):
    return questionary.text(message).ask()


def _ask_password(message: str):
    return questionary.password(message).ask()


def _ask_confirm(message: str, default=True):
    return questionary.confirm(message, default=default).ask()


async def run_setup() -> Config:
    config = load_config()

    # Banner
    console.print(Panel(Text(LOGO, style="bold"), title="LifeClaw Setup", border_style="bright_cyan"))
    console.print()

    # --- 1. Theme (arrow-key select) ---
    theme_choices = [
        questionary.Choice(f"{t.name} — {t.slug}", value=t.slug)
        for t in ALL_THEMES.values()
    ]
    result = await asyncio.to_thread(
        _ask_select,
        "Choose your theme (arrow keys to navigate):",
        theme_choices,
        default="aurora",
        instruction="(Use arrow keys)",
    )
    if result:
        config.theme = result

    # --- 2. LLM Provider ---
    console.print("\n[bold cyan]Setting up LLM provider...[/]")
    ollama_url = await OllamaProvider.detect()

    if ollama_url:
        console.print(f"[green]  ● Found Ollama at {ollama_url}[/]")
        config.providers.ollama.api_base = ollama_url

        provider = OllamaProvider(base_url=ollama_url)
        try:
            models = await provider.list_models()
            if models:
                console.print(f"[green]  ● {len(models)} models available[/]")
                model_choices = [questionary.Choice(m, value=m) for m in models[:20]]
                model_choices.append(questionary.Choice("(enter custom)", value="__custom__"))
                model_result = await asyncio.to_thread(
                    _ask_select,
                    "Select default model:",
                    model_choices,
                    instruction="(Use arrow keys)",
                )
                if model_result == "__custom__":
                    model_result = await asyncio.to_thread(_ask_text, "Enter model name:")
                if model_result and model_result != "__custom__":
                    config.agent.model = f"ollama/{model_result}"
                    config.agent.provider = "ollama"
            else:
                console.print("[yellow]  No models found. Run: ollama pull qwen3.5:4b[/]")
        except Exception as e:
            console.print(f"[yellow]  Could not list models: {e}[/]")
    else:
        console.print("[yellow]  Ollama not detected. Install at https://ollama.ai[/]")
        provider_choices = [
            questionary.Choice("OpenAI (gpt-4o)", value="openai"),
            questionary.Choice("Anthropic (claude-sonnet)", value="anthropic"),
            questionary.Choice("OpenRouter (any model)", value="openrouter"),
            questionary.Choice("DeepSeek", value="deepseek"),
            questionary.Choice("Groq (fast inference)", value="groq"),
            questionary.Choice("Mistral", value="mistral"),
            questionary.Choice("Gemini", value="gemini"),
            questionary.Choice("Skip for now", value="skip"),
        ]
        prov = await asyncio.to_thread(
            _ask_select, "Choose cloud provider:", provider_choices,
            instruction="(Use arrow keys)",
        )
        if prov and prov != "skip":
            key = await asyncio.to_thread(_ask_password, f"Enter {prov} API key:")
            if key:
                prov_cfg: ProviderConfig = getattr(config.providers, prov)
                prov_cfg.api_key = key
                config.agent.provider = prov
                defaults = {
                    "openai": "openai/gpt-4o",
                    "anthropic": "anthropic/claude-sonnet-4-20250514",
                    "openrouter": "openrouter/anthropic/claude-sonnet-4-20250514",
                    "deepseek": "deepseek/deepseek-chat",
                    "groq": "groq/llama-3.3-70b-versatile",
                    "mistral": "mistral/mistral-large-latest",
                    "gemini": "gemini/gemini-2.0-flash",
                }
                config.agent.model = defaults.get(prov, f"{prov}/default")

    # --- 3. MCP Servers ---
    console.print("\n[bold cyan]Setting up MCP servers...[/]")

    # Pre-install defaults
    for name, srv_data in DEFAULT_MCP_SERVERS.items():
        if name not in config.mcp_servers:
            config.mcp_servers[name] = MCPServerConfig(
                command=srv_data["command"],
                args=srv_data["args"],
                env=srv_data.get("env", {}),
            )
    console.print(f"[green]  ● {len(DEFAULT_MCP_SERVERS)} default MCP servers pre-installed[/]")
    for name, srv_data in DEFAULT_MCP_SERVERS.items():
        console.print(f"    [dim]{name}[/] — {srv_data['description']}")

    # Import from external configs
    config = import_external_mcp(config)
    imported = set(config.mcp_servers.keys()) - set(DEFAULT_MCP_SERVERS.keys())
    if imported:
        console.print(f"[green]  ● {len(imported)} additional servers imported[/]")
        for name in imported:
            console.print(f"    [dim]{name}[/]")

    # Optional servers
    optional_choices = [
        questionary.Choice(
            f"{name} — {data['description']}",
            value=name,
            checked=(name in config.mcp_servers),
        )
        for name, data in OPTIONAL_MCP_SERVERS.items()
    ]
    if optional_choices:
        selected = await asyncio.to_thread(
            _ask_checkbox,
            "Enable optional MCP servers? (space to toggle, enter to confirm):",
            optional_choices,
            instruction="(Space to select, Enter to confirm)",
        ) or []
        for name in selected:
            if name not in config.mcp_servers:
                data = OPTIONAL_MCP_SERVERS[name]
                env = data.get("env", {})
                requires = data.get("requires")
                if requires and not env.get(requires):
                    key = await asyncio.to_thread(_ask_password, f"Enter {requires}:")
                    if key:
                        env[requires] = key
                config.mcp_servers[name] = MCPServerConfig(
                    command=data["command"], args=data["args"], env=env,
                )

    # --- 4. Import external skills ---
    console.print("\n[bold cyan]Importing skills...[/]")
    from lifeclaw.config.loader import discover_external_skills
    from lifeclaw.skills.manager import SkillsManager

    ext_skills = discover_external_skills()
    mgr = SkillsManager(config.skills_dir)
    if ext_skills:
        for skill_data in ext_skills:
            mgr.install(skill_data)
        console.print(f"[green]  ● {len(ext_skills)} skills imported from plugins[/]")

    total_skills = len(mgr.list_skills())
    console.print(f"[green]  ● {total_skills} total skills available (built-in + imported)[/]")

    # --- 5. Web UI ---
    config.web.enabled = await asyncio.to_thread(
        _ask_confirm, "Enable web dashboard? (localhost:3120)", True
    )

    # --- Save ---
    save_config(config)
    theme = get_theme(config.theme)

    console.print()
    console.print(Panel(
        f"[bold]Setup complete![/]\n\n"
        f"  Theme:       [{theme.primary}]{theme.name}[/]\n"
        f"  Model:       {config.agent.model}\n"
        f"  Provider:    {config.agent.provider}\n"
        f"  MCP Servers: {len(config.mcp_servers)}\n"
        f"  Skills:      {total_skills}\n"
        f"  Web UI:      {'enabled' if config.web.enabled else 'disabled'}\n\n"
        f"  Run [bold cyan]lifeclaw chat[/] to start!\n"
        f"  Run [bold cyan]lifeclaw chat --coder[/] for focused coding mode",
        title="LifeClaw",
        border_style=theme.primary,
    ))

    return config
