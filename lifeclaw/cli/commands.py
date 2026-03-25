"""CLI commands for LifeClaw — terminal experience."""

import asyncio
import os
import sys
from pathlib import Path

import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from lifeclaw import LOGO, __version__
from lifeclaw.cli.stream import (
    StatusLine,
    StreamRenderer,
    ThinkingSpinner,
    make_rich_theme,
)
from lifeclaw.config.loader import load_config, save_config
from lifeclaw.config.schema import get_config_dir
from lifeclaw.themes import ALL_THEMES, get_theme

app = typer.Typer(
    name="lifeclaw",
    help="LifeClaw — Hybrid AI Assistant for Terminal & Web",
    no_args_is_help=True,
)

EXIT_COMMANDS = {"exit", "quit", "/exit", "/quit", ":q", "bye"}

# Mode definitions — each mode shapes agent behavior
MODES = {
    "coder": {
        "label": "coder",
        "description": "Expert coding mode — reads before writing, surgical edits, tests",
        "system_addendum": (
            "\nYou are in CODER MODE. Focus on code quality:\n"
            "- Always read existing files before editing them\n"
            "- Make minimal, targeted changes\n"
            "- Run tests when available\n"
            "- Use proper error handling\n"
            "- Follow the project's existing code style\n"
            "- Explain your changes briefly\n"
        ),
    },
    "general": {
        "label": "general",
        "description": "General assistant — handles any task",
        "system_addendum": "",
    },
    "researcher": {
        "label": "researcher",
        "description": "Research mode — thorough analysis, literature review, paper generation",
        "system_addendum": (
            "\nYou are in RESEARCHER MODE with deep analytical capabilities:\n"
            "- Explore broadly before answering\n"
            "- Search multiple files, directories, and web sources\n"
            "- For academic topics: search arXiv, Semantic Scholar, OpenAlex\n"
            "- Provide comprehensive analysis with citations\n"
            "- Cite specific file paths and line numbers for code\n"
            "- Use /research <topic> for full autonomous paper generation\n"
            "- Synthesize findings across multiple sources\n"
            "- Identify gaps, contradictions, and open questions\n"
        ),
    },
    "shell": {
        "label": "shell",
        "description": "Shell expert — system administration, automation, DevOps",
        "system_addendum": (
            "\nYou are in SHELL MODE. Focus on system tasks:\n"
            "- Prefer shell commands for system operations\n"
            "- Explain what each command does before running\n"
            "- Use safe defaults (avoid destructive operations without confirmation)\n"
            "- Help with automation scripts, cron, services\n"
        ),
    },
}


def _get_console() -> Console:
    config = load_config()
    theme = get_theme(config.theme)
    return Console(theme=make_rich_theme(theme))


@app.command()
def chat(
    model: str = typer.Option(None, "--model", "-m", help="Model (e.g. ollama/llama3.2)"),
    theme: str = typer.Option(None, "--theme", "-t", help="Theme override"),
    mode: str = typer.Option("general", "--mode", help="Mode: coder, general, researcher, shell"),
    no_web: bool = typer.Option(False, "--no-web", help="Disable web UI"),
    coder: bool = typer.Option(False, "--coder", "-c", help="Start in coder mode"),
):
    """Start an interactive chat session."""
    if coder:
        mode = "coder"
    asyncio.run(_chat_async(model, theme, mode, no_web))


async def _chat_async(
    model_override: str | None,
    theme_override: str | None,
    initial_mode: str,
    no_web: bool,
):
    config = load_config()

    if theme_override:
        config.theme = theme_override

    theme = get_theme(config.theme)
    console = Console(theme=make_rich_theme(theme))
    current_mode = initial_mode if initial_mode in MODES else "general"

    # Welcome banner with theme-colored box
    import random
    from lifeclaw.config.defaults import TIPS

    console.print()

    # Build the welcome panel content
    model_display = model_override or config.agent.model
    mcp_count = len(config.mcp_servers)

    left_col = Text()
    left_col.append("\n", style="")
    left_col.append("  LifeClaw", style=f"bold {theme.primary}")
    left_col.append(f" v{__version__}\n", style=f"{theme.muted}")
    left_col.append(f"\n  [{theme.muted}]", style="")
    left_col.append(f"  {model_display}", style=f"{theme.accent}")
    left_col.append(f"  ·  ", style=f"{theme.muted}")
    left_col.append(f"{current_mode}", style=f"bold {theme.secondary}")
    left_col.append(f"  ·  ", style=f"{theme.muted}")
    left_col.append(f"{theme.name}", style=f"{theme.primary}")
    if mcp_count:
        left_col.append(f"  ·  ", style=f"{theme.muted}")
        left_col.append(f"{mcp_count} MCP", style=f"{theme.muted}")
    left_col.append("\n", style="")

    tip = random.choice(TIPS)
    right_text = (
        f"[{theme.accent}]Tips[/]\n"
        f"[{theme.muted}]{tip}[/]\n"
        f"[{theme.muted}]/help for commands · /mode to switch · exit to quit[/]"
    )

    console.print(Panel(
        left_col,
        title=f"[{theme.primary} bold]LifeClaw[/]",
        subtitle=f"[{theme.muted}]{tip}[/]",
        border_style=theme.primary,
        padding=(0, 1),
    ))
    console.print()

    # Initialize provider
    from lifeclaw.providers.registry import resolve_provider
    try:
        provider, model_name = resolve_provider(config, model_override)
    except ValueError as e:
        console.print(f"  [{theme.error}]{e}[/]")
        console.print(f"  [{theme.muted}]Run 'lifeclaw setup' to configure a provider.[/]")
        return

    # Initialize MCP
    from lifeclaw.mcp.client import MCPClient
    mcp = MCPClient()
    if config.mcp_servers:
        console.print(f"  [{theme.muted}]Connecting MCP servers...[/]", end="")
        connected = await mcp.connect_all(config.mcp_servers)
        console.print(f"\r  [{theme.success}]● {connected}/{len(config.mcp_servers)} MCP servers[/]  ")

    # Initialize agent
    from lifeclaw.agent.loop import AgentLoop
    from lifeclaw.agent.memory import Memory

    session_dir = get_config_dir() / "sessions"
    memory = Memory(session_dir=session_dir)
    renderer = StreamRenderer(theme, console)
    spinner = ThinkingSpinner(theme, console)
    status = StatusLine(theme, console)
    status.mode = current_mode
    status.model = model_name
    status.mcp_count = len(config.mcp_servers)

    agent = AgentLoop(
        provider=provider,
        model=model_name,
        memory=memory,
        max_iterations=config.agent.max_iterations,
        temperature=config.agent.temperature,
        max_tokens=config.agent.max_tokens,
        mcp_tools=mcp.get_tool_definitions(),
        mcp_executor=mcp.call_tool,
        on_tool_call=lambda name, args: renderer.print_tool_call(name, args),
    )

    # Apply mode system addendum
    _apply_mode(agent, current_mode)

    # Start WebSocket server
    ws_server = None
    if config.web.enabled and not no_web:
        from lifeclaw.server.websocket import WebSocketServer
        ws_server = WebSocketServer(config, on_message=agent.process)
        await ws_server.start()
        console.print(f"  [{theme.info}]● Web UI: http://{config.web.host}:{config.web.port + 1}[/]")

    console.print()

    # Prompt session
    history_file = get_config_dir() / "history"
    session = PromptSession(history=FileHistory(str(history_file)))

    try:
        while True:
            # Mode-aware prompt
            mode_color = {
                "coder": theme.accent,
                "general": theme.primary,
                "researcher": theme.secondary,
                "shell": theme.success,
            }.get(current_mode, theme.primary)

            try:
                user_input = await asyncio.to_thread(
                    session.prompt,
                    HTML(f'<style fg="{mode_color}" bold="true">{current_mode} &gt; </style>'),
                )
            except (EOFError, KeyboardInterrupt):
                break

            user_input = user_input.strip()
            if not user_input:
                continue
            if user_input.lower() in EXIT_COMMANDS:
                break

            # Handle slash commands
            if user_input.startswith("/"):
                result = await _handle_command(
                    user_input, config, console, theme, memory, agent,
                    current_mode, status, mcp
                )
                if result and result.startswith("MODE:"):
                    current_mode = result.split(":")[1]
                    _apply_mode(agent, current_mode)
                    status.mode = current_mode
                continue

            # Process with agent
            spinner.start()
            try:
                response = await agent.process(user_input)
                spinner.stop()
                console.print()
                console.print(Markdown(response))

                # Update token estimate
                status.token_count = memory.token_estimate

                # Status line
                renderer.finish()

                # Show random tip ~25% of the time
                if random.random() < 0.25:
                    console.print(f"  [{theme.muted}]{random.choice(TIPS)}[/]")

                # Broadcast to web clients
                if ws_server:
                    await ws_server.broadcast_stream(response)

            except Exception as e:
                spinner.stop()
                console.print(f"\n  [{theme.error}]Error: {e}[/]")

            console.print()

    finally:
        memory.save_session()
        if ws_server:
            await ws_server.stop()
        await mcp.shutdown()
        console.print(f"\n  [{theme.muted}]Session saved. Goodbye![/]")


def _apply_mode(agent, mode_name: str):
    """Apply mode-specific system prompt addendum."""
    from lifeclaw.agent.loop import SYSTEM_PROMPT
    mode = MODES.get(mode_name, MODES["general"])
    full_prompt = SYSTEM_PROMPT + mode["system_addendum"]
    agent.memory.add_system(full_prompt)


async def _handle_command(
    cmd: str, config, console: Console, theme, memory, agent,
    current_mode: str, status, mcp
):
    parts = cmd.split(maxsplit=1)
    command = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if command == "/help":
        table = Table(border_style=theme.muted, show_header=False, padding=(0, 2))
        table.add_column(style=f"{theme.accent}")
        table.add_column()
        table.add_row("/help", "Show this help")
        table.add_row("/mode [name]", "Switch mode (coder, general, researcher, shell)")
        table.add_row("/model [name]", "Switch model (e.g. ollama/llama3.2)")
        table.add_row("/theme [name]", "Switch theme (aurora, midnight, forest, ocean, monochrome)")
        table.add_row("/skills", "List available skills")
        table.add_row("/skill [name]", "Activate a skill")
        table.add_row("/mcp", "List MCP servers and tools")
        table.add_row("/research [topic]", "Start autonomous research pipeline on a topic")
        table.add_row("/review", "Review code in current directory (PR-style)")
        table.add_row("/clear", "Clear conversation")
        table.add_row("/save", "Save session")
        table.add_row("/status", "Show current status")
        table.add_row("exit", "Quit")
        console.print(table)

    elif command == "/mode":
        if arg in MODES:
            console.print(f"  [{theme.success}]Switched to {arg} mode[/] [{theme.muted}]— {MODES[arg]['description']}[/]")
            return f"MODE:{arg}"
        else:
            # Arrow-key interactive menu
            import questionary
            mode_choices = [
                questionary.Choice(
                    f"{name} — {info['description']}",
                    value=name,
                )
                for name, info in MODES.items()
            ]
            selected = await asyncio.to_thread(
                lambda: questionary.select(
                    "Select mode (arrow keys):",
                    choices=mode_choices,
                    default=current_mode,
                    instruction="(↑↓ to navigate, Enter to select)",
                ).ask()
            )
            if selected and selected in MODES:
                console.print(f"  [{theme.success}]Switched to {selected} mode[/]")
                return f"MODE:{selected}"

    elif command == "/theme":
        if arg in ALL_THEMES:
            config.theme = arg
            save_config(config)
            console.print(f"  [{theme.success}]Theme → {arg}. Restart for full effect.[/]")
        else:
            import questionary
            theme_choices = [
                questionary.Choice(f"{t.name} ({t.slug})", value=t.slug)
                for t in ALL_THEMES.values()
            ]
            selected = await asyncio.to_thread(
                lambda: questionary.select(
                    "Select theme (arrow keys):",
                    choices=theme_choices,
                    default=config.theme,
                    instruction="(↑↓ to navigate, Enter to select)",
                ).ask()
            )
            if selected:
                config.theme = selected
                save_config(config)
                console.print(f"  [{theme.success}]Theme → {selected}. Restart for full effect.[/]")

    elif command == "/model":
        if arg:
            config.agent.model = arg
            save_config(config)
            # Hot-swap provider and model
            from lifeclaw.providers.registry import resolve_provider
            try:
                new_provider, new_model = resolve_provider(config, arg)
                agent.provider = new_provider
                agent.model = new_model
                status.model = new_model
                console.print(f"  [{theme.success}]Model → {arg} (live)[/]")
            except ValueError as e:
                console.print(f"  [{theme.error}]{e}[/]")
        else:
            # Live model picker — fetch Ollama models + show manual entry
            import questionary
            model_choices = []
            # Try fetching local Ollama models
            try:
                from lifeclaw.providers.ollama import OllamaProvider
                ollama_base = config.providers.ollama.api_base or "http://localhost:11434"
                ollama = OllamaProvider(base_url=ollama_base)
                models = await ollama.list_models()
                for m in models[:30]:
                    model_choices.append(questionary.Choice(f"ollama/{m}", value=f"ollama/{m}"))
            except Exception:
                pass
            model_choices.append(questionary.Choice("(enter custom model string)", value="__custom__"))
            selected = await asyncio.to_thread(
                lambda: questionary.select(
                    "Select model (arrow keys):",
                    choices=model_choices,
                    instruction="(↑↓ to navigate, Enter to select)",
                ).ask()
            )
            if selected == "__custom__":
                custom = await asyncio.to_thread(
                    lambda: questionary.text(
                        "Model string (e.g. openai/gpt-4o, anthropic/claude-sonnet-4-20250514):"
                    ).ask()
                )
                if custom:
                    selected = custom
            if selected and selected != "__custom__":
                config.agent.model = selected
                save_config(config)
                from lifeclaw.providers.registry import resolve_provider
                try:
                    new_provider, new_model = resolve_provider(config, selected)
                    agent.provider = new_provider
                    agent.model = new_model
                    status.model = new_model
                    console.print(f"  [{theme.success}]Model → {selected} (live)[/]")
                except ValueError as e:
                    console.print(f"  [{theme.error}]{e}[/]")

    elif command == "/skills":
        from lifeclaw.skills.manager import SkillsManager
        mgr = SkillsManager(config.skills_dir)
        for s in mgr.list_skills():
            console.print(f"  [{theme.accent}]{s.name}[/] [{theme.muted}]({s.category}) — {s.description}[/]")

    elif command == "/skill":
        from lifeclaw.skills.manager import SkillsManager
        mgr = SkillsManager(config.skills_dir)
        if arg:
            skill = mgr.get(arg)
            if skill:
                memory.add_system(skill.system_prompt)
                console.print(f"  [{theme.success}]Activated: {skill.name}[/] [{theme.muted}]— {skill.description}[/]")
            else:
                console.print(f"  [{theme.error}]Skill not found: {arg}[/]")
        else:
            # Arrow-key interactive skill selector
            import questionary
            skill_choices = [
                questionary.Choice(
                    f"{s.name} ({s.category}) — {s.description}",
                    value=s.name,
                )
                for s in mgr.list_skills()
            ]
            selected = await asyncio.to_thread(
                lambda: questionary.select(
                    "Select skill (arrow keys):",
                    choices=skill_choices,
                    instruction="(↑↓ to navigate, Enter to select)",
                ).ask()
            )
            if selected:
                skill = mgr.get(selected)
                if skill:
                    memory.add_system(skill.system_prompt)
                    console.print(f"  [{theme.success}]Activated: {skill.name}[/] [{theme.muted}]— {skill.description}[/]")

    elif command == "/mcp":
        if config.mcp_servers:
            tool_defs = mcp.get_tool_definitions() if mcp else []
            console.print(f"  [{theme.muted}]{len(config.mcp_servers)} servers, {len(tool_defs)} tools[/]")
            for name in config.mcp_servers:
                console.print(f"  [{theme.accent}]● {name}[/]")
            if tool_defs:
                console.print(f"\n  [{theme.muted}]Tools:[/]")
                for td in tool_defs[:20]:
                    fn = td.get("function", {})
                    console.print(f"    [{theme.muted}]{fn.get('name', '?')}[/]")
                if len(tool_defs) > 20:
                    console.print(f"    [{theme.muted}]... +{len(tool_defs) - 20} more[/]")
        else:
            console.print(f"  [{theme.muted}]No MCP servers configured[/]")

    elif command == "/research":
        if not arg:
            console.print(f"  [{theme.warning}]Usage: /research <topic>[/]")
            console.print(f"  [{theme.muted}]Example: /research transformer attention mechanisms for long documents[/]")
        else:
            # Activate research-paper skill and inject the topic
            from lifeclaw.skills.manager import SkillsManager
            mgr = SkillsManager(config.skills_dir)
            skill = mgr.get("research-paper")
            if skill:
                memory.add_system(skill.system_prompt)
                console.print(f"  [{theme.success}]● Research pipeline activated[/]")
                console.print(f"  [{theme.muted}]Topic: {arg}[/]")
                console.print(f"  [{theme.muted}]Stages: ideation → literature → methodology → experiments → analysis → writing → review[/]")
                # Feed the topic as a user message for the agent to process
                research_prompt = (
                    f"Execute the full autonomous research pipeline for this topic:\n\n"
                    f"**{arg}**\n\n"
                    f"Follow all 7 stages. Create output files in ./research_output/. "
                    f"Search the web for real papers. Write runnable experiment code. "
                    f"Produce a complete paper draft in markdown."
                )
                memory.add_user(research_prompt)
                console.print(f"  [{theme.info}]Starting research... this may take a while.[/]\n")

    elif command == "/review":
        # Code review of current directory changes
        review_prompt = (
            "Review the code in the current directory. Do a thorough review:\n"
            "1. Run `git diff` to see recent changes\n"
            "2. Run `git status` to see modified files\n"
            "3. Read each modified file\n"
            "4. Check for bugs, security issues, code quality\n"
            "5. Produce a structured review with specific line references\n"
            "If no git changes, review the project structure and key files."
        )
        memory.add_user(review_prompt)
        console.print(f"  [{theme.info}]Starting code review...[/]\n")

    elif command == "/clear":
        memory.clear()
        console.print(f"  [{theme.success}]Conversation cleared.[/]")

    elif command == "/save":
        memory.save_session()
        console.print(f"  [{theme.success}]Session saved.[/]")

    elif command == "/status":
        status.render()

    return None


@app.command()
def setup():
    """Run the interactive setup wizard."""
    from lifeclaw.config.setup import run_setup
    asyncio.run(run_setup())


@app.command()
def version():
    """Show version."""
    console = _get_console()
    console.print(f"LifeClaw v{__version__}")


@app.command()
def themes():
    """List available themes."""
    config = load_config()
    console = _get_console()
    for t in ALL_THEMES.values():
        active = " ●" if t.slug == config.theme else "  "
        console.print(f"  {active} [{t.primary}]{t.name}[/] ({t.slug})")


@app.command()
def skills():
    """List available skills."""
    config = load_config()
    console = _get_console()
    from lifeclaw.skills.manager import SkillsManager
    mgr = SkillsManager(config.skills_dir)
    for s in mgr.list_skills():
        console.print(f"  [{s.name}] ({s.category}) — {s.description}")


@app.command()
def web():
    """Start only the web dashboard server."""
    asyncio.run(_web_async())


async def _web_async():
    config = load_config()
    theme = get_theme(config.theme)
    console = Console(theme=make_rich_theme(theme))

    from lifeclaw.providers.registry import resolve_provider
    from lifeclaw.agent.loop import AgentLoop
    from lifeclaw.agent.memory import Memory
    from lifeclaw.server.websocket import WebSocketServer
    from lifeclaw.mcp.client import MCPClient

    provider, model_name = resolve_provider(config)
    memory = Memory()
    mcp = MCPClient()
    if config.mcp_servers:
        await mcp.connect_all(config.mcp_servers)

    agent = AgentLoop(
        provider=provider, model=model_name, memory=memory,
        mcp_tools=mcp.get_tool_definitions(), mcp_executor=mcp.call_tool,
    )

    ws = WebSocketServer(config, on_message=agent.process)
    await ws.start()
    console.print(f"  [{theme.success}]● Web server at ws://{config.web.host}:{config.web.port}[/]")
    console.print(f"  [{theme.muted}]Press Ctrl+C to stop[/]")

    try:
        await asyncio.Future()
    except (KeyboardInterrupt, asyncio.CancelledError):
        await ws.stop()
        await mcp.shutdown()
