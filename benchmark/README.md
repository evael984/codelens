# intent-drift-bench

A small benchmark for measuring whether CodeLens (or any LLM reviewer) can
detect **intent drift** — PRs where the diff doesn't match what the description
promises.

## Definitions

| Label | Meaning |
|-------|---------|
| `aligned` | Diff implements exactly what the PR description claims. |
| `claimed_not_done` | Description promises X, diff omits X. |
| `done_not_claimed` | Diff includes substantive changes the description never mentions. |
| `misaligned` | Both of the above, or a deeper mismatch (different feature entirely). |

A reviewer is scored on whether it produces the right *label* — not on whether
the natural-language explanation matches.

## Dataset format (`data/*.jsonl`)

One JSON object per line:

```json
{
  "id": "stringly-unique",
  "source": "synthetic" | "github:owner/repo#1234",
  "pr_title": "...",
  "pr_body": "...",
  "diff": "<unified diff text>",
  "label": "aligned" | "claimed_not_done" | "done_not_claimed" | "misaligned",
  "rationale": "Why this label was assigned (human-written).",
  "reverted": true | false,
  "revert_commit": "sha or null"
}
```

## How the seed dataset was built

`data/seed.jsonl` contains 10 hand-curated synthetic examples covering the four
labels. They are intentionally short and unambiguous — meant to validate the
harness end-to-end before running on real mined data.

## Mining real PRs

```bash
export GITHUB_TOKEN=ghp_...
python -m benchmark.mine_reverts \
  --org kubernetes \
  --max 50 \
  --out data/mined.jsonl
```

The miner finds commits whose subject starts with `Revert "` and walks back to
the original PR. Each candidate is written with `label="?"` for human review.
**Auto-mined rows must be human-labeled before scoring** — `revert` ≠
`misaligned` (sometimes a correct PR is reverted for unrelated reasons).

## Running the eval

```bash
python -m benchmark.run_eval \
  --dataset data/seed.jsonl \
  --provider mock \
  --out runs/seed-mock.jsonl

python -m benchmark.metrics --run runs/seed-mock.jsonl
```

`metrics.py` reports per-label precision/recall and a confusion matrix.

## Caveats

- This is a 50-example benchmark, not a leaderboard. It exists so that prompt
  changes can be validated against a fixed reference set, not to claim SOTA.
- Synthetic seeds are easier than real PRs — production numbers will be lower.
- Cost: ~$0.10 per 50-PR run with Claude Sonnet (with prompt caching).
