"""In-memory Toulmin argument graph + PageRank claim ranking.

Walking-skeleton implementation backed by `networkx`. Production replaces this
with Neo4j (plan §4.6) without changing the call surface much — `ArgumentGraph`
is the seam.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from uuid import UUID

import networkx as nx
import numpy as np

from polylogos.schemas.argument import ArgumentEdge, Claim, EdgeType, Stance

_CLAIM_RE = re.compile(r"\[\[CLAIM:(?P<stance>[a-z_]+)\]\]\s*(?P<text>.+?)\s*\[\[/CLAIM\]\]", re.DOTALL)


@dataclass
class ArgumentGraph:
    """Toulmin argument graph: nodes are claims, edges typed (supports/rebuts/qualifies)."""

    claims: dict[UUID, Claim] = field(default_factory=dict)
    edges: list[ArgumentEdge] = field(default_factory=list)

    def add_claim(self, claim: Claim) -> None:
        self.claims[claim.claim_id] = claim

    def link(self, source: UUID, target: UUID, edge_type: EdgeType, weight: float = 0.5) -> None:
        self.edges.append(
            ArgumentEdge(source=source, target=target, type=edge_type, weight=weight)
        )

    def to_networkx(self) -> nx.DiGraph:
        g: nx.DiGraph = nx.DiGraph()
        for claim_id, claim in self.claims.items():
            g.add_node(claim_id, stance=claim.stance, text=claim.text, asserted_by=claim.asserted_by)
        for edge in self.edges:
            g.add_edge(edge.source, edge.target, type=edge.type, weight=edge.weight)
        return g

    def auto_link_within_round(self) -> None:
        """Heuristic: within a round, claims with same stance support each other;
        opposed stances rebut.

        Real synthesis (Phase 2+) will use stance-conditioned NLI to assign edge
        types from claim text. For the skeleton this is good enough for PageRank
        to surface central claims.
        """
        by_round: dict[int, list[Claim]] = {}
        for claim in self.claims.values():
            by_round.setdefault(claim.round_number, []).append(claim)
        for claims_in_round in by_round.values():
            for a in claims_in_round:
                for b in claims_in_round:
                    if a.claim_id == b.claim_id:
                        continue
                    if a.stance == b.stance:
                        self.link(a.claim_id, b.claim_id, EdgeType.SUPPORTS, weight=0.3)
                    elif a.stance.to_scalar() * b.stance.to_scalar() < 0:
                        self.link(a.claim_id, b.claim_id, EdgeType.REBUTS, weight=0.4)


def extract_claims_from_turn(text: str, asserted_by: UUID, round_number: int) -> list[Claim]:
    """Pull marker-delimited claims out of a mock-generated turn.

    The MockProvider embeds claims as "[[CLAIM:<stance>]] ... [[/CLAIM]]". Real
    LLM providers will produce structured outputs (Pydantic / function-calling)
    so this regex path is mock-only — kept here to keep the skeleton self-contained.
    """
    out: list[Claim] = []
    for match in _CLAIM_RE.finditer(text):
        stance_str = match.group("stance").strip()
        try:
            stance = Stance(stance_str)
        except ValueError:
            continue
        out.append(
            Claim(
                asserted_by=asserted_by,
                text=match.group("text").strip(),
                stance=stance,
                round_number=round_number,
                confidence=0.65,
            )
        )
    return out


def rank_claims(
    graph: ArgumentGraph,
    alpha: float = 0.85,
    max_iter: int = 100,
    tol: float = 1e-6,
) -> dict[UUID, float]:
    """Personalised PageRank over claim nodes (plan §4.6).

    Numpy-only implementation — avoids scipy dep that networkx 3.6 wants.
    Uniform teleport in the skeleton; Phase 2+ biases toward evidence-anchored claims.
    """
    nodes = list(graph.claims.keys())
    n = len(nodes)
    if n == 0:
        return {}

    index = {nid: i for i, nid in enumerate(nodes)}
    weights = np.zeros((n, n))
    for edge in graph.edges:
        i = index.get(edge.source)
        j = index.get(edge.target)
        if i is None or j is None:
            continue
        weights[i, j] += edge.weight

    out_sums = weights.sum(axis=1, keepdims=True)
    dangling = (out_sums.flatten() == 0)
    out_sums[out_sums == 0] = 1.0
    transition = weights / out_sums  # row-stochastic on non-dangling rows

    teleport = np.full(n, 1.0 / n)
    rank = np.full(n, 1.0 / n)
    for _ in range(max_iter):
        dangling_mass = rank[dangling].sum()
        new_rank = (
            alpha * (transition.T @ rank + dangling_mass * teleport)
            + (1.0 - alpha) * teleport
        )
        if np.linalg.norm(new_rank - rank, ord=1) < tol:
            rank = new_rank
            break
        rank = new_rank

    return {nodes[i]: float(rank[i]) for i in range(n)}


# Keep the import lint-clean: networkx is still used by `to_networkx` for
# downstream visualisations; the rank now does not require it.
_ = nx
