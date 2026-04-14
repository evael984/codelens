"""Provider abstraction.

A provider takes a system prompt + user prompt and returns a string response.
The `cacheable_system` field hints to providers that support prompt caching
(currently Anthropic) which prefix is stable across calls and worth caching.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Message:
    system: str
    user: str
    cacheable_system: str | None = None


class LLMProvider(ABC):
    @abstractmethod
    def complete(self, message: Message, max_tokens: int = 2048) -> str:
        ...
