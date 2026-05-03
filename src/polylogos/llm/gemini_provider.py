"""GeminiProvider — real LLM provider backed by Google Gemini 2.5.

Same contract as AnthropicProvider: builds a per-persona system prompt (life
narrative + 5 formative books + ideology + output contract) and a per-turn
user prompt (topic + round instruction + bounded prior-turn context). Returns
text containing exactly one `[[CLAIM:<stance>]] ... [[/CLAIM]]` marker so the
existing argument-graph extractor works unchanged.

Default model is `gemini-2.5-flash` — fast and cheap enough to amortise across
40 turns/cluster without thinking. Override with POLYLOGOS_GEMINI_MODEL.

API key: passed via the env var `GEMINI_API_KEY` (or `GOOGLE_API_KEY`). Never
write the key to a config file from this code; pass it through the process env.
"""

from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass, field
from threading import Lock

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from polylogos.llm.provider import GenerationRequest
from polylogos.schemas.persona import Persona

_DEFAULT_MODEL = "gemini-2.5-flash"
_USD_INR = 83.0
# Gemini 2.5 models do internal "thinking" by default, which eats the output-token
# budget before producing visible prose. For debate turns we want fast, expressive
# generation, not extended chain-of-thought, so we explicitly disable it.
_DISABLE_THINKING_BUDGET = 0
# Public Gemini 2.5 Flash list pricing (rough; use only for the metrics line in
# the UI, not for billing). Pro pricing is ~10× higher; Flash is the right
# default for cluster turns per plan §16.2 routing.
_PRICE_INPUT_USD_PER_MTOK = 0.30
_PRICE_OUTPUT_USD_PER_MTOK = 2.50


_INSTRUCTION_PHRASING = {
    "opening": "your OPENING statement",
    "cross_exam": (
        "your CROSS-EXAMINATION turn — probe the strongest opposing argument from the prior turns"
    ),
    "rebuttal": (
        "your REBUTTAL — answer the strongest opposing argument so far without conceding "
        "your stance unless evidence demands it"
    ),
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
    requests: int = 0


@dataclass
class GeminiProvider:
    """Real Gemini-backed provider. Defaults to Gemini 2.5 Flash."""

    name: str = "gemini"
    model: str = field(default_factory=lambda: os.environ.get("POLYLOGOS_GEMINI_MODEL", _DEFAULT_MODEL))
    api_key: str | None = None
    temperature: float = 0.7
    max_tokens: int = 1400  # generous to absorb any preamble before the [[CLAIM]] marker
    _usage: _Usage = field(default_factory=_Usage)
    _usage_lock: Lock = field(default_factory=Lock)

    def __post_init__(self) -> None:
        key = (
            self.api_key
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
        )
        if not key:
            msg = (
                "GeminiProvider requires an API key — set GEMINI_API_KEY (or GOOGLE_API_KEY) "
                "in the environment, or pass api_key= explicitly."
            )
            raise RuntimeError(msg)
        # The new google-genai SDK; we use the developer-API path (api_key auth).
        self._client = genai.Client(api_key=key)

    def cost_per_1k_tokens_inr(self) -> float:
        blended = (_PRICE_INPUT_USD_PER_MTOK + _PRICE_OUTPUT_USD_PER_MTOK) / 2
        return (blended * _USD_INR) / 1000.0

    @property
    def usage_snapshot(self) -> dict[str, int]:
        with self._usage_lock:
            return {
                "input_tokens": self._usage.input_tokens,
                "output_tokens": self._usage.output_tokens,
                "requests": self._usage.requests,
            }

    def total_cost_inr(self) -> float:
        u = self.usage_snapshot
        usd = (
            u["input_tokens"] * _PRICE_INPUT_USD_PER_MTOK
            + u["output_tokens"] * _PRICE_OUTPUT_USD_PER_MTOK
        ) / 1_000_000
        return usd * _USD_INR

    def generate(self, request: GenerationRequest) -> str:
        system_text = _build_system_prompt(request.persona)
        user_text = _build_user_prompt(request)

        max_tokens = max(request.max_tokens, self.max_tokens)
        config = types.GenerateContentConfig(
            system_instruction=system_text,
            temperature=self.temperature,
            max_output_tokens=max_tokens,
            # Disable internal "thinking" — debate turns are short structured prose;
            # extended chain-of-thought just consumes the output budget before any
            # visible text is produced (which truncates the [[CLAIM]] marker).
            thinking_config=types.ThinkingConfig(thinking_budget=_DISABLE_THINKING_BUDGET),
        )

        # Saga-pattern retry with exponential backoff + jitter for transient
        # Gemini 5xx (UNAVAILABLE / INTERNAL). The google-genai SDK has its own
        # retry policy but it's miserly — a single 503 kills a 40-call debate.
        # We add a thin outer retry so one flaky call doesn't burn the run.
        attempts = 4
        for attempt in range(attempts):
            try:
                response = self._client.models.generate_content(
                    model=self.model,
                    contents=user_text,
                    config=config,
                )
                break
            except genai_errors.ServerError:
                if attempt == attempts - 1:
                    raise
                # 0.5, 1.0, 2.0 s with ±25% jitter
                delay = (0.5 * (2 ** attempt)) * (0.75 + random.random() * 0.5)
                time.sleep(delay)
            except genai_errors.APIError as exc:
                # 4xx: don't retry (config / auth / rate limit-ish error). Surface fast.
                code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
                if isinstance(code, int) and 400 <= code < 500:
                    raise
                if attempt == attempts - 1:
                    raise
                time.sleep(0.5 * (2 ** attempt))

        # Token usage tracking
        usage = getattr(response, "usage_metadata", None)
        if usage is not None:
            with self._usage_lock:
                self._usage.requests += 1
                self._usage.input_tokens += int(getattr(usage, "prompt_token_count", 0) or 0)
                self._usage.output_tokens += int(getattr(usage, "candidates_token_count", 0) or 0)

        # Pull text. The new SDK exposes `response.text`; fall back to walking parts if absent.
        text = getattr(response, "text", None)
        if text:
            return text
        chunks: list[str] = []
        for cand in getattr(response, "candidates", []) or []:
            content = getattr(cand, "content", None)
            for part in getattr(content, "parts", []) or []:
                t = getattr(part, "text", None)
                if t:
                    chunks.append(t)
        return "".join(chunks)
