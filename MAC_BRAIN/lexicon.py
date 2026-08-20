"""Learned preferences and the living lexicon for the Mac Brain.

Implements the P0 Soul learning/development spec (docs/06-soul 06) and the
communication/living-lexicon spec (docs/06-soul 07): scoped, evidence-backed,
revisable communication preferences plus a lexicon whose entries move through a
candidate->adoption lifecycle with provenance, scope, decay and retirement.

P0 invariants honored:
  - A preference is distinct from personality, and never a permission.
  - A single unusual phrase is not enough for global adoption.
  - A relationship/context-scoped expression does not become global automatically.
  - Explicit corrections supersede older preferences (recency, not silent overwrite).
  - Learned vocabulary does not grant the right to disclose associated info
    (private/scoped language is gated by audience).
  - Current context can override stale learned assumptions.
  - Adaptive changes retain provenance and reversibility.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class LexiconStatus(str, Enum):
    OBSERVED = "observed"
    UNDERSTOOD = "understood"
    CANDIDATE = "candidate"
    VALIDATED = "validated"
    ADOPTED = "adopted"
    SCOPED = "scoped"
    DEPRECATED = "deprecated"
    REJECTED = "rejected"


class Scope(str, Enum):
    GLOBAL = "global"
    RELATIONSHIP = "relationship"
    CONTEXT = "context"
    EPHEMERAL = "ephemeral"


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


@dataclass
class LexiconEntry:
    expression: str
    source: str = ""
    category: str = "expression"
    meaning_hypothesis: str = ""
    scope: Scope = Scope.EPHEMERAL
    person: str = ""  # set when relationship-scoped
    context: str = ""
    status: LexiconStatus = LexiconStatus.OBSERVED
    first_seen: str = ""
    last_seen: str = ""
    frequency: int = 1
    confidence: float = 0.2
    appropriateness: float = 0.5
    provenance: list[str] = field(default_factory=list)

    def snapshot(self) -> dict[str, Any]:
        return {
            "expression": self.expression,
            "category": self.category,
            "meaning_hypothesis": self.meaning_hypothesis,
            "source": self.source,
            "scope": self.scope.value,
            "person": self.person,
            "context": self.context,
            "status": self.status.value,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "frequency": self.frequency,
            "confidence": self.confidence,
            "appropriateness": self.appropriateness,
            "provenance": list(self.provenance),
        }

    @classmethod
    def from_snapshot(cls, data: dict[str, Any]) -> "LexiconEntry":
        allowed = {f for f in cls.__dataclass_fields__}
        fields = {k: v for k, v in data.items() if k in allowed}
        for key, enum_type in (("scope", Scope), ("status", LexiconStatus)):
            if key in fields and not isinstance(fields[key], enum_type):
                try:
                    fields[key] = enum_type(fields[key])
                except ValueError:
                    fields[key] = enum_type.GLOBAL if key == "scope" else LexiconStatus.OBSERVED
        return cls(**fields)


@dataclass
class CommunicationPreference:
    kind: str
    person: str
    value: Any
    confidence: float = 0.3
    evidence_count: int = 1
    source: str = "interaction"
    first_seen: str = ""
    last_seen: str = ""
    active: bool = True
    superseded_by: str = ""
    provenance: list[str] = field(default_factory=list)

    def snapshot(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "person": self.person,
            "value": self.value,
            "confidence": self.confidence,
            "evidence_count": self.evidence_count,
            "source": self.source,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "active": self.active,
            "superseded_by": self.superseded_by,
            "provenance": list(self.provenance),
        }

    @classmethod
    def from_snapshot(cls, data: dict[str, Any]) -> "CommunicationPreference":
        allowed = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in allowed})


class Lexicon:
    """Living lexicon: seed vocabulary that grows through observed, validated expression."""

    GLOBAL_ADOPTION_FREQ = 3
    SCOPED_ADOPTION_FREQ = 2
    VALIDATION_FREQ = 2

    def __init__(self, seed: dict[str, str] | None = None) -> None:
        self._entries: dict[str, LexiconEntry] = {}
        for word, meaning in (seed or {}).items():
            entry = LexiconEntry(word, category="core", meaning_hypothesis=meaning, scope=Scope.GLOBAL, status=LexiconStatus.ADOPTED, confidence=1.0, appropriateness=1.0)
            self._entries[self._key(word)] = entry

    @staticmethod
    def _key(expression: str) -> str:
        return expression.strip().lower()

    @staticmethod
    def _key_scoped(expression: str, person: str) -> str:
        return f"{Lexicon._key(expression)}::{person}".strip(":")

    def observe(self, expression: str, *, source: str, category: str = "expression", meaning: str = "", person: str = "", scope: Scope = Scope.EPHEMERAL, appropriateness: float = 0.6, now: str = "") -> LexiconEntry:
        key = self._key_scoped(expression, person) if person else self._key(expression)
        if key in self._entries:
            entry = self._entries[key]
            entry.frequency += 1
            entry.last_seen = now or entry.last_seen
            entry.confidence = _clamp01(entry.confidence + 0.1)
            if entry.status is LexiconStatus.OBSERVED:
                entry.status = LexiconStatus.UNDERSTOOD if meaning else LexiconStatus.CANDIDATE
        else:
            entry = LexiconEntry(
                expression,
                category=category,
                meaning_hypothesis=meaning,
                source=source,
                scope=scope,
                person=person,
                first_seen=now,
                last_seen=now,
                frequency=1,
                appropriateness=appropriateness,
            )
            self._entries[key] = entry
        self._advance(entry)
        return entry

    def _advance(self, entry: LexiconEntry) -> None:
        if entry.status in (LexiconStatus.DEPRECATED, LexiconStatus.REJECTED):
            return
        scoped = entry.person != "" or entry.scope in (Scope.RELATIONSHIP, Scope.CONTEXT)
        threshold = self.SCOPED_ADOPTION_FREQ if scoped else self.GLOBAL_ADOPTION_FREQ
        if entry.frequency >= self.VALIDATION_FREQ and entry.status not in (LexiconStatus.ADOPTED, LexiconStatus.SCOPED, LexiconStatus.VALIDATED):
            entry.status = LexiconStatus.VALIDATED
            entry.confidence = _clamp01(entry.confidence + 0.1)
        if entry.frequency >= threshold and entry.appropriateness >= 0.5:
            entry.status = LexiconStatus.SCOPED if scoped else LexiconStatus.ADOPTED
            entry.confidence = max(entry.confidence, 0.6)

    def status_of(self, expression: str, person: str = "") -> LexiconStatus:
        key = self._key_scoped(expression, person) if person else self._key(expression)
        entry = self._entries.get(key)
        return entry.status if entry else LexiconStatus.OBSERVED

    def is_usable(self, expression: str, *, person: str = "", stranger_present: bool = False, in_context: str = "") -> bool:
        key = self._key_scoped(expression, person) if person else self._key(expression)
        entry = self._entries.get(key)
        if entry is None:
            return False
        if entry.status not in (LexiconStatus.ADOPTED, LexiconStatus.SCOPED, LexiconStatus.VALIDATED):
            return False
        # privacy: relationship-scoped/person-scoped expression is not spoken to a stranger audience
        if entry.scope in (Scope.RELATIONSHIP,) or entry.person:
            if stranger_present:
                return False
        if entry.scope == Scope.CONTEXT and entry.context and entry.context != in_context:
            return False
        return True

    def vocabulary_for(self, person: str) -> list[str]:
        """Adopted global + relationship-scoped vocabulary available to a person."""
        out = []
        for entry in self._entries.values():
            if entry.status not in (LexiconStatus.ADOPTED, LexiconStatus.SCOPED, LexiconStatus.VALIDATED):
                continue
            if not entry.person or entry.person == person:
                out.append(entry.expression)
        return out

    def deprecate(self, expression: str, person: str = "") -> None:
        key = self._key_scoped(expression, person) if person else self._key(expression)
        if key in self._entries:
            self._entries[key].status = LexiconStatus.DEPRECATED

    def reject(self, expression: str, person: str = "") -> None:
        key = self._key_scoped(expression, person) if person else self._key(expression)
        if key in self._entries:
            self._entries[key].status = LexiconStatus.REJECTED

    def snapshot(self) -> list[dict[str, Any]]:
        return [e.snapshot() for e in self._entries.values()]

    @classmethod
    def from_snapshot(cls, rows: list[dict[str, Any]]) -> "Lexicon":
        lex = cls()
        lex._entries = {}
        for row in rows:
            entry = LexiconEntry.from_snapshot(row)
            key = cls._key_scoped(entry.expression, entry.person) if entry.person else cls._key(entry.expression)
            lex._entries[key] = entry
        return lex


class LearnedPreferences:
    """Scoped, evidence-backed, revisable communication preferences."""

    def __init__(self) -> None:
        self._prefs: dict[tuple[str, str], CommunicationPreference] = {}

    @staticmethod
    def _person_key(person: str, kind: str) -> tuple[str, str]:
        return (person or "", kind)

    def learn(self, person: str, kind: str, value: Any, *, explicit: bool = False, now: str = "") -> CommunicationPreference:
        key = self._person_key(person, kind)
        pref = self._prefs.get(key)
        if pref is None:
            pref = CommunicationPreference(kind=kind, person=person, value=value, first_seen=now, last_seen=now)
            self._prefs[key] = pref
        else:
            pref.evidence_count += 1
            pref.confidence = _clamp01(pref.confidence + (0.25 if explicit else 0.1))
            if explicit:
                # explicit preference updates the value and marks older evidence superseded
                pref.value = value
                pref.superseded_by = f"{person}:{kind}@{now}"
            pref.last_seen = now or pref.last_seen
        return pref

    def record_correction(self, person: str, kind: str, value: Any, *, now: str = "") -> CommunicationPreference:
        key = self._person_key(person, kind)
        old = self._prefs.get(key)
        if old is not None:
            old.active = False
        pref = CommunicationPreference(kind=kind, person=person, value=value, confidence=0.9, evidence_count=1, source="explicit_correction", first_seen=now, last_seen=now, active=True, superseded_by="")
        self._prefs[key] = pref
        return pref

    def preference_for(self, person: str, kind: str, *, default: Any = None, context_override: Any | None = None) -> Any:
        if context_override is not None:
            return context_override
        pref = self._prefs.get(self._person_key(person, kind))
        if pref is not None and pref.active:
            return pref.value
        return default

    def has_for(self, person: str, kind: str) -> bool:
        pref = self._prefs.get(self._person_key(person, kind))
        return pref is not None and pref.active

    def snapshot(self) -> list[dict[str, Any]]:
        return [p.snapshot() for p in self._prefs.values()]

    @classmethod
    def from_snapshot(cls, rows: list[dict[str, Any]]) -> "LearnedPreferences":
        prefs = cls()
        for row in rows:
            pref = CommunicationPreference.from_snapshot(row)
            prefs._prefs[(pref.person or "", pref.kind)] = pref
        return prefs
