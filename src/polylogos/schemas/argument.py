"""Toulmin argument graph schema (plan §4.6).

Nodes: Claim, Evidence.
Edges: SUPPORTS, REBUTS, QUALIFIES.

Each Claim is asserted by one Persona (via persona_id); each Claim points to
a stance (a position in topic-space). Citation grounding (plan §4.7) is
enforced at synthesis-time via mutual-information test — here we just store
the candidate evidence links.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class Stance(str, Enum):
    """Coarse stance buckets for cluster-entropy and dissent scoring."""

    STRONGLY_FOR = "strongly_for"
    FOR = "for"
    NEUTRAL = "neutral"
    AGAINST = "against"
    STRONGLY_AGAINST = "strongly_against"

    def to_scalar(self) -> float:
        return {
            Stance.STRONGLY_FOR: 1.0,
            Stance.FOR: 0.5,
            Stance.NEUTRAL: 0.0,
            Stance.AGAINST: -0.5,
            Stance.STRONGLY_AGAINST: -1.0,
        }[self]


class EdgeType(str, Enum):
    SUPPORTS = "supports"
    REBUTS = "rebuts"
    QUALIFIES = "qualifies"


class Evidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    evidence_id: UUID = Field(default_factory=uuid4)
    source_id: str  # citation key (e.g., "IDSA-2024-001"); MI-verified at synthesis
    snippet: str
    credibility: Annotated[float, Field(ge=0, le=1)] = 0.7


class Claim(BaseModel):
    model_config = ConfigDict(frozen=True)

    claim_id: UUID = Field(default_factory=uuid4)
    asserted_by: UUID  # persona_id
    text: str
    stance: Stance
    confidence: Annotated[float, Field(ge=0, le=1)] = 0.7
    round_number: int = 0
    cited_evidence: list[UUID] = Field(default_factory=list)


class ArgumentEdge(BaseModel):
    model_config = ConfigDict(frozen=True)

    source: UUID  # claim_id
    target: UUID  # claim_id
    type: EdgeType
    weight: Annotated[float, Field(ge=0, le=1)] = 0.5
