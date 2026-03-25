"""Configuration schema for LifeClaw."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ProviderConfig(BaseModel):
    api_key: str = ""
    api_base: str | None = None
    extra_headers: dict[str, str] | None = None


class ProvidersConfig(BaseModel):
    # Local
    ollama: ProviderConfig = Field(default_factory=ProviderConfig)
    vllm: ProviderConfig = Field(default_factory=ProviderConfig)
    # Major cloud
    openai: ProviderConfig = Field(default_factory=ProviderConfig)
    anthropic: ProviderConfig = Field(default_factory=ProviderConfig)
    gemini: ProviderConfig = Field(default_factory=ProviderConfig)
    # Aggregators
    openrouter: ProviderConfig = Field(default_factory=ProviderConfig)
    # Specialized
    deepseek: ProviderConfig = Field(default_factory=ProviderConfig)
    groq: ProviderConfig = Field(default_factory=ProviderConfig)
    mistral: ProviderConfig = Field(default_factory=ProviderConfig)
    # China providers
    moonshot: ProviderConfig = Field(default_factory=ProviderConfig)
    zhipu: ProviderConfig = Field(default_factory=ProviderConfig)
    dashscope: ProviderConfig = Field(default_factory=ProviderConfig)
    minimax: ProviderConfig = Field(default_factory=ProviderConfig)
    siliconflow: ProviderConfig = Field(default_factory=ProviderConfig)
    volcengine: ProviderConfig = Field(default_factory=ProviderConfig)
    # Cloud infra
    azure_openai: ProviderConfig = Field(default_factory=ProviderConfig)
    # Any OpenAI-compatible endpoint
    custom: ProviderConfig = Field(default_factory=ProviderConfig)


class AgentConfig(BaseModel):
    model: str = "ollama/auto"
    provider: str = "auto"
    max_tokens: int = 8192
    context_window: int = 65536
    temperature: float = 0.1
    max_iterations: int = 40


class MCPServerConfig(BaseModel):
    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)


class WebConfig(BaseModel):
    enabled: bool = True
    host: str = "127.0.0.1"
    port: int = 3119


class Config(BaseModel):
    theme: str = "aurora"
    agent: AgentConfig = Field(default_factory=AgentConfig)
    providers: ProvidersConfig = Field(default_factory=ProvidersConfig)
    mcp_servers: dict[str, MCPServerConfig] = Field(default_factory=dict)
    web: WebConfig = Field(default_factory=WebConfig)
    skills_dir: str = "~/.lifeclaw/skills"


def get_config_dir() -> Path:
    p = Path.home() / ".lifeclaw"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_config_path() -> Path:
    return get_config_dir() / "config.json"
