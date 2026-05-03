"""Math invariants: Friedkin-Johnsen on the simplex, orthogonality bounds."""

from __future__ import annotations

import numpy as np

from polylogos.dynamics import (
    cluster_entropy,
    fj_step,
    init_state,
    trust_matrix,
)
from polylogos.personas.seed_archetypes import DEFENSE_SEED


def test_fj_update_preserves_simplex() -> None:
    state = init_state(DEFENSE_SEED, topic="test topic")
    w = trust_matrix(DEFENSE_SEED)
    for _ in range(8):
        state = fj_step(state, w)
        for row in state.p_now:
            assert np.all(row >= 0)
            assert abs(row.sum() - 1.0) < 1e-8


def test_entropy_floor_holds_under_lambda_min() -> None:
    """Plan §4.1 corollary: with λ_min = 0.15, cluster entropy stays above
    ~0.42 nats — i.e. the cluster doesn't collapse to a single mode."""
    state = init_state(DEFENSE_SEED, topic="should we accelerate AMCA Mk-2")
    w = trust_matrix(DEFENSE_SEED)
    entropies: list[float] = [cluster_entropy(state)]
    for _ in range(8):
        state = fj_step(state, w)
        entropies.append(cluster_entropy(state))
    assert min(entropies) > 0.42, (
        f"Cluster entropy fell below the anti-collapse floor: {entropies}"
    )


def test_trust_matrix_is_row_stochastic() -> None:
    w = trust_matrix(DEFENSE_SEED)
    row_sums = w.sum(axis=1)
    assert np.allclose(row_sums, 1.0, atol=1e-8)
    assert (np.diag(w) == 0).all()  # no self-trust by construction
