"""Token economics tracker — every LLM call has a real cost.

Tracks token usage, costs, and efficiency across sessions.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


# Approximate pricing per 1M tokens (input/output) — updated periodically
MODEL_PRICING: dict[str, tuple[float, float]] = {
    # (input_per_1M, output_per_1M)
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4.1": (2.00, 8.00),
    "o1": (15.00, 60.00),
    "o3": (10.00, 40.00),
    "claude-opus": (15.00, 75.00),
    "claude-sonnet": (3.00, 15.00),
    "claude-haiku": (0.25, 1.25),
    "gemini-2.0-flash": (0.075, 0.30),
    "gemini-1.5-pro": (1.25, 5.00),
    "deepseek-chat": (0.14, 0.28),
    "deepseek-coder": (0.14, 0.28),
    "qwen-turbo": (0.08, 0.20),
    "qwen-max": (1.60, 6.40),
    "mistral-large": (2.00, 6.00),
    "llama3": (0.00, 0.00),  # Local = free
    "ollama": (0.00, 0.00),  # Local = free
}


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    model: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class SessionEconomics:
    """Track economics for an entire session."""
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    call_count: int = 0
    calls: list[TokenUsage] = field(default_factory=list)
    session_start: str = ""

    def __post_init__(self):
        if not self.session_start:
            self.session_start = datetime.now().isoformat()


class EconomicsTracker:
    """Tracks token costs across the session."""

    def __init__(self, store_path: str | Path = "~/.lifeclaw/economics"):
        self.store_path = Path(store_path).expanduser()
        self.store_path.mkdir(parents=True, exist_ok=True)
        self.session = SessionEconomics()

    def record(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Record a single LLM call and return its cost."""
        cost = self._estimate_cost(model, input_tokens, output_tokens)

        usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            model=model,
        )
        self.session.calls.append(usage)
        self.session.total_input_tokens += input_tokens
        self.session.total_output_tokens += output_tokens
        self.session.total_cost += cost
        self.session.call_count += 1

        return cost

    def _estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost based on model pricing."""
        # Find best matching pricing
        model_lower = model.lower()
        for key, (inp_rate, out_rate) in MODEL_PRICING.items():
            if key in model_lower:
                return (input_tokens * inp_rate / 1_000_000) + (output_tokens * out_rate / 1_000_000)

        # Local models (ollama) are free
        if "ollama" in model_lower or "/" not in model:
            return 0.0

        # Default: assume moderate pricing
        return (input_tokens * 1.0 / 1_000_000) + (output_tokens * 4.0 / 1_000_000)

    @property
    def summary(self) -> dict:
        return {
            "calls": self.session.call_count,
            "input_tokens": self.session.total_input_tokens,
            "output_tokens": self.session.total_output_tokens,
            "total_tokens": self.session.total_input_tokens + self.session.total_output_tokens,
            "total_cost": round(self.session.total_cost, 6),
            "cost_display": f"${self.session.total_cost:.4f}",
        }

    @property
    def cost_footer(self) -> str:
        """Cost footer for display after each response."""
        s = self.session
        if s.total_cost == 0:
            return f"Tokens: {s.total_input_tokens + s.total_output_tokens:,} (local)"
        return (
            f"Cost: ${s.total_cost:.4f} | "
            f"Tokens: {s.total_input_tokens + s.total_output_tokens:,} | "
            f"Calls: {s.call_count}"
        )

    def save_session(self):
        """Persist session economics to disk."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_file = self.store_path / f"session_{ts}.json"
        data = {
            "session_start": self.session.session_start,
            "session_end": datetime.now().isoformat(),
            **self.summary,
            "calls": [
                {
                    "model": c.model,
                    "input_tokens": c.input_tokens,
                    "output_tokens": c.output_tokens,
                    "cost": c.cost,
                    "timestamp": c.timestamp,
                }
                for c in self.session.calls
            ],
        }
        session_file.write_text(json.dumps(data, indent=2))
