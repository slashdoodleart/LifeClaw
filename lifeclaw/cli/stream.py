"""Streaming output renderer with theme support for the terminal."""

import sys
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
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
    """Renders streaming LLM output with Rich formatting."""

    def __init__(self, theme: Theme, console: Console):
        self.theme = theme
        self.console = console
        self._buffer = ""
        self._live: Live | None = None

    def start(self):
        self._buffer = ""
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
        # Print final formatted version
        if self._buffer.strip():
            self.console.print()
            self.console.print(Markdown(self._buffer))

    def print_tool_call(self, name: str, args: dict):
        self.console.print(
            f"  [{self.theme.muted}]> tool:[/] [{self.theme.accent}]{name}[/]",
            highlight=False,
        )


class ThinkingSpinner:
    """Shows a spinner while the AI is thinking."""

    def __init__(self, theme: Theme, console: Console):
        self.theme = theme
        self.console = console
        self._live: Live | None = None

    def start(self, message: str = "Thinking"):
        spinner = Spinner("dots", text=Text(f" {message}...", style=f"{self.theme.secondary}"))
        self._live = Live(spinner, console=self.console, refresh_per_second=10, transient=True)
        self._live.start()

    def stop(self):
        if self._live:
            self._live.stop()
            self._live = None
