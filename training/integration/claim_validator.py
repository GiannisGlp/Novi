"""Automatic anti-hallucination checks (plan 23 §38, step 38).

Before a response is spoken, validate its claims against the context packet:

- unknown person claimed as known            (person_claim)
- unknown object claimed as known            (object_claim)
- memory not retrieved but referenced        (memory_claim)
- location not present in world state        (location_claim)
- unsupported action completion              (action_completion)
- unsupported certainty                      (certainty_claim)

A flagged response should be regenerated, simplified or converted to an
uncertainty/clarification response (plan §38) — `ClaimValidator.is_safe` is
the deterministic gate the brain consults before verbalization.
"""

from __future__ import annotations

import re
from typing import Any

from training.collection.deduplicator import extract_claims

_PERSON_LEXICON = frozenset({
    "alice", "bob", "charlie", "dana", "eve", "vano", "guest", "owner", "user",
})
_MEMORY_PHRASES = re.compile(
    r"\b(we decided|we agreed|you said|you told me|you mentioned|remember|"
    r"as we discussed|we talked about|you asked me to)\b", re.IGNORECASE)
_COMPLETION_PHRASES = re.compile(
    r"\b(done|completed|finished|accomplished|i moved it|i've done|i did it|it's done)\b",
    re.IGNORECASE)
_CERTAINTY_WORDS = re.compile(r"\b(definitely|certainly|absolutely|i'm sure|no doubt)\b", re.IGNORECASE)


def _mentioned_persons(response: str) -> list[str]:
    tokens = re.findall(r"[a-z]+", response.lower())
    return [t for t in tokens if t in _PERSON_LEXICON]


def validate_response(response: str, packet: dict[str, Any]) -> list[dict[str, Any]]:
    """Deterministic claim flags for one response against one context packet."""
    flags: list[dict[str, Any]] = []
    known_persons = {str(p).lower() for p in packet.get("known_persons", [])}
    world_entities = {str(e).lower() for e in packet.get("world_entities", [])}
    known_locations = {str(loc).lower() for loc in packet.get("known_locations", [])}
    summaries = [str(s).lower() for s in packet.get("retrieved_memory_summaries", [])]

    for _person in _mentioned_persons(response):
        if _person not in known_persons:
            flags.append({"field": "person_claim", "severity": "high",
                          "reason": f"claims familiarity with unknown person {_person!r}"})

    for subject, _rel, obj in extract_claims(response):
        if subject != "it" and subject not in world_entities and subject not in known_locations:
            flags.append({"field": "object_claim", "severity": "high",
                          "reason": f"claims knowledge of unknown object {subject!r}"})
        if obj not in known_locations and obj not in world_entities:
            flags.append({"field": "location_claim", "severity": "medium",
                          "reason": f"location {obj!r} not present in world state"})

    if _MEMORY_PHRASES.search(response):
        supported = any(
            bool(set(_norm(summary)) & set(_norm(response)))
            for summary in summaries
        )
        if not supported:
            flags.append({"field": "memory_claim", "severity": "high",
                          "reason": "references memory that was not retrieved (unsupported recall)"})

    if _COMPLETION_PHRASES.search(response) and not packet.get("active_tasks"):
        flags.append({"field": "action_completion", "severity": "medium",
                      "reason": "claims action completion with no active task"})

    if _CERTAINTY_WORDS.search(response) and float(packet.get("evidence_confidence", 1.0)) < 0.7:
        flags.append({"field": "certainty_claim", "severity": "medium",
                      "reason": "unsupported certainty given low evidence confidence"})
    return flags


def _norm(text: str) -> set[str]:
    return set("".join(ch for ch in text.lower() if ch.isalnum() or ch == " ").split())


class ClaimValidator:
    """Aggregate gate: safe = zero flags (plan §38: flagged -> regenerate/clarify)."""

    def validate(self, response: str, packet: dict[str, Any]) -> list[dict[str, Any]]:
        return validate_response(response, packet)

    def is_safe(self, response: str, packet: dict[str, Any]) -> bool:
        return not self.validate(response, packet)
