"""Debate config + runtime artifacts."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class Round(str, Enum):
    OPENING = "opening"
    CROSS_EXAM = "cross_exam"
    REBUTTAL = "rebuttal"
    CLOSING = "closing"


class DebateConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    debate_id: UUID = Field(default_factory=uuid4)
    topic: str
    cluster_size: int = 10
    seed: int = 42
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Turn(BaseModel):
    """One agent's contribution in one round."""

    model_config = ConfigDict(frozen=True)

    turn_id: UUID = Field(default_factory=uuid4)
    persona_id: UUID
    persona_label: str
    round: Round
    round_number: int
    text: str
    claim_ids: list[UUID] = Field(default_factory=list)
    persuasion_kl: Annotated[float, Field(ge=0)] = 0.0
    """KL divergence from prior to posterior in mean-receiver belief (plan §4.5)."""


class DebateOutput(BaseModel):
    config: DebateConfig
    transcript: list[Turn]
    article: str
    executive_remark: str
    minority_report: str
    quality_band: str = "fast"
    cost_estimate_inr: float = 0.0
    final_orthogonality: float = 0.0
    final_cluster_entropy: float = 0.0
    final_diversity_volume: float = 0.0
