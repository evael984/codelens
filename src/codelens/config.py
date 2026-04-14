"""Configuration loading. Resolves `.codelens.toml` + env vars into a typed config object."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


ProviderName = Literal["anthropic", "openai", "ollama", "mock"]


class ProviderConfig(BaseModel):
    name: ProviderName = "anthropic"
    model: str = "claude-opus-4-6"
    base_url: str | None = None


class AnalyzersConfig(BaseModel):
    intent_drift: bool = True
    side_effects: bool = True
    test_gap: bool = True


class FiltersConfig(BaseModel):
    ignore_paths: list[str] = Field(default_factory=list)
    max_diff_lines: int = 2000


class Config(BaseModel):
    provider: ProviderConfig = Field(default_factory=ProviderConfig)
    analyzers: AnalyzersConfig = Field(default_factory=AnalyzersConfig)
    filters: FiltersConfig = Field(default_factory=FiltersConfig)

    @classmethod
    def load(cls, path: Path | None = None) -> "Config":
        candidate = path or Path.cwd() / ".codelens.toml"
        if not candidate.exists():
            return cls()
        with candidate.open("rb") as f:
            data = tomllib.load(f)
        return cls.model_validate(data)

    def api_key(self) -> str | None:
        env = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "ollama": None,
            "mock": None,
        }[self.provider.name]
        return os.environ.get(env) if env else None
