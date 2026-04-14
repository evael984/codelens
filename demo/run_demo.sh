#!/usr/bin/env bash
# Build a fresh git repo from a scenario's before/after snapshots, then run CodeLens.
# Usage: ./demo/run_demo.sh [scenario_name]   (default: cache_invalidation)
#
# By default uses the mock provider so this works without an API key.
# To run against a real provider:
#   CODELENS_PROVIDER=anthropic ANTHROPIC_API_KEY=sk-... ./demo/run_demo.sh

set -euo pipefail

SCENARIO="${1:-cache_invalidation}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCENARIO_DIR="$SCRIPT_DIR/scenarios/$SCENARIO"

if [ ! -d "$SCENARIO_DIR" ]; then
  echo "Scenario not found: $SCENARIO_DIR" >&2
  exit 1
fi

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

cd "$WORKDIR"
git init -q
git symbolic-ref HEAD refs/heads/main
git config user.email "demo@codelens.dev"
git config user.name "CodeLens Demo"

cp -r "$SCENARIO_DIR/before/." .
git add -A
git commit -q -m "baseline"

git checkout -q -b feature

rm -rf ./*
cp -r "$SCENARIO_DIR/after/." .
git add -A
git commit -q -m "feature change"

PROVIDER="${CODELENS_PROVIDER:-mock}"

if [ "$PROVIDER" = "mock" ]; then
  export CODELENS_MOCK_SCRIPT="$SCENARIO_DIR/mock_responses.json"
  cat > .codelens.toml <<EOF
[provider]
name = "mock"
model = "mock"
EOF
fi

echo "==> Running CodeLens on scenario: $SCENARIO (provider=$PROVIDER)"
echo

if command -v codelens >/dev/null 2>&1; then
  CODELENS_CMD="codelens"
else
  CODELENS_CMD="python -m codelens.cli"
fi

$CODELENS_CMD \
  --base main \
  --head feature \
  --pr-body "$SCENARIO_DIR/PR_BODY.md" \
  --repo "$WORKDIR" || true
