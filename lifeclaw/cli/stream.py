"""Streaming output renderer with theme support."""

import time
from typing import Any

from rich.columns import Columns
from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.rule import Rule
from rich.spinner import Spinner
from rich.syntax import Syntax
from rich.text import Text
from rich.theme import Theme as RichTheme

from lifeclaw.themes import Theme, get_theme


def make_rich_theme(theme: Theme) -> RichTheme:
    return RichTheme({
        "lc.primary": f"{theme.primary}",
        "lc.secondary": f"{theme.secondary}",
        "lc.accent": f"{theme.accent}",
        "lc.muted": f"{theme.muted}",
        "lc.success": f"{theme.success}",
        "lc.error": f"{theme.error}",
        "lc.warning": f"{theme.warning}",
        "lc.info": f"{theme.info}",
        "lc.user": f"bold {theme.primary}",
        "lc.ai": f"bold {theme.secondary}",
    })


class StreamRenderer:
    """Streaming renderer with tool call indicators."""

    def __init__(self, theme: Theme, console: Console):
        self.theme = theme
        self.console = console
        self._buffer = ""
        self._live: Live | None = None
        self._tool_count = 0
        self._start_time = 0.0

    def start(self):
        self._buffer = ""
        self._tool_count = 0
        self._start_time = time.monotonic()
        self._live = Live("", console=self.console, refresh_per_second=15, transient=True)
        self._live.start()

    def update(self, chunk: str):
        self._buffer += chunk
        if self._live:
            try:
                md = Markdown(self._buffer)
                self._live.update(md)
            except Exception:
                self._live.update(Text(self._buffer))

    def finish(self):
        if self._live:
            self._live.stop()
        if self._buffer.strip():
            self.console.print(Markdown(self._buffer))
        # Status line
        elapsed = time.monotonic() - self._start_time if self._start_time else 0
        status_parts = []
        if self._tool_count:
            status_parts.append(f"{self._tool_count} tool use{'s' if self._tool_count != 1 else ''}")
        status_parts.append(f"{elapsed:.1f}s")
        status = " · ".join(status_parts)
        self.console.print(f"  [{self.theme.muted}]{status}[/]")

    def print_tool_call(self, name: str, args: dict):
        self._tool_count += 1
        # Indented with bullet, tool name highlighted
        arg_summary = ""
        if "path" in args:
            arg_summary = f" [{self.theme.muted}]{args['path']}[/]"
        elif "command" in args:
            cmd = args["command"]
            if len(cmd) > 60:
                cmd = cmd[:57] + "..."
            arg_summary = f" [{self.theme.muted}]{cmd}[/]"
        elif "query" in args:
            arg_summary = f" [{self.theme.muted}]{args['query']}[/]"
        elif "pattern" in args:
            arg_summary = f" [{self.theme.muted}]{args['pattern']}[/]"

        self.console.print(
            f"  [{self.theme.accent}]●[/] [{self.theme.accent} bold]{name}[/]{arg_summary}",
            highlight=False,
        )

    def print_tool_result(self, name: str, result: str, success: bool = True):
        """Show abbreviated tool result."""
        lines = result.strip().split("\n")
        if len(lines) > 3:
            preview = "\n".join(lines[:3]) + f"\n  ... +{len(lines) - 3} lines"
        else:
            preview = result.strip()

        if len(preview) > 200:
            preview = preview[:197] + "..."

        color = self.theme.success if success else self.theme.error
        self.console.print(f"    [{color}]{'✓' if success else '✗'}[/] [{self.theme.muted}]{preview}[/]")


class ThinkingSpinner:
    """Thinking indicator with spinner."""

    def __init__(self, theme: Theme, console: Console):
        self.theme = theme
        self.console = console
        self._live: Live | None = None

    def start(self, message: str = "Thinking"):
        spinner_text = Text(f" {message}...", style=f"{self.theme.secondary}")
        spinner = Spinner("dots", text=spinner_text, style=f"{self.theme.secondary}")
        self._live = Live(spinner, console=self.console, refresh_per_second=10, transient=True)
        self._live.start()

    def update_message(self, message: str):
        if self._live:
            spinner_text = Text(f" {message}...", style=f"{self.theme.secondary}")
            spinner = Spinner("dots", text=spinner_text, style=f"{self.theme.secondary}")
            self._live.update(spinner)

    def stop(self):
        if self._live:
            self._live.stop()
            self._live = None


class StatusLine:
    """Persistent status line at bottom of terminal."""

    def __init__(self, theme: Theme, console: Console):
        self.theme = theme
        self.console = console
        self.mode = "general"
        self.model = ""
        self.provider = ""
        self.mcp_count = 0
        self.token_count = 0

    def render(self):
        """Print a status bar."""
        mode_colors = {
            "coder": self.theme.accent,
            "general": self.theme.primary,
            "researcher": self.theme.secondary,
            "shell": self.theme.success,
        }
        mode_color = mode_colors.get(self.mode, self.theme.primary)

        parts = [
            f"[{mode_color} bold]{self.mode}[/]",
            f"[{self.theme.muted}]{self.model}[/]",
        ]
        if self.mcp_count:
            parts.append(f"[{self.theme.muted}]{self.mcp_count} MCP[/]")
        if self.token_count:
            parts.append(f"[{self.theme.muted}]~{self.token_count} tokens[/]")

        bar = f"  [{self.theme.muted}]│[/] ".join(parts)
        self.console.print(f"  {bar}")
