"""Provider registry - resolves model strings to the right provider."""

from lifeclaw.config.schema import Config
from lifeclaw.providers.anthropic_provider import AnthropicProvider
from lifeclaw.providers.base import LLMProvider
from lifeclaw.providers.ollama import OllamaProvider
from lifeclaw.providers.openai_compat import OpenAICompatProvider


def resolve_provider(config: Config, model_override: str | None = None) -> tuple[LLMProvider, str]:
    """Resolve a provider and model name from config.

    Model strings can be:
      - "ollama/llama3.2" -> OllamaProvider, "llama3.2"
      - "anthropic/claude-sonnet-4-20250514" -> AnthropicProvider, "claude-sonnet-4-20250514"
      - "openai/gpt-4o" -> OpenAICompatProvider, "gpt-4o"
      - "openrouter/meta-llama/llama-3-70b" -> OpenAICompatProvider (openrouter), "meta-llama/llama-3-70b"
      - "llama3.2" (no prefix) -> auto-detect

    Returns (provider_instance, model_name).
    """
    model_str = model_override or config.agent.model
    provider_name = config.agent.provider

    # All known provider prefixes
    known = {
        "ollama", "openai", "anthropic", "openrouter", "deepseek", "groq",
        "gemini", "mistral", "moonshot", "zhipu", "dashscope", "minimax",
        "siliconflow", "volcengine", "azure_openai", "vllm", "custom",
    }

    # Parse "provider/model" format
    if "/" in model_str:
        parts = model_str.split("/", 1)
        candidate = parts[0].lower()
        if candidate in known:
            provider_name = candidate
            model_str = parts[1]
        elif candidate in ("claude", "gpt"):
            provider_name = "anthropic" if candidate == "claude" else "openai"
            model_str = "/".join(parts)

    # Auto-detect
    if provider_name == "auto":
        if any(k in model_str for k in ("llama", "gemma", "phi", "qwen", "codellama", "starcoder", "yi-")):
            provider_name = "ollama"
        elif "claude" in model_str:
            provider_name = "anthropic"
        elif "gpt" in model_str or "o1" in model_str or "o3" in model_str:
            provider_name = "openai"
        elif "deepseek" in model_str:
            provider_name = "deepseek"
        elif "mistral" in model_str or "mixtral" in model_str:
            provider_name = "mistral"
        elif "moonshot" in model_str or "kimi" in model_str:
            provider_name = "moonshot"
        elif "glm" in model_str:
            provider_name = "zhipu"
        elif "qwen" in model_str:
            provider_name = "dashscope"
        else:
            provider_name = "ollama"  # Default to local

    # Instantiate
    providers_cfg = config.providers
    if provider_name == "ollama":
        base = providers_cfg.ollama.api_base or "http://localhost:11434"
        return OllamaProvider(base_url=base), model_str

    if provider_name == "anthropic":
        key = providers_cfg.anthropic.api_key
        if not key:
            raise ValueError("Anthropic API key not set. Run: lifeclaw setup")
        return AnthropicProvider(api_key=key), model_str

    # All OpenAI-compatible providers
    prov_cfg = getattr(providers_cfg, provider_name, providers_cfg.custom)
    key = prov_cfg.api_key
    if not key:
        raise ValueError(f"{provider_name} API key not set. Run: lifeclaw setup")
    return (
        OpenAICompatProvider(
            provider_name=provider_name,
            api_key=key,
            api_base=prov_cfg.api_base,
            extra_headers=prov_cfg.extra_headers,
        ),
        model_str,
    )
