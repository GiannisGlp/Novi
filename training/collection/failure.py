"""Emotional failure classification (plan 24 §31, §51 item 19).

Every failure is classified into one of the 11 plan classes so it can become
a training candidate after quality review. Classification is deterministic
and rule-based: it reads the decision trace (outcome, correction, social
context, dialogue act, response) and returns the single most specific class,
or None when the interaction was not a failure.

The classes (plan §31):

    MISREAD_EMOTION      — the affective interpretation was wrong
    OVERREACTED          — strong response to a weak signal
    UNDERREACTED         — weak response to a strong signal
    INTERRUPTED          — interrupted a busy person
    FAILED_TO_SUPPORT    — distress present, no support offered
    OVER_SUPPORTED       — support offered when none was needed
    IGNORED_BOUNDARY     — pushed past an explicit boundary
    REPEATED_ERROR       — the same mistake repeated
    DEFENSIVE_RESPONSE   — got defensive instead of owning the error
    EXCESSIVE_APOLOGY    — apologized when Novi was not at fault
    UNNATURAL_EMPATHY    — canned, template empathy phrasing
"""

from __future__ import annotations

import re
from typing import Any

FAILURE_CLASSES: frozenset[str] = frozenset({
    "MISREAD_EMOTION", "OVERREACTED", "UNDERREACTED", "INTERRUPTED",
    "FAILED_TO_SUPPORT", "OVER_SUPPORTED", "IGNORED_BOUNDARY",
    "REPEATED_ERROR", "DEFENSIVE_RESPONSE", "EXCESSIVE_APOLOGY",
    "UNNATURAL_EMPATHY",
})

_GOOD_OUTCOMES = frozenset({"acknowledged", "thanks", "follow_up", "positive", "accepted"})
_PUSHY_ACTS = frozenset({"ASK", "PROBE", "COMMENT", "INFORM", "SUGGEST", "WARN", "INTERRUPT"})
_PROACTIVE_ACTS = frozenset({"COMMENT", "INFORM", "SUGGEST", "WARN", "GREETING", "FAREWELL", "CONTINUE", "INTERRUPT"})
_SUPPORT_ACTS = frozenset({"SUPPORT", "VALIDATE", "LISTEN", "NORMALIZE", "ENCOURAGE"})
_STRONG_ACTS = frozenset({"APOLOGIZE", "SUPPORT", "ENCOURAGE", "CELEBRATE", "VALIDATE", "ACKNOWLEDGE"})
_WEAK_ACTS = frozenset({"SILENCE", "GIVE_SPACE"})

_DISTRESS_DIMS = (
    "frustration_likelihood", "stress_likelihood", "distress_likelihood",
    "sadness_likelihood", "anger_likelihood", "anxiety_likelihood",
)

_EMOTION_WORDS = (
    "frustrated", "angry", "sad", "upset", "annoyed", "tired", "stressed",
    "anxious", "emotional", "feeling", "fine", "okay",
)

_CANNED_EMPATHY = (
    "i understand that you are experiencing",
    "i sincerely apologize",
    "i am so terribly sorry",
    "i understand how you feel",
    "it sounds like you're going through",
    "i'm here to support you through this",
    "i completely understand your frustration",
)

_CANNED_RE = re.compile("|".join(re.escape(p) for p in _CANNED_EMPATHY), re.IGNORECASE)


def _effective_signal(social: dict[str, Any], dims: tuple[str, ...]) -> float:
    """Peak value x confidence across the given affective dimensions."""
    signal = social.get("emotional_signal") or {}
    best = 0.0
    for dim, raw in signal.items():
        if dim not in dims or not isinstance(raw, dict):
            continue
        best = max(best, float(raw.get("value", 0.0)) * float(raw.get("confidence", 0.0)))
    return best


def _mentions_emotion(text: str) -> bool:
    low = (text or "").lower()
    return any(w in low for w in _EMOTION_WORDS)


def classify_failure(trace: dict[str, Any]) -> str | None:
    """Classify a decision trace into one plan §31 failure class, or None."""
    if trace.get("outcome") in _GOOD_OUTCOMES:
        return None
    social = trace.get("social_context") or {}
    act = trace.get("dialogue_act", "")
    response = trace.get("response", "")
    correction = trace.get("correction", "")

    # MISREAD_EMOTION: the user corrected Novi's reading of their emotion.
    if correction and _mentions_emotion(correction):
        return "MISREAD_EMOTION"

    # IGNORED_BOUNDARY: pushed past an explicit boundary.
    if social.get("boundary_state", "NORMAL") != "NORMAL" and act in _PUSHY_ACTS:
        return "IGNORED_BOUNDARY"

    # INTERRUPTED: interrupted a busy person.
    if social.get("user_availability") == "busy" and act in _PROACTIVE_ACTS:
        return "INTERRUPTED"

    # REPEATED_ERROR: the same mistake repeated.
    if int(trace.get("repeat_count", 0)) >= 2:
        return "REPEATED_ERROR"

    # DEFENSIVE_RESPONSE: got defensive instead of owning the error.
    if trace.get("defensiveness") in ("moderate", "high"):
        return "DEFENSIVE_RESPONSE"

    # EXCESSIVE_APOLOGY: apologized when Novi was not at fault.
    if act == "APOLOGIZE" and not trace.get("novi_caused_problem"):
        return "EXCESSIVE_APOLOGY"

    # UNNATURAL_EMPATHY: canned, template empathy phrasing.
    if _CANNED_RE.search(response):
        return "UNNATURAL_EMPATHY"

    distress = _effective_signal(social, _DISTRESS_DIMS)

    # UNDERREACTED: strong distress met with a terse/weak response.
    if distress >= 0.6 and (trace.get("verbosity") == "terse" or act in _WEAK_ACTS):
        return "UNDERREACTED"

    # FAILED_TO_SUPPORT: distress present, no support offered.
    if distress >= 0.5 and act not in _SUPPORT_ACTS:
        return "FAILED_TO_SUPPORT"

    # OVER_SUPPORTED: support offered when none was needed.
    if distress < 0.2 and act in _SUPPORT_ACTS:
        return "OVER_SUPPORTED"

    # OVERREACTED: strong response to a weak signal.
    signal = _effective_signal(social, tuple(social.get("emotional_signal") or {}))
    if signal < 0.3 and (trace.get("verbosity") in ("medium", "long") or act in _STRONG_ACTS):
        return "OVERREACTED"

    return None
