"""Test gap analyzer — semantic (not line) coverage of new behaviors."""

from __future__ import annotations

from .base import AnalysisContext, Analyzer, Finding

TEST_PATH_HINTS = ("test_", "_test.", "/tests/", "/test/", ".spec.", ".test.")


def is_test_path(path: str) -> bool:
    lowered = path.lower()
    return any(hint in lowered for hint in TEST_PATH_HINTS)


class TestGapAnalyzer(Analyzer):
    name = "test_gap"

    def run(self, ctx: AnalysisContext) -> list[Finding]:
        prod_hunks = [h for h in ctx.diff.hunks if not is_test_path(h.file_path)]
        test_hunks = [h for h in ctx.diff.hunks if is_test_path(h.file_path)]
        if not prod_hunks:
            return []

        new_behavior = "\n\n".join(h.summary() for h in prod_hunks[:60])
        test_diff = "\n\n".join(h.summary() for h in test_hunks[:60]) or "(no test changes in this PR)"

        user = f"NEW_BEHAVIOR:\n{new_behavior}\n\nTEST_DIFF:\n{test_diff}"
        msg = self._message("test_gap.txt", user)
        raw = self.provider.complete(msg, max_tokens=1200)
        data = self.parse_json(raw)

        findings: list[Finding] = []
        for item in data.get("gaps", []):
            findings.append(
                Finding(
                    analyzer=self.name,
                    severity="medium",
                    title=item.get("behavior", "Untested behavior"),
                    detail=f"Suggested test: {item.get('suggested_test', '')}",
                    location=item.get("location"),
                )
            )
        return findings
