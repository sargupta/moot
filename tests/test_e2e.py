"""End-to-end smoke test of the walking skeleton.

Uses the deterministic mock provider (`force_mock=True`) so tests stay
hermetic and don't require an API key in CI.
"""

from __future__ import annotations

from polylogos.debate import Polylogos


TOPIC = (
    "Should India accelerate AMCA Mk-2 versus committing to a second tranche of "
    "foreign 4.5-gen fighters?"
)


def test_e2e_produces_article_and_minority_report() -> None:
    engine = Polylogos(force_mock=True)
    output = engine.run(topic=TOPIC, cluster_size=10, seed=1234)

    # 10 personas × 4 rounds = 40 turns
    assert len(output.transcript) == 40

    # Article must be substantive
    assert len(output.article.split()) >= 600
    assert "Polylogos Synthesis" in output.article
    assert "Methodological note" in output.article
    assert "Disclosure" in output.article

    # Executive remark and minority report exist
    assert TOPIC in output.executive_remark
    assert "Minority Report" in output.minority_report or "No minority view" in output.minority_report

    # Quality / diversity sanity
    assert output.quality_band in {"fast", "full"}
    assert output.final_orthogonality < 0.7
    assert output.final_cluster_entropy > 0.42  # anti-collapse floor


def test_e2e_is_deterministic_given_seed() -> None:
    engine = Polylogos(force_mock=True)
    out_a = engine.run(topic=TOPIC, cluster_size=10, seed=99)
    out_b = engine.run(topic=TOPIC, cluster_size=10, seed=99)
    # Same seed → same article text
    assert out_a.article == out_b.article
