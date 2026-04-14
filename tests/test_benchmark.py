"""Sanity checks: seed dataset round-trips and metric math is correct."""

from pathlib import Path

from benchmark.metrics import _per_label_prf
from benchmark.schema import Example, RunResult, load_jsonl
from codelens.diff_parser import parse_diff

SEED_PATH = Path(__file__).parent.parent / "benchmark" / "data" / "seed.jsonl"


def test_seed_dataset_loads():
    examples = list(load_jsonl(SEED_PATH))
    assert len(examples) >= 10
    assert all(isinstance(e, Example) for e in examples)
    assert all(e.label in {"aligned", "claimed_not_done", "done_not_claimed", "misaligned"} for e in examples)
    assert {e.label for e in examples} == {"aligned", "claimed_not_done", "done_not_claimed", "misaligned"}, \
        "Seed dataset must include every label so the eval covers all rows of the confusion matrix"


def test_seed_diffs_all_parse():
    """Catches malformed @@ headers in build_seed.py before they hit run_eval."""
    for ex in load_jsonl(SEED_PATH):
        diff = parse_diff(ex.diff)
        assert diff.total_lines() > 0, f"{ex.id} produced an empty diff"


def test_metrics_perfect_predictions():
    results = [
        RunResult(id=str(i), gold_label="aligned", predicted_label="aligned") for i in range(5)
    ]
    p, r, f1 = _per_label_prf(results, "aligned")
    assert (p, r, f1) == (1.0, 1.0, 1.0)


def test_metrics_all_wrong():
    results = [RunResult(id=str(i), gold_label="aligned", predicted_label="misaligned") for i in range(3)]
    p, r, f1 = _per_label_prf(results, "aligned")
    assert (p, r, f1) == (0.0, 0.0, 0.0)


def test_metrics_partial_recall():
    results = [
        RunResult(id="a", gold_label="claimed_not_done", predicted_label="claimed_not_done"),
        RunResult(id="b", gold_label="claimed_not_done", predicted_label="aligned"),
        RunResult(id="c", gold_label="aligned", predicted_label="aligned"),
    ]
    p, r, _ = _per_label_prf(results, "claimed_not_done")
    assert p == 1.0
    assert r == 0.5
