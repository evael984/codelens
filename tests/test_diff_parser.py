from codelens.diff_parser import parse_diff

SAMPLE_DIFF = """\
diff --git a/foo.py b/foo.py
index 1111111..2222222 100644
--- a/foo.py
+++ b/foo.py
@@ -1,2 +1,3 @@
 def hello():
-    return "hi"
+    return "hello"
+    # added line
diff --git a/vendor/lib.py b/vendor/lib.py
index 3333333..4444444 100644
--- a/vendor/lib.py
+++ b/vendor/lib.py
@@ -1 +1 @@
-x = 1
+x = 2
"""


def test_parse_diff_basic():
    diff = parse_diff(SAMPLE_DIFF)
    assert "foo.py" in diff.files_changed()
    assert diff.total_lines() > 0


def test_parse_diff_ignore_paths():
    diff = parse_diff(SAMPLE_DIFF, ignore_paths=["vendor/**"])
    assert "vendor/lib.py" not in diff.files_changed()
    assert "foo.py" in diff.files_changed()


def test_hunk_summary_contains_added_and_removed():
    diff = parse_diff(SAMPLE_DIFF)
    foo_hunk = next(h for h in diff.hunks if h.file_path == "foo.py")
    summary = foo_hunk.summary()
    assert '+' in summary
    assert '-' in summary
