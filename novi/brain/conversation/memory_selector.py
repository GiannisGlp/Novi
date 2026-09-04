"""Plan 03 Phase 5 — memory selection and retrieval quality.

Selects the *right* memories on top of the existing
``DurableMemoryStore.retrieve_ranked`` (never raw SQL duplication):

- Step 5.2 — query memory from conversation state (intent + topic +
  entities + identity + open question), never the raw sentence alone;
- Step 5.3 — negative relevance checks (wrong-entity / stale-superseded /
  low-confidence / contradicted / private / irrelevant rejection);
- Step 5.4 — internal citation records
  (memory_id / memory_type / source / confidence / why_selected);
- Step 5.5 — no-fabrication verdicts: missing memory is reported honestly.

Deterministic, socket-free, stdlib-only. Records are handled generically
(``MemoryRecord`` dataclass or plain dict snapshot) so the checks stay usable
for both durable-store rows and in-memory candidates.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Any

# Step 5.3 thresholds (documented constants; calibrate from eval data).
MIN_MEMORY_CONFIDENCE = 0.35
MAX_SELECTION = 4

# Privacy classes withheld from the default (conversational) scope. Mirrors
# the ContextAssembler's default-scope filter plus the governance "protected"
# class: private memories must never leak into a packet.
PRIVATE_CLASSES = frozenset({"private", "restricted", "protected"})

# Verification markers that disqualify a memory from selection.
CONTRADICTED_MARKERS = frozenset({"contradicted", "refuted", "retracted"})
STALE_MARKERS = frozenset({"superseded", "expired", "deleted", "archived", "tombstoned"})

_STOPWORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "of", "at", "by", "for", "with",
    "about", "into", "through", "during", "before", "after", "to", "from",
    "in", "on", "is", "are", "was", "were", "be", "been", "being", "it",
    "its", "this", "that", "these", "those", "i", "you", "he", "she", "we",
    "they", "me", "him", "her", "us", "them", "my", "your", "his", "our",
    "their", "what", "which", "who", "whom", "how", "when", "where", "why",
    "do", "does", "did", "can", "could", "should", "would", "there", "here",
    "so", "as", "no", "yes", "not", "just", "very", "really",
})


def _tokens(text: str) -> set[str]:
    return {t for t in "".join(c.lower() if c.isalnum() else " " for c in text).split()
            if t and t not in _STOPWORDS}


def _field(record: Any, name: str, default: Any = None) -> Any:
    if isinstance(record, dict):
        return record.get(name, default)
    return getattr(record, name, default)


def _record_text(record: Any) -> str:
    content = _field(record, "content", "")
    if isinstance(content, dict):
        parts = [str(v) for v in content.values() if isinstance(v, (str, int, float))]
        return " ".join(parts)
    return str(content or "")


def _record_entities(record: Any) -> tuple[str, ...]:
    refs = _field(record, "entity_refs", ()) or ()
    extra: list[str] = []
    provenance = _field(record, "provenance", {}) or {}
    if isinstance(provenance, dict):
        for key in ("person", "entity", "speaker"):
            value = provenance.get(key)
            if value:
                extra.append(str(value))
    return tuple(str(e) for e in list(refs) + extra)


def _record_state(record: Any) -> str:
    for name in ("state", "lifecycle_state", "status"):
        value = _field(record, name, "")
        if value:
            return str(value).lower()
    return "active"


@dataclass
class MemoryQuery:
    """Step 5.2: a memory query composed from conversation state."""

    text: str = ""
    intent: str = ""
    topic: str = ""
    entities: tuple[str, ...] = ()
    person: str = ""
    open_question: str = ""

    def __str__(self) -> str:
        return self.text


@dataclass
class MissingMemoryVerdict:
    """Step 5.5: honest verdict when no reliable memory exists."""

    found: bool = False
    statement: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"found": self.found, "statement": self.statement}


def build_memory_query(text: str, state: Any, intent: Any,
                       referents: Any | None = None,
                       brain: Any | None = None) -> MemoryQuery:
    """Compose a memory query from state, never the raw sentence alone.

    The query joins the intent label, active topic, active entities (plus any
    referent resolutions), the identified person, and the open question, with
    salient keywords from the current turn as grounding. Even with an empty
    state the intent label is always present, so the store never sees the bare
    user sentence as the whole query.
    """
    topic = (getattr(state, "topic", "") or "").strip()
    entities = [e for e in (getattr(state, "active_entities", []) or []) if e]
    if referents is not None:
        for resolved in (getattr(referents, "resolutions", {}) or {}).values():
            if resolved and resolved not in entities:
                entities.append(resolved)
    intent_label = (getattr(intent, "intent", "") or "INFORMATION_REQUEST").strip()
    open_questions = getattr(state, "open_questions", []) or []
    open_question = open_questions[-1] if open_questions else ""
    person = ""
    if brain is not None:
        with contextlib.suppress(Exception):
            belief = brain.identity.identity_for("person")
            if belief is not None and getattr(belief, "name", ""):
                person = belief.name
    keywords = sorted(_tokens(text or ""))[:8]
    parts = [intent_label]
    if topic:
        parts.append(topic)
    parts.extend(entities[:4])
    if person:
        parts.append(person)
    if open_question:
        parts.append(open_question)
    if keywords:
        parts.append(" ".join(keywords))
    return MemoryQuery(text=" ".join(p for p in parts if p).strip(),
                       intent=intent_label, topic=topic,
                       entities=tuple(entities[:4]), person=person,
                       open_question=open_question)


def reject_memory(record: Any, *, query_entities: tuple[str, ...] = (),
                  query_topic: str = "", query_text: str = "",
                  query_person: str = "") -> str | None:
    """Step 5.3 negative relevance checks. Returns a reason or None (keep)."""
    confidence = float(_field(record, "confidence", 0.0) or 0.0)
    if confidence < MIN_MEMORY_CONFIDENCE:
        return "low_confidence"
    verification = str(_field(record, "verification_status", "") or "").lower()
    if verification in CONTRADICTED_MARKERS:
        return "contradicted"
    if verification in STALE_MARKERS or _record_state(record) in STALE_MARKERS:
        return "superseded"
    privacy = str(_field(record, "privacy_class", "unclassified") or "").lower()
    if privacy in PRIVATE_CLASSES:
        return "private"
    record_entities = {e.lower() for e in _record_entities(record)}
    wanted = {e.lower() for e in query_entities}
    if query_person:
        wanted.add(query_person.lower())
    if record_entities and wanted and record_entities.isdisjoint(wanted):
        return "wrong_entity"
    haystack = f"{_record_text(record)} {' '.join(record_entities)} {query_topic}".lower()
    query_tokens = _tokens(query_text or "")
    entity_match = bool(record_entities and wanted and not record_entities.isdisjoint(wanted))
    if query_tokens and not (_tokens(haystack) & query_tokens) and not entity_match:
        return "irrelevant"
    return None


def cite_memory(record: Any, why_selected: str) -> dict[str, Any]:
    """Step 5.4: internal citation for a selected memory."""
    provenance = _field(record, "provenance", {}) or {}
    source = _field(record, "source", "")
    if not source and isinstance(provenance, dict):
        source = provenance.get("source", "")
    return {
        "memory_id": _field(record, "memory_id", ""),
        "memory_type": _field(record, "memory_type", ""),
        "source": source or "memory",
        "confidence": round(float(_field(record, "confidence", 0.0) or 0.0), 4),
        "why_selected": why_selected,
        "text": _record_text(record)[:500],
        "entity_refs": list(_record_entities(record)),
    }


def _why_selected(record: Any, query: MemoryQuery) -> str:
    signals: list[str] = []
    record_entities = {e.lower() for e in _record_entities(record)}
    wanted = {e.lower() for e in query.entities}
    if query.person:
        wanted.add(query.person.lower())
    if record_entities and wanted and not record_entities.isdisjoint(wanted):
        signals.append("entity_match")
    if query.topic and query.topic.lower() in _record_text(record).lower():
        signals.append("topic_match")
    if str(_field(record, "memory_type", "")).lower() in query.intent.lower():
        signals.append("intent_match")
    if float(_field(record, "confidence", 0.0) or 0.0) >= 0.8:
        signals.append("high_confidence")
    return "+".join(signals) or "ranked_relevant"


def select_memories(store: Any, query: MemoryQuery | str, *,
                    limit: int = MAX_SELECTION,
                    query_person: str = "") -> list[dict[str, Any]]:
    """Retrieve via ``store.retrieve_ranked`` then apply negative checks.

    Never issues raw SQL: all candidates come from the store's own ranked
    retrieval. Returns citation dicts (Step 5.4 shape) for survivors only.
    """
    if isinstance(query, str):
        query = MemoryQuery(text=query)
    candidates: tuple[Any, ...] = ()
    with contextlib.suppress(Exception):
        candidates = tuple(store.retrieve_ranked(query.text, limit=max(limit * 3, limit)) or ())
    selected: list[dict[str, Any]] = []
    person = query_person or query.person
    for record in candidates:
        reason = reject_memory(record, query_entities=query.entities,
                               query_topic=query.topic, query_text=query.text,
                               query_person=person)
        if reason is not None:
            continue
        selected.append(cite_memory(record, _why_selected(record, query)))
        if len(selected) >= max(1, limit):
            break
    return selected


def missing_memory_verdict(query_text: str, selected: list[dict[str, Any]]) -> MissingMemoryVerdict:
    """Step 5.5: admit honestly when no reliable memory exists."""
    if selected:
        return MissingMemoryVerdict(found=True, statement="")
    short = (query_text or "").strip()[:120] or "that detail"
    return MissingMemoryVerdict(
        found=False,
        statement=f"I don't have a reliable memory of {short}.",
    )


__all__ = [
    "MAX_SELECTION",
    "MIN_MEMORY_CONFIDENCE",
    "PRIVATE_CLASSES",
    "MemoryQuery",
    "MissingMemoryVerdict",
    "build_memory_query",
    "cite_memory",
    "missing_memory_verdict",
    "reject_memory",
    "select_memories",
]
