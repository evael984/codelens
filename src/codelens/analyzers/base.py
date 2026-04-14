"""Analyzer interface — each analyzer takes parsed context and returns findings."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import Any

from ..diff_parser import Diff
from ..providers import LLMProvider, Message


@dataclass
class Finding:
    analyzer: str
    severity: str  # "low" | "medium" | "high"
    title: str
    detail: str
    location: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisContext:
    diff: Diff
    pr_description: str
    repo_root: Path


class Analyzer(ABC):
    name: str

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    @abstractmethod
    def run(self, ctx: AnalysisContext) -> list[Finding]:
        ...

    @staticmethod
    def load_prompt(filename: str) -> str:
        return resources.files("codelens.prompts").joinpath(filename).read_text(encoding="utf-8")

    @staticmethod
    def parse_json(text: str) -> dict:
        """Tolerant JSON parser — strips fences and locates the first JSON object."""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```", 2)[1]
            if cleaned.lstrip().startswith("json"):
                cleaned = cleaned.lstrip()[4:]
            cleaned = cleaned.rstrip("`").strip()

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1:
            return {}
        try:
            return json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError:
            return {}

    def _message(self, prompt_file: str, user: str, cacheable_system: str | None = None) -> Message:
        return Message(
            system=self.load_prompt(prompt_file),
            user=user,
            cacheable_system=cacheable_system,
        )
