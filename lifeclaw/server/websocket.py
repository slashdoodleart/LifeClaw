"""WebSocket server bridging LifeClaw backend to the web dashboard."""

import asyncio
import json
from typing import Any, Callable

import websockets
from loguru import logger

from lifeclaw.config.schema import Config
from lifeclaw.themes import ALL_THEMES, get_theme


class WebSocketServer:
    """Serves the LifeClaw web dashboard via WebSocket."""

    def __init__(self, config: Config, on_message: Callable | None = None):
        self.config = config
        self.on_message = on_message
        self.clients: set = set()
        self._server = None

    async def start(self):
        host = self.config.web.host
        port = self.config.web.port
        self._server = await websockets.serve(self._handler, host, port)
        logger.info(f"WebSocket server started on ws://{host}:{port}")

    async def _handler(self, websocket):
        self.clients.add(websocket)
        try:
            # Send initial state
            await websocket.send(json.dumps({
                "type": "init",
                "data": {
                    "theme": self.config.theme,
                    "themes": {k: {"name": v.name, "slug": v.slug, "web_primary": v.web_primary,
                                    "web_secondary": v.web_secondary, "web_accent": v.web_accent,
                                    "web_bg": v.web_bg, "web_surface": v.web_surface,
                                    "web_text": v.web_text, "web_muted": v.web_muted}
                               for k, v in ALL_THEMES.items()},
                    "model": self.config.agent.model,
                    "provider": self.config.agent.provider,
                    "mcp_servers": list(self.config.mcp_servers.keys()),
                },
            }))

            async for raw in websocket:
                msg = json.loads(raw)
                await self._handle_message(websocket, msg)

        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.discard(websocket)

    async def _handle_message(self, websocket, msg: dict):
        msg_type = msg.get("type", "")

        if msg_type == "chat":
            user_input = msg.get("content", "")
            if self.on_message:
                # Callback processes and returns response
                response = await self.on_message(user_input)
                await websocket.send(json.dumps({
                    "type": "response",
                    "content": response,
                }))

        elif msg_type == "get_config":
            await websocket.send(json.dumps({
                "type": "config",
                "data": self.config.model_dump(),
            }))

        elif msg_type == "set_theme":
            self.config.theme = msg.get("theme", "aurora")
            from lifeclaw.config.loader import save_config
            save_config(self.config)
            await self._broadcast({
                "type": "theme_changed",
                "theme": self.config.theme,
            })

        elif msg_type == "get_skills":
            from lifeclaw.skills.manager import SkillsManager
            mgr = SkillsManager(self.config.skills_dir)
            skills = [{"name": s.name, "description": s.description, "category": s.category}
                      for s in mgr.list_skills()]
            await websocket.send(json.dumps({"type": "skills", "data": skills}))

    async def _broadcast(self, msg: dict):
        data = json.dumps(msg)
        for client in self.clients:
            try:
                await client.send(data)
            except Exception:
                pass

    async def broadcast_stream(self, chunk: str):
        await self._broadcast({"type": "stream", "content": chunk})

    async def stop(self):
        if self._server:
            self._server.close()
            await self._server.wait_closed()
