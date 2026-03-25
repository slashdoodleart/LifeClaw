"""OpenAI-compatible provider - works with OpenAI, OpenRouter, DeepSeek, Groq, etc."""

import json
from typing import AsyncIterator

from openai import AsyncOpenAI

from lifeclaw.providers.base import (
    LLMMessage,
    LLMProvider,
    LLMResponse,
    StreamChunk,
    ToolCall,
)

# Provider presets: name -> (base_url, env_key_name)
PRESETS = {
    "openai": ("https://api.openai.com/v1", "OPENAI_API_KEY"),
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
    "deepseek": ("https://api.deepseek.com/v1", "DEEPSEEK_API_KEY"),
    "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai/", "GEMINI_API_KEY"),
    "custom": (None, None),
}


def _to_openai_messages(messages: list[LLMMessage]) -> list[dict]:
    out = []
    for m in messages:
        msg: dict = {"role": m.role}
        if m.content is not None:
            msg["content"] = m.content
        if m.tool_calls:
            msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": json.dumps(tc.arguments),
                    },
                }
                for tc in m.tool_calls
            ]
        if m.tool_call_id:
            msg["tool_call_id"] = m.tool_call_id
        if m.name:
            msg["name"] = m.name
        out.append(msg)
    return out


class OpenAICompatProvider(LLMProvider):
    def __init__(self, provider_name: str, api_key: str, api_base: str | None = None,
                 extra_headers: dict | None = None):
        self.name = provider_name
        preset_base, _ = PRESETS.get(provider_name, (None, None))
        base = api_base or preset_base or "https://api.openai.com/v1"

        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base,
            default_headers=extra_headers,
        )

    async def chat(
        self,
        messages: list[LLMMessage],
        tools: list[dict] | None = None,
        temperature: float = 0.1,
        max_tokens: int = 8192,
        stream: bool = False,
        model: str | None = None,
    ) -> LLMResponse:
        kwargs: dict = {
            "model": model or "gpt-4o-mini",
            "messages": _to_openai_messages(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools

        resp = await self.client.chat.completions.create(**kwargs)
        choice = resp.choices[0]
        msg = choice.message

        tool_calls = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                args = tc.function.arguments
                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=json.loads(args) if isinstance(args, str) else args,
                    )
                )

        return LLMResponse(
            content=msg.content,
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason or "stop",
            usage={
                "prompt_tokens": resp.usage.prompt_tokens if resp.usage else 0,
                "completion_tokens": resp.usage.completion_tokens if resp.usage else 0,
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
        kwargs: dict = {
            "model": model or "gpt-4o-mini",
            "messages": _to_openai_messages(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        if tools:
            kwargs["tools"] = tools

        stream = await self.client.chat.completions.create(**kwargs)
        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            yield StreamChunk(
                delta=delta.content or "",
                finish_reason=chunk.choices[0].finish_reason,
            )

    async def list_models(self) -> list[str]:
        models = await self.client.models.list()
        return [m.id for m in models.data]
