"""Persona pool & sampler.

Walking-skeleton implementation: load hand-crafted seed archetypes and let the
orchestrator request a cluster sample. The generator pipeline (plan §3.2) —
Latin Hypercube Sampling, narrative gen, orthogonality gate — is a Phase-2+
deliverable.

Two pools ship with the skeleton:
  - "defense" (default) — the original 10 Indian-defense archetypes
  - "investors"          — 10 deeptech VC / mentor / operator archetypes for
                           stress-testing a business case (dogfooding the engine
                           on commercial questions like its own viability)
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from polylogos.personas.citizens_seed import CITIZENS_SEED
from polylogos.personas.eval_seed import EVAL_SEED
from polylogos.personas.investor_seed import INVESTOR_SEED
from polylogos.personas.seed_archetypes import DEFENSE_SEED
from polylogos.schemas.persona import Persona


@dataclass
class PersonaPool:
    personas: list[Persona]
    name: str = "defense"

    def __len__(self) -> int:
        return len(self.personas)


_POOLS: dict[str, list[Persona]] = {
    "citizens": CITIZENS_SEED,
    "defense": DEFENSE_SEED,
    "investors": INVESTOR_SEED,
    "evaluators": EVAL_SEED,
}


def available_pools() -> list[str]:
    return list(_POOLS.keys())


def default_pool(name: str = "defense") -> PersonaPool:
    if name not in _POOLS:
        msg = f"Unknown pool '{name}'. Available: {sorted(_POOLS)}"
        raise ValueError(msg)
    return PersonaPool(personas=list(_POOLS[name]), name=name)


def sample_cluster(pool: PersonaPool, size: int, seed: int) -> list[Persona]:
    """Sample `size` personas from the pool deterministically."""
    rng = random.Random(seed)
    if size > len(pool):
        msg = f"Requested cluster size {size} exceeds pool size {len(pool)}"
        raise ValueError(msg)
    return rng.sample(pool.personas, size)
