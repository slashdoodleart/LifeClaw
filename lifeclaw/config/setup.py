"""Interactive setup wizard for LifeClaw."""

import asyncio

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from lifeclaw import LOGO
from lifeclaw.config.loader import load_config, merge_claude_mcp, save_config
from lifeclaw.config.schema import Config, ProviderConfig
from lifeclaw.providers.ollama import OllamaProvider
from lifeclaw.themes import ALL_THEMES, get_theme

console = Console()


async def run_setup() -> Config:
    config = load_config()

    # Banner
    console.print(Panel(Text(LOGO, style="bold"), title="LifeClaw Setup", border_style="bright_cyan"))
    console.print()

    # 1. Theme selection
    theme_choices = [f"{t.name} ({t.slug})" for t in ALL_THEMES.values()]
    theme_answer = await asyncio.to_thread(
        questionary.select,
        "Choose your theme:",
        choices=theme_choices,
        default=f"Aurora (aurora)",
    )
    result = theme_answer.ask()
    if result:
        config.theme = result.split("(")[1].rstrip(")")

    # 2. Ollama auto-detect
    console.print("\n[bold cyan]Checking for local Ollama...[/]")
    ollama_url = await OllamaProvider.detect()

    if ollama_url:
        console.print(f"[green]Found Ollama at {ollama_url}[/]")
        config.providers.ollama.api_base = ollama_url

        # List models
        provider = OllamaProvider(base_url=ollama_url)
        try:
            models = await provider.list_models()
            if models:
                console.print(f"[green]Available models: {', '.join(models[:10])}[/]")
                model_answer = await asyncio.to_thread(
                    questionary.select,
                    "Select default model:",
                    choices=models[:20] + ["(enter custom)"],
                )
                model_result = model_answer.ask()
                if model_result and model_result != "(enter custom)":
                    config.agent.model = f"ollama/{model_result}"
                    config.agent.provider = "ollama"
                elif model_result == "(enter custom)":
                    custom = await asyncio.to_thread(
                        questionary.text, "Enter model name:"
                    )
                    custom_result = custom.ask()
                    if custom_result:
                        config.agent.model = f"ollama/{custom_result}"
                        config.agent.provider = "ollama"
            else:
                console.print("[yellow]No models found. Pull one with: ollama pull llama3.2[/]")
        except Exception as e:
            console.print(f"[yellow]Could not list models: {e}[/]")
    else:
        console.print("[yellow]Ollama not detected. You can install it at https://ollama.ai[/]")
        use_cloud = await asyncio.to_thread(
            questionary.confirm, "Set up a cloud provider instead?"
        )
        if use_cloud.ask():
            provider_choice = await asyncio.to_thread(
                questionary.select,
                "Choose provider:",
                choices=["OpenAI", "Anthropic", "OpenRouter", "DeepSeek", "Groq", "Skip"],
            )
            prov = provider_choice.ask()
            if prov and prov != "Skip":
                prov_lower = prov.lower()
                key_input = await asyncio.to_thread(
                    questionary.password, f"Enter {prov} API key:"
                )
                key = key_input.ask()
                if key:
                    prov_cfg: ProviderConfig = getattr(config.providers, prov_lower)
                    prov_cfg.api_key = key
                    config.agent.provider = prov_lower

                    # Suggest default model
                    defaults = {
                        "openai": "openai/gpt-4o",
                        "anthropic": "anthropic/claude-sonnet-4-20250514",
                        "openrouter": "openrouter/anthropic/claude-sonnet-4-20250514",
                        "deepseek": "deepseek/deepseek-chat",
                        "groq": "groq/llama-3.3-70b-versatile",
                    }
                    config.agent.model = defaults.get(prov_lower, f"{prov_lower}/default")

    # 3. Import MCP from Claude Code
    console.print("\n[bold cyan]Importing Claude Code MCP servers...[/]")
    config = merge_claude_mcp(config)
    if config.mcp_servers:
        console.print(f"[green]Imported {len(config.mcp_servers)} MCP servers[/]")
        for name in config.mcp_servers:
            console.print(f"  [dim]-[/] {name}")
    else:
        console.print("[dim]No MCP servers found[/]")

    # 3b. Import Claude Code skills
    console.print("\n[bold cyan]Importing Claude Code skills...[/]")
    from lifeclaw.config.loader import merge_claude_skills
    from lifeclaw.skills.manager import SkillsManager

    cc_skills = merge_claude_skills(config)
    if cc_skills:
        mgr = SkillsManager(config.skills_dir)
        for skill_data in cc_skills:
            mgr.install(skill_data)
        console.print(f"[green]Imported {len(cc_skills)} skills from Claude Code[/]")
    else:
        console.print("[dim]No Claude Code skills found (this is fine)[/]")

    # 4. Web UI
    enable_web = await asyncio.to_thread(
        questionary.confirm, "Enable web dashboard? (accessible at localhost:3119)", default=True
    )
    config.web.enabled = enable_web.ask()

    # Save
    save_config(config)
    theme = get_theme(config.theme)
    console.print(Panel(
        f"[bold]Setup complete![/]\n"
        f"Theme: {theme.name}\n"
        f"Model: {config.agent.model}\n"
        f"Provider: {config.agent.provider}\n"
        f"MCP Servers: {len(config.mcp_servers)}\n"
        f"Web UI: {'enabled' if config.web.enabled else 'disabled'}\n\n"
        f"Run [bold cyan]lifeclaw chat[/] to start!",
        title="LifeClaw",
        border_style=theme.primary,
    ))

    return config
