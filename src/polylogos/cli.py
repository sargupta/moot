"""`polylogos debate "..."` — walking-skeleton CLI."""

from __future__ import annotations

import os
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from polylogos.debate import Polylogos


def _load_dotenv_if_present() -> None:
    """Lightweight .env loader (no python-dotenv dependency).

    Reads the first `.env` file found by walking up from CWD, sets KEY=VALUE
    pairs into os.environ if not already set. Lines starting with `#` and blank
    lines are ignored. Surrounding double-quotes on values are stripped.

    This lets `uv run polylogos serve` and the Claude Preview launcher work
    without requiring the user to export keys in their shell rc, while still
    keeping secrets out of source (the .env file is gitignored).
    """
    cwd = Path.cwd().resolve()
    for parent in (cwd, *cwd.parents):
        candidate = parent / ".env"
        if candidate.is_file():
            try:
                for raw in candidate.read_text(encoding="utf-8").splitlines():
                    line = raw.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = value
            except OSError:
                pass
            return


_load_dotenv_if_present()


app = typer.Typer(help="Moot — open multi-agent debate engine. A product of SARGVISION Intelligence.")
console = Console()


@app.command()
def debate(
    topic: str = typer.Argument(..., help="The strategic question for the cluster to debate."),
    cluster_size: int = typer.Option(10, help="Personas in the cluster (max 10 in skeleton)."),
    seed: int = typer.Option(42, help="Deterministic RNG seed."),
    mock: bool = typer.Option(
        False,
        "--mock",
        help="Force the deterministic mock LLM. Default: use Anthropic Claude if "
        "ANTHROPIC_API_KEY is set, else fall back to mock.",
    ),
    out_dir: Path = typer.Option(
        Path("out"),
        help="Directory under which a per-debate folder is written.",
    ),
) -> None:
    engine = Polylogos(force_mock=mock)
    output = engine.run(topic=topic, cluster_size=cluster_size, seed=seed)

    debate_dir = out_dir / str(output.config.debate_id)
    debate_dir.mkdir(parents=True, exist_ok=True)

    article_path = debate_dir / "article.md"
    remark_path = debate_dir / "executive_remark.md"
    minority_path = debate_dir / "minority_report.md"
    transcript_path = debate_dir / "transcript.md"
    metrics_path = debate_dir / "metrics.json"

    article_path.write_text(output.article, encoding="utf-8")
    remark_path.write_text(output.executive_remark, encoding="utf-8")
    minority_path.write_text(output.minority_report, encoding="utf-8")

    transcript_lines: list[str] = [f"# Debate transcript: {topic}\n"]
    for turn in output.transcript:
        transcript_lines.append(
            f"## Round {turn.round_number} — {turn.round.value} — {turn.persona_label}"
        )
        transcript_lines.append(turn.text)
        transcript_lines.append("")
    transcript_path.write_text("\n".join(transcript_lines), encoding="utf-8")

    import json as _json

    metrics_path.write_text(
        _json.dumps(
            {
                "debate_id": str(output.config.debate_id),
                "topic": output.config.topic,
                "cluster_size": output.config.cluster_size,
                "seed": output.config.seed,
                "quality_band": output.quality_band,
                "article_word_count": len(output.article.split()),
                "estimated_cost_inr": output.cost_estimate_inr,
                "final_orthogonality": output.final_orthogonality,
                "final_cluster_entropy": output.final_cluster_entropy,
                "final_diversity_volume": output.final_diversity_volume,
                "n_turns": len(output.transcript),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    table = Table(title="Moot debate metrics", show_header=True)
    table.add_column("metric")
    table.add_column("value", justify="right")
    table.add_row("debate_id", str(output.config.debate_id))
    table.add_row("topic", output.config.topic[:80] + ("…" if len(output.config.topic) > 80 else ""))
    table.add_row("cluster_size", str(output.config.cluster_size))
    table.add_row("rounds", "4")
    table.add_row("turns", str(len(output.transcript)))
    table.add_row("article words", str(len(output.article.split())))
    table.add_row("quality_band", output.quality_band)
    table.add_row("est. cost (INR)", f"₹{output.cost_estimate_inr:.2f}")
    table.add_row("orthogonality (mean cos)", f"{output.final_orthogonality:.3f}")
    table.add_row("cluster entropy (nats)", f"{output.final_cluster_entropy:.3f}")
    table.add_row("diversity volume", f"{output.final_diversity_volume:.3f}")

    console.print(Panel.fit(f"Topic: {output.config.topic}", title="Moot"))
    console.print(table)
    console.print(f"\nWrote:\n  {article_path}\n  {remark_path}\n  {minority_path}\n  {transcript_path}\n  {metrics_path}")


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Bind host. Use 0.0.0.0 to expose on the LAN."),
    port: int = typer.Option(8765, help="Bind port for the web UI."),
    reload: bool = typer.Option(False, "--reload", help="Reload on source change (dev only)."),
) -> None:
    """Boot the Moot web UI (Stance Chamber at http://host:port/)."""
    import uvicorn

    console.print(
        Panel.fit(
            f"Moot UI booting at [bold]http://{host}:{port}/[/bold]\n"
            "Open the URL in a browser to convene the chamber.",
            title="Moot · serve",
        )
    )
    # Importable string so uvicorn's reload mode works; otherwise uvicorn will
    # fall through to the same path without re-importing.
    uvicorn.run(
        "polylogos.web.app:create_app",
        host=host,
        port=port,
        factory=True,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    app()
