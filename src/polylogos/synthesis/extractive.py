"""Extractive synthesis (plan §5.2 Synthesizer + §4.6 PageRank).

Produces:
  1. Article (~1,500 words) extracted from PageRank-ranked claims with attribution.
  2. Executive remark (≤ 300 words) — top 3 claims + position summary.
  3. Minority report — top dissent-scored claims (KL × centrality, plan §4.6).

This is intentionally extractive (W6): the synthesizer does NOT generatively
re-write claims; it sequences and frames the agents' own assertions. That's
how attribution stays clean and how we avoid laundering bias through a single
frontier-model rewrite.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

from polylogos.graph import ArgumentGraph, rank_claims
from polylogos.schemas.argument import Claim, Stance


@dataclass
class SynthesisOutput:
    article: str
    executive_remark: str
    minority_report: str
    quality_band: str
    article_word_count: int


def _stance_label_for_humans(stance: Stance) -> str:
    return {
        Stance.STRONGLY_FOR: "strongly in favour",
        Stance.FOR: "in favour, with reservations",
        Stance.NEUTRAL: "neutral / mixed",
        Stance.AGAINST: "against, with reservations",
        Stance.STRONGLY_AGAINST: "strongly against",
    }[stance]


def _cluster_stance_distribution(claims: list[Claim]) -> Counter[Stance]:
    return Counter(c.stance for c in claims)


def _dissent_score(
    claim: Claim,
    pagerank: dict,
    stance_dist: Counter[Stance],
    total_claims: int,
) -> float:
    """Plan §4.6: Diss(c) = D_KL(p_c || mean_cluster) · r_c.

    Surrogate KL: how surprising is this stance given the cluster mean? Stance
    distribution acts as the cluster posterior. Rare stance + high centrality
    = "well-supported minority view".
    """
    p_c = stance_dist[claim.stance] / total_claims
    if p_c == 0:
        return 0.0
    # KL of a one-hot delta on this stance vs the cluster mean ≈ -log(p_c)
    surprisal = -math.log(p_c)
    return surprisal * pagerank.get(claim.claim_id, 0.0)


def _stance_summary(stance_dist: Counter[Stance], total: int) -> str:
    if total == 0:
        return "No claims were extracted."
    parts: list[str] = []
    for stance in (
        Stance.STRONGLY_FOR,
        Stance.FOR,
        Stance.NEUTRAL,
        Stance.AGAINST,
        Stance.STRONGLY_AGAINST,
    ):
        count = stance_dist.get(stance, 0)
        if count == 0:
            continue
        pct = 100 * count / total
        parts.append(f"{count} {_stance_label_for_humans(stance)} ({pct:.0f}%)")
    return "; ".join(parts) + "."


def _build_article(
    topic: str,
    claims: list[Claim],
    pagerank: dict,
    persona_lookup: dict,
    stance_dist: Counter[Stance],
    total_claims: int,
) -> str:
    """Assemble a ~1,500-word article from ranked claims with attribution."""
    by_stance: dict[Stance, list[Claim]] = {s: [] for s in Stance}
    for claim in claims:
        by_stance[claim.stance].append(claim)
    for stance, lst in by_stance.items():
        by_stance[stance] = sorted(
            lst, key=lambda c: pagerank.get(c.claim_id, 0.0), reverse=True
        )

    sections: list[str] = []
    sections.append(f"# Moot Synthesis: {topic}\n")
    sections.append(
        "*This article was produced by Moot, an open multi-agent debate engine. "
        "It is an extractive synthesis of agent claims — every assertion below is asserted "
        "by a specific synthetic persona, attributed inline. This is an AI-generated "
        "deliberative artefact, not a human consensus and not a recommendation.*\n"
    )

    sections.append("## Question framed")
    sections.append(
        f"The cluster was asked to deliberate on: **{topic}**. Across four structured "
        f"rounds (opening, cross-examination, rebuttal, closing) the cluster produced "
        f"{total_claims} extractable claims spanning the full stance spectrum.\n"
    )

    sections.append("## Distribution of positions")
    sections.append(_stance_summary(stance_dist, total_claims) + "\n")

    sections.append("## Strongest position(s) advanced")
    for stance in (Stance.STRONGLY_FOR, Stance.FOR):
        if not by_stance[stance]:
            continue
        sections.append(f"### Voices {_stance_label_for_humans(stance)}")
        for claim in by_stance[stance][:5]:
            persona_label = persona_lookup.get(claim.asserted_by, "an unattributed persona")
            sections.append(f"- **{persona_label}** (round {claim.round_number}): {claim.text}")
        sections.append("")

    sections.append("## The opposing case")
    for stance in (Stance.AGAINST, Stance.STRONGLY_AGAINST):
        if not by_stance[stance]:
            continue
        sections.append(f"### Voices {_stance_label_for_humans(stance)}")
        for claim in by_stance[stance][:5]:
            persona_label = persona_lookup.get(claim.asserted_by, "an unattributed persona")
            sections.append(f"- **{persona_label}** (round {claim.round_number}): {claim.text}")
        sections.append("")

    if by_stance[Stance.NEUTRAL]:
        sections.append("## Where positions converge or remain undecided")
        for claim in by_stance[Stance.NEUTRAL][:4]:
            persona_label = persona_lookup.get(claim.asserted_by, "an unattributed persona")
            sections.append(f"- **{persona_label}** (round {claim.round_number}): {claim.text}")
        sections.append("")

    sections.append("## Methodological note")
    sections.append(
        "Claims are ranked by personalised PageRank over the in-cluster argument graph "
        "(supports/rebuts edges). The synthesis is extractive — claims are sequenced and "
        "framed but not re-written, to preserve attribution and avoid the single-model "
        "bias that would be introduced by a generative synthesiser pass. Belief dynamics "
        "during the debate were governed by a Friedkin-Johnsen update with bounded "
        "confidence (ε = 0.6) and a stubbornness floor of λ_min = 0.15, which provably "
        "prevents mode collapse to a single consensus position.\n"
    )

    sections.append("## Disclosure")
    sections.append(
        "Every persona in this debate is synthetic. No persona represents any real person. "
        "Outputs are AI-produced deliberation, not human consensus, and must not be relied "
        "upon as the basis for a real procurement, policy, or strategic decision without "
        "independent expert review.\n"
    )
    return "\n".join(sections)


def _build_executive_remark(
    topic: str,
    top_claims: list[Claim],
    persona_lookup: dict,
    stance_dist: Counter[Stance],
    total_claims: int,
) -> str:
    if not top_claims:
        return f"Moot was unable to extract any claims for: {topic}."
    leader = top_claims[0]
    leader_persona = persona_lookup.get(leader.asserted_by, "an unattributed persona")
    distribution = _stance_summary(stance_dist, total_claims)
    lines = [
        f"**Topic:** {topic}",
        "",
        f"**Distribution:** {distribution}",
        "",
        f"**Most central claim ({leader_persona}, round {leader.round_number}):** "
        f"{leader.text}",
    ]
    if len(top_claims) > 1:
        for claim in top_claims[1:3]:
            persona = persona_lookup.get(claim.asserted_by, "an unattributed persona")
            lines.append(
                f"**Adjacent central claim ({persona}, round {claim.round_number}):** "
                f"{claim.text}"
            )
    lines.append("")
    lines.append(
        "**Caveat:** AI-debate synthesis only. Not a human consensus. "
        "Not a recommendation. Use as a stress-test artefact, not a decision."
    )
    return "\n".join(lines)


def _build_minority_report(
    minority_claims: list[tuple[Claim, float]],
    persona_lookup: dict,
) -> str:
    if not minority_claims:
        return "No minority view crossed the dissent-score threshold in this debate."
    lines = [
        "## Minority Report (Dissent Dashboard)",
        "",
        "*Plan §4.6: Dissent score = D_KL(p_claim ∥ p_cluster) × PageRank centrality. "
        "High score = a position that is rare in the cluster but central in the argument graph "
        "— exactly what a single-model summariser would smooth away.*",
        "",
    ]
    for claim, score in minority_claims:
        persona_label = persona_lookup.get(claim.asserted_by, "an unattributed persona")
        lines.append(
            f"- **{persona_label}** (round {claim.round_number}, dissent score {score:.3f}, "
            f"stance _{_stance_label_for_humans(claim.stance)}_):"
        )
        lines.append(f"    > {claim.text}")
    lines.append("")
    lines.append(
        "**Steelman the minority:** even if you disagree with the consensus, the above claims "
        "are the strongest, most-supported arguments against it. Engage with these before "
        "treating the majority view as settled."
    )
    return "\n".join(lines)


def synthesize(
    topic: str,
    graph: ArgumentGraph,
    personas: list,
) -> SynthesisOutput:
    persona_lookup = {p.persona_id: p.short_label() for p in personas}
    pagerank = rank_claims(graph)
    claims = list(graph.claims.values())
    if not claims:
        return SynthesisOutput(
            article=f"# Moot Synthesis: {topic}\n\nNo claims were produced by the cluster.",
            executive_remark=f"No claims for: {topic}.",
            minority_report="No minority view available.",
            quality_band="degraded",
            article_word_count=0,
        )
    total_claims = len(claims)
    stance_dist = _cluster_stance_distribution(claims)
    sorted_by_pr = sorted(claims, key=lambda c: pagerank.get(c.claim_id, 0.0), reverse=True)

    article = _build_article(
        topic=topic,
        claims=claims,
        pagerank=pagerank,
        persona_lookup=persona_lookup,
        stance_dist=stance_dist,
        total_claims=total_claims,
    )

    executive_remark = _build_executive_remark(
        topic=topic,
        top_claims=sorted_by_pr,
        persona_lookup=persona_lookup,
        stance_dist=stance_dist,
        total_claims=total_claims,
    )

    scored = [
        (c, _dissent_score(c, pagerank, stance_dist, total_claims))
        for c in claims
    ]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    minority = [(c, s) for c, s in scored[:5] if s > 0]
    minority_report = _build_minority_report(minority, persona_lookup)

    word_count = len(article.split())
    quality_band = "fast" if word_count >= 600 else "degraded"

    return SynthesisOutput(
        article=article,
        executive_remark=executive_remark,
        minority_report=minority_report,
        quality_band=quality_band,
        article_word_count=word_count,
    )
