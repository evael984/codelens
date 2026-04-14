"""Anthropic provider with prompt caching.

The repo-level system prompt (project conventions, style guide, etc.) is marked
as a cache breakpoint so repeated reviews on the same repo only pay for the
delta tokens in the diff.
"""

from __future__ import annotations

from anthropic import Anthropic

from .base import LLMProvider, Message


class AnthropicProvider(LLMProvider):
    def __init__(self, model: str, api_key: str | None) -> None:
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        self._client = Anthropic(api_key=api_key)
        self._model = model

    def complete(self, message: Message, max_tokens: int = 2048) -> str:
        system_blocks: list[dict] = []
        if message.cacheable_system:
            system_blocks.append(
                {
                    "type": "text",
                    "text": message.cacheable_system,
                    "cache_control": {"type": "ephemeral"},
                }
            )
        if message.system:
            system_blocks.append({"type": "text", "text": message.system})

        response = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system_blocks or message.system,
            messages=[{"role": "user", "content": message.user}],
        )

        parts = []
        for block in response.content:
            if getattr(block, "type", None) == "text":
                parts.append(block.text)
        return "".join(parts).strip()
