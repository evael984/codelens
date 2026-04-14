"""Unit test for IntentDriftAnalyzer using a fake provider — no network calls."""

from pathlib import Path

from codelens.analyzers import IntentDriftAnalyzer
from codelens.analyzers.base import AnalysisContext
from codelens.diff_parser import parse_diff
from codelens.providers.base import LLMProvider, Message


class FakeProvider(LLMProvider):
    def __init__(self, response: str) -> None:
        self.response = response
        self.last_message: Message | None = None

    def complete(self, message: Message, max_tokens: int = 2048) -> str:
        self.last_message = message
        return self.response


SAMPLE_DIFF = """\
diff --git a/auth.py b/auth.py
--- a/auth.py
+++ b/auth.py
@@ -1,2 +1,4 @@
 def login(user):
-    return True
+    if not user:
+        raise ValueError("missing user")
+    return True
"""


def test_intent_drift_parses_findings():
    fake = FakeProvider(
        response='{"claimed_not_done": [{"claim": "add password check", "evidence": "no password handling in diff"}],'
        '"done_not_claimed": [], "verdict": "partial"}'
    )
    diff = parse_diff(SAMPLE_DIFF)
    ctx = AnalysisContext(
        diff=diff,
        pr_description="Add password check to login()",
        repo_root=Path.cwd(),
    )
    findings = IntentDriftAnalyzer(fake).run(ctx)
    assert len(findings) == 1
    assert findings[0].severity == "high"
    assert "password" in findings[0].title.lower()


def test_intent_drift_handles_aligned_response():
    fake = FakeProvider(response='{"claimed_not_done": [], "done_not_claimed": [], "verdict": "aligned"}')
    diff = parse_diff(SAMPLE_DIFF)
    ctx = AnalysisContext(diff=diff, pr_description="Validate user", repo_root=Path.cwd())
    assert IntentDriftAnalyzer(fake).run(ctx) == []


def test_intent_drift_tolerates_fenced_json():
    fake = FakeProvider(
        response='```json\n{"claimed_not_done": [], "done_not_claimed": [{"change": "added input validation", "file": "auth.py", "risk": "low"}], "verdict": "aligned"}\n```'
    )
    diff = parse_diff(SAMPLE_DIFF)
    ctx = AnalysisContext(diff=diff, pr_description="", repo_root=Path.cwd())
    findings = IntentDriftAnalyzer(fake).run(ctx)
    assert len(findings) == 1
    assert findings[0].severity == "low"
