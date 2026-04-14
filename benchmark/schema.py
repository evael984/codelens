"""Typed records for benchmark datasets and run results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Iterator, Literal

from pydantic import BaseModel, Field

Label = Literal["aligned", "claimed_not_done", "done_not_claimed", "misaligned", "?"]


class Example(BaseModel):
    id: str
    source: str
    pr_title: str
    pr_body: str
    diff: str
    label: Label
    rationale: str = ""
    reverted: bool = False
    revert_commit: str | None = None


class RunResult(BaseModel):
    id: str
    gold_label: Label
    predicted_label: Label
    findings: list[dict] = Field(default_factory=list)
    raw_provider_output: str = ""
    error: str | None = None


def load_jsonl(path: Path) -> Iterator[Example]:
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield Example.model_validate_json(line)


def write_jsonl(path: Path, records: Iterable[BaseModel]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(r.model_dump_json())
            f.write("\n")


def load_results(path: Path) -> list[RunResult]:
    out: list[RunResult] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(RunResult.model_validate(json.loads(line)))
    return out
