"""Deterministic, persona-flavored mock LLM.

Used as the only provider in the walking skeleton. Produces recognizably
distinct debate turns from each persona by templating against:
  - the persona's professional identity & rhetorical register
  - the persona's ideology vector (drives stance polarity & framing)
  - the persona's 5 formative books (rotated as authority anchors per round)
  - a deterministic seed (so debates are reproducible)

Generated turns embed claims marked with the sentinel "[[CLAIM]] ... [[/CLAIM]]"
so the orchestrator can extract them into the Toulmin argument graph without
parsing prose.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass

from polylogos.llm.provider import GenerationRequest
from polylogos.schemas.persona import ArgumentationStyle, Persona

# Book-cite phrasings keyed by argumentation style — gives surface diversity
# without losing the deterministic mapping persona → output.
_BOOK_CITES: dict[ArgumentationStyle, list[str]] = {
    ArgumentationStyle.SOCRATIC: [
        "But what would {author} ask us in {title}? Surely",
        "If we follow {author}'s line of questioning in {title},",
    ],
    ArgumentationStyle.AGGRESSIVE: [
        "{author} was blunt about this in {title}:",
        "Read {title} again. {author} made it plain:",
    ],
    ArgumentationStyle.DIDACTIC: [
        "As {author} carefully sets out in {title},",
        "The argument in {title} by {author} is direct:",
    ],
    ArgumentationStyle.CONSENSUAL: [
        "{author}'s synthesis in {title} reminds us that reasonable people can agree that",
        "There is a reading of {title} ({author}) that suggests",
    ],
    ArgumentationStyle.CONTRARIAN: [
        "Most miss the actual argument of {title}. {author} held that",
        "Against the consensus reading of {title}, {author} actually argued",
    ],
}

_OPENERS = [
    "From where I sit — {profession} — the question",
    "After {career_years} years as a {profession}, I see this question",
    "Let me state my position plainly. The proposal",
]

_CROSS_EXAM_PROBES = [
    "I want to press the previous speaker:",
    "Let me ask the room a hard question:",
    "Three things in the prior arguments don't survive scrutiny:",
]

_REBUTTAL_FRAMES = [
    "I have heard the counter-arguments. They miss",
    "Respectfully, the opposing view assumes",
    "The most persuasive opposing point still leaves",
]

_CLOSING_FRAMES = [
    "If I have to compress my position into one paragraph:",
    "Closing where I began, but with the room's arguments now in mind:",
    "My final word, weighed against everything heard today:",
]


def _deterministic_choice[T](rng: random.Random, options: list[T]) -> T:
    return options[rng.randrange(len(options))]


def _stance_from_persona(persona: Persona, topic: str) -> tuple[str, float]:
    """Map (persona ideology, topic) → (stance label, scalar in [-1, +1]).

    Defense-MVP heuristic: hawkish + nationalist + statist axes drive 'for'
    stances on procurement-acceleration/strategic topics. Persona-specific.
    """
    iv = persona.ideology
    weight = (
        0.45 * iv.hawkish_dovish
        + 0.20 * iv.nationalist_globalist
        + 0.15 * iv.statist_libertarian
        + 0.10 * iv.realist_idealist
        + 0.10 * iv.composite_hindutva
    )
    # Topic seed shifts the weight slightly so different topics produce
    # different distributions even from the same population.
    topic_shift = (int(hashlib.sha256(topic.encode()).hexdigest(), 16) % 1000 - 500) / 5000.0
    scalar = max(-1.0, min(1.0, weight - topic_shift))
    if scalar > 0.6:
        return "strongly_for", scalar
    if scalar > 0.15:
        return "for", scalar
    if scalar > -0.15:
        return "neutral", scalar
    if scalar > -0.6:
        return "against", scalar
    return "strongly_against", scalar


def _stance_phrase(stance_label: str) -> str:
    return {
        "strongly_for": "I believe we must act decisively in favour",
        "for": "On balance, I support the proposal",
        "neutral": "I can argue either side; the evidence is mixed",
        "against": "I am not persuaded; the costs outstrip the gains",
        "strongly_against": "I oppose this firmly, and the risk is grave",
    }[stance_label]


def _career_years_estimate(persona: Persona) -> int:
    # Rough heuristic so opener templates have a non-zero number.
    age = 2026 - persona.birth_year
    return max(5, min(45, age - 22))


@dataclass
class MockProvider:
    """Deterministic mock LLM.

    Marker-based claim extraction lets the orchestrator pull structured
    claims out of free-form turns without a real parser.
    """

    name: str = "mock"
    seed: int = 42

    def cost_per_1k_tokens_inr(self) -> float:
        return 0.0

    def generate(self, request: GenerationRequest) -> str:
        persona = request.persona
        rng = self._rng_for_request(request)

        # Rotate formative books across rounds so different turns invoke different anchors.
        book_idx = (request.extra.get("round_number", 0) if request.extra else 0) % len(
            persona.formative_books
        )
        book = persona.formative_books[book_idx]

        stance_label, _stance_scalar = _stance_from_persona(persona, request.topic)
        stance_phrase = _stance_phrase(stance_label)
        cite_template = _deterministic_choice(rng, _BOOK_CITES[persona.argumentation_style])
        book_cite = cite_template.format(author=book.author, title=book.title)

        round_kind = request.instruction
        if round_kind == "opening":
            opener = _deterministic_choice(rng, _OPENERS).format(
                profession=persona.professional_identity,
                career_years=_career_years_estimate(persona),
            )
            paragraphs = [
                f"{opener} cannot be answered without first stating priors. {stance_phrase} on the proposal "
                f"as posed, and I will defend that across this debate.",
                f"{book_cite} {self._book_paraphrase(book, stance_label)}",
                f"[[CLAIM:{stance_label}]] {self._claim_text(persona, request.topic, stance_label, book)} "
                f"[[/CLAIM]]",
            ]

        elif round_kind == "cross_exam":
            probe = _deterministic_choice(rng, _CROSS_EXAM_PROBES)
            paragraphs = [
                f"{probe} {self._cross_exam_question(persona, stance_label, request.context)}",
                f"{book_cite} {self._book_paraphrase(book, stance_label)}",
                f"[[CLAIM:{stance_label}]] {self._sharper_claim(persona, request.topic, stance_label)} "
                f"[[/CLAIM]]",
            ]

        elif round_kind == "rebuttal":
            frame = _deterministic_choice(rng, _REBUTTAL_FRAMES)
            paragraphs = [
                f"{frame} {self._rebuttal_target(persona, stance_label)}.",
                f"My position has been tested and survives. {stance_phrase}.",
                f"[[CLAIM:{stance_label}]] {self._rebuttal_claim(persona, request.topic, stance_label, book)} "
                f"[[/CLAIM]]",
            ]

        elif round_kind == "closing":
            frame = _deterministic_choice(rng, _CLOSING_FRAMES)
            paragraphs = [
                f"{frame} {stance_phrase}.",
                f"{book_cite} {self._book_paraphrase(book, stance_label)}",
                f"[[CLAIM:{stance_label}]] {self._closing_claim(persona, request.topic, stance_label)} "
                f"[[/CLAIM]]",
            ]

        else:
            paragraphs = [
                f"On the matter raised: {stance_phrase}.",
                f"[[CLAIM:{stance_label}]] {self._claim_text(persona, request.topic, stance_label, book)} "
                f"[[/CLAIM]]",
            ]

        return "\n\n".join(paragraphs)

    # ────────────────────────── content helpers ──────────────────────────

    def _book_paraphrase(self, book, stance_label: str) -> str:
        return (
            f"his core point — paraphrased — is that {book.beliefs_changed[0].lower()}, and that "
            f"reading has shaped how I weigh this question."
        )

    def _claim_text(self, persona: Persona, topic: str, stance_label: str, book) -> str:
        verb = {
            "strongly_for": "must move decisively to commit",
            "for": "should commit, with sequencing safeguards",
            "neutral": "must be parameterised before commitment",
            "against": "should be deferred pending material new evidence",
            "strongly_against": "must be rejected on the present record",
        }[stance_label]
        return (
            f"On the question — '{topic[:120]}' — India {verb}, given the lifetime cost-benefit "
            f"profile and the lessons of {book.title}."
        )

    def _sharper_claim(self, persona: Persona, topic: str, stance_label: str) -> str:
        return (
            f"The opposing view's strongest premise — that capability gaps will be filled in time — "
            f"is unsupported by the procurement record of the last fifteen years; my "
            f"{stance_label.replace('_', ' ')} stance therefore stands."
        )

    def _cross_exam_question(self, persona: Persona, stance_label: str, context: str) -> str:
        return (
            "What is the basis for the prior speaker's confidence in delivery timelines, and what is "
            "the sensitivity of the conclusion to a 24-month slip? My contention is that under realistic "
            f"slip distributions, the {stance_label.replace('_', ' ')} position dominates."
        )

    def _rebuttal_target(self, persona: Persona, stance_label: str) -> str:
        return (
            "the asymmetry between revocable and irrevocable commitments — and treats opportunity cost "
            "as a residual rather than a binding constraint"
        )

    def _rebuttal_claim(self, persona: Persona, topic: str, stance_label: str, book) -> str:
        return (
            f"Given the irreversibility of the commitment and the distribution of likely outcomes, "
            f"a {stance_label.replace('_', ' ')} posture is the dominant strategy — a point that "
            f"{book.author} would have recognised in {book.title}."
        )

    def _closing_claim(self, persona: Persona, topic: str, stance_label: str) -> str:
        return (
            f"Across opening, examination, and rebuttal, my {stance_label.replace('_', ' ')} stance "
            f"on '{topic[:80]}' has not been displaced; I rest on it."
        )

    def _rng_for_request(self, request: GenerationRequest) -> random.Random:
        # Deterministic per (debate seed, persona, round, topic).
        round_number = request.extra.get("round_number", 0) if request.extra else 0
        key = (
            f"{self.seed}|{request.persona.persona_id}|{request.instruction}|"
            f"{round_number}|{request.topic}"
        )
        digest = hashlib.sha256(key.encode()).digest()
        return random.Random(int.from_bytes(digest[:8], "big"))
