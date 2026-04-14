# CodeLens

> LLM-powered semantic review for pull requests — catches **intent drift**, **hidden side effects**, and **test coverage gaps** that static analyzers miss.

![demo](demo/demo.gif)

CodeLens does *not* compete with Copilot / aider / continue. It does one thing:
**checks whether a PR's code changes actually match what the PR description promises.**

## Try it in 30 seconds (no API key)

```bash
pip install -e .
./demo/run_demo.sh
```

The demo uses a scripted `mock` provider and runs against a synthetic PR that
*looks* like a small bug fix but quietly introduces two regressions. CodeLens
flags all of them.

## Why

Static analyzers (ESLint, SonarQube) check syntax and known anti-patterns.
AI assistants (Copilot Review) are closed-source and opinionated.
Neither answers the question a reviewer actually asks first:

> "Does this diff do what the author said it does — no more, no less?"

## Features

- **Intent Drift Detection** — parses PR title + description, compares against diff, flags claims not implemented and changes not described.
- **Hidden Side Effects** — for each modified symbol, surfaces cross-file callers that may be affected.
- **Semantic Test Gap** — LLM identifies new logic branches lacking test coverage (not line coverage — *behavior* coverage).
- **Provider-agnostic** — Anthropic, OpenAI, or local Ollama. Anthropic path uses prompt caching to keep repeat-review cost near-zero.
- **Two entry points** — CLI for local use, GitHub Action for CI.

## Install

```bash
pip install codelens
```

Or from source:

```bash
git clone https://github.com/yourname/codelens
cd codelens
pip install -e .
```

## Quickstart

### CLI

```bash
export ANTHROPIC_API_KEY=sk-ant-...
codelens --base main --head HEAD --pr-body examples/sample_pr.md
```

### GitHub Action

```yaml
# .github/workflows/review.yml
name: CodeLens Review
on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: yourname/codelens@v0
        with:
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Configuration

Create `.codelens.toml` at the repo root:

```toml
[provider]
name = "anthropic"        # "anthropic" | "openai" | "ollama"
model = "claude-opus-4-6"

[analyzers]
intent_drift = true
side_effects = true
test_gap = true

[filters]
ignore_paths = ["vendor/**", "*.generated.*"]
max_diff_lines = 2000
```

## How it works

1. `git diff base..head` → unified diff
2. Tree-sitter parses changed hunks into language-agnostic AST fragments
3. Each analyzer constructs a focused prompt:
   - **intent_drift** → (PR description, diff summary) → list of mismatches
   - **side_effects** → (changed symbols, repo grep of callers) → risk list
   - **test_gap** → (new branches, existing tests) → uncovered behaviors
4. Results merged into a single Markdown report (stdout or PR comment)

Anthropic provider caches the repo-level system prompt, so the N-th review of the same repo costs only the delta tokens.

## Roadmap

- [x] Python diff parser + intent drift analyzer
- [x] Anthropic + OpenAI providers with prompt caching
- [ ] Tree-sitter multi-language support (JS/TS, Go, Rust)
- [ ] Intent-drift benchmark: mined from reverted GitHub PRs
- [ ] Ollama local-model provider
- [ ] VSCode extension

## Benchmark

`benchmark/` is a small evaluation suite for the intent-drift detector.

```bash
make bench-eval DATASET=benchmark/data/seed.jsonl PROVIDER=mock      # smoke test
make bench-eval DATASET=benchmark/data/seed.jsonl PROVIDER=anthropic # real run
```

Reports per-label precision/recall/F1 and a confusion matrix.

### Results on the 10-example seed dataset

| Provider | Accuracy | aligned F1 | claimed_not_done F1 | done_not_claimed F1 | misaligned F1 |
|----------|----------|-----------|---------------------|---------------------|---------------|
| deepseek-reasoner (R1) | **70%** | 0.80 | **1.00** | 0.40 | 0.00 |
| deepseek-chat          | 50%   | 0.75 | 0.50 | 0.40 | 0.00 |
| mock (smoke test)      | 40%   | 0.57 | 0.00 | 0.00 | 0.00 |

Reading the table:

- **`claimed_not_done` is the strongest signal** (R1 gets every case). If CodeLens
  flags this, the PR description is genuinely promising something the diff
  doesn't deliver — high-confidence "block this PR" signal.
- **`aligned` recall is 100%** — clean PRs aren't spammed with false alarms.
- **`done_not_claimed` is harder** (33% recall): the model under-flags quiet
  scope creep. Improving this is the top prompt-tuning priority.
- **`misaligned`** has support=1 in this seed set; not statistically meaningful.
  Mining real reverted PRs (`benchmark/mine_reverts.py`) is how we'll grow it.

**Caveats**: 10 hand-curated examples is small. Production numbers on real
PRs will be lower. The benchmark exists to validate prompt changes, not to
claim SOTA.

| Component | What it does |
|-----------|--------------|
| `benchmark/data/seed.jsonl` | 10 hand-curated synthetic PRs covering all four labels |
| `benchmark/build_seed.py` | Source of truth for the seed set (Python literals → JSONL) |
| `benchmark/mine_reverts.py` | Mines reverted PRs from GitHub for human labeling |
| `benchmark/run_eval.py` | Runs CodeLens against a labeled dataset |
| `benchmark/metrics.py` | Precision/recall/F1 + confusion matrix |

See [`benchmark/README.md`](benchmark/README.md) for methodology and how to
contribute labeled PRs from real-world repos.

## Contributing

Good first issues:
- Add Tree-sitter grammar for a new language (see `src/codelens/diff_parser.py`)
- Write a new analyzer (see `src/codelens/analyzers/base.py` interface)
- Improve a prompt in `src/codelens/prompts/`

## License

MIT
