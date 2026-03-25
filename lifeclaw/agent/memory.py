"""Simple conversation memory for LifeClaw agent."""

import json
from pathlib import Path
from datetime import datetime

from lifeclaw.providers.base import LLMMessage


class Memory:
    """Manages conversation history with persistence."""

    def __init__(self, session_dir: Path | None = None):
        self.messages: list[LLMMessage] = []
        self.session_dir = session_dir
        if session_dir:
            session_dir.mkdir(parents=True, exist_ok=True)

    def add(self, message: LLMMessage) -> None:
        self.messages.append(message)

    def add_system(self, content: str) -> None:
        # Only one system message, always first
        if self.messages and self.messages[0].role == "system":
            self.messages[0].content = content
        else:
            self.messages.insert(0, LLMMessage(role="system", content=content))

    def add_user(self, content: str) -> None:
        self.add(LLMMessage(role="user", content=content))

    def add_assistant(self, content: str, tool_calls=None) -> None:
        self.add(LLMMessage(role="assistant", content=content, tool_calls=tool_calls or []))

    def add_tool_result(self, tool_call_id: str, content: str) -> None:
        self.add(LLMMessage(role="tool", content=content, tool_call_id=tool_call_id))

    def get_messages(self, max_tokens: int | None = None) -> list[LLMMessage]:
        return list(self.messages)

    def clear(self) -> None:
        system = None
        if self.messages and self.messages[0].role == "system":
            system = self.messages[0]
        self.messages.clear()
        if system:
            self.messages.append(system)

    def save_session(self) -> None:
        if not self.session_dir:
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.session_dir / f"session_{ts}.json"
        data = []
        for m in self.messages:
            entry = {"role": m.role, "content": m.content}
            if m.tool_calls:
                entry["tool_calls"] = [
                    {"id": tc.id, "name": tc.name, "arguments": tc.arguments}
                    for tc in m.tool_calls
                ]
            if m.tool_call_id:
                entry["tool_call_id"] = m.tool_call_id
            data.append(entry)
        path.write_text(json.dumps(data, indent=2))

    @property
    def token_estimate(self) -> int:
        """Rough token estimate (4 chars per token)."""
        total = sum(len(m.content or "") for m in self.messages)
        return total // 4
