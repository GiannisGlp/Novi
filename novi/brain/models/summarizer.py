"""LLM-enhanced memory summaries (Memory 3.1).

Writes a true semantic gist for a group of episodic memories using the local
Ollama model, instead of a deterministic concatenation. Best-effort: any failure
returns None so the caller falls back to the deterministic summary.
"""

from __future__ import annotations

import json
import urllib.request
from typing import Any

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "qwen3:4b"


def _summary_prompt(entity: str, records: list[Any]) -> str:
    # Prompt-boundary cap: an entity can accumulate hundreds of episodic
    # records; feeding them all verbatim made this prompt ~40K chars (~10K
    # tokens). The most recent 20 records, 200 chars each, carries the gist.
    recent = records[-20:]
    episodes = "\n".join(
        f"- {str(r.content)[:200]}" if not isinstance(r.content, str) else f"- {r.content[:200]}" for r in recent
    )
    return (
        f"You are Novi's memory consolidator. Distill these episodic memories about '{entity}' "
        "into ONE concise, higher-level summary (2-3 sentences). Preserve the key facts and "
        "the overall gist; do not invent facts.\n"
        f"Episodes:\n{episodes}\n"
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
    # best-effort: pull the first JSON object if embedded in prose
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


class LLMSummarizer:
    """Callable summarizer that uses a local Ollama model to write a semantic gist."""

    def __init__(
        self,
        *,
        model: str = DEFAULT_OLLAMA_MODEL,
        base_url: str = DEFAULT_OLLAMA_URL,
        max_tokens: int = 200,
    ) -> None:
        self.model = model
        self.base_url = base_url
        self.max_tokens = max_tokens

    def __call__(self, entity: str, records: list[Any]) -> str | None:
        from novi.brain.models.ollama_reasoning import disable_thinking_for, num_predict_for

        body: dict[str, Any] = {
            "model": self.model,
            "system": "You are Novi's memory consolidator. Respond ONLY with the requested JSON.",
            "prompt": _summary_prompt(entity, records),
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
        return _extract_summary(raw)
