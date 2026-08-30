"""Reasoning-provider adapter (plan 12, §43 Phase 43, §44 Phase 44).

Bridge between the existing ``ReasoningProvider`` contract
(``decide(...) -> ActionIntent``) and the ``InferenceRuntime``:

    existing reasoning request
        -> InferenceRequest
        -> InferenceRuntime
        -> InferenceResponse
        -> existing reasoning response (ActionIntent)

``MacBrain`` keeps receiving a ``ReasoningProvider``; the runtime-backed
provider is one implementation of that contract. This lets all current
cognition tests remain valid while the backend changes underneath, and keeps
the brain model/backend agnostic (it never constructs a backend directly).
"""

from __future__ import annotations

from typing import Any

from .errors import InferenceError
from .request import InferenceRequest, RequestPriority
from .response import InferenceResponse
from .runtime import InferenceRuntime

#: Deliberation level for reasoning requests (plan 12, §46): the reasoning
#: budget maps to model selection through router hypotheses.
_REASONING_BUDGET = "NORMAL"


def build_reasoning_request(
    *,
    conclusion: str,
    confidence: float,
    situation: Any,
    recall: Any = (),
    caller: str = "reasoning-provider",
    purpose: str = "decide",
    model_hint: str = "",
    reasoning_budget: str = _REASONING_BUDGET,
    max_output_tokens: int = 512,
) -> InferenceRequest:
    """Build a backend-neutral ``InferenceRequest`` from reasoning inputs.

    The situation is serialized as a bounded context package (messages), never
    as direct memory access (plan 12, §24 Phase 19).
    """
    situation_payload = _stable_repr(situation)
    system = (
        "You are Novi's reasoning layer. Given a cognition conclusion, "
        "confidence, situation summary, and recalled memories, choose a single "
        "bounded action from the allowed set and explain why. Never take an "
        "action outside the allowed set."
    )
    messages = [
        {
            "role": "user",
            "content": (
                f"conclusion: {conclusion}\n"
                f"confidence: {confidence:.3f}\n"
                f"situation: {situation_payload}\n"
                f"recalled_memories: {len(list(recall))}"
            ),
        }
    ]
    return InferenceRequest(
        caller=caller,
        purpose=purpose,
        model_hint=model_hint,
        messages=messages,
        system=system,
        max_output_tokens=max_output_tokens,
        priority=RequestPriority.NORMAL,
        reasoning_budget=reasoning_budget,
    )


def _stable_repr(value: Any) -> str:
    import json

    try:
        return json.dumps(value, sort_keys=True, default=repr)
    except (TypeError, ValueError):
        return repr(value)


def parse_reasoning_response(response: InferenceResponse, *, default_action: str = "observe") -> dict[str, Any]:
    """Translate an ``InferenceResponse`` into reasoning result fields.

    Returns ``{"action", "parameters", "rationale", "confidence"}``. A failed
    or empty response degrades to the safe default action with a low confidence
    so Policy/Safety still gates everything downstream (plan 12, §30).
    """
    text = (response.text or "").strip()
    if not text or not response.ok:
        return {
            "action": default_action,
            "parameters": {},
            "rationale": f"fallback:{default_action} (no usable model output)",
            "confidence": 0.0,
            "model_id": response.model_id,
            "backend_id": response.backend_id,
        }
    rationale = text[:400]
    # Best-effort structured extraction; never trust free text as a command.
    action = default_action
    parameters: dict[str, Any] = {}
    lowered = text.lower()
    for candidate in ("observe", "inspect", "wait", "move_forward", "turn_left", "turn_right"):
        if f"action: {candidate}" in lowered or candidate in lowered.split()[:12]:
            action = candidate
            break
    return {
        "action": action,
        "parameters": parameters,
        "rationale": rationale,
        "confidence": 0.5,
        "model_id": response.model_id,
        "backend_id": response.backend_id,
    }


class RuntimeBackedReasoningProvider:
    """A ``ReasoningProvider`` implementation backed by the inference runtime.

    Satisfies the existing reasoning contract (``decide`` -> ``ActionIntent``)
    so ``MacBrain`` can receive it exactly where it currently receives
    ``DeliberativeReasoningProvider`` or the ``ReasoningRouter``. The brain
    never knows which backend executes the request.
    """

    def __init__(
        self,
        runtime: InferenceRuntime,
        *,
        default_action: str = "observe",
        reasoning_budget: str = _REASONING_BUDGET,
    ) -> None:
        self.runtime = runtime
        self.default_action = default_action
        self.reasoning_budget = reasoning_budget
        self.last_request: InferenceRequest | None = None
        self.last_response: InferenceResponse | None = None

    def decide(self, *, conclusion: str, confidence: float, situation: Any, recall: Any = ()) -> Any:
        from novi.brain.models.reasoning import ActionIntent

        request = build_reasoning_request(
            conclusion=conclusion,
            confidence=confidence,
            situation=situation,
            recall=recall,
            caller="runtime-reasoning-provider",
            purpose="decide",
            reasoning_budget=self.reasoning_budget,
        )
        self.last_request = request
        try:
            response = self.runtime.generate(request)
        except InferenceError as exc:
            # Runtime fallback already handles degraded paths; if the runtime
            # itself is unusable, degrade to the safe default deterministically.
            return ActionIntent(
                action=self.default_action,
                parameters={},
                rationale=f"runtime_unavailable:{exc.code}",
            )
        self.last_response = response
        parsed = parse_reasoning_response(response, default_action=self.default_action)
        return ActionIntent(
            action=parsed["action"],
            parameters=parsed["parameters"],
            rationale=parsed["rationale"],
        )
