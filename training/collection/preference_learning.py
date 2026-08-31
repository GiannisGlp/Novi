"""Long-term preference learning (plan 24 §29-31, §51 item 31).

Every meaningful social interaction generates an outcome record; explicit
feedback is high-quality evidence; every classified failure becomes a training
candidate after quality review. This module accumulates those signals into
preference pairs (chosen/rejected) that feed DPO (plan §26) and policy
ranking (plan §27) over the long term.

    outcome record (§29)  -> outcome_to_preference  -> preference signal
    explicit feedback (§30) -> feedback_to_preference -> preference signal
    failure class (§31)    -> FAILURE_TO_PREFERRED_ACT -> preferred act

A preference signal is a lightweight chosen/rejected act pair plus the
situation it occurred in. `accumulate_preferences` folds a batch of records
into a growing log; `write_preference_log` persists it for later DPO folding.

Never infer success from silence alone (plan §29): a bare "acknowledged"
outcome with no explicit positive reaction produces no signal.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from training.collection.failure import classify_failure

# plan §31: each failure class maps to the act that should have been chosen.
FAILURE_TO_PREFERRED_ACT: dict[str, str] = {
    "MISREAD_EMOTION": "CLARIFY",      # ask what they actually feel
    "OVERREACTED": "ACKNOWLEDGE",      # proportional, not gushing
    "UNDERREACTED": "SUPPORT",         # match the signal strength
    "INTERRUPTED": "GIVE_SPACE",       # don't speak when busy
    "FAILED_TO_SUPPORT": "SUPPORT",    # distress present, offer support
    "OVER_SUPPORTED": "RESPOND",       # normal response, not support
    "IGNORED_BOUNDARY": "GIVE_SPACE",  # respect the boundary
    "REPEATED_ERROR": "APOLOGIZE",     # own the repeated error
    "DEFENSIVE_RESPONSE": "ACKNOWLEDGE",  # own the error, don't defend
    "EXCESSIVE_APOLOGY": "ACKNOWLEDGE",   # acknowledge without over-apologizing
    "UNNATURAL_EMPATHY": "VALIDATE",      # natural, specific validation
}

# plan §31: failure class -> dominant §26 preference dimension.
_FAILURE_CATEGORY: dict[str, str] = {
    "MISREAD_EMOTION": "emotional_timing",
    "OVERREACTED": "proportionality",
    "UNDERREACTED": "proportionality",
    "INTERRUPTED": "restraint",
    "FAILED_TO_SUPPORT": "proportionality",
    "OVER_SUPPORTED": "proportionality",
    "IGNORED_BOUNDARY": "boundary_respect",
    "REPEATED_ERROR": "humility",
    "DEFENSIVE_RESPONSE": "humility",
    "EXCESSIVE_APOLOGY": "humility",
    "UNNATURAL_EMPATHY": "naturalness",
}

# plan §29: only explicit positive reactions confirm success. Silence alone
# (a bare "acknowledged" outcome) is never treated as success.
_EXPLICIT_POSITIVE = frozenset({"thanks", "follow_up"})

# Feedback kinds that map to a concrete act preference (plan §30).
_FEEDBACK_ACT: dict[str, tuple[str, str]] = {
    "give_space": ("GIVE_SPACE", "restraint"),
    "boundary": ("GIVE_SPACE", "boundary_respect"),
}


def _situation_from(trace: dict[str, Any]) -> dict[str, Any]:
    """Derive the DPO situation (relationship, phase, affect, interruptibility)."""
    social = trace.get("social_context") or {}
    signals = trace.get("affective_signals") or {}
    hyps = [
        {"label": k.replace("_likelihood", ""), "probability": round(float(v), 3)}
        for k, v in signals.items()
        if isinstance(v, (int, float)) and float(v) > 0.1
    ]
    hyps.sort(key=lambda h: h["probability"], reverse=True)
    return {
        "relationship": social.get("relationship", "unknown"),
        "conversation_phase": trace.get("conversation_phase")
        or social.get("conversation_phase", "normal"),
        "affective_hypotheses": hyps[:3],
        "interruptibility": social.get("interruptibility", 0.5),
    }


def _failure_signal(trace: dict[str, Any]) -> dict[str, Any] | None:
    """Classify a corrected interaction and build its preference signal."""
    failure = classify_failure({
        "outcome": trace.get("outcome"),
        "social_context": trace.get("social_context") or {},
        "dialogue_act": trace.get("dialogue_act", ""),
        "response": trace.get("response_text", ""),
        "correction": trace.get("correction", ""),
    })
    if failure is None:
        return None
    return {
        "situation": _situation_from(trace),
        "chosen_act": FAILURE_TO_PREFERRED_ACT[failure],
        "rejected_act": trace.get("dialogue_act", ""),
        "category": _FAILURE_CATEGORY[failure],
        "source": "outcome",
        "outcome": trace.get("outcome", ""),
        "failure_class": failure,
        "synthetic": False,
    }


def outcome_to_preference(trace: dict[str, Any]) -> dict[str, Any] | None:
    """Convert an interaction outcome record (§29) into a preference signal.

    Returns None for neutral outcomes — never infer success from silence alone.
    """
    reaction = trace.get("user_reaction", "")
    outcome = trace.get("outcome", "")
    if outcome == "corrected" or reaction == "correction":
        return _failure_signal(trace)
    if reaction in _EXPLICIT_POSITIVE:
        return {
            "situation": _situation_from(trace),
            "chosen_act": trace.get("dialogue_act", ""),
            "rejected_act": "",
            "category": "naturalness",
            "source": "outcome",
            "outcome": outcome,
            "failure_class": "",
            "synthetic": False,
        }
    return None


def feedback_to_preference(feedback: dict[str, Any],
                           trace: dict[str, Any]) -> dict[str, Any] | None:
    """Convert an explicit feedback record (§30) into a preference signal."""
    kind = feedback.get("kind", "")
    if kind in _FEEDBACK_ACT:
        chosen, category = _FEEDBACK_ACT[kind]
        return {
            "situation": _situation_from(trace),
            "chosen_act": chosen,
            "rejected_act": trace.get("dialogue_act", ""),
            "category": category,
            "source": "feedback",
            "outcome": "",
            "failure_class": "",
            "synthetic": False,
        }
    if kind == "verbosity":
        act = trace.get("dialogue_act", "")
        return {
            "situation": _situation_from(trace),
            "chosen_act": act,
            "rejected_act": act,
            "category": "naturalness",
            "source": "feedback",
            "outcome": "",
            "failure_class": "",
            "verbosity": "terse",
            "synthetic": False,
        }
    if kind == "positive_outcome":
        return {
            "situation": _situation_from(trace),
            "chosen_act": trace.get("dialogue_act", ""),
            "rejected_act": "",
            "category": "naturalness",
            "source": "feedback",
            "outcome": "",
            "failure_class": "",
            "synthetic": False,
        }
    if kind == "correction":
        return _failure_signal(trace)
    return None


def accumulate_preferences(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Fold a batch of outcome/feedback records into a preference log.

    Neutral records (silence alone) are skipped; signals get sequential
    `emo-pref-lt-NNNN` ids so the log is stable and appendable.
    """
    signals: list[dict[str, Any]] = []
    n = 0
    for rec in records:
        sig = (feedback_to_preference(rec, rec.get("trace") or {})
               if "kind" in rec else outcome_to_preference(rec))
        if sig is None:
            continue
        n += 1
        sig["example_id"] = f"emo-pref-lt-{n:04d}"
        signals.append(sig)
    return signals


def write_preference_log(signals: list[dict[str, Any]], path: str | Path) -> None:
    """Persist the preference log as JSONL (one signal per line)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w") as f:
        for sig in signals:
            f.write(json.dumps(sig, ensure_ascii=False) + "\n")
