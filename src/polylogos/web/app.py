"""FastAPI app for the Polylogos web UI.

Endpoints:
  GET  /                       → static single-page UI (the Stance Theatre)
  GET  /api/health             → liveness + provider info
  GET  /api/sample-topics      → suggested defense MVP topics (plan §6.3)
  GET  /api/personas           → metadata for the seed persona pool
  POST /api/debate             → run a debate, return rich JSON for the UI

Design notes:
  * Per-round per-agent belief simplices are projected to 2D in
    `_project_beliefs_to_2d` so the frontend doesn't need numpy.
  * The argument graph is serialised flat (nodes + edges) with PageRank scores
    so D3-force can render it without re-computing centrality.
  * Dissent score per claim mirrors the synthesis layer (plan §4.6) and is
    included so the Dissent Dashboard maps to the same numbers as the report.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from polylogos.debate import DebateRun, Polylogos
from polylogos.graph import rank_claims
from polylogos.personas import available_pools, default_pool
from polylogos.schemas.argument import Stance


_STATIC_DIR = Path(__file__).resolve().parent / "static"

# 5-bin support score weights — matches the FJ stance bins ordering.
# (strongly_against, against, neutral, for, strongly_for)
_SUPPORT_WEIGHTS = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])
_LOG_BINS = math.log(5)  # max entropy of a 5-way simplex


# Sample questions per pool. Each list is curated to span multiple domains the
# panel's archetypes can credibly speak to — so a question may touch on
# operational, strategic, ethical, financial, or methodological dimensions
# beyond the panel's headline specialty. Force-a-stance phrasing throughout;
# vague "discuss X" prompts are deliberately avoided.
_SAMPLE_TOPICS_BY_POOL: dict[str, list[str]] = {
    "citizens": [
        # Education ministry scheme
        "Should the Ministry of Education's PM SHRI Schools scheme replace the existing Kendriya Vidyalaya network, or run in parallel?",
        # Aviation ministry pricing
        "Should the Ministry of Civil Aviation cap dynamic surge-pricing on domestic flights at 30% over base fare during festival season?",
        # Labour & gig economy
        "Should EPFO auto-enrol gig workers (Uber / Zomato / Swiggy / Urban Company) at the platform's expense, or keep enrolment voluntary?",
        # Health / digital
        "Should the Ayushman Bharat Digital Mission make every citizen's health record auto-portable across hospitals by default, with opt-out?",
        # Urban / transport
        "Should Bengaluru / Mumbai / Delhi introduce congestion-pricing for private cars in the central business district during peak hours?",
        # GST / tax simplification
        "Should the GST Council move to a single-rate structure (one merit + one demerit slab) or retain the current four-slab system?",
        # Agriculture
        "Should farm MSP be replaced by a direct-cash crop-diversification incentive (PM-KISAN style), or retained as the price floor?",
        # Banking / inclusion
        "Should public-sector banks be ranked publicly each quarter on their lending-to-MSMEs ratio, with consequences for laggards?",
        # Enterprise / pricing decision
        "An enterprise SaaS company sells to Indian banks. The largest bank asks for a 60% discount assuming all banks will follow — accept or hold?",
        # Enterprise / hiring
        "A 200-person Indian IT company is debating a 4-day work-week pilot for engineering. Does it lift productivity or normalise underperformance?",
        # Election / governance
        "Should the proposed 'One Nation, One Voter ID' linking Aadhaar to electoral rolls be made mandatory, or remain opt-in?",
        # Climate / state economy
        "Should Indian metro states phase out registrations for new ICE two-wheelers by 2030, or wait for the EV charging network to mature?",
    ],
    "defense": [
        # Procurement
        "Should India accelerate AMCA Mk-2 versus committing to a second tranche of foreign 4.5-gen fighters?",
        # Doctrine / organisation
        "Is theaterisation in its currently proposed form executable by 2030 given inter-service cultural and resource constraints?",
        # Crisis scenario
        "What is the optimal Indian posture if the Strait of Hormuz is interdicted for 90 days?",
        # Budget
        "Should India increase defence R&D from 6% to 12% of the defence budget within five years?",
        # Doctrine / counter-terror
        "Should India publicly declare a no-first-use shift on conventional precision strikes against terror infrastructure?",
        # Cyber
        "Does India need a dedicated Cyber Command separate from existing tri-service structures, or is integration sufficient?",
        # Unmanned systems
        "Should the IAF prioritise unmanned loyal-wingman programmes over fifth-generation manned fighter procurement?",
        # Industrial base
        "Is Aatmanirbhar Bharat in defence — strictly enforced — accelerating or delaying real Indian capability?",
        # Personnel
        "Should the Agnipath scheme be extended, modified, or retired before its first five-year evaluation?",
        # Diplomacy / alliance
        "Does India gain or lose by formalising QUAD's military components beyond current ad-hoc cooperation?",
        # Space
        "Is Indian space-domain awareness a 24-month build-it-now problem, or a 10-year strategic-patience problem?",
        # Ethics / transparency
        "Should civilian-casualty estimates be made public for any cross-border kinetic operation, or is opacity an operational necessity?",
    ],
    "investors": [
        # Polylogos-specific (the founder's own questions)
        "Is Polylogos — a 500-AI-agent debate engine targeting Indian defense as MVP — a fundable, defensible deeptech business?",
        "If Polylogos must pivot, which wedge wins: AI-lab eval / red-teaming, corporate strategy red-teaming, or litigation simulation for top law firms?",
        "Should the founder kill this idea, build it as a paper / library only, or commit to one narrow vertical and cut the rest?",
        "Is 'open-core MIT engine + paid SaaS / sovereign tier' the right business model, or does it kill defensibility?",
        # Generic founder decisions
        "Founder asks for an $8M seed at $30M post on a prototype with no paying customers — is that a fundable round in 2026?",
        "Should an Indian-incorporated deeptech company chase Bay Area pricing power, or is regional pricing the realistic ceiling?",
        "If three Big Law partners each wire $100K for a 90-day litigation-simulation pilot today, take them — or hold for the AI-lab buyer that wires more?",
        "Should a deeptech founder hire a product-distribution-first second co-founder, or a technical one, given the engine already works?",
        # Market / category timing
        "Is 'AI eval & red-teaming' a venture-fundable category in 2026, or is it already consolidating into incumbents (Anthropic, Scale, Patronus)?",
        "Is now (2026) still the right time to start an AI infrastructure company, or has the window closed as foundation labs vertically integrate?",
        # Cap table / strategy
        "Should an early-stage deeptech founder accept defense-industrial-base capital, or is dilution by primes a strategic mistake?",
        # Talent / culture
        "Is hiring senior alignment researchers away at 4× pay strategically rational, or does the cultural cost outweigh the speed gain?",
    ],
    "evaluators": [
        # Polylogos's own wedge (current)
        "Is a curated 500-persona evaluator population a genuinely defensible moat for AI-lab eval / red-teaming, or six months of work for any motivated alignment team?",
        "Should frontier-lab post-training teams pay $50K–$300K ARR per seat for diverse-population evals, or build internally?",
        # Methodology
        "Does persona-population eval surface failure modes that current benchmarks (MMLU, HELM, AdvBench, etc.) systematically miss?",
        "Is 'augmentation of red-team workflows' a sharper value-prop than 'replace human red-teamers'?",
        # Business model
        "Should the eval product be open-source with a hosted tier (à la Weaviate / LangChain), or proprietary like Scale AI's evals?",
        # Adversarial / robustness
        "If a frontier lab fine-tunes its own model to game the persona-eval suite, has the evaluator failed — or is gameable evaluation still useful?",
        # Deception / sandbagging
        "Is sandbagging during evals a real safety problem on current frontier models, or a theoretical artifact of contrived test conditions?",
        # Release decision
        "Should a model that fails 5% of persona-population safety prompts be released with mitigations, or held back entirely?",
        # Regulation / policy
        "Is mandatory pre-release red-teaming (per EU AI Act and similar) a net positive for safety, or has it become regulatory theatre?",
        # Open weights
        "Should open-weight frontier models be released at all in 2026, given the current jailbreak and fine-tune attack surface?",
        # Eval scope / sociotechnical
        "Are sociotechnical evals (ethnographic, cross-cultural) more important than capability evals — or merely complementary?",
        # Field coordination
        "Should the field standardise on a single shared red-team corpus, or does fragmentation actually serve safety better?",
    ],
}


class DebateRequest(BaseModel):
    topic: str = Field(min_length=10, max_length=500)
    cluster_size: int = Field(default=10, ge=2, le=10)
    seed: int = Field(default=42, ge=0, le=10_000_000)
    pool: str = Field(
        default="citizens",
        description="Which persona pool to draw from. One of: citizens, defense, investors, evaluators.",
    )
    provider: str | None = Field(
        default=None,
        description=(
            "Explicit provider choice. One of: mock, anthropic, gemini. None = auto: "
            "prefer Gemini if GEMINI_API_KEY set, else Anthropic if ANTHROPIC_API_KEY set, "
            "else mock."
        ),
    )
    force_mock: bool = Field(
        default=False,
        description="Backwards-compat shortcut for provider='mock'.",
    )


@dataclass
class _StanceTheatrePoint:
    persona_id: str
    persona_label: str
    round_index: int
    x: float
    y: float
    expected_stance: float
    confidence: float


def _project_beliefs_to_2d(beliefs: np.ndarray) -> list[tuple[float, float, float, float]]:
    """Project per-agent simplex beliefs to (x, y, expected_stance, confidence).

    x = expected stance value in [-1, +1]   (negative = against, positive = for)
    y = confidence in [0, 1]                  (1 - normalised entropy)

    Returns a list of (x, y, expected_stance, confidence) tuples, one per agent.
    """
    expected = beliefs @ _SUPPORT_WEIGHTS  # shape (N,)
    eps = 1e-12
    entropy = -(beliefs * np.log(beliefs + eps)).sum(axis=1)  # shape (N,), nats
    confidence = 1.0 - np.clip(entropy / _LOG_BINS, 0.0, 1.0)
    out: list[tuple[float, float, float, float]] = []
    for i in range(beliefs.shape[0]):
        out.append(
            (
                float(expected[i]),
                float(confidence[i]),
                float(expected[i]),
                float(confidence[i]),
            )
        )
    return out


def _serialise_personas(personas: list) -> list[dict[str, Any]]:  # noqa: ANN001
    rows: list[dict[str, Any]] = []
    for p in personas:
        rows.append(
            {
                "persona_id": str(p.persona_id),
                "synthetic_name": p.synthetic_name,
                "professional_identity": p.professional_identity,
                "short_label": p.short_label(),
                "birth_year": p.birth_year,
                "birth_place": p.birth_place,
                "mother_tongue": p.mother_tongue,
                "socioeconomic_class_at_birth": p.socioeconomic_class_at_birth,
                "education_summary": p.education_summary,
                "career_summary": p.career_summary,
                "argumentation_style": p.argumentation_style.value,
                "epistemic_style": p.epistemic_style.value,
                "stubbornness": float(p.stubbornness()),
                "ideology": {
                    "hawkish_dovish": p.ideology.hawkish_dovish,
                    "statist_libertarian": p.ideology.statist_libertarian,
                    "nationalist_globalist": p.ideology.nationalist_globalist,
                    "market_planner": p.ideology.market_planner,
                    "realist_idealist": p.ideology.realist_idealist,
                },
                "formative_books": [
                    {
                        "title": b.title,
                        "author": b.author,
                        "year_first_read": b.year_first_read,
                        "age_when_read": b.age_when_read,
                        "why_it_mattered": b.why_it_mattered,
                        "beliefs_changed": list(b.beliefs_changed),
                    }
                    for b in p.formative_books
                ],
            }
        )
    return rows


def _serialise_stance_theatre(run: DebateRun) -> list[list[dict[str, Any]]]:
    """One frame per round_index (0..4). Each frame is a list of N agent points."""
    frames: list[list[dict[str, Any]]] = []
    persona_meta = [(str(p.persona_id), p.short_label()) for p in run.personas]
    for round_index, beliefs in enumerate(run.cluster.belief_snapshots):
        projected = _project_beliefs_to_2d(beliefs)
        frame: list[dict[str, Any]] = []
        for (pid, label), (x, y, exp_s, conf) in zip(persona_meta, projected):
            frame.append(
                asdict(
                    _StanceTheatrePoint(
                        persona_id=pid,
                        persona_label=label,
                        round_index=round_index,
                        x=x,
                        y=y,
                        expected_stance=exp_s,
                        confidence=conf,
                    )
                )
            )
        frames.append(frame)
    return frames


def _serialise_argument_graph(run: DebateRun) -> dict[str, Any]:
    pagerank = rank_claims(run.cluster.graph)
    persona_lookup = {p.persona_id: p.short_label() for p in run.personas}
    nodes: list[dict[str, Any]] = []
    for claim_id, claim in run.cluster.graph.claims.items():
        nodes.append(
            {
                "id": str(claim_id),
                "stance": claim.stance.value,
                "round_number": claim.round_number,
                "text": claim.text,
                "asserted_by": persona_lookup.get(claim.asserted_by, "unknown"),
                "pagerank": float(pagerank.get(claim_id, 0.0)),
            }
        )
    edges: list[dict[str, Any]] = []
    for edge in run.cluster.graph.edges:
        edges.append(
            {
                "source": str(edge.source),
                "target": str(edge.target),
                "type": edge.type.value,
                "weight": float(edge.weight),
            }
        )
    return {"nodes": nodes, "edges": edges}


def _dissent_table(run: DebateRun) -> list[dict[str, Any]]:
    """Mirrors plan §4.6 dissent score: -log(p_stance) × pagerank centrality."""
    pagerank = rank_claims(run.cluster.graph)
    claims = list(run.cluster.graph.claims.values())
    if not claims:
        return []
    persona_lookup = {p.persona_id: p.short_label() for p in run.personas}
    stance_dist = Counter(c.stance for c in claims)
    total = len(claims)
    rows: list[dict[str, Any]] = []
    for c in claims:
        p_stance = stance_dist[c.stance] / total
        if p_stance == 0:
            score = 0.0
        else:
            score = -math.log(p_stance) * pagerank.get(c.claim_id, 0.0)
        rows.append(
            {
                "claim_id": str(c.claim_id),
                "stance": c.stance.value,
                "round_number": c.round_number,
                "text": c.text,
                "asserted_by": persona_lookup.get(c.asserted_by, "unknown"),
                "pagerank": float(pagerank.get(c.claim_id, 0.0)),
                "dissent_score": float(score),
            }
        )
    rows.sort(key=lambda r: r["dissent_score"], reverse=True)
    return rows


def _serialise_debate_run(run: DebateRun) -> dict[str, Any]:
    out = run.output
    return {
        "config": {
            "debate_id": str(out.config.debate_id),
            "topic": out.config.topic,
            "cluster_size": out.config.cluster_size,
            "seed": out.config.seed,
        },
        "metrics": {
            "article_word_count": len(out.article.split()),
            "quality_band": out.quality_band,
            "estimated_cost_inr": out.cost_estimate_inr,
            "final_orthogonality": out.final_orthogonality,
            "final_cluster_entropy": out.final_cluster_entropy,
            "final_diversity_volume": out.final_diversity_volume,
            "round_entropies": run.cluster.round_entropies,
            "entropy_floor_violations": run.cluster.entropy_floor_violations,
            "n_turns": len(out.transcript),
            "n_claims": len(run.cluster.graph.claims),
        },
        "article": out.article,
        "executive_remark": out.executive_remark,
        "minority_report": out.minority_report,
        "transcript": [
            {
                "turn_id": str(t.turn_id),
                "persona_id": str(t.persona_id),
                "persona_label": t.persona_label,
                "round": t.round.value,
                "round_number": t.round_number,
                "text": t.text,
                "claim_ids": [str(cid) for cid in t.claim_ids],
            }
            for t in out.transcript
        ],
        "personas": _serialise_personas(run.personas),
        "stance_theatre": _serialise_stance_theatre(run),
        "argument_graph": _serialise_argument_graph(run),
        "dissent": _dissent_table(run),
    }


def create_app() -> FastAPI:
    app = FastAPI(
        title="Polylogos",
        version="0.0.1",
        description="Open 500-agent debate engine — Phase-1 web UI (Live Stance Theatre).",
    )

    if _STATIC_DIR.is_dir():
        app.mount(
            "/static", StaticFiles(directory=str(_STATIC_DIR), html=False), name="static"
        )

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        import os

        return {
            "ok": True,
            "anthropic_key_present": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "gemini_key_present": bool(
                os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            ),
        }

    @app.get("/api/sample-topics")
    def sample_topics(pool: str = "citizens") -> dict[str, Any]:
        return {
            "pool": pool,
            "topics": _SAMPLE_TOPICS_BY_POOL.get(pool, _SAMPLE_TOPICS_BY_POOL["citizens"]),
            "available_pools": available_pools(),
        }

    @app.get("/api/personas")
    def personas(pool: str = "citizens") -> dict[str, Any]:
        return {"pool": pool, "personas": _serialise_personas(default_pool(pool).personas)}

    @app.post("/api/debate")
    def debate(req: DebateRequest) -> JSONResponse:
        try:
            engine = Polylogos(
                force_mock=req.force_mock, provider_choice=req.provider
            )
            run = engine.run_with_diagnostics(
                topic=req.topic,
                cluster_size=req.cluster_size,
                seed=req.seed,
                pool_name=req.pool,
            )
        except (RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        payload = _serialise_debate_run(run)
        payload["pool"] = req.pool
        payload["provider"] = req.provider or "auto"
        return JSONResponse(payload)

    @app.get("/")
    def root() -> FileResponse:
        index = _STATIC_DIR / "index.html"
        if not index.is_file():
            raise HTTPException(status_code=500, detail="UI bundle missing.")
        return FileResponse(index)

    return app
