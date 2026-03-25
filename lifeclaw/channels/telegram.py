"""Telegram channel integration using Bot API."""

import asyncio
import json
from typing import Any

import httpx
from loguru import logger

from lifeclaw.channels.base import BaseChannel, InboundMessage, MessageHandler, OutboundMessage


class TelegramChannel(BaseChannel):
    """Telegram bot integration via polling."""

    name = "telegram"

    def __init__(self, config: dict, handler: MessageHandler):
        super().__init__(config, handler)
        self.token = config.get("token", "")
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.allow_from: list[str] = config.get("allowFrom", ["*"])
        self._offset = 0
        self._running = False
        self._client: httpx.AsyncClient | None = None
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if not self.token:
            logger.warning("Telegram: no bot token configured")
            return
        self._client = httpx.AsyncClient(timeout=30)
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        me = await self._api("getMe")
        bot_name = me.get("result", {}).get("username", "unknown")
        logger.info(f"Telegram: connected as @{bot_name}")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
        if self._client:
            await self._client.aclose()

    async def send(self, message: OutboundMessage) -> None:
        await self._api("sendMessage", {
            "chat_id": message.recipient_id,
            "text": message.text,
            "parse_mode": "Markdown",
            **({"reply_to_message_id": message.reply_to} if message.reply_to else {}),
        })

    async def _api(self, method: str, data: dict | None = None) -> dict:
        if not self._client:
            return {}
        resp = await self._client.post(f"{self.base_url}/{method}", json=data or {})
        return resp.json()

    async def _poll_loop(self) -> None:
        while self._running:
            try:
                updates = await self._api("getUpdates", {
                    "offset": self._offset,
                    "timeout": 20,
                })
                for update in updates.get("result", []):
                    self._offset = update["update_id"] + 1
                    msg = update.get("message", {})
                    text = msg.get("text", "")
                    if not text:
                        continue
                    sender = msg.get("from", {})
                    sender_id = str(sender.get("id", ""))
                    if self.allow_from != ["*"] and sender_id not in self.allow_from:
                        continue
                    inbound = InboundMessage(
                        channel="telegram",
                        sender_id=str(msg.get("chat", {}).get("id", "")),
                        sender_name=sender.get("first_name", "User"),
                        text=text,
                        thread_id=str(msg.get("message_thread_id", "")),
                        reply_to=str(msg.get("message_id", "")),
                        raw=msg,
                    )
                    asyncio.create_task(self.on_message(inbound))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Telegram poll error: {e}")
                await asyncio.sleep(5)
