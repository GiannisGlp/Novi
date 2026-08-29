from __future__ import annotations

import json
import urllib.request
from typing import Any, Callable

from .provider import MacModelProvider, MacModelSpec
from .reasoning import ActionIntent, LLMReasoningProvider

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "nemotron-3.5-lightning"


def disable_thinking_for(model: str) -> bool:
    """True when the model's chain-of-thought should be disabled.

    Fast tiers (qwen3:4b, qwen3:8b, nemotron-3.5-lightning) answer directly;
    qwen3.8:27b is the heavy-thinking tier and keeps its reasoning (user
    tiering, 2026-08-29).
    """
    m = (model or "").lower()
    return (m.startswith("qwen3:") or "nemotron" in m) and not m.startswith("qwen3.8")


def num_predict_for(model: str, fast_budget: int) -> int:
    """Completion token budget: 2x (min 600) for the heavy-thinking tier.

    qwen3.8:27b thinks THEN answers (~250 + ~250 tokens typical); at ~3 tok/s
    on MPS a 1200-token budget would take 6+ minutes. 2x/min-600 keeps a deep
    reply under ~3.5 min worst case while still fitting thought + answer.
    """
    if (model or "").lower().startswith("qwen3.8"):
        return max(int(fast_budget) * 2, 600)
    return int(fast_budget)


def _ollama_backend_fn(*, base_url: str, model: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Return a callable that runs a single-shot JSON completion via Ollama."""

    def invoke(payload: dict[str, Any]) -> dict[str, Any]:
        system = (
            "You are Novi's bounded behavioral reasoner. Decide ONE action to take "
            "from the allowed set. Respond ONLY with a JSON object of the form "
            '{"action": "<name>", "parameters": {"<key>": "<value>"}}. '
            "Never propose an action outside the allowed set."
        )
        user = json.dumps(payload, sort_keys=True)
        body: dict[str, Any] = {
            "model": model,
            "system": system,
            "prompt": user,
            "format": "json",
            "stream": False,
            "options": {"num_predict": num_predict_for(model, 400)},
        }
        # Structured action decisions ALWAYS run think:false — chain-of-thought
        # is wasted on a bounded JSON decision (and on the heavy-thinking tier
        # it would blow every timeout). Heavy thinking belongs to the user
        # facing reply (_llm_chat), not the internal decision.
        body["think"] = False
        request = urllib.request.Request(f"{base_url}/api/generate", data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
        raw = data.get("response", "{}")
        if not (raw or "").strip():
            # Chain-of-thought fallback: the JSON decision may sit in `thinking`.
            raw = _extract_json_from_thinking(data.get("thinking", ""))
        try:
            parsed = json.loads(raw or "{}")
        except json.JSONDecodeError:
            return {}
        return {"action": str(parsed.get("action", "")), "parameters": dict(parsed.get("parameters", {}) or {})}

    return invoke


def _extract_json_from_thinking(thinking: str) -> str:
    """Best-effort pull of the first JSON object embedded in a CoT dump."""
    if not thinking:
        return ""
    depth = 0
    for i, ch in enumerate(thinking):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return thinking[start : i + 1]
    return ""


class OllamaReasoningProvider:
    """Real local reasoning model running through Ollama and ``MacModelProvider``.

    Routes the cognition conclusion through a local LLM (e.g. qwen3) and returns
    a bounded ``ActionIntent``. The LLM is offered only a fixed allowlist and its
    chosen action is re-validated, so it can never authorize an unbounded action.
    """

    def __init__(
        self,
        *,
        model: str = DEFAULT_OLLAMA_MODEL,
        base_url: str = DEFAULT_OLLAMA_URL,
        allowed_actions: frozenset[str] = frozenset({"inspect", "observe", "wait", "stop", "move_forward", "turn_left", "turn_right"}),
        default_action: str = "observe",
    ) -> None:
        spec = MacModelSpec(
            capability="reasoning",
            model_id=f"ollama:{model}",
            model_version="1.0.0",
            artifact_digest="sha256:local-ollama",
            runtime="ollama",
            runtime_version="0.32",
            modalities=("text",),
        )
        backend = _ollama_backend_fn(base_url=base_url, model=model)
        provider = MacModelProvider(spec, backend)
        self._llm = LLMReasoningProvider(provider, allowed_actions=allowed_actions, default_action=default_action)
        self.model_id = spec.model_id
        self.model = model
        self.base_url = base_url

    def set_model(self, name: str) -> None:
        """Rebind the provider to another Ollama model at runtime."""
        name = name.strip()
        if not name:
            return
        spec = MacModelSpec(
            capability="reasoning",
            model_id=f"ollama:{name}",
            model_version="1.0.0",
            artifact_digest="sha256:local-ollama",
            runtime="ollama",
            runtime_version="0.32",
            modalities=("text",),
        )
        backend = _ollama_backend_fn(base_url=self.base_url, model=name)
        provider = MacModelProvider(spec, backend)
        self._llm = LLMReasoningProvider(provider, allowed_actions=self._llm.allowed_actions, default_action=self._llm.default_action)
        self.model_id = spec.model_id
        self.model = name

    def decide(self, *, conclusion: str, confidence: float, situation: Any, recall: Any = ()) -> ActionIntent:
        return self._llm.decide(conclusion=conclusion, confidence=confidence, situation=situation, recall=recall)
