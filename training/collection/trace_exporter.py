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

from training.schemas import EMOTIONAL_ACTS

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

# ---------------------------------------------------------------------------
# Emotional trace export (plan 24 §29, §51 item 19)
# ---------------------------------------------------------------------------

# AffectiveState dimension -> emotional example label (plan 24 §6 dimensions).
_DIMENSION_LABEL: dict[str, str] = {
    "frustration_likelihood": "frustration",
    "fatigue_likelihood": "fatigue",
    "stress_likelihood": "stress",
    "enthusiasm_likelihood": "enthusiasm",
    "confusion_likelihood": "confusion",
    "comfort_likelihood": "comfort",
    "engagement": "engagement",
}

# dialogue act -> emotional SFT task (plan 24 §25); unknown acts fall back to
# appropriate_acknowledgement (the generic emotional realization task).
_EMOTIONAL_TASK_BY_ACT: dict[str, str] = {
    "ACKNOWLEDGE": "appropriate_acknowledgement",
    "SILENCE": "appropriate_silence",
    "REPAIR": "repair",
    "APOLOGIZE": "apology",
    "GIVE_SPACE": "boundary_respect",
    "SUPPORT": "support",
    "ENCOURAGE": "encouragement",
    "CELEBRATE": "celebration",
    "CLARIFY": "uncertainty",
    "ASK": "uncertainty",
    "VALIDATE": "support",
    "LISTEN": "support",
    "NORMALIZE": "support",
    "REDIRECT": "calm_disagreement",
}

_HYPOTHESIS_THRESHOLD = 0.1
_MAX_HYPOTHESES = 3


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


def emotional_task_for_act(act: str) -> str:
    """Map a dialogue act to its emotional SFT task (plan 24 §25)."""
    return _EMOTIONAL_TASK_BY_ACT.get(act, "appropriate_acknowledgement")


def _affective_hypotheses(social: dict[str, Any]) -> list[dict[str, Any]]:
    """AffectiveState snapshot -> normalized {label, probability} hypotheses.

    Only dimensions with a mapped label and effective signal (value x
    confidence) above threshold are kept; the top few are normalized to sum to
    1.0 so the example carries a proper distribution (plan 24 §24).
    """
    signal = social.get("emotional_signal") or {}
    scored: list[tuple[float, str]] = []
    for dim, raw in signal.items():
        label = _DIMENSION_LABEL.get(dim)
        if not label or not isinstance(raw, dict):
            continue
        effective = float(raw.get("value", 0.0)) * float(raw.get("confidence", 0.0))
        if effective >= _HYPOTHESIS_THRESHOLD:
            scored.append((effective, label))
    scored.sort(reverse=True)
    scored = scored[:_MAX_HYPOTHESES]
    total = sum(s for s, _ in scored) or 1.0
    return [{"label": label, "probability": round(s / total, 3)} for s, label in scored]


def _conversation_phase(social: dict[str, Any]) -> str:
    """Derive the emotional conversation phase from observable context."""
    temp = social.get("conversation_temperature", "")
    if temp == "tense":
        return "tension"
    if temp == "calm":
        return "normal"
    events = " ".join(social.get("recent_social_events") or [])
    if "correction" in events or "corrected" in events:
        return "correction"
    if "thanks" in events or "appreciated" in events or "positive" in events:
        return "resolution"
    if social.get("boundary_state", "NORMAL") != "NORMAL":
        return "tension"
    return "normal"


def _certainty(social: dict[str, Any]) -> str:
    """Certainty from the peak affective confidence (plan 24 §24)."""
    signal = social.get("emotional_signal") or {}
    confs = [float(d.get("confidence", 0.0)) for d in signal.values() if isinstance(d, dict)]
    peak = max(confs) if confs else 0.0
    if peak < 0.6:
        return "low"
    if peak < 0.8:
        return "moderate"
    return "high"


def emotional_eligibility_reasons(trace: dict[str, Any]) -> list[str]:
    """Deterministic reasons this trace is worth emotional training on (§29)."""
    reasons: list[str] = []
    social = trace.get("social_context") or {}
    if social.get("emotional_signal"):
        reasons.append("affective_evidence")
    if trace.get("dialogue_act"):
        reasons.append("clear_decision")
    outcome = trace.get("outcome", "")
    if outcome in _GOOD_OUTCOMES:
        reasons.append("successful_outcome")
    if outcome == "corrected" or trace.get("correction"):
        reasons.append("explicit_correction")
    if outcome in _BAD_OUTCOMES:
        reasons.append("interesting_failure")
    if trace.get("user_reaction"):
        reasons.append("user_reaction")
    return reasons


def is_emotional_eligible(trace: dict[str, Any]) -> bool:
    """§29: affective evidence + clear decision + an explicit outcome signal.

    Success is never inferred from silence alone: a trace with no outcome,
    correction, or reaction is not eligible even when the decision was clear.
    """
    reasons = emotional_eligibility_reasons(trace)
    if "affective_evidence" not in reasons or "clear_decision" not in reasons:
        return False
    value_signals = {
        "successful_outcome", "explicit_correction", "interesting_failure", "user_reaction",
    }
    return bool(value_signals & set(reasons))


class EmotionalTraceExporter:
    """DecisionTrace snapshot -> emotional-kind training example (plan 24 §29).

    Maps the affective state snapshot to probabilistic hypotheses, the
    dialogue act to the selected strategy, and the observable social context
    to the emotional situation. Real traces are `synthetic: False`; they
    complement the template-derived `synthetic: True` rows in the emotional
    datasets (plan 24 §23-§28).
    """

    def __init__(self, task_for_act: Callable[[str], str] = emotional_task_for_act) -> None:
        self._task_for_act = task_for_act

    def export(self, trace: dict[str, Any]) -> list[dict[str, Any]]:
        """Export one trace snapshot; [] when it is not emotionally eligible."""
        if not is_emotional_eligible(trace):
            return []
        act = trace.get("dialogue_act", "")
        identity = trace.get("identity_resolution") or {}
        social = trace.get("social_context") or {}
        example: dict[str, Any] = {
            "example_id": f"{trace.get('trace_id', 'trace')}-emo",
            "task": self._task_for_act(act),
            "situation": {
                "person": {
                    "id": identity.get("person_id", ""),
                    "name": identity.get("name", ""),
                },
                "relationship": social.get("relationship", ""),
                "conversation_phase": _conversation_phase(social),
                "user_goal": social.get("user_goal", ""),
                "affective_hypotheses": _affective_hypotheses(social),
                "novi_caused_problem": bool(trace.get("correction")) or bool(trace.get("novi_caused_problem")),
                "interruptibility": float(social.get("interruptibility", 1.0)),
            },
            "desired_behavior": {
                "act": [act] if act in EMOTIONAL_ACTS else ["RESPOND"],
                "verbosity": trace.get("verbosity", "short"),
                "defensiveness": trace.get("defensiveness", "none"),
                "certainty": _certainty(social),
            },
            "preferred_response": trace.get("response", ""),
            "synthetic": False,
        }
        return [example]

    def export_all(self, traces: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Export a batch of trace snapshots, keeping only eligible examples."""
        out: list[dict[str, Any]] = []
        for trace in traces:
            out.extend(self.export(trace))
        return out
