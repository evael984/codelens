"""Generates `data/seed.jsonl` from in-source Python literals.

Keeping the dataset as Python source (not raw JSONL) means humans can edit
diffs without manually escaping newlines. Run after editing:

    python -m benchmark.build_seed

Hunk headers `@@ -src_start,src_len +tgt_start,tgt_len @@` must be exact:
- `src_len` = context lines + removed lines
- `tgt_len` = context lines + added lines
unidiff (which CodeLens uses) rejects mismatches.
"""

from __future__ import annotations

from pathlib import Path

from .schema import Example, write_jsonl

SEED: list[Example] = [
    Example(
        id="seed-001",
        source="synthetic",
        pr_title="Add input validation to login()",
        pr_body="Raise ValueError for empty user. Adds unit test.",
        diff="""\
diff --git a/auth.py b/auth.py
--- a/auth.py
+++ b/auth.py
@@ -1,2 +1,4 @@
 def login(user):
-    return True
+    if not user:
+        raise ValueError("missing user")
+    return True
diff --git a/tests/test_auth.py b/tests/test_auth.py
--- a/tests/test_auth.py
+++ b/tests/test_auth.py
@@ -1 +1,5 @@
 from auth import login
+import pytest
+def test_empty_user_raises():
+    with pytest.raises(ValueError):
+        login("")
""",
        label="aligned",
        rationale="Diff implements exactly what the PR body claims (validation + test).",
    ),
    Example(
        id="seed-002",
        source="synthetic",
        pr_title="Fix typo in error message",
        pr_body="Changes 'recieved' to 'received' in the API error.",
        diff="""\
diff --git a/api.py b/api.py
--- a/api.py
+++ b/api.py
@@ -10 +10,5 @@ def handle(req):
-        raise BadRequest("recieved invalid payload")
+        raise BadRequest("received invalid payload")
+
+def _new_helper(x):
+    # quietly added; not mentioned in PR body
+    return x * 2
""",
        label="done_not_claimed",
        rationale="PR claims a typo fix but also introduces _new_helper.",
    ),
    Example(
        id="seed-003",
        source="synthetic",
        pr_title="Add retry logic and circuit breaker to HTTP client",
        pr_body="Add exponential-backoff retries (max 3) and a circuit breaker that opens after 5 consecutive failures.",
        diff="""\
diff --git a/client.py b/client.py
--- a/client.py
+++ b/client.py
@@ -5,2 +5,8 @@ class Client:
     def get(self, url):
-        return requests.get(url)
+        for attempt in range(3):
+            try:
+                return requests.get(url)
+            except requests.RequestException:
+                if attempt == 2:
+                    raise
+                time.sleep(2 ** attempt)
""",
        label="claimed_not_done",
        rationale="Retry is implemented but the circuit breaker is missing entirely.",
    ),
    Example(
        id="seed-004",
        source="synthetic",
        pr_title="Rename db_user_id to user_id across the codebase",
        pr_body="Pure rename. No behavior change.",
        diff="""\
diff --git a/models.py b/models.py
--- a/models.py
+++ b/models.py
@@ -1,3 +1,3 @@
 class User:
-    def __init__(self, db_user_id):
-        self.db_user_id = db_user_id
+    def __init__(self, user_id):
+        self.user_id = user_id
diff --git a/queries.py b/queries.py
--- a/queries.py
+++ b/queries.py
@@ -1 +1 @@
-SELECT_USER = "SELECT * FROM users WHERE db_user_id = ?"
+SELECT_USER = "SELECT * FROM users WHERE user_id = ?"
""",
        label="done_not_claimed",
        rationale="The SQL change is a behavior change (column rename), not a pure code rename.",
    ),
    Example(
        id="seed-005",
        source="synthetic",
        pr_title="Bump dependency: requests 2.28 -> 2.31",
        pr_body="Routine version bump for security advisory.",
        diff="""\
diff --git a/requirements.txt b/requirements.txt
--- a/requirements.txt
+++ b/requirements.txt
@@ -1 +1 @@
-requests==2.28.0
+requests==2.31.0
""",
        label="aligned",
        rationale="Single-line dependency bump matches the description.",
    ),
    Example(
        id="seed-006",
        source="synthetic",
        pr_title="Add caching to expensive_query()",
        pr_body="Wrap expensive_query() with a 5-minute TTL cache to reduce DB load.",
        diff="""\
diff --git a/queries.py b/queries.py
--- a/queries.py
+++ b/queries.py
@@ -1 +1,8 @@
 # queries module
+_cache = {}
+def expensive_query(arg):
+    if arg in _cache:
+        return _cache[arg]
+    result = _do_query(arg)
+    _cache[arg] = result
+    return result
""",
        label="claimed_not_done",
        rationale="Cache exists but has no TTL — entries live forever, contradicting the '5-minute TTL' claim.",
    ),
    Example(
        id="seed-007",
        source="synthetic",
        pr_title="Refactor: extract _validate() helper",
        pr_body="Pure refactor. No behavior change.",
        diff="""\
diff --git a/svc.py b/svc.py
--- a/svc.py
+++ b/svc.py
@@ -1,4 +1,9 @@
+def _validate(x):
+    if x is None:
+        raise ValueError("nope")
+    if x < 0:
+        raise ValueError("negative")
+    return x
+
 def process(x):
-    if x is None:
-        raise ValueError("nope")
-    return x * 2
+    return _validate(x) * 2
""",
        label="done_not_claimed",
        rationale="Refactor accidentally adds a new constraint (rejects negative numbers) — behavior change.",
    ),
    Example(
        id="seed-008",
        source="synthetic",
        pr_title="Disable telemetry in test mode",
        pr_body="When TEST_MODE env var is set, skip the telemetry POST.",
        diff="""\
diff --git a/telemetry.py b/telemetry.py
--- a/telemetry.py
+++ b/telemetry.py
@@ -1,2 +1,5 @@
+import os
 def emit(event):
+    if os.environ.get("TEST_MODE"):
+        return
     requests.post(URL, json=event)
""",
        label="aligned",
        rationale="Implements exactly what the description states.",
    ),
    Example(
        id="seed-009",
        source="synthetic",
        pr_title="Fix off-by-one in pagination",
        pr_body="The last page was being skipped due to <= vs < bug.",
        diff="""\
diff --git a/page.py b/page.py
--- a/page.py
+++ b/page.py
@@ -1,2 +1,5 @@
 def pages(total, size):
-    return [(i, i+size) for i in range(0, total, size) if i+size < total]
+    return [(i, min(i+size, total)) for i in range(0, total, size)]
+
+# also lowered default page size
+DEFAULT_PAGE_SIZE = 25  # was 100
""",
        label="misaligned",
        rationale="Pagination fix is correct but the PR also lowers DEFAULT_PAGE_SIZE — a real config change not mentioned anywhere.",
    ),
    Example(
        id="seed-010",
        source="synthetic",
        pr_title="Update README links",
        pr_body="Fix three broken links in README.",
        diff="""\
diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -3 +3 @@
-[Docs](http://old.example.com/docs)
+[Docs](https://docs.example.com)
@@ -10 +10 @@
-[API](http://old.example.com/api)
+[API](https://api.example.com)
@@ -20 +20 @@
-[Blog](http://old.example.com/blog)
+[Blog](https://blog.example.com)
""",
        label="aligned",
        rationale="Pure docs change, matches description exactly.",
    ),
]


def main() -> None:
    out = Path(__file__).parent / "data" / "seed.jsonl"
    write_jsonl(out, SEED)
    print(f"Wrote {len(SEED)} examples to {out}")


if __name__ == "__main__":
    main()
