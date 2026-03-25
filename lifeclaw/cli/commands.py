"""CLI commands for LifeClaw."""

import asyncio
import os
import sys
from pathlib import Path

import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from lifeclaw import LOGO, __version__
from lifeclaw.cli.stream import StreamRenderer, ThinkingSpinner, make_rich_theme
from lifeclaw.config.loader import load_config, save_config
from lifeclaw.config.schema import get_config_dir
from lifeclaw.themes import ALL_THEMES, get_theme

app = typer.Typer(
    name="lifeclaw",
    help="LifeClaw - Hybrid AI Assistant for Terminal & Web",
    no_args_is_help=True,
)

EXIT_COMMANDS = {"exit", "quit", "/exit", "/quit", ":q", "bye"}


def _get_console() -> Console:
    config = load_config()
    theme = get_theme(config.theme)
    return Console(theme=make_rich_theme(theme))


@app.command()
def chat(
    model: str = typer.Option(None, "--model", "-m", help="Model override (e.g. ollama/llama3.2)"),
    theme: str = typer.Option(None, "--theme", "-t", help="Theme override"),
    no_web: bool = typer.Option(False, "--no-web", help="Disable web UI"),
):
    """Start an interactive chat session."""
    asyncio.run(_chat_async(model, theme, no_web))


async def _chat_async(model_override: str | None, theme_override: str | None, no_web: bool):
    config = load_config()

    if theme_override:
        config.theme = theme_override

    theme = get_theme(config.theme)
    console = Console(theme=make_rich_theme(theme))

    # Banner
    banner_text = Text(LOGO, style=f"bold {theme.primary}")
    console.print(Panel(
        banner_text,
        subtitle=f"v{__version__} | {config.agent.model} | theme: {theme.name}",
        border_style=theme.secondary,
    ))
    console.print(f"  [{theme.muted}]Type /help for commands, or start chatting. {', '.join(EXIT_COMMANDS)} to quit.[/]")
    console.print()

    # Initialize provider
    from lifeclaw.providers.registry import resolve_provider
    try:
        provider, model_name = resolve_provider(config, model_override)
    except ValueError as e:
        console.print(f"[{theme.error}]{e}[/]")
        console.print(f"[{theme.muted}]Run 'lifeclaw setup' to configure a provider.[/]")
        return

    # Initialize MCP
    from lifeclaw.mcp.client import MCPClient
    mcp = MCPClient()
    if config.mcp_servers:
        console.print(f"  [{theme.muted}]Connecting MCP servers...[/]")
        connected = await mcp.connect_all(config.mcp_servers)
        console.print(f"  [{theme.success}]{connected}/{len(config.mcp_servers)} MCP servers connected[/]")

    # Initialize agent
    from lifeclaw.agent.loop import AgentLoop
    from lifeclaw.agent.memory import Memory

    session_dir = get_config_dir() / "sessions"
    memory = Memory(session_dir=session_dir)
    renderer = StreamRenderer(theme, console)
    spinner = ThinkingSpinner(theme, console)

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

    # Start WebSocket server
    ws_server = None
    if config.web.enabled and not no_web:
        from lifeclaw.server.websocket import WebSocketServer
        ws_server = WebSocketServer(config, on_message=agent.process)
        await ws_server.start()
        console.print(f"  [{theme.info}]Web UI: http://{config.web.host}:{config.web.port}[/]")

    console.print()

    # Prompt session
    history_file = get_config_dir() / "history"
    session = PromptSession(history=FileHistory(str(history_file)))

    try:
        while True:
            try:
                user_input = await asyncio.to_thread(
                    session.prompt,
                    HTML(f'<style fg="{theme.primary}" bg="" bold="true">you > </style>'),
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
                await _handle_command(user_input, config, console, theme, memory, agent)
                continue

            # Process with streaming
            spinner.start()
            collected = ""
            try:
                # Use non-streaming for reliability with tool calls
                response = await agent.process(user_input)
                spinner.stop()
                console.print()
                console.print(
                    Text("  claw > ", style=f"bold {theme.secondary}"),
                    end="",
                )
                console.print(Markdown(response))

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
        console.print(f"\n[{theme.muted}]Session saved. Goodbye![/]")


async def _handle_command(
    cmd: str, config, console: Console, theme, memory, agent
):
    parts = cmd.split(maxsplit=1)
    command = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if command == "/help":
        table = Table(title="Commands", border_style=theme.muted)
        table.add_column("Command", style=f"{theme.accent}")
        table.add_column("Description")
        table.add_row("/help", "Show this help")
        table.add_row("/model <name>", "Switch model (e.g. /model ollama/llama3.2)")
        table.add_row("/theme <name>", "Switch theme (aurora, midnight, forest, ocean, monochrome)")
        table.add_row("/skills", "List available skills")
        table.add_row("/skill <name>", "Activate a skill")
        table.add_row("/mcp", "List MCP servers")
        table.add_row("/clear", "Clear conversation")
        table.add_row("/save", "Save session")
        table.add_row("/config", "Show current config")
        table.add_row("exit", "Quit")
        console.print(table)

    elif command == "/theme":
        if arg in ALL_THEMES:
            config.theme = arg
            save_config(config)
            console.print(f"  [{theme.success}]Theme changed to {arg}. Restart for full effect.[/]")
        else:
            console.print(f"  [{theme.warning}]Available: {', '.join(ALL_THEMES.keys())}[/]")

    elif command == "/model":
        if arg:
            config.agent.model = arg
            save_config(config)
            console.print(f"  [{theme.success}]Model changed to {arg}. Restart to apply.[/]")
        else:
            console.print(f"  [{theme.info}]Current: {config.agent.model}[/]")

    elif command == "/skills":
        from lifeclaw.skills.manager import SkillsManager
        mgr = SkillsManager(config.skills_dir)
        table = Table(title="Skills", border_style=theme.muted)
        table.add_column("Name", style=f"{theme.accent}")
        table.add_column("Category")
        table.add_column("Description")
        for s in mgr.list_skills():
            table.add_row(s.name, s.category, s.description)
        console.print(table)

    elif command == "/skill":
        if arg:
            from lifeclaw.skills.manager import SkillsManager
            mgr = SkillsManager(config.skills_dir)
            skill = mgr.get(arg)
            if skill:
                memory.add_system(skill.system_prompt)
                console.print(f"  [{theme.success}]Activated skill: {skill.name}[/]")
            else:
                console.print(f"  [{theme.error}]Skill not found: {arg}[/]")

    elif command == "/mcp":
        if config.mcp_servers:
            for name in config.mcp_servers:
                console.print(f"  [{theme.accent}]{name}[/]")
        else:
            console.print(f"  [{theme.muted}]No MCP servers configured[/]")

    elif command == "/clear":
        memory.clear()
        console.print(f"  [{theme.success}]Conversation cleared.[/]")

    elif command == "/save":
        memory.save_session()
        console.print(f"  [{theme.success}]Session saved.[/]")

    elif command == "/config":
        console.print(f"  Model: [{theme.accent}]{config.agent.model}[/]")
        console.print(f"  Provider: [{theme.accent}]{config.agent.provider}[/]")
        console.print(f"  Theme: [{theme.accent}]{config.theme}[/]")
        console.print(f"  MCP Servers: [{theme.accent}]{len(config.mcp_servers)}[/]")
        console.print(f"  Web UI: [{theme.accent}]{'on' if config.web.enabled else 'off'}[/]")


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
    console = _get_console()
    config = load_config()
    table = Table(title="Themes", border_style="dim")
    table.add_column("Name")
    table.add_column("Slug")
    table.add_column("Colors")
    table.add_column("Active")
    for t in ALL_THEMES.values():
        active = "  *" if t.slug == config.theme else ""
        colors = f"[{t.primary}]primary[/] [{t.secondary}]secondary[/] [{t.accent}]accent[/]"
        table.add_row(t.name, t.slug, colors, active)
    console.print(table)


@app.command()
def skills():
    """List available skills."""
    config = load_config()
    console = _get_console()
    from lifeclaw.skills.manager import SkillsManager
    mgr = SkillsManager(config.skills_dir)
    table = Table(title="Skills", border_style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Category")
    table.add_column("Description")
    for s in mgr.list_skills():
        table.add_row(s.name, s.category, s.description)
    console.print(table)


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
    console.print(f"[{theme.success}]Web server running at ws://{config.web.host}:{config.web.port}[/]")
    console.print(f"[{theme.muted}]Press Ctrl+C to stop[/]")

    try:
        await asyncio.Future()  # run forever
    except (KeyboardInterrupt, asyncio.CancelledError):
        await ws.stop()
        await mcp.shutdown()
