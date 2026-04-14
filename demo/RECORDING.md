# Recording the README GIF

The demo runs against a deterministic scripted-response provider (`mock`), so
the GIF is reproducible — no API key, no flakiness.

## Prerequisites

```bash
pip install -e .
brew install vhs        # or: scoop install vhs   /  go install github.com/charmbracelet/vhs@latest
```

## Generate `demo.gif`

```bash
vhs demo/demo.tape
```

This writes `demo/demo.gif` (~1.5 MB). The tape file (`demo.tape`) is the
single source of truth — to change pacing, theme, or text, edit there and
re-run.

## What the demo shows

Scenario: `demo/scenarios/cache_invalidation/`

The PR description claims one thing (invalidate stale cache on email update,
add a regression test). The diff actually does three things:

1. ✅ Invalidates the old-email cache entry (matches description)
2. ❌ Silently introduces a 60-second TTL expiration mechanism (undocumented)
3. ❌ Breaks `delete_user` — it no longer clears the cache (regression)
4. ❌ No test was added (description lied)

A human reviewer might miss #2 and #3 in a hurry. CodeLens flags all four.

## Running against a real provider

```bash
CODELENS_PROVIDER=anthropic ANTHROPIC_API_KEY=sk-ant-... ./demo/run_demo.sh
```

The output will differ slightly (real LLMs are non-deterministic) but the
high-severity findings should match.

## Adding a new scenario

1. Create `demo/scenarios/<name>/before/` and `after/` with the file snapshots.
2. Write `PR_BODY.md` (the author's claimed intent).
3. Write `mock_responses.json` (scripted JSON for each analyzer).
4. Run `./demo/run_demo.sh <name>` to verify.

Good scenarios show *non-obvious* drift — a careful human reviewer should plausibly miss it.
