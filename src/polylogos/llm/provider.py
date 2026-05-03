"""LLM provider seam.

The mock implementation is the only concrete provider in the walking skeleton.
Real providers (Vertex Gemini, Anthropic Claude, vLLM/Llama) implement the same
protocol later — see plan §16.2 (tiered routing).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from polylogos.schemas.persona import Persona


@dataclass(frozen=True)
class GenerationRequest:
    """Single generation call from the orchestrator to a provider."""

    persona: Persona
    topic: str
    instruction: str
    """Round-specific instruction: opening, cross-exam, rebuttal, closing, etc."""
    context: str = ""
    """Concatenated prior turns (cluster transcript so far)."""
    target_stance_hint: float | None = None
    """Optional hint from belief state (Friedkin-Johnsen) — scalar in [-1, 1]."""
    max_tokens: int = 220
    seed: int = 0
    extra: dict[str, object] = field(default_factory=dict)


class LLMProvider(Protocol):
    """Minimal contract every provider must satisfy."""

    name: str

    def generate(self, request: GenerationRequest) -> str: ...

    def cost_per_1k_tokens_inr(self) -> float: ...
