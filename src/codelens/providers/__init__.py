import os
from pathlib import Path

from .base import LLMProvider, Message
from .anthropic_provider import AnthropicProvider
from .openai_provider import OpenAIProvider
from .mock_provider import MockProvider


def build_provider(name: str, model: str, api_key: str | None, base_url: str | None = None) -> LLMProvider:
    if name == "mock":
        script = os.environ.get("CODELENS_MOCK_SCRIPT")
        if not script:
            raise RuntimeError("Mock provider requires CODELENS_MOCK_SCRIPT to point at a JSON script.")
        return MockProvider(Path(script))
    if name == "anthropic":
        return AnthropicProvider(model=model, api_key=api_key)
    if name == "openai":
        return OpenAIProvider(model=model, api_key=api_key, base_url=base_url)
    if name == "ollama":
        return OpenAIProvider(
            model=model,
            api_key=api_key or "ollama",
            base_url=base_url or "http://localhost:11434/v1",
        )
    raise ValueError(f"Unknown provider: {name}")


__all__ = [
    "LLMProvider",
    "Message",
    "AnthropicProvider",
    "OpenAIProvider",
    "MockProvider",
    "build_provider",
]
