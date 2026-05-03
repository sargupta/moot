"""Persona schema — the deep narrative model (W1, plan §3.1).

A persona is not a feature vector. It is a generated life: 60-year arc with
formative events, a 5-book reading list with read-age and impact narrative,
an ideology coordinate set, cognitive biases, and a debate-behavior prior.

The schema is the contract between persona generation, prompt construction,
and synthesis attribution. Keep it stable; evolve additively.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


# ───────────────────────── Cognitive primitives ──────────────────────────


class BigFive(BaseModel):
    model_config = ConfigDict(frozen=True)

    openness: Annotated[float, Field(ge=0, le=1)]
    conscientiousness: Annotated[float, Field(ge=0, le=1)]
    extraversion: Annotated[float, Field(ge=0, le=1)]
    agreeableness: Annotated[float, Field(ge=0, le=1)]
    neuroticism: Annotated[float, Field(ge=0, le=1)]


class IdeologyVector(BaseModel):
    """12-dim ideological coordinate. Each axis in [-1, +1]."""

    model_config = ConfigDict(frozen=True)

    statist_libertarian: Annotated[float, Field(ge=-1, le=1)]
    traditionalist_progressive: Annotated[float, Field(ge=-1, le=1)]
    hawkish_dovish: Annotated[float, Field(ge=-1, le=1)]
    centralist_federalist: Annotated[float, Field(ge=-1, le=1)]
    equality_meritocracy: Annotated[float, Field(ge=-1, le=1)]
    secular_religious: Annotated[float, Field(ge=-1, le=1)]
    nationalist_globalist: Annotated[float, Field(ge=-1, le=1)]
    market_planner: Annotated[float, Field(ge=-1, le=1)]
    individualist_collectivist: Annotated[float, Field(ge=-1, le=1)]
    realist_idealist: Annotated[float, Field(ge=-1, le=1)]
    interventionist_nonaligned: Annotated[float, Field(ge=-1, le=1)]
    composite_hindutva: Annotated[float, Field(ge=-1, le=1)]


# ────────────────────────── Narrative primitives ─────────────────────────


class LifeEventType(str, Enum):
    BEREAVEMENT = "bereavement"
    DISPLACEMENT = "displacement"
    CONVERSION = "conversion"
    SUCCESS = "success"
    FAILURE = "failure"
    BETRAYAL = "betrayal"
    MENTORSHIP = "mentorship"
    ROMANCE = "romance"
    ILLNESS = "illness"
    WAR = "war"
    RIOT = "riot"
    MIGRATION = "migration"


class LifeEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    year: int
    age: int
    type: LifeEventType
    description: str
    valence: Annotated[float, Field(ge=-1, le=1)]
    persistence: Annotated[float, Field(ge=0, le=1)]


class FormativeBook(BaseModel):
    """The 5 books that shaped this persona — epistemic anchor points (plan §3.3)."""

    model_config = ConfigDict(frozen=True)

    title: str
    author: str
    year_first_read: int
    age_when_read: int
    why_it_mattered: str  # ~100 words, persona's own framing
    beliefs_changed: list[str]
    re_read_count: int = 0


class EpistemicStyle(str, Enum):
    RATIONALIST = "rationalist"
    EMPIRICIST = "empiricist"
    PRAGMATIST = "pragmatist"
    PHENOMENOLOGIST = "phenomenologist"
    TRADITIONALIST = "traditionalist"


class ArgumentationStyle(str, Enum):
    SOCRATIC = "socratic"
    AGGRESSIVE = "aggressive"
    DIDACTIC = "didactic"
    CONSENSUAL = "consensual"
    CONTRARIAN = "contrarian"


# ───────────────────────────────── Persona ────────────────────────────────


class Persona(BaseModel):
    """A synthetic life. Always disclaim — never a real person."""

    model_config = ConfigDict(frozen=True)

    # Identity (synthetic)
    persona_id: UUID = Field(default_factory=uuid4)
    synthetic_name: str
    pronouns: str = "they/them"
    birth_year: int
    birth_place: str
    mother_tongue: str
    other_languages: list[str] = Field(default_factory=list)

    # Family of origin
    socioeconomic_class_at_birth: str
    family_political_lean: Annotated[float, Field(ge=-1, le=1)] = 0.0
    family_religiosity: Annotated[float, Field(ge=0, le=1)] = 0.5

    # Narrative spine
    life_events: list[LifeEvent] = Field(default_factory=list)

    # Education & career (compact at the skeleton stage)
    education_summary: str
    career_summary: str
    professional_identity: str
    domain_expertise: dict[str, Annotated[float, Field(ge=0, le=1)]] = Field(default_factory=dict)

    # The 5 books — exactly 5, this is the epistemic anchor (W1)
    formative_books: list[FormativeBook] = Field(min_length=5, max_length=5)

    # Cognitive architecture
    big_five: BigFive
    ideology: IdeologyVector
    epistemic_style: EpistemicStyle
    argumentation_style: ArgumentationStyle
    confidence_calibration: Annotated[float, Field(ge=0, le=1)] = 0.7

    # Debate-behavior priors
    persuasion_susceptibility: Annotated[float, Field(ge=0, le=1)] = 0.5
    """1 - λ_i in Friedkin-Johnsen. Low = stubborn, high = open-minded."""

    # Linguistic fingerprint
    linguistic_register: str = "formal"
    typical_sentence_length: int = 22
    rhetorical_devices: list[str] = Field(default_factory=list)

    def stubbornness(self) -> float:
        """λ_i ∈ [0, 1] for Friedkin-Johnsen (plan §4.1)."""
        return 1.0 - self.persuasion_susceptibility

    def short_label(self) -> str:
        """Compact identifier for transcripts and audit logs."""
        return f"{self.synthetic_name} ({self.professional_identity})"
