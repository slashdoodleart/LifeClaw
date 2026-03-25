"""Base channel interface for all messaging platforms."""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine


@dataclass
class InboundMessage:
    """A message received from a channel."""
    channel: str  # e.g. "telegram", "discord"
    sender_id: str
    sender_name: str
    text: str
    media_url: str | None = None
    media_type: str | None = None  # "image", "audio", "video", "file"
    reply_to: str | None = None
    thread_id: str | None = None
    raw: dict = field(default_factory=dict)


@dataclass
class OutboundMessage:
    """A message to send back through a channel."""
    text: str
    channel: str
    recipient_id: str
    thread_id: str | None = None
    media_url: str | None = None
    media_type: str | None = None
    reply_to: str | None = None


# Callback type: receives InboundMessage, returns response text
MessageHandler = Callable[[InboundMessage], Coroutine[Any, Any, str]]


class BaseChannel(ABC):
    """Abstract base for all messaging channel integrations."""

    name: str = "base"
    enabled: bool = False

    def __init__(self, config: dict, handler: MessageHandler):
        self.config = config
        self.handler = handler
        self.enabled = config.get("enabled", False)

    @abstractmethod
    async def start(self) -> None:
        """Start listening for messages."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop the channel gracefully."""
        ...

    @abstractmethod
    async def send(self, message: OutboundMessage) -> None:
        """Send a message through the channel."""
        ...

    async def on_message(self, msg: InboundMessage) -> None:
        """Process an incoming message through the agent handler."""
        try:
            response = await self.handler(msg)
            await self.send(OutboundMessage(
                text=response,
                channel=self.name,
                recipient_id=msg.sender_id,
                thread_id=msg.thread_id,
            ))
        except Exception as e:
            await self.send(OutboundMessage(
                text=f"Error processing message: {e}",
                channel=self.name,
                recipient_id=msg.sender_id,
            ))
