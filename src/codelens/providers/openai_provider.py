"""OpenAI-compatible provider. Also serves Ollama (which exposes an OpenAI-compatible API)."""

from __future__ import annotations

from openai import OpenAI

from .base import LLMProvider, Message


class OpenAIProvider(LLMProvider):
    def __init__(self, model: str, api_key: str | None, base_url: str | None = None) -> None:
        self._client = OpenAI(api_key=api_key or "missing", base_url=base_url)
        self._model = model

    def complete(self, message: Message, max_tokens: int = 2048) -> str:
        system_text = "\n\n".join(s for s in [message.cacheable_system, message.system] if s)
        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_text},
                {"role": "user", "content": message.user},
            ],
        )
        return (response.choices[0].message.content or "").strip()
