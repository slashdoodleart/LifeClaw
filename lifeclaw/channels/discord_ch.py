"""Discord channel integration using Bot API (lightweight, no discord.py dependency)."""

import asyncio
import json

import httpx
from loguru import logger

from lifeclaw.channels.base import BaseChannel, InboundMessage, MessageHandler, OutboundMessage


class DiscordChannel(BaseChannel):
    """Discord bot via HTTP API + Gateway websocket."""

    name = "discord"

    def __init__(self, config: dict, handler: MessageHandler):
        super().__init__(config, handler)
        self.token = config.get("token", "")
        self.base_url = "https://discord.com/api/v10"
        self.allow_from: list[str] = config.get("allowFrom", ["*"])
        self._running = False
        self._client: httpx.AsyncClient | None = None
        self._ws_task: asyncio.Task | None = None

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json",
        }

    async def start(self) -> None:
        if not self.token:
            logger.warning("Discord: no bot token configured")
            return
        self._client = httpx.AsyncClient(timeout=30, headers=self._headers)
        self._running = True
        # Get gateway URL and start WebSocket listener
        resp = await self._client.get(f"{self.base_url}/gateway/bot")
        gateway_url = resp.json().get("url", "wss://gateway.discord.gg")
        self._ws_task = asyncio.create_task(self._ws_loop(gateway_url))
        logger.info("Discord: connected")

    async def stop(self) -> None:
        self._running = False
        if self._ws_task:
            self._ws_task.cancel()
        if self._client:
            await self._client.aclose()

    async def send(self, message: OutboundMessage) -> None:
        if not self._client:
            return
        await self._client.post(
            f"{self.base_url}/channels/{message.recipient_id}/messages",
            json={"content": message.text},
        )

    async def _ws_loop(self, gateway_url: str) -> None:
        import websockets
        while self._running:
            try:
                async with websockets.connect(f"{gateway_url}/?v=10&encoding=json") as ws:
                    # Identify
                    hello = json.loads(await ws.recv())
                    heartbeat_interval = hello.get("d", {}).get("heartbeat_interval", 41250) / 1000
                    await ws.send(json.dumps({
                        "op": 2,
                        "d": {
                            "token": self.token,
                            "intents": 513,  # GUILDS + GUILD_MESSAGES
                            "properties": {"os": "linux", "browser": "lifeclaw", "device": "lifeclaw"},
                        },
                    }))
                    heartbeat_task = asyncio.create_task(self._heartbeat(ws, heartbeat_interval))
                    try:
                        async for raw in ws:
                            data = json.loads(raw)
                            if data.get("t") == "MESSAGE_CREATE":
                                msg = data["d"]
                                if msg.get("author", {}).get("bot"):
                                    continue
                                sender_id = msg["author"]["id"]
                                if self.allow_from != ["*"] and sender_id not in self.allow_from:
                                    continue
                                inbound = InboundMessage(
                                    channel="discord",
                                    sender_id=msg["channel_id"],
                                    sender_name=msg["author"].get("username", "User"),
                                    text=msg.get("content", ""),
                                    raw=msg,
                                )
                                asyncio.create_task(self.on_message(inbound))
                    finally:
                        heartbeat_task.cancel()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Discord WS error: {e}")
                await asyncio.sleep(5)

    async def _heartbeat(self, ws, interval: float) -> None:
        while True:
            await asyncio.sleep(interval)
            await ws.send(json.dumps({"op": 1, "d": None}))
