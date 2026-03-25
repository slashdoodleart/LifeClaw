"""Gateway server — runs the agent as a service with channels, cron, and web search."""

import asyncio
from typing import Any

from loguru import logger

from lifeclaw.agent.loop import AgentLoop
from lifeclaw.agent.memory import Memory
from lifeclaw.channels.base import InboundMessage
from lifeclaw.channels.registry import ChannelManager
from lifeclaw.config.loader import load_config
from lifeclaw.config.schema import Config, get_config_dir
from lifeclaw.cron.scheduler import CronScheduler
from lifeclaw.mcp.client import MCPClient
from lifeclaw.providers.registry import resolve_provider
from lifeclaw.websearch.search import WebSearchProvider


class Gateway:
    """Central gateway that manages all LifeClaw services."""

    def __init__(self, config: Config | None = None):
        self.config = config or load_config()
        self._agent: AgentLoop | None = None
        self._mcp: MCPClient | None = None
        self._channels: ChannelManager | None = None
        self._cron: CronScheduler | None = None
        self._web_search: WebSearchProvider | None = None

    async def start(self) -> None:
        """Start all gateway services."""
        logger.info("Gateway starting...")

        # 1. Resolve provider
        provider, model_name = resolve_provider(self.config)

        # Handle Ollama auto model
        from lifeclaw.providers.ollama import OllamaProvider
        if isinstance(provider, OllamaProvider) and model_name == "auto":
            try:
                models = await provider.list_models()
                if models:
                    model_name = models[0]
                else:
                    logger.error("No Ollama models available")
                    return
            except Exception as e:
                logger.error(f"Ollama not available: {e}")
                return

        logger.info(f"Model: {model_name}")

        # 2. MCP
        self._mcp = MCPClient()
        if self.config.mcp_servers:
            connected = await self._mcp.connect_all(self.config.mcp_servers)
            logger.info(f"MCP: {connected}/{len(self.config.mcp_servers)} servers connected")

        # 3. Web search
        web_search_config = {}  # Could come from config.tools.web.search in future
        self._web_search = WebSearchProvider(web_search_config)

        # 4. Agent
        session_dir = get_config_dir() / "sessions"
        memory = Memory(session_dir=session_dir)
        self._agent = AgentLoop(
            provider=provider,
            model=model_name,
            memory=memory,
            max_iterations=self.config.agent.max_iterations,
            temperature=self.config.agent.temperature,
            max_tokens=self.config.agent.max_tokens,
            mcp_tools=self._mcp.get_tool_definitions(),
            mcp_executor=self._mcp.call_tool,
        )

        # 5. Channels
        channels_config = getattr(self.config, "channels", {})
        if isinstance(channels_config, dict) and channels_config:
            self._channels = ChannelManager(channels_config, self._handle_channel_message)
            started = await self._channels.start_all()
            logger.info(f"Channels: {started} active")
        else:
            logger.info("Channels: none configured")

        # 6. Cron
        self._cron = CronScheduler()
        if self._cron.list_jobs():
            await self._cron.start(self._agent.process)
            logger.info(f"Cron: {len(self._cron.list_jobs())} jobs")

        logger.info("Gateway running. Press Ctrl+C to stop.")

    async def stop(self) -> None:
        """Gracefully shut down all services."""
        logger.info("Gateway shutting down...")
        if self._cron:
            await self._cron.stop()
        if self._channels:
            await self._channels.stop_all()
        if self._mcp:
            await self._mcp.shutdown()
        logger.info("Gateway stopped.")

    async def _handle_channel_message(self, msg: InboundMessage) -> str:
        """Route an inbound channel message to the agent."""
        if not self._agent:
            return "Agent not initialized"
        prefix = f"[{msg.channel}:{msg.sender_name}] "
        return await self._agent.process(prefix + msg.text)

    async def run_forever(self) -> None:
        """Start and run until interrupted."""
        await self.start()
        try:
            await asyncio.Future()  # Block forever
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass
        finally:
            await self.stop()
