"""Persona orthogonality / diversity volume (plan §4.3).

Each persona is mapped to a real-valued embedding by concatenating its
ideology vector and selected Big-Five components. The Gram-spectrum diversity
volume V(Θ) = log det(G̃ + εI) measures how non-degenerate the population is;
generation rejects any candidate that does not strictly increase V.

For the walking skeleton this is used as an audit metric on each debate.
"""

from __future__ import annotations

import numpy as np

from polylogos.schemas.persona import Persona


def persona_embedding(persona: Persona) -> np.ndarray:
    """17-d embedding: 12 ideology axes + 5 Big-Five.

    Stable order — DO NOT permute without bumping the schema version.
    """
    iv = persona.ideology
    bf = persona.big_five
    return np.array(
        [
            iv.statist_libertarian,
            iv.traditionalist_progressive,
            iv.hawkish_dovish,
            iv.centralist_federalist,
            iv.equality_meritocracy,
            iv.secular_religious,
            iv.nationalist_globalist,
            iv.market_planner,
            iv.individualist_collectivist,
            iv.realist_idealist,
            iv.interventionist_nonaligned,
            iv.composite_hindutva,
            bf.openness,
            bf.conscientiousness,
            bf.extraversion,
            bf.agreeableness,
            bf.neuroticism,
        ],
        dtype=np.float64,
    )


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def diversity_volume(personas: list[Persona], eps: float = 1e-3) -> float:
    """V(Θ) = log det(G̃ + εI); higher = more diverse."""
    if not personas:
        return float("-inf")
    embeddings = np.stack([persona_embedding(p) for p in personas])
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    normed = embeddings / norms
    g_tilde = normed @ normed.T
    sign, logdet = np.linalg.slogdet(g_tilde + eps * np.eye(len(personas)))
    if sign <= 0:
        return float("-inf")
    return float(logdet)


def population_orthogonality(personas: list[Persona]) -> float:
    """Mean pairwise cosine over the off-diagonal of the embedding Gram matrix.

    Lower is more orthogonal. Plan SLO target: < 0.7.
    """
    if len(personas) < 2:
        return 0.0
    embeddings = np.stack([persona_embedding(p) for p in personas])
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    normed = embeddings / norms
    g = normed @ normed.T
    n = g.shape[0]
    off_diag_sum = g.sum() - np.trace(g)
    return float(off_diag_sum / (n * (n - 1)))
