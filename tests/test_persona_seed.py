"""Sanity tests for the hand-crafted defense seed."""

from __future__ import annotations

from polylogos.dynamics.orthogonality import (
    diversity_volume,
    population_orthogonality,
)
from polylogos.personas.seed_archetypes import DEFENSE_SEED, assert_seed_size


def test_seed_has_ten_personas() -> None:
    assert_seed_size()
    assert len(DEFENSE_SEED) == 10


def test_each_persona_has_exactly_five_books() -> None:
    for persona in DEFENSE_SEED:
        assert len(persona.formative_books) == 5, persona.synthetic_name


def test_books_are_temporally_plausible() -> None:
    """Sanity: a persona cannot have read a book before they were born."""
    for persona in DEFENSE_SEED:
        for book in persona.formative_books:
            assert book.year_first_read >= persona.birth_year, (
                f"{persona.synthetic_name} read {book.title} before they were born"
            )
            # Age-when-read should match (year_first_read - birth_year), allowing ±1
            implied_age = book.year_first_read - persona.birth_year
            assert abs(implied_age - book.age_when_read) <= 1, (
                f"{persona.synthetic_name}: {book.title} age mismatch "
                f"({book.age_when_read} vs implied {implied_age})"
            )


def test_population_is_orthogonal_enough() -> None:
    """Plan SLO target: mean pairwise cosine < 0.7 across the population."""
    cos = population_orthogonality(DEFENSE_SEED)
    assert cos < 0.7, f"Population orthogonality SLO violated: {cos:.3f}"


def test_population_has_finite_diversity_volume() -> None:
    vol = diversity_volume(DEFENSE_SEED)
    assert vol > float("-inf")
