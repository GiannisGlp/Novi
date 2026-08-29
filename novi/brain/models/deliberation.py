"""Multi-step LLM deliberation (Reasoning 3.0).

Replaces the single-shot conclusion→action LLM call with a bounded, structured
deliberation: the model explicitly reasons through ANALYSIS → OPTIONS → DECISION
before committing to one action. The deliberation trace is captured for
inspection, and the chosen action is re-validated against the allowlist so the
LLM can never authorize an unbounded action.

Boundaries:
  - Deliberation is bounded to a single structured call (no unbounded thinking).
  - The decision is validated against the fixed allowlist; an invalid or missing
    decision falls back to the safe default action.
  - Policy/Safety still gates every resulting action at execution time.
"""

from __future__ import annotations

import json
import urllib.request
from typing import Any

from .reasoning import ActionIntent

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "qwen3:4b"
DEFAULT_ALLOWED = frozenset({"inspect", "observe", "wait", "stop", "move_forward", "turn_left", "turn_right"})


def _deliberation_prompt(situation: dict[str, Any], recall: Any, allowed: frozenset[str]) -> str:
    allowed_list = ", ".join(sorted(allowed))
    return (
        "You are Novi's deliberative reasoner. Reason through multiple steps before choosing ONE action.\n"
        "Allowed actions: " + allowed_list + ".\n"
        "Situation: " + json.dumps(situation, sort_keys=True) + "\n"
        "Recalled memories: " + json.dumps(list(recall), sort_keys=True) + "\n"
        "Steps:\n"
        "1. ANALYSIS: briefly explain what is happening and what matters.\n"
        "2. OPTIONS: list 2-4 candidate actions from the allowed set with pros/cons.\n"
        "3. DECISION: choose the single best action.\n"
        'Respond ONLY with JSON: {"analysis": "...", "options": [{"action": "...", "pros": "...", "cons": "..."}], '
        '"decision": {"action": "...", "parameters": {"<key>": "<value>"}, "rationale": "..."}}'
    )


def _extract_json(text: str) -> dict[str, Any]:
    """Best-effort parse of the first JSON object in a model response."""
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
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
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    return {}
    return {}


class DeliberativeLLMReasoningProvider:
    """Local LLM that deliberates (analysis → options → decision) before acting.

    Drop-in for ``OllamaReasoningProvider``: same ``decide`` signature, but the
    model is prompted to reason through multiple steps and the structured
    deliberation is captured on ``last_deliberation`` for the reasoning trace.

    Multi-round (Reasoning 3.2): after the initial decision the model critiques
    its own choice and either confirms it or revises it, up to ``max_rounds``
    total rounds. The loop is bounded and the final decision is re-validated
    against the allowlist.
    """

    def __init__(
        self,
        *,
        model: str = DEFAULT_OLLAMA_MODEL,
        base_url: str = DEFAULT_OLLAMA_URL,
        allowed_actions: frozenset[str] = DEFAULT_ALLOWED,
        default_action: str = "observe",
        max_rounds: int = 2,
        max_tokens: int = 600,
        timeout: float = 60,
    ) -> None:
        self.model = model
        self.base_url = base_url
        self.allowed_actions = allowed_actions
        self.default_action = default_action
        self.max_rounds = max(1, int(max_rounds))
        self.max_tokens = max(1, int(max_tokens))
        self.timeout = max(1.0, float(timeout))
        self.last_deliberation: dict[str, Any] | None = None

    def decide(self, *, conclusion: str, confidence: float, situation: Any, recall: Any = ()) -> ActionIntent:
        situation = situation if isinstance(situation, dict) else {}
        raw = self._invoke(_deliberation_prompt(situation, recall, self.allowed_actions))
        deliberation = _extract_json(raw)
        decision = deliberation.get("decision") or {}
        rounds: list[dict[str, Any]] = [
            {
                "round": 1,
                "analysis": str(deliberation.get("analysis", "")),
                "options": list(deliberation.get("options", []) or []),
                "decision": decision,
            }
        ]
        # Self-critique rounds: the model evaluates its own decision and either
        # confirms it or revises it. Bounded by max_rounds.
        for r in range(2, self.max_rounds + 1):
            critique_raw = self._invoke(_critique_prompt(decision, situation, recall, self.allowed_actions))
            critique = _extract_json(critique_raw)
            confirmed = bool(critique.get("confirm", False))
            revised = critique.get("decision") or {}
            rounds.append(
                {
                    "round": r,
                    "evaluation": str(critique.get("evaluation", "")),
                    "confirm": confirmed,
                    "decision": revised,
                }
            )
            if confirmed:
                break
            if revised.get("action"):
                decision = revised

        action = str(decision.get("action", ""))
        if action not in self.allowed_actions:
            action = self.default_action
            parameters: dict[str, Any] = {}
        else:
            parameters = dict(decision.get("parameters", {}) or {})
        self.last_deliberation = {
            "analysis": str(deliberation.get("analysis", "")),
            "options": list(deliberation.get("options", []) or []),
            "decision": {"action": action, "parameters": parameters, "rationale": str(decision.get("rationale", ""))},
            "rounds": rounds,
        }
        rationale = f"deliberated:{conclusion} -> {action} ({len(rounds)} rounds)"
        if decision.get("rationale"):
            rationale += f" ({decision['rationale']})"
        return ActionIntent(action=action, parameters=parameters, rationale=rationale)

    def _invoke(self, user_prompt: str) -> str:
        from novi.brain.models.ollama_reasoning import disable_thinking_for, num_predict_for

        system = "You are Novi's bounded deliberative reasoner. Respond ONLY with the requested JSON."
        body: dict[str, Any] = {
            "model": self.model,
            "system": system,
            "prompt": user_prompt,
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
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        raw = data.get("response", "")
        if not (raw or "").strip():
            raw = data.get("thinking", "")
        return raw


def _critique_prompt(decision: dict[str, Any], situation: dict[str, Any], recall: Any, allowed: frozenset[str]) -> str:
    allowed_list = ", ".join(sorted(allowed))
    return (
        "You are Novi's deliberative reasoner. You proposed this decision:\n"
        + json.dumps(decision, sort_keys=True) + "\n"
        "Critically evaluate it against the situation. If it is sound, confirm it. "
        "If a better action from the allowed set exists, revise it.\n"
        "Allowed actions: " + allowed_list + ".\n"
        "Situation: " + json.dumps(situation, sort_keys=True) + "\n"
        'Respond ONLY with JSON: {"evaluation": "...", "confirm": true/false, '
        '"decision": {"action": "...", "parameters": {"<key>": "<value>"}, "rationale": "..."}}'
    )
