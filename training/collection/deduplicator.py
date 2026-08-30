"""Dataset deduplication + contradiction detection (plan 23 §8, step 06).

- Exact duplication: normalized fingerprint (whitespace/case-insensitive).
- Near duplication: overlap coefficient on response tokens, same topic.
- Contradiction: two examples asserting the same subject+relation with
  different objects (e.g. "the mug is on the desk" vs "… on the shelf").

Contradictions are surfaced to human review — never auto-deleted.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

_WS = re.compile(r"\s+")
_POSITION_CLAIM = re.compile(
    r"\bthe\s+([a-z][a-z0-9' -]{1,24}?)\s+(?:is|are)\s+"
    r"(on|in|at|by|next to|under|behind|near)\s+(?:the\s+)?([a-z][a-z0-9' -]{1,24})"
)


def _normalize(text: str) -> str:
    return _WS.sub(" ", (text or "").lower()).strip()


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9']+", _normalize(text)))


def _topic(example: dict[str, Any]) -> str:
    return _normalize((((example.get("situation") or {}).get("conversation") or {}).get("topic") or ""))


def exact_fingerprint(example: dict[str, Any]) -> str:
    """Deterministic fingerprint: response + act + topic, whitespace-normalized."""
    decision = example.get("decision") or {}
    payload = "|".join([
        _normalize(example.get("response", "")),
        str(decision.get("dialogue_act", "")),
        _topic(example),
    ])
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def find_near_duplicates(
    examples: list[dict[str, Any]],
    threshold: float = 0.8,
) -> list[list[tuple[str, str, float]]]:
    """Groups of near-duplicate example ids, each pair as (keep, drop, score).

    Uses the overlap coefficient on response tokens (Jaccard-like but
    sensitive when one response is a strict prefix/subset of the other).
    """
    groups: list[list[tuple[str, str, float]]] = []
    seen_ids: set[str] = set()
    for i, a in enumerate(examples):
        if a["example_id"] in seen_ids:
            continue
        ta = _tokens(a.get("response", ""))
        if not ta:
            continue
        group: list[tuple[str, str, float]] = []
        for b in examples[i + 1:]:
            tb = _tokens(b.get("response", ""))
            if not tb:
                continue
            overlap = len(ta & tb) / min(len(ta), len(tb))
            if overlap >= threshold:
                group.append((a["example_id"], b["example_id"], round(overlap, 3)))
                seen_ids.add(b["example_id"])
        if group:
            groups.append(group)
            seen_ids.add(a["example_id"])
    return groups


def extract_claims(response: str) -> list[tuple[str, str, str]]:
    """Extract (subject, relation, object) position claims from a response."""
    out: list[tuple[str, str, str]] = []
    for m in _POSITION_CLAIM.finditer(_normalize(response)):
        out.append((m.group(1).strip(), m.group(2), m.group(3).strip()))
    return out


def find_contradictions(examples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pairs of examples asserting contradictory facts about the same subject.

    Deterministic: same subject + same relation, different object.
    """
    by_subject: dict[tuple[str, str], list[tuple[str, str, str]]] = {}
    for ex in examples:
        for subject, relation, obj in extract_claims(ex.get("response", "")):
            key = (subject, relation)
            by_subject.setdefault(key, []).append((ex["example_id"], obj, ex.get("response", "")))
    out: list[dict[str, Any]] = []
    for (subject, relation), claims in by_subject.items():
        objects: dict[str, list[tuple[str, str]]] = {}
        for example_id, obj, _resp in claims:
            objects.setdefault(obj, []).append((example_id, _resp))
        if len(objects) < 2:
            continue
        pairs = list(objects.items())
        for i in range(len(pairs)):
            for j in range(i + 1, len(pairs)):
                obj_a, a_refs = pairs[i]
                obj_b, b_refs = pairs[j]
                out.append({
                    "subject": subject,
                    "relation": relation,
                    "object_a": obj_a,
                    "object_b": obj_b,
                    "example_a": a_refs[0][0],
                    "example_b": b_refs[0][0],
                })
    return out
