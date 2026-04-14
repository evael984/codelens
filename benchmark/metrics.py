"""Compute precision/recall/F1 + confusion matrix from a run results file."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .schema import load_results

app = typer.Typer(add_completion=False)
console = Console()

LABELS = ["aligned", "claimed_not_done", "done_not_claimed", "misaligned"]


def _per_label_prf(results, label: str) -> tuple[float, float, float]:
    tp = sum(1 for r in results if r.predicted_label == label and r.gold_label == label)
    fp = sum(1 for r in results if r.predicted_label == label and r.gold_label != label)
    fn = sum(1 for r in results if r.predicted_label != label and r.gold_label == label)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return precision, recall, f1


@app.command()
def main(run: Path = typer.Option(..., "--run")) -> None:
    results = load_results(run)
    valid = [r for r in results if r.error is None and r.gold_label != "?"]
    errored = len(results) - len(valid)

    console.rule(f"Run: {run.name} — {len(valid)} scored, {errored} skipped")

    overall_correct = sum(1 for r in valid if r.predicted_label == r.gold_label)
    accuracy = overall_correct / len(valid) if valid else 0.0
    console.print(f"[bold]Accuracy:[/bold] {accuracy:.1%} ({overall_correct}/{len(valid)})\n")

    metrics = Table(title="Per-label metrics")
    metrics.add_column("Label")
    metrics.add_column("Precision", justify="right")
    metrics.add_column("Recall", justify="right")
    metrics.add_column("F1", justify="right")
    metrics.add_column("Support", justify="right")
    for label in LABELS:
        p, r_, f1 = _per_label_prf(valid, label)
        support = sum(1 for r in valid if r.gold_label == label)
        metrics.add_row(label, f"{p:.2f}", f"{r_:.2f}", f"{f1:.2f}", str(support))
    console.print(metrics)

    matrix = Table(title="Confusion matrix (rows = gold, cols = pred)")
    matrix.add_column("gold \\ pred")
    for label in LABELS:
        matrix.add_column(label, justify="right")
    cm: dict[tuple[str, str], int] = defaultdict(int)
    for r in valid:
        cm[(r.gold_label, r.predicted_label)] += 1
    for gold in LABELS:
        row = [gold]
        for pred in LABELS:
            row.append(str(cm[(gold, pred)]))
        matrix.add_row(*row)
    console.print(matrix)


if __name__ == "__main__":
    app()
