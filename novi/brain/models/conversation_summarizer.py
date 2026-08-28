"""Conversation summarization (Memory 3.4).

Distills a long chat thread into a durable summary using the local Ollama model,
with a deterministic fallback. The summary is stored as a memory so Novi keeps
the gist of a conversation even after the raw turns are trimmed.
"""

from __future__ import annotations

import json
import urllib.request
from typing import Any

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "qwen3:4b"


def _summary_prompt(turns: list[dict[str, Any]]) -> str:
    lines = "\n".join(f"- {t.get('role', '?')}: {t.get('text', '')}" for t in turns)
    return (
        "You are Novi's conversation summarizer. Distill this conversation into a "
        "concise summary (2-4 sentences) that preserves the key facts, decisions, "
        "and anything the user told you. Do not invent content.\n"
        f"Conversation:\n{lines}\n"
        'Respond ONLY with JSON: {"summary": "..."}'
    )


def _extract_summary(text: str) -> str | None:
    if not text:
        return None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict) and parsed.get("summary"):
        return str(parsed["summary"]).strip()
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
                    if isinstance(obj, dict) and obj.get("summary"):
                        return str(obj["summary"]).strip()
                except json.JSONDecodeError:
                    return None
    return None


class ConversationSummarizer:
    """Callable summarizer that distills a chat thread into a durable summary."""

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

    def __call__(self, turns: list[dict[str, Any]]) -> str | None:
        body: dict[str, Any] = {
            "model": self.model,
            "system": "You are Novi's conversation summarizer. Respond ONLY with the requested JSON.",
            "prompt": _summary_prompt(turns),
            "format": "json",
            "stream": False,
            "options": {"num_predict": self.max_tokens},
        }
        if "nemotron" in self.model.lower():
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
        return _extract_summary(raw)
