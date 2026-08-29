"""LLM-enhanced episodic narrative (Memory 3.3).

Writes a natural, coherent "what happened" recap of recent episodic memories
using the local Ollama model, instead of a deterministic concatenation.
Best-effort: any failure returns None so the caller falls back to the
deterministic list.
"""

from __future__ import annotations

import json
import urllib.request
from typing import Any

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "nemotron-3.5-lightning"


def _narrative_prompt(episodes: list[dict[str, Any]]) -> str:
    lines = "\n".join(f"- [{e.get('memory_type', 'event')}] {e.get('content', '')}" for e in episodes)
    return (
        "You are Novi's episodic memory narrator. Reconstruct a short, natural "
        "narrative (2-4 sentences) of what happened, in chronological order. "
        "Preserve the key facts; do not invent events.\n"
        f"Recent episodes:\n{lines}\n"
        'Respond ONLY with JSON: {"narrative": "..."}'
    )


def _extract_narrative(text: str) -> str | None:
    if not text:
        return None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict) and parsed.get("narrative"):
        return str(parsed["narrative"]).strip()
    depth = 0
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    obj = json.loads(text[start : i + 1])
                    if isinstance(obj, dict) and obj.get("narrative"):
                        return str(obj["narrative"]).strip()
                except json.JSONDecodeError:
                    return None
    return None


class LLMNarrator:
    """Callable narrator that uses a local Ollama model to write an episodic recap."""

    def __init__(
        self,
        *,
        model: str = DEFAULT_OLLAMA_MODEL,
        base_url: str = DEFAULT_OLLAMA_URL,
        max_tokens: int = 300,
    ) -> None:
        self.model = model
        self.base_url = base_url
        self.max_tokens = max_tokens

    def __call__(self, episodes: list[dict[str, Any]]) -> str | None:
        from novi.brain.models.ollama_reasoning import disable_thinking_for, num_predict_for

        body: dict[str, Any] = {
            "model": self.model,
            "system": "You are Novi's episodic memory narrator. Respond ONLY with the requested JSON.",
            "prompt": _narrative_prompt(episodes),
            "format": "json",
            "stream": False,
            "options": {"num_predict": num_predict_for(self.model, self.max_tokens)},
        }
        if disable_thinking_for(self.model):
            body["think"] = False
        request = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
        except Exception:
            return None
        raw = data.get("response", "")
        if not (raw or "").strip():
            raw = data.get("thinking", "")
        return _extract_narrative(raw)
