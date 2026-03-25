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
    theme_answer = await asyncio.to_thread(
        questionary.select,
        "Choose your theme (arrow keys to navigate):",
        choices=theme_choices,
        default="aurora",
        instruction="(Use arrow keys)",
    )
    result = theme_answer.ask()
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
                model_answer = await asyncio.to_thread(
                    questionary.select,
                    "Select default model:",
                    choices=model_choices,
                    instruction="(Use arrow keys)",
                )
                model_result = model_answer.ask()
                if model_result == "__custom__":
                    custom = await asyncio.to_thread(questionary.text, "Enter model name:")
                    model_result = custom.ask()
                if model_result and model_result != "__custom__":
                    config.agent.model = f"ollama/{model_result}"
                    config.agent.provider = "ollama"
            else:
                console.print("[yellow]  No models found. Run: ollama pull llama3.2[/]")
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
        provider_answer = await asyncio.to_thread(
            questionary.select, "Choose cloud provider:", choices=provider_choices,
            instruction="(Use arrow keys)",
        )
        prov = provider_answer.ask()
        if prov and prov != "skip":
            key_input = await asyncio.to_thread(questionary.password, f"Enter {prov} API key:")
            key = key_input.ask()
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
        opt_answer = await asyncio.to_thread(
            questionary.checkbox,
            "Enable optional MCP servers? (space to toggle, enter to confirm):",
            choices=optional_choices,
            instruction="(Space to select, Enter to confirm)",
        )
        selected = opt_answer.ask() or []
        for name in selected:
            if name not in config.mcp_servers:
                data = OPTIONAL_MCP_SERVERS[name]
                env = data.get("env", {})
                requires = data.get("requires")
                if requires and not env.get(requires):
                    key_input = await asyncio.to_thread(
                        questionary.password, f"Enter {requires}:"
                    )
                    key = key_input.ask()
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
    enable_web = await asyncio.to_thread(
        questionary.confirm, "Enable web dashboard? (localhost:3120)", default=True
    )
    config.web.enabled = enable_web.ask()

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
