"""MCP (Model Context Protocol) client for LifeClaw."""

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from loguru import logger

from lifeclaw.config.schema import MCPServerConfig


class MCPClient:
    """Manages connections to MCP servers and exposes their tools."""

    def __init__(self):
        self._servers: dict[str, MCPServerConfig] = {}
        self._processes: dict[str, asyncio.subprocess.Process] = {}
        self._tools: dict[str, dict] = {}  # tool_name -> {server, definition}
        self._stdin: dict[str, asyncio.StreamWriter] = {}
        self._stdout: dict[str, asyncio.StreamReader] = {}
        self._request_id = 0

    async def connect(self, name: str, config: MCPServerConfig) -> bool:
        """Start an MCP server process and initialize it."""
        self._servers[name] = config
        try:
            env = {**os.environ, **config.env}
            proc = await asyncio.create_subprocess_exec(
                config.command,
                *config.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            self._processes[name] = proc
            self._stdin[name] = proc.stdin
            self._stdout[name] = proc.stdout

            # Initialize MCP protocol
            init_result = await self._send_request(name, "initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "lifeclaw", "version": "0.1.0"},
            })

            if init_result:
                # Send initialized notification
                await self._send_notification(name, "notifications/initialized", {})
                # List available tools
                tools_result = await self._send_request(name, "tools/list", {})
                if tools_result and "tools" in tools_result:
                    for tool in tools_result["tools"]:
                        tool_name = f"mcp_{name}_{tool['name']}"
                        self._tools[tool_name] = {
                            "server": name,
                            "original_name": tool["name"],
                            "definition": {
                                "type": "function",
                                "function": {
                                    "name": tool_name,
                                    "description": tool.get("description", ""),
                                    "parameters": tool.get("inputSchema", {
                                        "type": "object",
                                        "properties": {},
                                    }),
                                },
                            },
                        }
                    logger.info(f"MCP '{name}': {len(tools_result['tools'])} tools loaded")
                return True

        except Exception as e:
            logger.warning(f"MCP '{name}' failed to connect: {e}")
            return False
        return False

    async def _send_request(self, server: str, method: str, params: dict) -> dict | None:
        self._request_id += 1
        msg = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params,
        }
        return await self._send_and_receive(server, msg)

    async def _send_notification(self, server: str, method: str, params: dict) -> None:
        msg = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }
        writer = self._stdin.get(server)
        if not writer:
            return
        payload = json.dumps(msg)
        header = f"Content-Length: {len(payload)}\r\n\r\n"
        writer.write(header.encode() + payload.encode())
        await writer.drain()

    async def _send_and_receive(self, server: str, msg: dict) -> dict | None:
        writer = self._stdin.get(server)
        reader = self._stdout.get(server)
        if not writer or not reader:
            return None

        payload = json.dumps(msg)
        header = f"Content-Length: {len(payload)}\r\n\r\n"
        writer.write(header.encode() + payload.encode())
        await writer.drain()

        try:
            # Read response header
            header_line = await asyncio.wait_for(reader.readline(), timeout=30)
            header_str = header_line.decode().strip()
            if not header_str.startswith("Content-Length:"):
                return None
            content_length = int(header_str.split(":")[1].strip())

            # Read blank line
            await reader.readline()

            # Read body
            body = await asyncio.wait_for(reader.readexactly(content_length), timeout=30)
            response = json.loads(body.decode())
            return response.get("result")
        except (asyncio.TimeoutError, Exception) as e:
            logger.debug(f"MCP '{server}' response error: {e}")
            return None

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Call an MCP tool by its prefixed name."""
        tool_info = self._tools.get(tool_name)
        if not tool_info:
            return f"Unknown MCP tool: {tool_name}"

        server = tool_info["server"]
        original_name = tool_info["original_name"]

        result = await self._send_request(server, "tools/call", {
            "name": original_name,
            "arguments": arguments,
        })

        if result is None:
            return "MCP tool call failed."

        # Extract text content from result
        content = result.get("content", [])
        texts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                texts.append(item["text"])
            elif isinstance(item, str):
                texts.append(item)
        return "\n".join(texts) if texts else json.dumps(result)

    def get_tool_definitions(self) -> list[dict]:
        """Get all MCP tools in OpenAI tool format."""
        return [info["definition"] for info in self._tools.values()]

    async def connect_all(self, servers: dict[str, MCPServerConfig]) -> int:
        """Connect to all configured MCP servers. Returns count of successful connections."""
        tasks = [self.connect(name, cfg) for name, cfg in servers.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return sum(1 for r in results if r is True)

    async def shutdown(self) -> None:
        for name, proc in self._processes.items():
            try:
                proc.terminate()
                await asyncio.wait_for(proc.wait(), timeout=5)
            except Exception:
                proc.kill()
        self._processes.clear()
        self._tools.clear()
