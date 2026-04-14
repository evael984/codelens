# Contributing to CodeLens

Thanks for your interest! CodeLens is intentionally small in scope — we want to
do *one* thing (semantic PR review) very well rather than become another
general AI coding assistant.

## Local setup

```bash
git clone https://github.com/yourname/codelens
cd codelens
pip install -e ".[dev]"
pytest -q
```

## Where to contribute

| Area | File(s) | Difficulty |
|------|---------|------------|
| New language support (Tree-sitter parser) | `src/codelens/diff_parser.py` | medium |
| New analyzer | `src/codelens/analyzers/base.py` (interface) | medium |
| Improve a prompt | `src/codelens/prompts/*.txt` | easy |
| New provider (e.g. Gemini) | `src/codelens/providers/` | easy |
| Benchmark dataset | `benchmark/` | hard |

## Adding a new analyzer

1. Create `src/codelens/analyzers/your_thing.py`, subclass `Analyzer`.
2. Add a prompt under `src/codelens/prompts/your_thing.txt` (must specify a JSON output schema).
3. Register it in `src/codelens/cli.py` and `src/codelens/config.py`.
4. Add a unit test using a `FakeProvider` (see `tests/test_intent_drift.py`).

## Style

- `ruff check src tests` must pass.
- Type hints are required on all public functions.
- Prompts must instruct the model to return JSON only — never free-form prose.
- Prefer adding a focused analyzer over expanding an existing one's scope.
