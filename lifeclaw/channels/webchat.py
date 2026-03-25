"""WebChat channel — browser-based chat widget via WebSocket."""

import asyncio
import json

from loguru import logger

from lifeclaw.channels.base import BaseChannel, InboundMessage, MessageHandler, OutboundMessage


class WebChatChannel(BaseChannel):
    """WebSocket-based chat for browser integration."""

    name = "webchat"

    def __init__(self, config: dict, handler: MessageHandler):
        super().__init__(config, handler)
        self.host = config.get("host", "127.0.0.1")
        self.port = config.get("port", 3125)
        self._server = None
        self._clients: set = set()

    async def start(self) -> None:
        import websockets
        self._server = await websockets.serve(self._handle_ws, self.host, self.port)
        logger.info(f"WebChat: listening on ws://{self.host}:{self.port}")

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    async def send(self, message: OutboundMessage) -> None:
        data = json.dumps({"type": "response", "text": message.text})
        for ws in self._clients.copy():
            try:
                await ws.send(data)
            except Exception:
                self._clients.discard(ws)

    async def _handle_ws(self, ws, path=None) -> None:
        self._clients.add(ws)
        try:
            async for raw in ws:
                data = json.loads(raw)
                if data.get("type") == "message":
                    inbound = InboundMessage(
                        channel="webchat",
                        sender_id="webchat-user",
                        sender_name=data.get("name", "User"),
                        text=data.get("text", ""),
                    )
                    asyncio.create_task(self.on_message(inbound))
        except Exception:
            pass
        finally:
            self._clients.discard(ws)
