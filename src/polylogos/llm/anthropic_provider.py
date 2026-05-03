"""AnthropicProvider — real LLM provider backed by Claude.

The persona's life narrative + 5 formative books are baked into the system
prompt; the user message carries the topic, round instruction, and bounded
prior-turn context. Every turn returns prose ending with exactly one marked
claim (`[[CLAIM:<stance>]] ... [[/CLAIM]]`) so the existing argument-graph
extractor in `polylogos.graph` works unchanged.

Prompt caching: the per-persona system prompt is large (~2K tokens) and stable
across the four rounds for that persona, so we mark it ephemerally cached.
Cache hits drop the input cost on rounds 2-4 to ~10% of a miss.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from threading import Lock

import anthropic

from polylogos.llm.provider import GenerationRequest
from polylogos.schemas.persona import Persona


# Sonnet 4.6 is the default for cluster turns per the plan §16.2 routing.
# Override with POLYLOGOS_ANTHROPIC_MODEL.
_DEFAULT_MODEL = "claude-sonnet-4-6"
_USD_INR = 83.0
# Anthropic public pricing for Sonnet 4.6 ($/Mtok). Conservative estimate; real
# pricing may differ. Used for the per-debate cost line in metrics, not billing.
_PRICE_INPUT_USD_PER_MTOK = 3.0
_PRICE_OUTPUT_USD_PER_MTOK = 15.0
_PRICE_CACHE_WRITE_USD_PER_MTOK = 3.75   # 1.25× input
_PRICE_CACHE_READ_USD_PER_MTOK = 0.30    # 0.1× input


_INSTRUCTION_PHRASING = {
    "opening": "your OPENING statement",
    "cross_exam": "your CROSS-EXAMINATION turn — probe the strongest opposing argument from the prior turns",
    "rebuttal": "your REBUTTAL — answer the strongest opposing argument so far without conceding your stance unless evidence demands it",
    "closing": "your CLOSING statement, weighing everything heard",
}


def _build_system_prompt(persona: Persona) -> str:
    iv = persona.ideology
    books_block = "\n".join(
        f"  {i + 1}. \"{b.title}\" by {b.author} — read at age {b.age_when_read} ({b.year_first_read}). "
        f"Why it mattered to you: {b.why_it_mattered} "
        f"It changed how you think: {'; '.join(b.beliefs_changed)}."
        for i, b in enumerate(persona.formative_books)
    )
    return f"""You are {persona.synthetic_name}, a {persona.professional_identity}.

You are a SYNTHETIC persona generated for an AI debate engine. You are not a real person. \
Speak in the first person. Argue from your own life experience. Stay tightly in character; \
do not break the fourth wall.

Born {persona.birth_year} in {persona.birth_place}. Mother tongue: {persona.mother_tongue}. \
Other languages: {", ".join(persona.other_languages) or "—"}.
Class at birth: {persona.socioeconomic_class_at_birth}.
Education: {persona.education_summary}
Career: {persona.career_summary}

Your argumentation style: {persona.argumentation_style.value}.
Your epistemic style: {persona.epistemic_style.value}.
Your linguistic register: {persona.linguistic_register}.
Rhetorical devices you favour: {", ".join(persona.rhetorical_devices) or "directness"}.

Your five formative books — you cite them when relevant; not every turn, but at least one of \
them must appear naturally somewhere in this turn:
{books_block}

Your ideological coordinates (each in [-1, +1] — let them shape your stance; do NOT recite them \
to the audience):
  hawkish/dovish: {iv.hawkish_dovish:+.2f}
  statist/libertarian: {iv.statist_libertarian:+.2f}
  nationalist/globalist: {iv.nationalist_globalist:+.2f}
  market/planner: {iv.market_planner:+.2f}
  realist/idealist: {iv.realist_idealist:+.2f}
  interventionist/non-aligned: {iv.interventionist_nonaligned:+.2f}
  centralist/federalist: {iv.centralist_federalist:+.2f}
  traditionalist/progressive: {iv.traditionalist_progressive:+.2f}
  equality/meritocracy: {iv.equality_meritocracy:+.2f}
  secular/religious: {iv.secular_religious:+.2f}
  individualist/collectivist: {iv.individualist_collectivist:+.2f}
  composite/hindutva: {iv.composite_hindutva:+.2f}

Your persuasion susceptibility is {persona.persuasion_susceptibility:.2f}: \
{"low — you hold your line under pressure" if persona.persuasion_susceptibility < 0.4 else \
 "moderate — you update on strong evidence but require it" if persona.persuasion_susceptibility < 0.65 else \
 "higher — you take opposing arguments seriously and may move"}.

OUTPUT CONTRACT (strict — the orchestrator will parse it programmatically):
  - 2 to 4 short paragraphs, 150-220 words total. No bullet lists. No headers.
  - Speak in the first person. Cite at least one of your five formative books by name.
  - End with EXACTLY ONE marked claim, on its own line, in this exact format:
        [[CLAIM:<stance>]] One sharp, defensible sentence stating your single most-important claim. [[/CLAIM]]
  - <stance> MUST be one of: strongly_for, for, neutral, against, strongly_against
  - The text inside the [[CLAIM]]…[[/CLAIM]] markers is what enters the argument graph. \
Make it specific, falsifiable where possible, and recognisably yours.

This is a deliberation artefact, not a real-world recommendation. You are entitled to be \
sharp, even uncomfortable; you are not entitled to slur or to fabricate facts.
"""


def _build_user_prompt(req: GenerationRequest) -> str:
    instruction_text = _INSTRUCTION_PHRASING.get(req.instruction, req.instruction.upper())
    parts: list[str] = [
        f"DEBATE TOPIC: {req.topic}",
        "",
        f"This turn: {instruction_text}.",
    ]
    if req.context.strip():
        parts.extend(
            [
                "",
                "Verbatim record of recent prior turns from your cluster (you may reference any of them):",
                "----",
                req.context,
                "----",
            ]
        )
    parts.extend(
        [
            "",
            "Now produce your turn following the OUTPUT CONTRACT in your system prompt. "
            "End with the [[CLAIM:<stance>]] ... [[/CLAIM]] marker.",
        ]
    )
    return "\n".join(parts)


@dataclass
class _Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0
    requests: int = 0


@dataclass
class AnthropicProvider:
    """Real Claude-backed provider. Defaults to Sonnet 4.6 with prompt caching."""

    name: str = "anthropic"
    model: str = field(default_factory=lambda: os.environ.get("POLYLOGOS_ANTHROPIC_MODEL", _DEFAULT_MODEL))
    api_key: str | None = None
    use_prompt_cache: bool = True
    temperature: float = 0.7
    max_tokens: int = 700
    _usage: _Usage = field(default_factory=_Usage)
    _usage_lock: Lock = field(default_factory=Lock)

    def __post_init__(self) -> None:
        key = self.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            msg = (
                "AnthropicProvider requires an API key — set ANTHROPIC_API_KEY in the "
                "environment or pass api_key= explicitly."
            )
            raise RuntimeError(msg)
        self._client = anthropic.Anthropic(api_key=key)

    def cost_per_1k_tokens_inr(self) -> float:
        # Blended estimate for metrics; exact cost is computed live in `total_cost_inr`.
        blended_usd_per_mtok = (_PRICE_INPUT_USD_PER_MTOK + _PRICE_OUTPUT_USD_PER_MTOK) / 2
        return (blended_usd_per_mtok * _USD_INR) / 1000.0

    @property
    def usage_snapshot(self) -> dict[str, int]:
        with self._usage_lock:
            return {
                "input_tokens": self._usage.input_tokens,
                "output_tokens": self._usage.output_tokens,
                "cache_creation_input_tokens": self._usage.cache_creation_input_tokens,
                "cache_read_input_tokens": self._usage.cache_read_input_tokens,
                "requests": self._usage.requests,
            }

    def total_cost_inr(self) -> float:
        u = self.usage_snapshot
        usd = (
            u["input_tokens"] * _PRICE_INPUT_USD_PER_MTOK
            + u["output_tokens"] * _PRICE_OUTPUT_USD_PER_MTOK
            + u["cache_creation_input_tokens"] * _PRICE_CACHE_WRITE_USD_PER_MTOK
            + u["cache_read_input_tokens"] * _PRICE_CACHE_READ_USD_PER_MTOK
        ) / 1_000_000
        return usd * _USD_INR

    def generate(self, request: GenerationRequest) -> str:
        system_text = _build_system_prompt(request.persona)
        user_text = _build_user_prompt(request)

        system_blocks: list[dict[str, object]] = [{"type": "text", "text": system_text}]
        if self.use_prompt_cache:
            system_blocks[0]["cache_control"] = {"type": "ephemeral"}

        max_tokens = max(request.max_tokens, self.max_tokens)
        response = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=self.temperature,
            system=system_blocks,
            messages=[{"role": "user", "content": user_text}],
        )

        with self._usage_lock:
            self._usage.requests += 1
            self._usage.input_tokens += getattr(response.usage, "input_tokens", 0)
            self._usage.output_tokens += getattr(response.usage, "output_tokens", 0)
            self._usage.cache_creation_input_tokens += getattr(
                response.usage, "cache_creation_input_tokens", 0
            ) or 0
            self._usage.cache_read_input_tokens += getattr(
                response.usage, "cache_read_input_tokens", 0
            ) or 0

        # Concatenate any text blocks; ignore tool_use / etc. (we don't use them here).
        chunks: list[str] = []
        for block in response.content:
            text = getattr(block, "text", None)
            if text:
                chunks.append(text)
        return "".join(chunks)
