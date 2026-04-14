"""Parses unified diff output into structured hunks usable by analyzers.

We stay language-agnostic here; language-specific AST work lives in each analyzer
(so adding a new language does not require touching this module).
"""

from __future__ import annotations

import fnmatch
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from unidiff import PatchSet


@dataclass
class ChangedHunk:
    file_path: str
    old_start: int
    new_start: int
    added_lines: list[str] = field(default_factory=list)
    removed_lines: list[str] = field(default_factory=list)
    context: str = ""

    def summary(self) -> str:
        added = "\n".join(f"+ {line}" for line in self.added_lines)
        removed = "\n".join(f"- {line}" for line in self.removed_lines)
        return f"{self.file_path}:{self.new_start}\n{removed}\n{added}".strip()


@dataclass
class Diff:
    hunks: list[ChangedHunk]
    raw: str

    def total_lines(self) -> int:
        return sum(len(h.added_lines) + len(h.removed_lines) for h in self.hunks)

    def files_changed(self) -> list[str]:
        return sorted({h.file_path for h in self.hunks})


def git_diff(base: str, head: str, repo: Path | None = None) -> str:
    repo_path = repo or Path.cwd()
    result = subprocess.run(
        ["git", "diff", "--unified=3", f"{base}..{head}"],
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def parse_diff(raw: str, ignore_paths: list[str] | None = None) -> Diff:
    ignore_paths = ignore_paths or []
    patch = PatchSet(raw)
    hunks: list[ChangedHunk] = []

    for patched_file in patch:
        path = patched_file.path
        if any(fnmatch.fnmatch(path, pat) for pat in ignore_paths):
            continue
        for hunk in patched_file:
            added = [line.value.rstrip("\n") for line in hunk if line.is_added]
            removed = [line.value.rstrip("\n") for line in hunk if line.is_removed]
            if not added and not removed:
                continue
            hunks.append(
                ChangedHunk(
                    file_path=path,
                    old_start=hunk.source_start,
                    new_start=hunk.target_start,
                    added_lines=added,
                    removed_lines=removed,
                    context=str(hunk),
                )
            )

    return Diff(hunks=hunks, raw=raw)
