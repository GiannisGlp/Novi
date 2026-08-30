"""Training trace export (plan 23 §6, step 03).

Consumes `novi.brain.decision_trace.DecisionTrace` snapshots (already recorded
by the brain) and exports only *training-eligible* examples (§6.2) in the
canonical format (plan §5). Eligibility is deterministic and explainable:

    meaningful context + clear decision
        + (successful outcome | explicit correction | interesting failure
           | initiative / memory / grounding decision)

The exporter never fabricates fields: everything it emits comes from the
trace. Person ids are copied verbatim here; `sanitizer.py` applies abstract
id mapping and PII redaction (§7) before anything becomes a dataset.
"""

from __future__ import annotations

from typing import Any, Callable

# dialogue act -> SFT task (plan §10.1); unknown acts fall back to
# natural_dialogue (the generic realization task).
_TASK_BY_ACT: dict[str, str] = {
    "GREETING": "social_greeting",
    "FAREWELL": "social_greeting",
    "CLARIFY": "clarification",
    "ASK": "clarification",
    "REPAIR": "repair",
    "CONTINUE": "context_continuation",
    "SILENCE": "silence_abstention",
    "COMMENT": "proactive_comment",
    "INFORM": "proactive_comment",
    "SUGGEST": "proactive_comment",
    "WARN": "proactive_comment",
}

_PROACTIVE_ACTS = frozenset({"COMMENT", "INFORM", "SUGGEST", "WARN", "GREETING", "FAREWELL", "CONTINUE"})
_GOOD_OUTCOMES = frozenset({"acknowledged", "thanks", "follow_up", "positive", "accepted"})
_BAD_OUTCOMES = frozenset({"ignored", "negative", "rejected", "confused"})


def default_task_for_act(act: str) -> str:
    """Map a dialogue act to its SFT task (plan §10.1)."""
    return _TASK_BY_ACT.get(act, "natural_dialogue")


def eligibility_reasons(trace: dict[str, Any]) -> list[str]:
    """Deterministic reasons this trace is worth training on (§6.2)."""
    reasons: list[str] = []
    act = trace.get("dialogue_act", "")
    if act:
        reasons.append("clear_decision")
    has_context = bool(
        trace.get("input_event") or trace.get("perception_evidence") or trace.get("retrieved_memories")
    )
    if has_context:
        reasons.append("meaningful_context")
    outcome = trace.get("outcome", "")
    if outcome in _GOOD_OUTCOMES:
        reasons.append("successful_outcome")
    if outcome == "corrected" or trace.get("correction"):
        reasons.append("explicit_correction")
    if outcome in _BAD_OUTCOMES:
        reasons.append("interesting_failure")
    if float(trace.get("initiative_score", 0.0)) > 0.0 or act in _PROACTIVE_ACTS:
        reasons.append("initiative_decision")
    if trace.get("retrieved_memories"):
        reasons.append("memory_retrieval_decision")
    if trace.get("perception_evidence") or trace.get("identity_resolution"):
        reasons.append("grounding_decision")
    return reasons


def is_eligible(trace: dict[str, Any]) -> bool:
    """§6.2: meaningful context + clear decision + at least one interest signal."""
    reasons = eligibility_reasons(trace)
    if "meaningful_context" not in reasons or "clear_decision" not in reasons:
        return False
    value_signals = {
        "successful_outcome", "explicit_correction", "interesting_failure",
        "initiative_decision", "memory_retrieval_decision", "grounding_decision",
    }
    return bool(value_signals & set(reasons))


def _memory_ref(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        return {
            "id": item.get("id", ""),
            "summary": item.get("summary") or item.get("id", ""),
            "confidence": float(item.get("confidence", 1.0)),
        }
    return {"id": str(item), "summary": str(item), "confidence": 1.0}


class TraceExporter:
    """DecisionTrace snapshot -> canonical training examples (plan §5)."""

    def __init__(self, task_for_act: Callable[[str], str] = default_task_for_act) -> None:
        self._task_for_act = task_for_act

    def export(self, trace: dict[str, Any]) -> list[dict[str, Any]]:
        """Export one trace snapshot; [] when it is not training-eligible."""
        if not is_eligible(trace):
            return []
        act = trace.get("dialogue_act", "")
        identity = trace.get("identity_resolution") or {}
        social = trace.get("social_context") or {}
        example_id = f"{trace.get('trace_id', 'trace')}-0"
        example: dict[str, Any] = {
            "example_id": example_id,
            "task": self._task_for_act(act),
            "situation": {
                "person": {
                    "id": identity.get("person_id", ""),
                    "name": identity.get("name", ""),
                    "relationship": social.get("relationship", ""),
                    "confidence": float(identity.get("confidence", 1.0)),
                },
                "world": {
                    "changes": list(trace.get("world_changes") or []),
                    "perception": list(trace.get("perception_evidence") or []),
                },
                "conversation": {
                    "topic": social.get("topic", ""),
                    "input_event": trace.get("input_event", ""),
                },
                "memory": [_memory_ref(m) for m in (trace.get("retrieved_memories") or [])],
                "social": dict(social),
            },
            "decision": {
                "dialogue_act": act,
                "reason": trace.get("dialogue_reason", ""),
                "verbosity": "medium",
            },
            "response": trace.get("response", ""),
        }
        return [example]

    def export_all(self, traces: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Export a batch of trace snapshots, keeping only eligible examples."""
        out: list[dict[str, Any]] = []
        for trace in traces:
            out.extend(self.export(trace))
        return out
