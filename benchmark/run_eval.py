"""Runs CodeLens against a labeled dataset and emits per-example predictions."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress

from codelens.analyzers.base import AnalysisContext
from codelens.analyzers.intent_drift import IntentDriftAnalyzer
from codelens.diff_parser import parse_diff
from codelens.providers import build_provider

from .schema import Example, RunResult, load_jsonl, write_jsonl

app = typer.Typer(add_completion=False)
console = Console()


def _predict_label(findings: list, raw: str) -> str:
    """Map analyzer findings → benchmark label.

    Prefer the LLM's explicit verdict (carried in finding.extra["verdict"]).
    Fall back to inferring from finding presence if the verdict is missing.
    """
    for f in findings:
        verdict = f.extra.get("verdict") if hasattr(f, "extra") else None
        if verdict in {"aligned", "claimed_not_done", "done_not_claimed", "misaligned"}:
            return verdict

    has_claimed = any("Claimed but not" in f.title for f in findings)
    has_undocumented = any("Undocumented change" in f.title for f in findings)
    if has_claimed and has_undocumented:
        return "misaligned"
    if has_claimed:
        return "claimed_not_done"
    if has_undocumented:
        return "done_not_claimed"
    return "aligned"


def _evaluate_example(example: Example, provider, repo_root: Path) -> RunResult:
    diff = parse_diff(example.diff)
    pr_text = f"{example.pr_title}\n\n{example.pr_body}"
    ctx = AnalysisContext(diff=diff, pr_description=pr_text, repo_root=repo_root)

    analyzer = IntentDriftAnalyzer(provider)
    try:
        findings = analyzer.run(ctx)
    except Exception as exc:
        return RunResult(
            id=example.id,
            gold_label=example.label,
            predicted_label="?",
            error=str(exc),
        )

    return RunResult(
        id=example.id,
        gold_label=example.label,
        predicted_label=_predict_label(findings, ""),
        findings=[f.__dict__ for f in findings],
    )


@app.command()
def run(
    dataset: Path = typer.Option(..., "--dataset"),
    out: Path = typer.Option(..., "--out"),
    provider_name: str = typer.Option("anthropic", "--provider"),
    model: str = typer.Option("claude-opus-4-6", "--model"),
    api_key_env: str = typer.Option("ANTHROPIC_API_KEY", "--api-key-env"),
    base_url: str = typer.Option(None, "--base-url", help="Override OpenAI-compatible endpoint."),
    skip_unlabeled: bool = typer.Option(True, "--skip-unlabeled/--include-unlabeled"),
) -> None:
    import os

    api_key = os.environ.get(api_key_env)
    provider = build_provider(provider_name, model, api_key=api_key, base_url=base_url)

    examples = list(load_jsonl(dataset))
    if skip_unlabeled:
        examples = [e for e in examples if e.label != "?"]
    console.print(f"Loaded {len(examples)} examples from {dataset}")

    results: list[RunResult] = []
    repo_root = Path.cwd()
    with Progress() as bar:
        task = bar.add_task("evaluating", total=len(examples))
        for ex in examples:
            results.append(_evaluate_example(ex, provider, repo_root))
            bar.advance(task)

    write_jsonl(out, results)
    console.print(f"[green]Wrote {len(results)} results to {out}[/green]")


if __name__ == "__main__":
    app()
