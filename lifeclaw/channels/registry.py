"""Channel registry — discovers and manages all channel integrations."""

import asyncio
from typing import Any

from loguru import logger

from lifeclaw.channels.base import BaseChannel, MessageHandler


# Channel name -> class mapping
CHANNEL_CLASSES: dict[str, type[BaseChannel]] = {}


def _register_channels():
    """Register all built-in channel classes."""
    global CHANNEL_CLASSES
    from lifeclaw.channels.telegram import TelegramChannel
    from lifeclaw.channels.discord_ch import DiscordChannel
    from lifeclaw.channels.slack import SlackChannel
    from lifeclaw.channels.webchat import WebChatChannel

    CHANNEL_CLASSES = {
        "telegram": TelegramChannel,
        "discord": DiscordChannel,
        "slack": SlackChannel,
        "webchat": WebChatChannel,
    }


class ChannelManager:
    """Manages all active channel connections."""

    def __init__(self, channels_config: dict[str, dict], handler: MessageHandler):
        _register_channels()
        self.handler = handler
        self.channels_config = channels_config
        self.active: dict[str, BaseChannel] = {}

    async def start_all(self) -> int:
        """Start all enabled channels. Returns count of started channels."""
        started = 0
        for name, cfg in self.channels_config.items():
            if not cfg.get("enabled", False):
                continue
            cls = CHANNEL_CLASSES.get(name)
            if not cls:
                logger.warning(f"Unknown channel: {name}")
                continue
            try:
                channel = cls(cfg, self.handler)
                await channel.start()
                self.active[name] = channel
                started += 1
                logger.info(f"Channel started: {name}")
            except Exception as e:
                logger.error(f"Failed to start channel {name}: {e}")
        return started

    async def stop_all(self) -> None:
        for name, channel in self.active.items():
            try:
                await channel.stop()
            except Exception as e:
                logger.error(f"Error stopping channel {name}: {e}")
        self.active.clear()

    def list_channels(self) -> list[str]:
        return list(CHANNEL_CLASSES.keys())

    def active_channels(self) -> list[str]:
        return list(self.active.keys())
