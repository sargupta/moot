"""Single-cluster 4-round structured debate (plan §4 + §5.2 ClusterDebate).

Walking-skeleton implementation: in-process, sequential. Production maps each
round to a Google-ADK ParallelAgent / SequentialAgent / LoopAgent (plan §5).
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from polylogos.dynamics import (
    cluster_entropy,
    fj_step,
    init_state,
    population_orthogonality,
    trust_matrix,
)
from polylogos.dynamics.orthogonality import diversity_volume
from polylogos.graph import ArgumentGraph, extract_claims_from_turn
from polylogos.llm import GenerationRequest
from polylogos.schemas.debate import Round, Turn

if TYPE_CHECKING:
    from polylogos.dynamics.friedkin_johnsen import FJState
    from polylogos.llm import LLMProvider
    from polylogos.schemas.persona import Persona


_ROUND_PLAN: list[tuple[Round, str, int]] = [
    (Round.OPENING, "opening", 0),
    (Round.CROSS_EXAM, "cross_exam", 1),
    (Round.REBUTTAL, "rebuttal", 2),
    (Round.CLOSING, "closing", 3),
]

_ENTROPY_FLOOR_NATS = 0.42  # plan §4.1 corollary


@dataclass
class ClusterResult:
    transcript: list[Turn]
    graph: ArgumentGraph
    personas: list
    final_orthogonality: float
    final_cluster_entropy: float
    final_diversity_volume: float
    entropy_floor_violations: int = 0
    round_entropies: list[float] = field(default_factory=list)
    belief_snapshots: list = field(default_factory=list)  # list[np.ndarray (N, 5)] per round_index 0..4


@dataclass
class ClusterDebate:
    """One cluster — 10 personas, 4 rounds, deterministic with a seed.

    Within a round all persona turns are independent (each agent answers from
    the prior-round transcript only), so they run in parallel via a thread
    pool — provider I/O is the bottleneck, not Python-level CPU. Across rounds
    we serialise: round k+1 sees round k's full transcript.
    """

    personas: list[Persona]
    topic: str
    provider: LLMProvider
    seed: int = 42
    max_concurrent_calls: int = 10

    def run(self) -> ClusterResult:
        graph = ArgumentGraph()
        transcript: list[Turn] = []

        # Belief dynamics initialisation (plan §4.1)
        state: FJState = init_state(self.personas, self.topic)
        w = trust_matrix(self.personas)
        round_entropies: list[float] = [cluster_entropy(state)]
        floor_violations = 0
        # Snapshot of per-agent belief simplex at each round boundary
        # (round_index 0 = before opening, 1 = after opening, …, 4 = after closing).
        belief_snapshots: list = [state.p_now.copy()]

        for round_kind, instruction, round_number in _ROUND_PLAN:
            context_for_round = self._render_context(transcript, round_number)
            requests = [
                (
                    persona,
                    GenerationRequest(
                        persona=persona,
                        topic=self.topic,
                        instruction=instruction,
                        context=context_for_round,
                        seed=self.seed,
                        extra={"round_number": round_number},
                    ),
                )
                for persona in self.personas
            ]

            # Concurrent within the round (independent calls, I/O-bound).
            # Saga-pattern: a single agent's failure must not kill the whole
            # debate. If a turn fails after the provider's own retries, we
            # substitute a flagged placeholder so the rest of the debate
            # continues; the placeholder carries a neutral claim marker.
            def _generate(pair):
                persona, req = pair
                try:
                    return (persona, self.provider.generate(req))
                except Exception as exc:
                    note = (
                        f"(Turn lost to transient provider failure: "
                        f"{type(exc).__name__}: {exc!s})"
                    )
                    fallback = (
                        f"{note}\n\n[[CLAIM:neutral]] "
                        f"This member's turn was not recorded due to a transient "
                        f"counsel-call failure; treat as abstention. [[/CLAIM]]"
                    )
                    return (persona, fallback)

            workers = max(1, min(self.max_concurrent_calls, len(requests)))
            with ThreadPoolExecutor(max_workers=workers) as pool:
                results = list(pool.map(_generate, requests))

            for persona, text in results:
                claims = extract_claims_from_turn(
                    text=text,
                    asserted_by=persona.persona_id,
                    round_number=round_number,
                )
                for claim in claims:
                    graph.add_claim(claim)
                turn = Turn(
                    persona_id=persona.persona_id,
                    persona_label=persona.short_label(),
                    round=round_kind,
                    round_number=round_number,
                    text=text,
                    claim_ids=[c.claim_id for c in claims],
                )
                transcript.append(turn)

            # Friedkin-Johnsen step at the end of each round
            state = fj_step(state, w, epsilon=0.6)
            entropy = cluster_entropy(state)
            round_entropies.append(entropy)
            belief_snapshots.append(state.p_now.copy())
            if entropy < _ENTROPY_FLOOR_NATS:
                floor_violations += 1

        # Heuristic supports/rebuts edges so PageRank is meaningful in the skeleton
        graph.auto_link_within_round()

        return ClusterResult(
            transcript=transcript,
            graph=graph,
            personas=list(self.personas),
            final_orthogonality=population_orthogonality(self.personas),
            final_cluster_entropy=round_entropies[-1],
            final_diversity_volume=diversity_volume(self.personas),
            entropy_floor_violations=floor_violations,
            round_entropies=round_entropies,
            belief_snapshots=belief_snapshots,
        )

    @staticmethod
    def _render_context(transcript: list[Turn], round_number: int) -> str:
        """Render prior turns from earlier rounds — bounded to keep prompts compact."""
        if round_number == 0:
            return ""
        prior = [t for t in transcript if t.round_number < round_number]
        # Take last 12 turns max so the mock receives a non-trivial but not enormous context.
        prior_tail = prior[-12:]
        return "\n\n".join(f"[{t.persona_label} | {t.round.value}] {t.text}" for t in prior_tail)
