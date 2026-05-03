"""Friedkin-Johnsen belief update with bounded confidence (plan §4.1).

p_i^(t+1) = λ_i · p_i^(0) + (1 - λ_i) · Σ_{j ∈ N_i^(t)} w_ij · p_j^(t)

where:
  - λ_i = persona stubbornness
  - N_i^(t) = bounded-confidence neighbourhood (∥p_i - p_j∥_1 ≤ ε)
  - w_ij ∝ trust based on persona similarity + topic-expertise

The skeleton uses 5 stance bins (matching Stance enum). The math holds for any
finite simplex.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from polylogos.dynamics.orthogonality import persona_embedding
from polylogos.schemas.persona import Persona


N_STANCE_BINS = 5


@dataclass
class FJState:
    """Belief state for one cluster.

    p_now: current beliefs (n_agents, N_STANCE_BINS), each row a simplex.
    p_init: initial beliefs (anchor for stubbornness term).
    """

    p_now: np.ndarray
    p_init: np.ndarray
    lambdas: np.ndarray  # (n_agents,)


def _stance_to_simplex(scalar: float) -> np.ndarray:
    """Convert ideology-driven scalar in [-1, 1] to a 5-bin distribution.

    Centred Gaussian-ish mass over the 5 stance bins; the scalar shifts the mode.
    """
    centers = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])
    sigma = 0.55
    raw = np.exp(-((centers - scalar) ** 2) / (2 * sigma**2))
    return raw / raw.sum()


def init_state(personas: list[Persona], topic: str) -> FJState:
    """Initial beliefs from persona ideology (deterministic per topic).

    The mock-debate stance heuristic in `MockProvider` uses a similar mapping;
    this simply lifts it onto a stance simplex for the dynamics layer.
    """
    del topic  # topic enters via the MockProvider; here we anchor on persona ideology
    n = len(personas)
    p = np.zeros((n, N_STANCE_BINS))
    lambdas = np.zeros(n)
    for i, persona in enumerate(personas):
        iv = persona.ideology
        scalar = (
            0.45 * iv.hawkish_dovish
            + 0.20 * iv.nationalist_globalist
            + 0.15 * iv.statist_libertarian
            + 0.10 * iv.realist_idealist
            + 0.10 * iv.composite_hindutva
        )
        p[i] = _stance_to_simplex(scalar)
        lambdas[i] = max(0.15, persona.stubbornness())  # plan §4.1 corollary: λ_min = 0.15
    return FJState(p_now=p, p_init=p.copy(), lambdas=lambdas)


def trust_matrix(personas: list[Persona]) -> np.ndarray:
    """Row-stochastic trust matrix W from persona similarity.

    w_ij ∝ exp(β · cos(θ_i, θ_j)); zero on diagonal; row-normalised.
    """
    n = len(personas)
    embeddings = np.stack([persona_embedding(p) for p in personas])
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normed = embeddings / np.where(norms == 0, 1, norms)
    sims = normed @ normed.T  # cosine similarities
    beta = 2.0
    raw = np.exp(beta * sims)
    np.fill_diagonal(raw, 0.0)  # don't self-trust in this formulation
    row_sums = raw.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    return raw / row_sums


def fj_step(state: FJState, w: np.ndarray, epsilon: float = 0.6) -> FJState:
    """One Friedkin-Johnsen update with Hegselmann-Krause bounded confidence.

    Returns a NEW FJState; original is unchanged (caller-friendly).
    """
    n = state.p_now.shape[0]
    new_p = np.zeros_like(state.p_now)
    for i in range(n):
        # Bounded-confidence: only listen to neighbours within ε in L1
        l1_dist = np.linalg.norm(state.p_now - state.p_now[i], ord=1, axis=1)
        in_neighbourhood = l1_dist <= epsilon
        in_neighbourhood[i] = False  # don't include self
        if not in_neighbourhood.any():
            new_p[i] = state.p_now[i]
            continue
        w_row = w[i].copy()
        w_row[~in_neighbourhood] = 0.0
        if w_row.sum() == 0:
            new_p[i] = state.p_now[i]
            continue
        w_row = w_row / w_row.sum()
        peer_mix = w_row @ state.p_now
        new_p[i] = state.lambdas[i] * state.p_init[i] + (1 - state.lambdas[i]) * peer_mix
        new_p[i] = new_p[i] / new_p[i].sum()  # numerical safety on the simplex
    return FJState(p_now=new_p, p_init=state.p_init, lambdas=state.lambdas)


def cluster_entropy(state: FJState) -> float:
    """Shannon entropy of the cluster mean stance (plan §4.1 corollary).

    H_min ≈ 0.42 nats is the anti-collapse floor. We monitor this number and
    flag debates that fall below it.
    """
    mean_p = state.p_now.mean(axis=0)
    eps = 1e-12
    return float(-(mean_p * np.log(mean_p + eps)).sum())
