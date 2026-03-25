"""Core agent loop - processes user input through LLM with tool calls."""

import asyncio
from typing import AsyncIterator, Callable

from loguru import logger

from lifeclaw.agent.memory import Memory
from lifeclaw.agent.tools import TOOL_DEFINITIONS, execute_tool
from lifeclaw.providers.base import LLMMessage, LLMProvider, LLMResponse, StreamChunk


SYSTEM_PROMPT = """You are LifeClaw, an elite AI coding assistant and general-purpose agent.

CORE IDENTITY:
You are a hybrid between a surgical code editor and a versatile personal assistant.
Your primary strength is software engineering, but you handle any task thrown at you.

CODING PRINCIPLES:
- Read before you write. Always understand existing code before modifying it.
- Prefer minimal, targeted edits over rewrites.
- Write clean, idiomatic code in the language and style of the existing codebase.
- Explain your reasoning briefly before making changes.
- Run tests and verify your work when possible.
- Never introduce security vulnerabilities (injection, XSS, etc).
- Keep solutions simple. Don't over-engineer or add unnecessary abstractions.

TOOL USAGE:
- Use read_file to understand code before editing.
- Use search_files and search_content to explore codebases.
- Use write_file for creating or rewriting files.
- Use run_command for building, testing, git operations, and system tasks.
- Use MCP tools when available for extended capabilities.

GENERAL TASKS:
Beyond coding, you help with research, writing, system administration, data analysis,
planning, and any task the user needs. Adapt your approach to the task at hand.

Be concise. Be precise. Ship working code.
"""


class AgentLoop:
    """Runs the agent loop: user -> LLM -> tool calls -> LLM -> response."""

    def __init__(
        self,
        provider: LLMProvider,
        model: str,
        memory: Memory,
        max_iterations: int = 40,
        temperature: float = 0.1,
        max_tokens: int = 8192,
        mcp_tools: list[dict] | None = None,
        mcp_executor: Callable | None = None,
        on_stream: Callable[[str], None] | None = None,
        on_tool_call: Callable[[str, dict], None] | None = None,
    ):
        self.provider = provider
        self.model = model
        self.memory = memory
        self.max_iterations = max_iterations
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.mcp_tools = mcp_tools or []
        self.mcp_executor = mcp_executor
        self.on_stream = on_stream
        self.on_tool_call = on_tool_call

        # Set system prompt
        self.memory.add_system(SYSTEM_PROMPT)

    def _get_tools(self) -> list[dict]:
        return TOOL_DEFINITIONS + self.mcp_tools

    async def process(self, user_input: str) -> str:
        """Process user input and return final response."""
        self.memory.add_user(user_input)

        for iteration in range(self.max_iterations):
            try:
                response = await self.provider.chat(
                    messages=self.memory.get_messages(),
                    tools=self._get_tools(),
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    model=self.model,
                )
            except Exception as e:
                error_msg = f"Provider error: {e}"
                logger.error(error_msg)
                return error_msg

            if not response.has_tool_calls:
                # Final text response
                text = response.content or ""
                self.memory.add_assistant(text)
                return text

            # Handle tool calls
            self.memory.add_assistant(response.content, tool_calls=response.tool_calls)

            for tc in response.tool_calls:
                if self.on_tool_call:
                    self.on_tool_call(tc.name, tc.arguments)

                # Check if it's an MCP tool
                mcp_tool_names = {t["function"]["name"] for t in self.mcp_tools}
                if tc.name in mcp_tool_names and self.mcp_executor:
                    result = await self.mcp_executor(tc.name, tc.arguments)
                else:
                    result = await execute_tool(tc.name, tc.arguments)

                self.memory.add_tool_result(tc.id, result)

        return "Reached maximum iterations. Please refine your request."

    async def process_stream(self, user_input: str) -> AsyncIterator[str]:
        """Process with streaming - yields text chunks."""
        self.memory.add_user(user_input)

        for iteration in range(self.max_iterations):
            collected = ""
            try:
                async for chunk in self.provider.chat_stream(
                    messages=self.memory.get_messages(),
                    tools=self._get_tools(),
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    model=self.model,
                ):
                    if chunk.delta:
                        collected += chunk.delta
                        yield chunk.delta
            except Exception as e:
                yield f"\nProvider error: {e}"
                return

            # After streaming, check if there were tool calls by doing a non-stream call
            # (Streaming with tool calls is complex; fall back to non-stream for tool rounds)
            if not collected.strip():
                # Likely a tool call round - use non-stream
                response = await self.provider.chat(
                    messages=self.memory.get_messages(),
                    tools=self._get_tools(),
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    model=self.model,
                )
                if response.has_tool_calls:
                    self.memory.add_assistant(response.content, tool_calls=response.tool_calls)
                    for tc in response.tool_calls:
                        if self.on_tool_call:
                            self.on_tool_call(tc.name, tc.arguments)
                        mcp_tool_names = {t["function"]["name"] for t in self.mcp_tools}
                        if tc.name in mcp_tool_names and self.mcp_executor:
                            result = await self.mcp_executor(tc.name, tc.arguments)
                        else:
                            result = await execute_tool(tc.name, tc.arguments)
                        self.memory.add_tool_result(tc.id, result)
                        yield f"\n[tool: {tc.name}]\n"
                    continue
                else:
                    text = response.content or ""
                    self.memory.add_assistant(text)
                    yield text
                    return
            else:
                self.memory.add_assistant(collected)
                return
