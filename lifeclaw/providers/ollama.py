"""Ollama provider - connects to local Ollama instance."""

import json
from typing import AsyncIterator

import httpx
from loguru import logger

from lifeclaw.providers.base import (
    LLMMessage,
    LLMProvider,
    LLMResponse,
    StreamChunk,
    ToolCall,
)


def _to_ollama_messages(messages: list[LLMMessage]) -> list[dict]:
    out = []
    for m in messages:
        msg = {"role": m.role, "content": m.content or ""}
        if m.tool_calls:
            msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.name, "arguments": tc.arguments},
                }
                for tc in m.tool_calls
            ]
        if m.tool_call_id:
            msg["role"] = "tool"
            msg["tool_call_id"] = m.tool_call_id
        out.append(msg)
    return out


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=120.0)

    async def chat(
        self,
        messages: list[LLMMessage],
        tools: list[dict] | None = None,
        temperature: float = 0.1,
        max_tokens: int = 8192,
        stream: bool = False,
        model: str | None = None,
    ) -> LLMResponse:
        payload: dict = {
            "model": model or "llama3.2",
            "messages": _to_ollama_messages(messages),
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if tools:
            payload["tools"] = tools

        data = await self._post_chat(payload, tools_sent=bool(tools))

        msg = data.get("message", {})
        tool_calls = []
        for tc in msg.get("tool_calls", []):
            fn = tc.get("function", {})
            tool_calls.append(
                ToolCall(
                    id=tc.get("id", f"call_{len(tool_calls)}"),
                    name=fn.get("name", ""),
                    arguments=fn.get("arguments", {}),
                )
            )

        return LLMResponse(
            content=msg.get("content"),
            tool_calls=tool_calls,
            finish_reason="tool_calls" if tool_calls else "stop",
            usage={
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
            },
        )

    async def _post_chat(self, payload: dict, tools_sent: bool = False) -> dict:
        """Send chat request to Ollama with error handling and tool fallback."""
        try:
            resp = await self.client.post("/api/chat", json=payload)
        except httpx.ConnectError:
            raise ConnectionError("Cannot connect to Ollama. Is it running? (ollama serve)")
        except httpx.TimeoutException:
            raise TimeoutError("Ollama request timed out. The model may be loading or the prompt is too large.")

        # Check for HTTP errors with body context
        if resp.status_code != 200:
            body = resp.text
            # If tools caused the error, retry without them
            if tools_sent and ("tool" in body.lower() or resp.status_code == 400):
                logger.warning(f"Ollama rejected tools (HTTP {resp.status_code}), retrying without tools")
                payload.pop("tools", None)
                return await self._post_chat(payload, tools_sent=False)
            raise RuntimeError(f"Ollama error (HTTP {resp.status_code}): {body[:500]}")

        try:
            data = resp.json()
        except json.JSONDecodeError:
            raise RuntimeError(f"Ollama returned invalid JSON: {resp.text[:300]}")

        # Check for Ollama-level error in response body
        if "error" in data:
            error_msg = data["error"]
            # If tools caused the error, retry without them
            if tools_sent and ("tool" in error_msg.lower() or "not supported" in error_msg.lower()):
                logger.warning(f"Model doesn't support tools: {error_msg}. Retrying without tools.")
                payload.pop("tools", None)
                return await self._post_chat(payload, tools_sent=False)
            raise RuntimeError(f"Ollama error: {error_msg}")

        return data

    async def chat_stream(
        self,
        messages: list[LLMMessage],
        tools: list[dict] | None = None,
        temperature: float = 0.1,
        max_tokens: int = 8192,
        model: str | None = None,
    ) -> AsyncIterator[StreamChunk]:
        payload: dict = {
            "model": model or "llama3.2",
            "messages": _to_ollama_messages(messages),
            "stream": True,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if tools:
            payload["tools"] = tools

        try:
            async with self.client.stream("POST", "/api/chat", json=payload) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    body_text = body.decode(errors="replace")
                    if tools and ("tool" in body_text.lower() or resp.status_code == 400):
                        logger.warning("Ollama rejected tools in stream, falling back without tools")
                        payload.pop("tools", None)
                        async for chunk in self.chat_stream(messages, tools=None, temperature=temperature, max_tokens=max_tokens, model=model):
                            yield chunk
                        return
                    raise RuntimeError(f"Ollama error (HTTP {resp.status_code}): {body_text[:500]}")

                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    if "error" in data:
                        raise RuntimeError(f"Ollama error: {data['error']}")
                    msg = data.get("message", {})
                    done = data.get("done", False)
                    yield StreamChunk(
                        delta=msg.get("content", ""),
                        finish_reason="stop" if done else None,
                    )
        except httpx.ConnectError:
            raise ConnectionError("Cannot connect to Ollama. Is it running? (ollama serve)")
        except httpx.TimeoutException:
            raise TimeoutError("Ollama request timed out.")

    async def list_models(self) -> list[str]:
        resp = await self.client.get("/api/tags")
        resp.raise_for_status()
        data = resp.json()
        return [m["name"] for m in data.get("models", [])]

    async def pull_model(self, model: str) -> AsyncIterator[dict]:
        async with self.client.stream(
            "POST", "/api/pull", json={"name": model}
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.strip():
                    yield json.loads(line)

    @staticmethod
    async def detect() -> str | None:
        """Try to detect a running Ollama instance. Returns base_url or None."""
        for url in ["http://localhost:11434", "http://127.0.0.1:11434"]:
            try:
                async with httpx.AsyncClient(timeout=3.0) as c:
                    r = await c.get(f"{url}/api/tags")
                    if r.status_code == 200:
                        return url
            except Exception:
                continue
        return None
