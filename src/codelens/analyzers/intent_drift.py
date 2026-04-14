"""Intent drift analyzer — does the diff match what the PR description claims?"""

from __future__ import annotations

from .base import AnalysisContext, Analyzer, Finding


class IntentDriftAnalyzer(Analyzer):
    name = "intent_drift"

    def run(self, ctx: AnalysisContext) -> list[Finding]:
        diff_summary = "\n\n".join(h.summary() for h in ctx.diff.hunks[:80])
        user = (
            f"PR_DESCRIPTION:\n{ctx.pr_description}\n\n"
            f"DIFF_SUMMARY:\n{diff_summary}"
        )
        msg = self._message("intent_drift.txt", user)
        raw = self.provider.complete(msg, max_tokens=1500)
        data = self.parse_json(raw)
        verdict = data.get("verdict", "aligned")

        findings: list[Finding] = []
        for item in data.get("claimed_not_done", []):
            findings.append(
                Finding(
                    analyzer=self.name,
                    severity="high",
                    title=f"Claimed but not implemented: {item.get('claim', '')[:80]}",
                    detail=item.get("evidence", ""),
                    extra={"verdict": verdict},
                )
            )
        for item in data.get("done_not_claimed", []):
            findings.append(
                Finding(
                    analyzer=self.name,
                    severity=item.get("risk", "medium"),
                    title=f"Undocumented change: {item.get('change', '')[:80]}",
                    detail=f"File: {item.get('file', '?')}",
                    location=item.get("file"),
                    extra={"verdict": verdict},
                )
            )
        if not findings and verdict != "aligned":
            findings.append(
                Finding(
                    analyzer=self.name,
                    severity="low",
                    title=f"Verdict: {verdict}",
                    detail="LLM produced a non-aligned verdict but no specific findings.",
                    extra={"verdict": verdict},
                )
            )
        return findings
