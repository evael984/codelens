"""Mock provider — replays scripted responses keyed by analyzer name.

Used for demos and tests so the project is runnable without an API key.

Responses are loaded from a JSON file:

    {
      "intent_drift": "{\\"claimed_not_done\\": [...], ...}",
      "side_effects": "{...}",
      "test_gap": "{...}"
    }

Selection logic: we look at the prompt to decide which scripted response to
return. This is brittle by design — mock is for demos, not production.
"""

from __future__ import annotations

import json
from pathlib import Path

from .base import LLMProvider, Message

_KEYWORD_MAP = {
    "intent_drift": ("PR_DESCRIPTION", "claimed_not_done"),
    "side_effects": ("CHANGED_SYMBOLS", "side_effects"),
    "test_gap": ("NEW_BEHAVIOR", "gaps"),
}


class MockProvider(LLMProvider):
    def __init__(self, script_path: Path) -> None:
        self._script: dict[str, str] = json.loads(script_path.read_text(encoding="utf-8"))

    def complete(self, message: Message, max_tokens: int = 2048) -> str:
        for analyzer, (system_kw, user_kw) in _KEYWORD_MAP.items():
            if system_kw in message.user or user_kw in message.system:
                response = self._script.get(analyzer)
                if response is not None:
                    return response
        return '{"verdict": "aligned", "claimed_not_done": [], "done_not_claimed": [], "side_effects": [], "gaps": []}'
