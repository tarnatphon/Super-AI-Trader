"""Agent base types and an optional LLM client.

Every agent returns a structured `Signal`. Agents have a *deterministic heuristic*
brain that always works offline, and (if an API key is configured) an optional
LLM brain that reasons in natural language. The risk manager — not the agents —
has final authority over order size and approval.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict


@dataclass
class Signal:
    agent: str
    action: str                 # "BUY" | "SELL" | "HOLD"
    conviction: float           # 0..100
    rationale: str
    stop_pct: float | None = None   # suggested stop distance as % of price

    def to_dict(self) -> dict:
        return asdict(self)


class LLMClient:
    """Thin OpenAI-compatible chat client. No hard dependency; works with
    OpenAI, DeepSeek, Groq, local Ollama, etc. via env vars."""

    def __init__(self) -> None:
        self.api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL")  # e.g. http://localhost:11434/v1 for Ollama
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.enabled = bool(self.api_key) or bool(self.base_url)

    def chat_json(self, system: str, user: str) -> dict | None:
        """Call the model and parse a JSON object. Returns None on any failure."""
        if not self.enabled:
            return None
        try:
            from openai import OpenAI  # type: ignore
        except ImportError:
            return None
        try:
            kwargs = {"model": self.model}
            if self.api_key:
                kwargs["api_key"] = self.api_key
            if self.base_url:
                kwargs["base_url"] = self.base_url
            client = OpenAI(**kwargs)
            resp = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.2,
            )
            text = resp.choices[0].message.content or ""
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1:
                return None
            return json.loads(text[start : end + 1])
        except Exception:
            return None


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))
