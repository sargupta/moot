"""Top-level debate orchestrator: persona pool → cluster debate → synthesis.

Walking-skeleton: 1 cluster of 10 personas, 4 rounds. Production adds the
hierarchical 50-cluster + plenary + adversarial-judge + Opus-synthesis
stages (plan §5.2).

Provider selection (in priority order):
  - explicit `provider_choice` argument: "mock" | "anthropic" | "gemini"
  - if `force_mock=True` → MockProvider
  - else GEMINI_API_KEY/GOOGLE_API_KEY → GeminiProvider
  - else ANTHROPIC_API_KEY → AnthropicProvider
  - else MockProvider
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from polylogos.llm import AnthropicProvider, GeminiProvider, MockProvider
from polylogos.llm.provider import LLMProvider
from polylogos.orchestration import ClusterDebate, ClusterResult
from polylogos.personas import default_pool, sample_cluster
from polylogos.schemas.debate import DebateConfig, DebateOutput
from polylogos.synthesis import synthesize


def _build_provider(
    provider_choice: str | None, force_mock: bool, seed: int
) -> LLMProvider:
    if force_mock or provider_choice == "mock":
        return MockProvider(seed=seed)
    if provider_choice == "gemini":
        return GeminiProvider()
    if provider_choice == "anthropic":
        return AnthropicProvider()
    # Auto-selection: prefer Gemini > Anthropic > Mock based on env.
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return GeminiProvider()
    if os.environ.get("ANTHROPIC_API_KEY"):
        return AnthropicProvider()
    return MockProvider(seed=seed)


@dataclass
class DebateRun:
    """Pair the user-facing DebateOutput with the rich diagnostics needed by the
    web UI (per-round belief snapshots, the live ArgumentGraph, the persona pool)."""

    output: DebateOutput
    cluster: ClusterResult
    personas: list  # noqa: ANN001 — list[Persona]; avoid the import here


@dataclass
class Polylogos:
    """Walking-skeleton entrypoint."""

    provider: LLMProvider | None = None
    force_mock: bool = False
    provider_choice: str | None = None

    def run(
        self,
        topic: str,
        cluster_size: int = 10,
        seed: int = 42,
        pool_name: str = "defense",
    ) -> DebateOutput:
        return self.run_with_diagnostics(topic, cluster_size, seed, pool_name).output

    def run_with_diagnostics(
        self,
        topic: str,
        cluster_size: int = 10,
        seed: int = 42,
        pool_name: str = "defense",
    ) -> DebateRun:
        provider = self.provider or _build_provider(
            self.provider_choice, self.force_mock, seed
        )
        config = DebateConfig(topic=topic, cluster_size=cluster_size, seed=seed)

        pool = default_pool(pool_name)
        if cluster_size > len(pool):
            cluster_size = len(pool)
        personas = sample_cluster(pool, size=cluster_size, seed=seed)

        cluster = ClusterDebate(
            personas=personas,
            topic=topic,
            provider=provider,
            seed=seed,
        )
        result: ClusterResult = cluster.run()

        synthesis = synthesize(topic=topic, graph=result.graph, personas=personas)

        cost_inr = 0.0
        total_cost = getattr(provider, "total_cost_inr", None)
        if callable(total_cost):
            cost_inr = float(total_cost())

        output = DebateOutput(
            config=config,
            transcript=result.transcript,
            article=synthesis.article,
            executive_remark=synthesis.executive_remark,
            minority_report=synthesis.minority_report,
            quality_band=synthesis.quality_band,
            cost_estimate_inr=cost_inr,
            final_orthogonality=result.final_orthogonality,
            final_cluster_entropy=result.final_cluster_entropy,
            final_diversity_volume=result.final_diversity_volume,
        )
        return DebateRun(output=output, cluster=result, personas=personas)
