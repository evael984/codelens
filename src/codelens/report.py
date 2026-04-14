"""Render findings as Markdown for stdout or PR comment."""

from __future__ import annotations

from .analyzers import Finding

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}
SEVERITY_BADGE = {"high": "[HIGH]", "medium": "[MED] ", "low": "[LOW] "}


def render_markdown(findings: list[Finding]) -> str:
    if not findings:
        return "## CodeLens Review\n\nNo issues found. Diff aligns with the PR description.\n"

    findings = sorted(findings, key=lambda f: (SEVERITY_ORDER.get(f.severity, 3), f.analyzer))
    lines: list[str] = ["## CodeLens Review", ""]
    lines.append(f"Found **{len(findings)}** issue(s) across {len({f.analyzer for f in findings})} analyzer(s).\n")

    by_analyzer: dict[str, list[Finding]] = {}
    for f in findings:
        by_analyzer.setdefault(f.analyzer, []).append(f)

    for analyzer, items in by_analyzer.items():
        lines.append(f"### {analyzer.replace('_', ' ').title()} ({len(items)})\n")
        for f in items:
            badge = SEVERITY_BADGE.get(f.severity, f.severity)
            loc = f" — `{f.location}`" if f.location else ""
            lines.append(f"- **{badge}** {f.title}{loc}")
            if f.detail:
                for line in f.detail.splitlines():
                    lines.append(f"  > {line}")
        lines.append("")

    return "\n".join(lines)
