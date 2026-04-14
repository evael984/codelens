"""CodeLens CLI."""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console

from .analyzers import (
    Analyzer,
    Finding,
    IntentDriftAnalyzer,
    SideEffectsAnalyzer,
    TestGapAnalyzer,
)
from .analyzers.base import AnalysisContext
from .config import Config
from .diff_parser import git_diff, parse_diff
from .providers import build_provider
from .report import render_markdown

app = typer.Typer(add_completion=False, help="CodeLens — semantic PR review.")
console = Console()


def _load_pr_body(path: Path | None, inline: str | None) -> str:
    if inline:
        return inline
    if path:
        return path.read_text(encoding="utf-8")
    return "(No PR description provided.)"


@app.command()
def review(
    base: str = typer.Option("main", "--base", help="Base git ref."),
    head: str = typer.Option("HEAD", "--head", help="Head git ref."),
    pr_body: Path | None = typer.Option(None, "--pr-body", help="File with the PR description (Markdown)."),
    pr_text: str | None = typer.Option(None, "--pr-text", help="Inline PR description."),
    config_path: Path | None = typer.Option(None, "--config", help="Path to .codelens.toml."),
    repo: Path = typer.Option(Path.cwd(), "--repo", help="Repository root."),
    output: Path | None = typer.Option(None, "--output", help="Write Markdown report to this file."),
) -> None:
    """Review the diff between two git refs."""
    cfg = Config.load(config_path)
    api_key = cfg.api_key()

    raw_diff = git_diff(base, head, repo=repo)
    diff = parse_diff(raw_diff, ignore_paths=cfg.filters.ignore_paths)
    if diff.total_lines() == 0:
        console.print("[yellow]No changes detected between refs.[/yellow]")
        raise typer.Exit(0)
    if diff.total_lines() > cfg.filters.max_diff_lines:
        console.print(
            f"[yellow]Diff has {diff.total_lines()} lines (limit {cfg.filters.max_diff_lines}). "
            "Consider splitting the PR.[/yellow]"
        )

    provider = build_provider(
        cfg.provider.name,
        cfg.provider.model,
        api_key=api_key,
        base_url=cfg.provider.base_url,
    )

    description = _load_pr_body(pr_body, pr_text)
    ctx = AnalysisContext(diff=diff, pr_description=description, repo_root=repo)

    enabled: list[Analyzer] = []
    if cfg.analyzers.intent_drift:
        enabled.append(IntentDriftAnalyzer(provider))
    if cfg.analyzers.side_effects:
        enabled.append(SideEffectsAnalyzer(provider))
    if cfg.analyzers.test_gap:
        enabled.append(TestGapAnalyzer(provider))

    findings: list[Finding] = []
    for analyzer in enabled:
        console.print(f"[cyan]Running {analyzer.name}...[/cyan]")
        try:
            findings.extend(analyzer.run(ctx))
        except Exception as exc:  # surface, don't swallow
            console.print(f"[red]{analyzer.name} failed: {exc}[/red]")

    report = render_markdown(findings)
    if output:
        output.write_text(report, encoding="utf-8")
        console.print(f"[green]Wrote report to {output}[/green]")
    else:
        # Force utf-8 so emoji/unicode in findings don't blow up on cp1252/GBK consoles.
        sys.stdout.buffer.write(report.encode("utf-8", errors="replace"))
        sys.stdout.buffer.write(b"\n")

    high_severity = [f for f in findings if f.severity == "high"]
    raise typer.Exit(1 if high_severity else 0)


if __name__ == "__main__":
    app()
