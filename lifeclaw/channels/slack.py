"""Slack channel integration using Socket Mode (app-level token)."""

import asyncio
import json

import httpx
from loguru import logger

from lifeclaw.channels.base import BaseChannel, InboundMessage, MessageHandler, OutboundMessage


class SlackChannel(BaseChannel):
    """Slack bot via Socket Mode for real-time events."""

    name = "slack"

    def __init__(self, config: dict, handler: MessageHandler):
        super().__init__(config, handler)
        self.bot_token = config.get("botToken", "")
        self.app_token = config.get("appToken", "")
        self.allow_from: list[str] = config.get("allowFrom", ["*"])
        self._running = False
        self._client: httpx.AsyncClient | None = None
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if not self.bot_token or not self.app_token:
            logger.warning("Slack: missing botToken or appToken")
            return
        self._client = httpx.AsyncClient(timeout=30)
        self._running = True
        self._task = asyncio.create_task(self._socket_mode_loop())
        logger.info("Slack: connected via Socket Mode")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
        if self._client:
            await self._client.aclose()

    async def send(self, message: OutboundMessage) -> None:
        if not self._client:
            return
        await self._client.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {self.bot_token}"},
            json={
                "channel": message.recipient_id,
                "text": message.text,
                **({"thread_ts": message.thread_id} if message.thread_id else {}),
            },
        )

    async def _socket_mode_loop(self) -> None:
        import websockets
        while self._running:
            try:
                resp = await self._client.post(
                    "https://slack.com/api/apps.connections.open",
                    headers={"Authorization": f"Bearer {self.app_token}"},
                )
                ws_url = resp.json().get("url", "")
                if not ws_url:
                    logger.error("Slack: failed to get WebSocket URL")
                    await asyncio.sleep(10)
                    continue
                async with websockets.connect(ws_url) as ws:
                    async for raw in ws:
                        data = json.loads(raw)
                        # Acknowledge envelope
                        if "envelope_id" in data:
                            await ws.send(json.dumps({"envelope_id": data["envelope_id"]}))
                        payload = data.get("payload", {})
                        event = payload.get("event", {})
                        if event.get("type") == "message" and not event.get("bot_id"):
                            user_id = event.get("user", "")
                            if self.allow_from != ["*"] and user_id not in self.allow_from:
                                continue
                            inbound = InboundMessage(
                                channel="slack",
                                sender_id=event.get("channel", ""),
                                sender_name=user_id,
                                text=event.get("text", ""),
                                thread_id=event.get("thread_ts"),
                                raw=event,
                            )
                            asyncio.create_task(self.on_message(inbound))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Slack WS error: {e}")
                await asyncio.sleep(5)
