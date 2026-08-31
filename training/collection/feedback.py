"""Explicit user feedback parsing (plan 24 §30, §51 item 19).

Direct feedback is the highest-quality evidence available. This module turns
a user utterance into a structured feedback record so the brain can persist
the appropriate preference or outcome (plan §30):

    "Stop asking me that."      -> boundary (stop_asking)
    "That's actually helpful."  -> positive_outcome
    "Don't explain it again."   -> verbosity (terse)
    "I need a minute."          -> give_space

Only information that is appropriate and useful is persisted; utterances that
match no known feedback pattern return None.
"""

from __future__ import annotations

import re
from typing import Any

_GIVE_SPACE_RE = re.compile(
    r"\b(need a minute|need space|give me space|give me a moment|leave me alone|not now)\b", re.IGNORECASE
)
_BOUNDARY_RE = re.compile(
    r"\b(stop|quit|don'?t|never)\b.*\b(ask|probe|bother|interrupt|push|nag)\w*\b", re.IGNORECASE
)
_VERBOSITY_RE = re.compile(
    r"\b(don'?t|stop)\b.*\b(explain|repeat|elaborate|long|detail)\w*\b", re.IGNORECASE
)
_CORRECTION_RE = re.compile(
    r"\b(no,? the|wrong|incorrect|not that|i meant|that'?s not)\b", re.IGNORECASE
)
_POSITIVE_RE = re.compile(
    r"\b(actually helpful|useful|great|thanks|appreciate|love that|good|nice)\b", re.IGNORECASE
)


def parse_feedback(text: str) -> dict[str, Any] | None:
    """Parse a user utterance into a structured feedback record, or None.

    Order matters: give-space and boundary take precedence over positive
    readings so "I need a minute" is never misread as approval.
    """
    text = (text or "").strip()
    if not text:
        return None
    if _GIVE_SPACE_RE.search(text):
        return {"kind": "give_space", "text": text, "preference": "space"}
    if _BOUNDARY_RE.search(text):
        return {"kind": "boundary", "text": text, "preference": "stop_asking"}
    if _VERBOSITY_RE.search(text):
        return {"kind": "verbosity", "text": text, "preference": "terse"}
    if _CORRECTION_RE.search(text):
        return {"kind": "correction", "text": text, "preference": ""}
    if _POSITIVE_RE.search(text):
        return {"kind": "positive_outcome", "text": text, "preference": ""}
    return None
