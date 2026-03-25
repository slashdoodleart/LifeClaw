"""Anthropic provider for Claude models."""

import json
from typing import AsyncIterator

import anthropic

from lifeclaw.providers.base import (
    LLMMessage,
    LLMProvider,
    LLMResponse,
    StreamChunk,
    ToolCall,
)


def _to_anthropic_messages(messages: list[LLMMessage]) -> tuple[str | None, list[dict]]:
    """Convert to Anthropic format. Returns (system_prompt, messages)."""
    system = None
    out = []
    for m in messages:
        if m.role == "system":
            system = m.content
            continue
        if m.role == "tool":
            out.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": m.tool_call_id,
                    "content": m.content or "",
                }],
            })
            continue

        content: list[dict] = []
        if m.content:
            content.append({"type": "text", "text": m.content})
        for tc in m.tool_calls:
            content.append({
                "type": "tool_use",
                "id": tc.id,
                "name": tc.name,
                "input": tc.arguments,
            })

        out.append({"role": m.role, "content": content or m.content or ""})
    return system, out


def _tools_to_anthropic(tools: list[dict] | None) -> list[dict] | None:
    if not tools:
        return None
    out = []
    for t in tools:
        fn = t.get("function", t)
        out.append({
            "name": fn["name"],
            "description": fn.get("description", ""),
            "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
        })
    return out


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, api_key: str):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)

    async def chat(
        self,
        messages: list[LLMMessage],
        tools: list[dict] | None = None,
        temperature: float = 0.1,
        max_tokens: int = 8192,
        stream: bool = False,
        model: str | None = None,
    ) -> LLMResponse:
        system, msgs = _to_anthropic_messages(messages)
        kwargs: dict = {
            "model": model or "claude-sonnet-4-20250514",
            "messages": msgs,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system:
            kwargs["system"] = system
        anthropic_tools = _tools_to_anthropic(tools)
        if anthropic_tools:
            kwargs["tools"] = anthropic_tools

        resp = await self.client.messages.create(**kwargs)

        content_text = ""
        tool_calls = []
        for block in resp.content:
            if block.type == "text":
                content_text += block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(id=block.id, name=block.name, arguments=block.input)
                )

        return LLMResponse(
            content=content_text or None,
            tool_calls=tool_calls,
            finish_reason="tool_use" if tool_calls else resp.stop_reason or "stop",
            usage={
                "prompt_tokens": resp.usage.input_tokens,
                "completion_tokens": resp.usage.output_tokens,
            },
        )

    async def chat_stream(
        self,
        messages: list[LLMMessage],
        tools: list[dict] | None = None,
        temperature: float = 0.1,
        max_tokens: int = 8192,
        model: str | None = None,
    ) -> AsyncIterator[StreamChunk]:
        system, msgs = _to_anthropic_messages(messages)
        kwargs: dict = {
            "model": model or "claude-sonnet-4-20250514",
            "messages": msgs,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system:
            kwargs["system"] = system
        anthropic_tools = _tools_to_anthropic(tools)
        if anthropic_tools:
            kwargs["tools"] = anthropic_tools

        async with self.client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield StreamChunk(delta=text)
            yield StreamChunk(finish_reason="stop")

    async def list_models(self) -> list[str]:
        return [
            "claude-opus-4-20250514",
            "claude-sonnet-4-20250514",
            "claude-haiku-4-20250514",
        ]
