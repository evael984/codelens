"""Side effects analyzer — finds callers of changed symbols and asks the LLM to assess risk."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .base import AnalysisContext, Analyzer, Finding

SYMBOL_RE = re.compile(r"\b(def|class|function|func|fn)\s+([A-Za-z_][A-Za-z_0-9]*)")


def extract_changed_symbols(diff_summary: str) -> list[str]:
    symbols: set[str] = set()
    for match in SYMBOL_RE.finditer(diff_summary):
        symbols.add(match.group(2))
    return sorted(symbols)


def grep_callers(symbol: str, repo_root: Path, exclude_files: set[str]) -> list[str]:
    """Best-effort caller search using git-grep. Returns up to 10 snippet lines."""
    try:
        result = subprocess.run(
            ["git", "grep", "-n", "--", rf"\b{symbol}\b"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return []
    lines: list[str] = []
    for line in result.stdout.splitlines():
        path = line.split(":", 1)[0]
        if path in exclude_files:
            continue
        lines.append(line)
        if len(lines) >= 10:
            break
    return lines


class SideEffectsAnalyzer(Analyzer):
    name = "side_effects"

    def run(self, ctx: AnalysisContext) -> list[Finding]:
        diff_summary = "\n\n".join(h.summary() for h in ctx.diff.hunks)
        symbols = extract_changed_symbols(diff_summary)
        if not symbols:
            return []

        changed_files = set(ctx.diff.files_changed())
        caller_snippets: list[str] = []
        for sym in symbols[:20]:
            hits = grep_callers(sym, ctx.repo_root, changed_files)
            if hits:
                caller_snippets.append(f"## {sym}\n" + "\n".join(hits))

        if not caller_snippets:
            return []

        user = (
            f"CHANGED_SYMBOLS:\n{', '.join(symbols)}\n\n"
            f"CALLER_SNIPPETS:\n" + "\n\n".join(caller_snippets) + "\n\n"
            f"DIFF_SUMMARY:\n{diff_summary[:4000]}"
        )
        msg = self._message("side_effects.txt", user)
        raw = self.provider.complete(msg, max_tokens=1500)
        data = self.parse_json(raw)

        findings: list[Finding] = []
        for item in data.get("side_effects", []):
            affected = ", ".join(item.get("affected_files", []))
            findings.append(
                Finding(
                    analyzer=self.name,
                    severity=item.get("severity", "medium"),
                    title=f"{item.get('kind', 'change')} change to {item.get('symbol', '?')}",
                    detail=f"{item.get('explanation', '')}\nAffected: {affected}",
                    location=affected or None,
                )
            )
        return findings
