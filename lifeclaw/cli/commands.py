"""CLI commands for LifeClaw — terminal experience."""

import asyncio
import os
import sys
from pathlib import Path

import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
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


class SlashCompleter(Completer):
    """Auto-complete for / commands and skills — shows dropdown as you type."""

    COMMANDS = [
        ("/mode", "Switch mode (coder, general, researcher, shell)"),
        ("/model", "Switch model"),
        ("/theme", "Switch theme"),
        ("/skill", "Activate a skill"),
        ("/skills", "List all skills"),
        ("/research", "Autonomous research pipeline"),
        ("/review", "Code review current directory"),
        ("/websearch", "Search the web"),
        ("/spawn", "Run a sub-agent"),
        ("/mcp", "MCP servers and tools"),
        ("/learn", "View cross-run lessons"),
        ("/channels", "Messaging integrations"),
        ("/cron", "Scheduled tasks"),
        ("/costs", "Token economics this session"),
        ("/clear", "Clear conversation"),
        ("/save", "Save session"),
        ("/status", "Current status"),
        ("/help", "Show help"),
    ]

    def __init__(self, skill_names: list[str] | None = None):
        self.skill_names = skill_names or []

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        # Only trigger on / prefix
        if not text.startswith("/"):
            return

        word = text.lstrip("/")

        # Check if this is a combo (contains +)
        if "+" in word:
            # Complete the part after the last +
            parts = word.split("+")
            prefix = "+".join(parts[:-1]) + "+"
            current = parts[-1]
            for name in self.skill_names:
                if name.startswith(current):
                    yield Completion(
                        name,
                        start_position=-len(current),
                        display=name,
                        display_meta="skill",
                    )
            return

        # Complete commands
        for cmd, desc in self.COMMANDS:
            cmd_name = cmd.lstrip("/")
            if cmd_name.startswith(word):
                yield Completion(
                    cmd,
                    start_position=-len(text),
                    display=cmd,
                    display_meta=desc,
                )

        # Complete skill names (as /skillname or for combos)
        for name in self.skill_names:
            if name.startswith(word):
                yield Completion(
                    f"/skill {name}",
                    start_position=-len(text),
                    display=f"/{name}",
                    display_meta="skill",
                )

app = typer.Typer(
    name="lifeclaw",
    help="LifeClaw — Hybrid AI Assistant for Terminal & Web",
    no_args_is_help=False,
    invoke_without_command=True,
)

EXIT_COMMANDS = {"exit", "quit", "/exit", "/quit", ":q", "bye"}


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """LifeClaw — launch the interactive menu or a subcommand."""
    if ctx.invoked_subcommand is not None:
        return
    # No subcommand — show interactive arrow-key main menu
    asyncio.run(_interactive_menu())


async def _interactive_menu():
    import questionary
    from lifeclaw.themes import get_theme

    config = load_config()
    theme = get_theme(config.theme)
    console = Console(theme=make_rich_theme(theme))

    console.print()
    logo = Text(LOGO, style=f"bold {theme.primary}")
    console.print(logo)
    console.print(f"  [{theme.muted}]v{__version__}[/]")
    console.print()

    while True:
        action = await asyncio.to_thread(
            lambda: questionary.select(
                "What would you like to do?",
                choices=[
                    questionary.Choice("Chat — Start a conversation", value="chat"),
                    questionary.Choice("Chat (Coder) — Coding assistant mode", value="coder"),
                    questionary.Choice("Chat (Researcher) — Research & analysis mode", value="researcher"),
                    questionary.Choice("Chat (Shell) — System administration mode", value="shell"),
                    questionary.Separator("── Services ──"),
                    questionary.Choice("Gateway — Run as service with channels & cron", value="gateway"),
                    questionary.Choice("Research — Autonomous 23-stage paper pipeline", value="research"),
                    questionary.Choice("Channels — View messaging integrations", value="channels"),
                    questionary.Choice("Cron — Scheduled tasks", value="cron"),
                    questionary.Separator("── Config ──"),
                    questionary.Choice("Setup — Configure providers, MCP, theme", value="setup"),
                    questionary.Choice("Themes — Browse and switch themes", value="themes"),
                    questionary.Choice("Skills — View available skills", value="skills"),
                    questionary.Choice("Web Dashboard — Launch browser UI", value="web"),
                    questionary.Choice("Exit", value="exit"),
                ],
                instruction="(↑↓ arrow keys, Enter to select, Ctrl+C to quit)",
            ).ask()
        )

        if action is None or action == "exit":
            console.print(f"  [{theme.muted}]Goodbye![/]\n")
            break
        elif action == "chat":
            await _chat_async(None, None, "general", False)
            break
        elif action == "coder":
            await _chat_async(None, None, "coder", False)
            break
        elif action == "researcher":
            await _chat_async(None, None, "researcher", False)
            break
        elif action == "shell":
            await _chat_async(None, None, "shell", False)
            break
        elif action == "setup":
            from lifeclaw.config.setup import run_setup
            await run_setup()
            # After setup, refresh config and loop back to menu
            config = load_config()
        elif action == "themes":
            import questionary as q_themes
            theme_choices = [
                questionary.Choice(
                    f"{'●' if t.slug == config.theme else ' '} {t.name} ({t.slug})",
                    value=t.slug,
                )
                for t in ALL_THEMES.values()
            ]
            selected_theme = await asyncio.to_thread(
                lambda: q_themes.select(
                    "Select theme:",
                    choices=theme_choices,
                    default=config.theme,
                    instruction="(↑↓ to navigate, Enter to select)",
                ).ask()
            )
            if selected_theme and selected_theme in ALL_THEMES:
                config.theme = selected_theme
                save_config(config)
                theme = get_theme(config.theme)
                console.print(f"  [{theme.primary}]Theme switched to {theme.name}![/]")
                console.print(f"  [{theme.muted}]Some colors take effect on next restart.[/]")
            console.print()
        elif action == "skills":
            from lifeclaw.skills.manager import SkillsManager
            mgr = SkillsManager(config.skills_dir)
            for s in mgr.list_skills():
                console.print(f"  [{theme.accent}]{s.name}[/] [{theme.muted}]({s.category}) — {s.description}[/]")
            console.print()
        elif action == "gateway":
            await _gateway_async()
            break
        elif action == "research":
            import questionary as q2
            topic_input = await asyncio.to_thread(
                lambda: q2.text("Research topic:").ask()
            )
            if topic_input:
                await _research_async(topic_input)
            break
        elif action == "channels":
            from lifeclaw.channels.registry import _register_channels, CHANNEL_CLASSES
            _register_channels()
            for name in CHANNEL_CLASSES:
                ch_cfg = config.channels.get(name, {})
                enabled = ch_cfg.get("enabled", False)
                status_str = f"[{theme.success}]enabled[/]" if enabled else f"[{theme.muted}]disabled[/]"
                console.print(f"  {name:<15} {status_str}")
            console.print()
        elif action == "cron":
            from lifeclaw.cron.scheduler import CronScheduler
            scheduler = CronScheduler()
            jobs = scheduler.list_jobs()
            if not jobs:
                console.print(f"  [{theme.muted}]No cron jobs configured.[/]\n")
            else:
                for job in jobs:
                    console.print(f"  [{theme.accent}]{job.name}[/] ({job.schedule})")
            console.print()
        elif action == "web":
            await _web_async()
            break

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

    import random
    from lifeclaw.config.defaults import TIPS

    # Initialize provider (auto-detect Ollama model if needed)
    from lifeclaw.providers.registry import resolve_provider
    try:
        provider, model_name = resolve_provider(config, model_override)
    except ValueError as e:
        console.print(f"  [{theme.error}]{e}[/]")
        console.print(f"  [{theme.muted}]Run 'lifeclaw setup' to configure a provider.[/]")
        return

    # If using Ollama, auto-detect model if needed and verify it exists
    from lifeclaw.providers.ollama import OllamaProvider
    if isinstance(provider, OllamaProvider):
        try:
            available = await provider.list_models()
            if available:
                if model_name == "auto" or model_name not in available:
                    if model_name != "auto":
                        console.print(f"  [{theme.warning}]Model '{model_name}' not found in Ollama[/]")
                    model_name = available[0]
                    console.print(f"  [{theme.success}]Auto-selected: {model_name}[/] [{theme.muted}]({len(available)} models available, use /model to switch)[/]")
            elif model_name == "auto":
                console.print(f"  [{theme.warning}]No models in Ollama. Run: ollama pull qwen3.5:4b[/]")
                return
        except Exception as e:
            if model_name == "auto":
                console.print(f"  [{theme.error}]Could not connect to Ollama: {e}[/]")
                console.print(f"  [{theme.muted}]Start Ollama or run 'lifeclaw setup' to configure a cloud provider.[/]")
                return

    # Welcome banner
    console.print()
    mcp_count = len(config.mcp_servers)
    model_display = model_name

    left_col = Text()
    left_col.append("\n", style="")
    left_col.append("  LifeClaw", style=f"bold {theme.primary}")
    left_col.append(f" v{__version__}\n", style=f"{theme.muted}")
    left_col.append(f"\n", style="")
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
    console.print(Panel(
        left_col,
        title=f"[{theme.primary} bold]LifeClaw[/]",
        subtitle=f"[{theme.muted}]{tip}[/]",
        border_style=theme.primary,
        padding=(0, 1),
    ))

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

    # Prompt session with live / autocomplete
    history_file = get_config_dir() / "history"
    from lifeclaw.skills.manager import SkillsManager
    _skill_mgr = SkillsManager(config.skills_dir)
    _all_skill_names = [s.name for s in _skill_mgr.list_skills()]
    completer = SlashCompleter(skill_names=_all_skill_names)
    session = PromptSession(
        history=FileHistory(str(history_file)),
        completer=completer,
        complete_while_typing=True,
    )

    try:
        while True:
            # Styled input prompt with horizontal rules
            mode_color = {
                "coder": theme.accent,
                "general": theme.primary,
                "researcher": theme.secondary,
                "shell": theme.success,
            }.get(current_mode, theme.primary)

            try:
                console.print(Rule(style=theme.muted))
                user_input = await asyncio.to_thread(
                    session.prompt,
                    HTML(f'<style fg="{mode_color}" bold="true">\u276f </style>'),
                )
                console.print(Rule(style=theme.muted))
            except (EOFError, KeyboardInterrupt):
                break

            user_input = user_input.strip()
            if not user_input:
                continue
            if user_input.lower() in EXIT_COMMANDS:
                break

            # Handle slash commands
            if user_input == "/":
                # Arrow-key command picker with skills inline
                import questionary
                from lifeclaw.skills.manager import SkillsManager

                # Mode-relevant skills — show only what matters for current mode
                MODE_SKILLS = {
                    "coder": ["debugging", "tdd", "code-review", "pr-review", "frontend-design",
                              "mcp-builder", "git-expert", "feature-dev", "changelog-generator"],
                    "researcher": ["autonomous-research", "web-research", "literature-review",
                                   "research-paper", "content-research-writer", "seo"],
                    "shell": ["file-organizer", "cron-tasks", "channel-setup", "daily-routine"],
                    "general": ["docx", "xlsx", "pptx", "pdf", "business-analyst", "prd",
                                "tailored-resume-generator", "image-enhancer", "canvas-design"],
                }
                relevant_skills = MODE_SKILLS.get(current_mode, MODE_SKILLS["general"])

                cmd_choices = [
                    questionary.Choice("/mode — Switch mode", value="/mode"),
                    questionary.Choice("/model — Switch model", value="/model"),
                    questionary.Choice("/theme — Switch theme", value="/theme"),
                ]

                # Show mode-relevant skills
                mgr = SkillsManager(config.skills_dir)
                cmd_choices.append(questionary.Separator(f"── {current_mode} skills ──"))
                for sname in relevant_skills:
                    s = mgr.get(sname)
                    if s:
                        cmd_choices.append(questionary.Choice(sname, value=f"/skill {sname}"))
                cmd_choices.append(questionary.Choice("all skills...", value="/skill"))

                cmd_choices.append(questionary.Separator("── actions ──"))
                cmd_choices.extend([
                    questionary.Choice("/research — Autonomous paper pipeline", value="/research"),
                    questionary.Choice("/review — Code review", value="/review"),
                    questionary.Choice("/websearch — Search the web", value="/websearch"),
                    questionary.Choice("/spawn — Run sub-agent", value="/spawn"),
                    questionary.Choice("/mcp — MCP servers", value="/mcp"),
                ])
                cmd_choices.append(questionary.Separator("── session ──"))
                cmd_choices.extend([
                    questionary.Choice("/clear", value="/clear"),
                    questionary.Choice("/save", value="/save"),
                    questionary.Choice("/status", value="/status"),
                    questionary.Choice("/help", value="/help"),
                    questionary.Choice("(cancel)", value="__cancel__"),
                ])
                selected = await asyncio.to_thread(
                    lambda: questionary.select(
                        "Command:",
                        choices=cmd_choices,
                        instruction="(↑↓ arrow keys, Enter to select)",
                    ).ask()
                )
                if selected and selected != "__cancel__":
                    user_input = selected
                else:
                    continue

            if user_input.startswith("/"):
                # Detect combo skill shorthand: /docx+research → /skill docx+research
                if "+" in user_input and not user_input.startswith("/skill"):
                    combo = user_input.lstrip("/")
                    # Check if all parts are valid skill names
                    parts = [p.strip() for p in combo.split("+") if p.strip()]
                    all_skills = all(
                        any(s.name == p for s in _skill_mgr.list_skills())
                        for p in parts
                    )
                    if all_skills:
                        user_input = f"/skill {combo}"

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

                # Status line with economics
                renderer.finish()
                cost_footer = agent.economics.cost_footer
                console.print(f"  [{theme.muted}]{cost_footer}[/]")

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
        agent.economics.save_session()
        if ws_server:
            await ws_server.stop()
        await mcp.shutdown()
        cost_summary = agent.economics.summary
        console.print(f"\n  [{theme.muted}]Session saved. {cost_summary['cost_display']} spent across {cost_summary['calls']} calls. Goodbye![/]")


def _apply_mode(agent, mode_name: str):
    """Apply mode-specific system prompt addendum."""
    from lifeclaw.agent.loop import SYSTEM_PROMPT
    from lifeclaw.agent import tools as agent_tools
    mode = MODES.get(mode_name, MODES["general"])
    full_prompt = SYSTEM_PROMPT + mode["system_addendum"]
    agent.memory.add_system(full_prompt)
    # Coder mode auto-accepts all tool edits (like a coding IDE)
    agent_tools.auto_accept = (mode_name == "coder")


async def _handle_command(
    cmd: str, config, console: Console, theme, memory, agent,
    current_mode: str, status, mcp
):
    parts = cmd.split(maxsplit=1)
    command = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if command == "/help":
        table = Table(border_style=theme.muted, show_header=False, padding=(0, 2))
        table.add_column(style=f"{theme.accent}", min_width=20)
        table.add_column()
        table.add_row("[bold]Commands[/]", "")
        table.add_row("/", "Open command picker (or press Esc)")
        table.add_row("/mode [name]", "Switch mode (coder, general, researcher, shell)")
        table.add_row("/model [name]", "Switch model with live picker")
        table.add_row("/theme [name]", "Switch theme")
        table.add_row("/skill [name]", "Activate a skill (60+ available)")
        table.add_row("/skills", "List all available skills")
        table.add_row("/research [topic]", "23-stage autonomous research pipeline")
        table.add_row("/review", "PR-style code review of current directory")
        table.add_row("/mcp", "MCP servers and tools")
        table.add_row("/spawn [task]", "Run a sub-agent in parallel")
        table.add_row("/learn", "View cross-run learned lessons")
        table.add_row("/websearch [query]", "Search the web")
        table.add_row("/channels", "View messaging integrations")
        table.add_row("/cron", "View scheduled tasks")
        table.add_row("/costs", "Token economics for this session")
        table.add_row("/clear", "Clear conversation")
        table.add_row("/save", "Save session")
        table.add_row("/status", "Current status")
        table.add_row("", "")
        table.add_row("[bold]Navigation[/]", "")
        table.add_row("/", "Open command picker (mode-aware)")
        table.add_row("↑↓", "Navigate history and menus")
        table.add_row("Ctrl+C", "Cancel / Exit")
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
            # Support combo skills: /skill docx+research or /skill docx+web-research
            skill_names = [s.strip() for s in arg.replace("+", " ").replace(",", " ").split() if s.strip()]
            activated = []
            for sname in skill_names:
                skill = mgr.get(sname)
                if skill:
                    memory.add_system(skill.system_prompt)
                    activated.append(skill.name)
                else:
                    console.print(f"  [{theme.error}]Skill not found: {sname}[/]")
            if activated:
                if len(activated) > 1:
                    console.print(f"  [{theme.success}]Combo activated: {' + '.join(activated)}[/]")
                else:
                    skill = mgr.get(activated[0])
                    console.print(f"  [{theme.success}]Activated: {activated[0]}[/] [{theme.muted}]— {skill.description if skill else ''}[/]")
        else:
            # Arrow-key skill picker — mode-relevant skills first, then all
            import questionary

            # Which categories matter for the current mode
            MODE_CATEGORIES = {
                "coder": ["development", "testing", "workflow"],
                "researcher": ["research", "content", "writing"],
                "shell": ["system", "utility", "automation"],
                "general": ["documents", "business", "creative", "professional", "productivity"],
            }
            relevant_cats = set(MODE_CATEGORIES.get(current_mode, []))

            all_skills = mgr.list_skills()
            skill_choices = []

            # Relevant skills first
            relevant = [s for s in all_skills if s.category in relevant_cats]
            others = [s for s in all_skills if s.category not in relevant_cats]

            if relevant:
                skill_choices.append(questionary.Separator(f"── {current_mode} mode ──"))
                for s in relevant:
                    skill_choices.append(questionary.Choice(s.name, value=s.name))

            if others:
                skill_choices.append(questionary.Separator("── other ──"))
                for s in others:
                    skill_choices.append(questionary.Choice(s.name, value=s.name))

            selected = await asyncio.to_thread(
                lambda: questionary.select(
                    f"Skill ({len(all_skills)} available):",
                    choices=skill_choices,
                    instruction="(↑↓ navigate, Enter select)",
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

    elif command == "/spawn":
        if not arg:
            import questionary
            arg = await asyncio.to_thread(
                lambda: questionary.text("Task for sub-agent:").ask()
            )
        if arg:
            console.print(f"  [{theme.info}]Spawning sub-agent...[/]")
            from lifeclaw.agent.subagent import SubAgentManager, SubAgentTask
            # Create a lightweight sub-agent (shares provider, fresh memory)
            from lifeclaw.agent.loop import AgentLoop
            from lifeclaw.agent.memory import Memory as FreshMemory
            def _make_agent():
                return AgentLoop(
                    provider=agent.provider, model=agent.model,
                    memory=FreshMemory(),
                    max_iterations=agent.max_iterations,
                    temperature=agent.temperature,
                    max_tokens=agent.max_tokens,
                    mcp_tools=agent.mcp_tools,
                    mcp_executor=agent.mcp_executor,
                )
            mgr = SubAgentManager(_make_agent)
            task = mgr.spawn("user-task", arg)
            result = await mgr.execute(task.id)
            from rich.markdown import Markdown as RichMarkdown
            console.print(RichMarkdown(result))

    elif command == "/learn":
        from lifeclaw.agent.metaclaw import LearningBridge
        mc = LearningBridge()
        lessons = mc.lessons
        if not lessons:
            console.print(f"  [{theme.muted}]No lessons learned yet. Lessons are extracted from research runs and errors.[/]")
        else:
            console.print(f"  [bold {theme.primary}]Learned Lessons ({len(lessons)})[/]")
            for l in lessons[:15]:
                console.print(f"  [{theme.accent}]{l.category}[/] [{theme.muted}]— {l.trigger}[/]")
                console.print(f"    {l.content[:100]}")
            stats = mc.stats()
            console.print(f"\n  [{theme.muted}]Avg confidence: {stats['avg_confidence']:.2f}, Applied: {stats['total_applications']}x[/]")

    elif command == "/websearch":
        if not arg:
            import questionary
            arg = await asyncio.to_thread(
                lambda: questionary.text("Search query:").ask()
            )
        if arg:
            console.print(f"  [{theme.info}]Searching...[/]")
            from lifeclaw.websearch.search import WebSearchProvider
            searcher = WebSearchProvider()
            results = await searcher.search(arg)
            for i, r in enumerate(results, 1):
                console.print(f"  [{theme.accent}]{i}.[/] [{theme.primary}]{r.title}[/]")
                console.print(f"    [{theme.muted}]{r.url}[/]")
                console.print(f"    {r.snippet[:120]}")

    elif command == "/channels":
        from lifeclaw.channels.registry import _register_channels, CHANNEL_CLASSES
        _register_channels()
        console.print(f"\n  [bold {theme.primary}]Messaging Channels[/]\n")
        for ch_name in CHANNEL_CLASSES:
            ch_cfg = config.channels.get(ch_name, {})
            enabled = ch_cfg.get("enabled", False)
            st = f"[{theme.success}]enabled[/]" if enabled else f"[{theme.muted}]disabled[/]"
            console.print(f"  {ch_name:<15} {st}")
        console.print(f"\n  [{theme.muted}]Configure in ~/.lifeclaw/config.json, start with: lifeclaw gateway[/]\n")

    elif command == "/cron":
        from lifeclaw.cron.scheduler import CronScheduler
        scheduler = CronScheduler()
        jobs = scheduler.list_jobs()
        if not jobs:
            console.print(f"  [{theme.muted}]No cron jobs. Add to ~/.lifeclaw/cron/jobs.json[/]")
        else:
            for job in jobs:
                console.print(f"  [{theme.accent}]{job.name}[/] ({job.schedule}) — {job.prompt[:60]}")

    elif command == "/costs":
        s = agent.economics.summary
        console.print(f"  [bold {theme.primary}]Token Economics[/]")
        console.print(f"  [{theme.accent}]LLM Calls:[/] {s['calls']}")
        console.print(f"  [{theme.accent}]Input Tokens:[/] {s['input_tokens']:,}")
        console.print(f"  [{theme.accent}]Output Tokens:[/] {s['output_tokens']:,}")
        console.print(f"  [{theme.accent}]Total Cost:[/] {s['cost_display']}")

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
def gateway():
    """Start the gateway server — connects channels, cron, and agent as a service."""
    asyncio.run(_gateway_async())


async def _gateway_async():
    from lifeclaw.gateway.server import Gateway
    config = load_config()
    gw = Gateway(config)
    await gw.run_forever()


@app.command()
def channels():
    """List available and active channels."""
    console = _get_console()
    config = load_config()
    theme = get_theme(config.theme)
    from lifeclaw.channels.registry import _register_channels, CHANNEL_CLASSES
    _register_channels()
    console.print(f"\n  [bold {theme.primary}]Available Channels[/]\n")
    for name in CHANNEL_CLASSES:
        ch_cfg = config.channels.get(name, {})
        enabled = ch_cfg.get("enabled", False)
        status = f"[{theme.success}]enabled[/]" if enabled else f"[{theme.muted}]disabled[/]"
        console.print(f"  {name:<15} {status}")
    console.print(f"\n  [{theme.muted}]Configure in ~/.lifeclaw/config.json under 'channels'[/]")
    console.print(f"  [{theme.muted}]Start with: lifeclaw gateway[/]\n")


@app.command()
def cron():
    """List and manage scheduled tasks."""
    console = _get_console()
    config = load_config()
    theme = get_theme(config.theme)
    from lifeclaw.cron.scheduler import CronScheduler
    scheduler = CronScheduler()
    jobs = scheduler.list_jobs()
    if not jobs:
        console.print(f"\n  [{theme.muted}]No cron jobs configured.[/]")
        console.print(f"  [{theme.muted}]Use the agent to create cron jobs or add them to ~/.lifeclaw/cron/jobs.json[/]\n")
        return
    console.print(f"\n  [bold {theme.primary}]Scheduled Tasks[/]\n")
    for job in jobs:
        status = f"[{theme.success}]active[/]" if job.enabled else f"[{theme.muted}]paused[/]"
        console.print(f"  [{theme.accent}]{job.name}[/] ({job.schedule}) {status}")
        console.print(f"    [{theme.muted}]{job.prompt[:60]}...[/]")
        if job.last_run:
            console.print(f"    [{theme.muted}]Last run: {job.last_run}[/]")
    console.print()


@app.command()
def research(topic: str = typer.Argument(..., help="Research topic")):
    """Run the autonomous research pipeline on a topic."""
    asyncio.run(_research_async(topic))


async def _research_async(topic: str):
    config = load_config()
    theme = get_theme(config.theme)
    console = Console(theme=make_rich_theme(theme))

    from lifeclaw.providers.registry import resolve_provider
    from lifeclaw.agent.loop import AgentLoop
    from lifeclaw.agent.memory import Memory
    from lifeclaw.research.pipeline import ResearchPipeline, STAGES

    provider, model_name = resolve_provider(config)

    from lifeclaw.providers.ollama import OllamaProvider
    if isinstance(provider, OllamaProvider) and model_name == "auto":
        models = await provider.list_models()
        model_name = models[0] if models else "auto"

    memory = Memory()
    agent = AgentLoop(provider=provider, model=model_name, memory=memory)

    console.print(f"\n  [bold {theme.primary}]Research Pipeline (8 phases, 23 stages)[/]")
    console.print(f"  [{theme.muted}]Topic: {topic}[/]")
    console.print(f"  [{theme.muted}]Model: {model_name}[/]")
    console.print(f"  [{theme.muted}]Features: PIVOT/REFINE loops, multi-agent debate, real literature APIs, citation verification[/]\n")

    def _on_stage(idx, name, phase):
        console.print(f"  [{theme.accent}][Phase {phase}][/] [{theme.muted}]Stage {idx+1}/23: {name}[/]")

    pipeline = ResearchPipeline(agent_fn=agent.process, on_stage=_on_stage)
    run = await pipeline.run(topic)

    console.print(f"\n  [{theme.success}]Pipeline {run.status}![/]")
    console.print(f"  [{theme.muted}]Stages: {len(run.stages_completed)}/{len(STAGES)} | "
                  f"Pivots: {run.pivot_count} | Refines: {run.refine_count}[/]")
    console.print(f"  [{theme.muted}]Papers found: {len(run.papers_found)} | Output: {run.output_dir}[/]\n")


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

    # Also serve the static web dashboard
    from lifeclaw.server.static import serve_web
    http_port = config.web.port + 1
    await serve_web(config.web.host, http_port)

    console.print(f"  [{theme.success}]● WebSocket: ws://{config.web.host}:{config.web.port}[/]")
    console.print(f"  [{theme.success}]● Dashboard: http://{config.web.host}:{http_port}[/]")
    console.print(f"  [{theme.muted}]Press Ctrl+C to stop[/]")

    try:
        await asyncio.Future()
    except (KeyboardInterrupt, asyncio.CancelledError):
        await ws.stop()
        await mcp.shutdown()
