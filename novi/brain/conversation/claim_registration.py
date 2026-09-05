"""Plan 03 C-133 — claim registration (the "recent claim" seam).

A *recent claim* is a user statement that asserts a concrete time, value, or
measurement about a subject ("The standup is at 9am", "I heard it's at 10am",
"Actually it is 330 miles", "it's at 10am"). These are exactly the statements
that can *conflict* across turns, so they must register as ``recent_claim``
fact candidates independent of how a later recall question is worded.

``is_fact_assertion`` is the deterministic recognizer: it accepts
time-of-day / o'clock / "at <N>" expressions and numeric+unit measurements,
and rejects questions, bare possession ("I have two dogs"), and plain
relational statements ("my sister lives in Porto"). ``has_anaphoric_subject``
reports whether an assertion's subject is a pronoun ("it"/"that"/"he"/"she"),
which lets a pronominal assertion bind to the active subject.

Deterministic, socket-free, stdlib-only.
"""

from __future__ import annotations

import re

# Time-of-day / "at N" / "N o'clock" expressions.
_TIME_RE = re.compile(
    r"\b\d{1,2}(?::\d{2})?\s*(?:am|pm)\b"
    r"|\bat\s+\d{1,2}\b"
    r"|\b\d{1,2}\s*o['']?clock\b",
    re.IGNORECASE,
)

# Numeric + unit value/measurement expressions.
_MEASURE_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:miles?|km|kilometers?|meters?|metres?|feet|inches|"
    r"mph|km/h|range|capacity|price|cost|weight|pounds?|lbs?|kg|kilograms?|"
    r"hours?|hrs?|minutes?|mins?|seconds?|secs?|days?|weeks?|months?|years?|"
    r"percent|%)\b",
    re.IGNORECASE,
)

# Question openers — a fact-assertion never starts like a question.
_QUESTION_START = re.compile(
    r"^(who|what|when|where|which|how|is|are|was|were|do|does|did|can|could|"
    r"will|would|should|have|has|had)\b",
    re.IGNORECASE,
)

# Anaphoric subject lead-ins: "it's", "it is", "that's", "he's", ...
_ANAPHORIC_START = re.compile(
    r"^(?:actually|well|so|hmm|ah|oh|okay|ok|right|look|listen)?[,\s]*"
    r"(?:it['’]?s\b|it\s+is\b|its\b|that['’]?s\b|that\s+is\b|"
    r"he['’]?s\b|he\s+is\b|she['’]?s\b|she\s+is\b)",
    re.IGNORECASE,
)


def is_fact_assertion(text: str) -> bool:
    """True when ``text`` asserts a concrete time/value/measurement fact.

    >>> is_fact_assertion("The standup is at 9am.")
    True
    >>> is_fact_assertion("I heard the standup is at 10am.")
    True
    >>> is_fact_assertion("Actually it is 330 miles.")
    True
    >>> is_fact_assertion("I have two dogs, Rex and Max.")
    False
    """
    stripped = (text or "").strip()
    if len(stripped) < 6:
        return False
    lowered = stripped.lower()
    if lowered.endswith("?") or _QUESTION_START.match(stripped):
        return False
    return bool(_TIME_RE.search(lowered) or _MEASURE_RE.search(lowered))


def has_anaphoric_subject(text: str) -> bool:
    """True when the statement's subject is a pronoun (it/that/he/she)."""
    stripped = (text or "").strip()
    return bool(_ANAPHORIC_START.match(stripped))


__all__ = ["has_anaphoric_subject", "is_fact_assertion"]
