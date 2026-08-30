"""Persistent person identity registry (plan 22, Phase 2).

Tasks:
- 2.1 PersonModel — canonical per-person fields; biometric *references* only,
  never raw biometric data in ordinary memory;
- 2.2 identity lifecycle — UNKNOWN → CANDIDATE → RECOGNIZED → CONFIRMED, with
  AMBIGUOUS / REJECTED. Recognition never automatically means confirmation;
- 2.3 cross-modal identity — face / voice / speech self-identification /
  context fuse into one belief; modality disagreement is *retained* (the
  person becomes AMBIGUOUS and confidence is lowered) rather than forcing a
  match;
- 2.4 recognition events — identity.recognized / lost / ambiguous /
  reidentified, drained for the brain's event bus.

Deterministic and hardware-free: providers are injected; this module only
accumulates and reasons about evidence.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

# Identity never reaches certainty without overwhelming evidence; noisy-or
# fusion is capped here so "never manufacture certainty" is enforced.
_CONFIDENCE_CEILING = 0.99
_CANDIDATE_FLOOR = 0.5
_RECOGNIZED_FLOOR = 0.8
_CONFIRMED_FLOOR = 0.9
_AMBIGUITY_DELTA = 0.15
_AMBIGUITY_FLOOR = 0.6
_MAX_RECENT_INTERACTIONS = 12

# A modality reporting one of these names means "no match", not a competing
# identity (plan Task 2.3 contradiction handling).
_NO_MATCH_NAMES = frozenset({"unknown", "stranger", "unidentified", "none", "no_match"})

# The only event types the brain's event bus should ever see (Task 2.4).
_CANONICAL_EVENTS = frozenset(
    {"identity.recognized", "identity.lost", "identity.ambiguous", "identity.reidentified"}
)


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class IdentityStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    CANDIDATE = "CANDIDATE"
    RECOGNIZED = "RECOGNIZED"
    CONFIRMED = "CONFIRMED"
    AMBIGUOUS = "AMBIGUOUS"
    REJECTED = "REJECTED"


def _status_rank(status: IdentityStatus) -> int:
    return {
        IdentityStatus.UNKNOWN: 0,
        IdentityStatus.CANDIDATE: 1,
        IdentityStatus.RECOGNIZED: 2,
        IdentityStatus.CONFIRMED: 3,
        IdentityStatus.AMBIGUOUS: 2,
        IdentityStatus.REJECTED: -1,
    }[status]


@dataclass
class PersonModel:
    """Canonical person entity (Task 2.1).

    ``face_identity_refs`` / ``voice_identity_refs`` are opaque, access-
    controlled references into biometric stores — never embeddings or raw
    biometric data in ordinary conversation memory (plan §2 Task 2.1).
    """

    person_id: str
    identity_status: IdentityStatus = IdentityStatus.UNKNOWN
    canonical_name: str | None = None
    aliases: list[str] = field(default_factory=list)
    face_identity_refs: list[str] = field(default_factory=list)
    voice_identity_refs: list[str] = field(default_factory=list)
    confidence: float = 0.0
    first_seen: str = ""
    last_seen: str = ""
    usual_locations: list[str] = field(default_factory=list)
    known_relationships: dict[str, str] = field(default_factory=dict)  # other person_id -> category
    interaction_count: int = 0
    recent_interactions: list[dict[str, Any]] = field(default_factory=list)
    preferences: dict[str, Any] = field(default_factory=dict)
    communication_patterns: dict[str, Any] = field(default_factory=dict)
    consent: dict[str, Any] = field(default_factory=dict)  # privacy/consent metadata
    modalities_seen: set[str] = field(default_factory=set)
    evidence_count: int = 0
    last_seen_cycle: int = 0
    # per-name combined confidences (contradiction retention, Task 2.3)
    _name_confidences: dict[str, float] = field(default_factory=dict, repr=False)

    @property
    def known(self) -> bool:
        return self.identity_status in (
            IdentityStatus.RECOGNIZED,
            IdentityStatus.CONFIRMED,
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "person_id": self.person_id,
            "identity_status": self.identity_status.value,
            "canonical_name": self.canonical_name,
            "aliases": list(self.aliases),
            "face_identity_refs": list(self.face_identity_refs),
            "voice_identity_refs": list(self.voice_identity_refs),
            "confidence": round(self.confidence, 4),
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "usual_locations": list(self.usual_locations),
            "known_relationships": dict(self.known_relationships),
            "interaction_count": self.interaction_count,
            "recent_interactions": list(self.recent_interactions),
            "preferences": dict(self.preferences),
            "communication_patterns": dict(self.communication_patterns),
            "consent": dict(self.consent),
            "modalities_seen": sorted(self.modalities_seen),
            "evidence_count": self.evidence_count,
            "last_seen_cycle": self.last_seen_cycle,
            "name_confidences": dict(self._name_confidences),
        }

    @classmethod
    def from_snapshot(cls, data: dict[str, Any]) -> "PersonModel":
        model = cls(person_id=str(data.get("person_id", "") or uuid.uuid4().hex[:12]))
        model.identity_status = IdentityStatus(data.get("identity_status", IdentityStatus.UNKNOWN.value))
        model.canonical_name = data.get("canonical_name")
        model.aliases = list(data.get("aliases", []))
        model.face_identity_refs = list(data.get("face_identity_refs", []))
        model.voice_identity_refs = list(data.get("voice_identity_refs", []))
        model.confidence = _clamp01(float(data.get("confidence", 0.0)))
        model.first_seen = str(data.get("first_seen", ""))
        model.last_seen = str(data.get("last_seen", ""))
        model.usual_locations = list(data.get("usual_locations", []))
        model.known_relationships = dict(data.get("known_relationships", {}))
        model.interaction_count = int(data.get("interaction_count", 0))
        model.recent_interactions = list(data.get("recent_interactions", []))
        model.preferences = dict(data.get("preferences", {}))
        model.communication_patterns = dict(data.get("communication_patterns", {}))
        model.consent = dict(data.get("consent", {}))
        model.modalities_seen = set(data.get("modalities_seen", []))
        model.evidence_count = int(data.get("evidence_count", 0))
        model.last_seen_cycle = int(data.get("last_seen_cycle", 0))
        model._name_confidences = {
            str(k): _clamp01(float(v)) for k, v in data.get("name_confidences", {}).items()
        }
        return model


class PersonRegistry:
    """Single canonical registry of persistent person identities (plan §2.3)."""

    def __init__(self) -> None:
        self._persons: dict[str, PersonModel] = {}
        self._pending_events: list[dict[str, Any]] = []

    # ---- evidence ---------------------------------------------------------

    def observe(
        self,
        *,
        person_id: str,
        name: str | None = None,
        confidence: float,
        modality: str,
        cycle: int,
        provenance: str = "",
        face_ref: str | None = None,
        voice_ref: str | None = None,
        location: str | None = None,
        now: str | None = None,
    ) -> PersonModel:
        """Accumulate one identity observation.

        Cross-modal fusion (Task 2.3): per-name combined confidence uses
        noisy-or over independent observations; contradicting candidates
        (both strong, close in score) make the person AMBIGUOUS and *lower*
        identity confidence instead of forcing a match.
        """
        person_id = person_id or "unknown"
        now = now or utc_now_iso()
        conf = _clamp01(confidence)
        model = self._persons.setdefault(
            person_id,
            PersonModel(person_id=person_id, first_seen=now, last_seen=now),
        )
        was_status = model.identity_status
        was_name = model.canonical_name

        model.last_seen = now
        model.last_seen_cycle = max(model.last_seen_cycle, int(cycle))
        model.modalities_seen.add(modality)
        model.evidence_count += 1
        if face_ref and face_ref not in model.face_identity_refs:
            model.face_identity_refs.append(face_ref)
        if voice_ref and voice_ref not in model.voice_identity_refs:
            model.voice_identity_refs.append(voice_ref)
        if location and (not model.usual_locations or model.usual_locations[-1] != location):
            model.usual_locations.append(location)
            model.usual_locations = model.usual_locations[-8:]

        if name and name.strip():
            key = name.strip().lower()
            if key in _NO_MATCH_NAMES:
                # A modality explicitly failed to match: this is a penalty on
                # the existing belief (Task 2.3 — contradiction retained,
                # confidence lowered), never a competing identity.
                self._apply_no_match_penalty(model, confidence=conf)
            else:
                combined = self._combine(model._name_confidences.get(key, 0.0), conf)
                model._name_confidences[key] = combined
                if combined >= _CANDIDATE_FLOOR and key not in model.aliases:
                    model.aliases.append(key)
        # presence-only observations still update confidence floor.
        if name is None:
            model.confidence = max(model.confidence, conf)

        self._recompute(model, was_status=was_status, was_name=was_name, now=now)
        return model

    @staticmethod
    def _combine(a: float, b: float) -> float:
        """Noisy-or fusion capped below certainty (Task 1.3 discipline)."""
        return min(_CONFIDENCE_CEILING, 1.0 - (1.0 - a) * (1.0 - b))

    @staticmethod
    def _apply_no_match_penalty(model: PersonModel, *, confidence: float) -> None:
        """Scale down all name confidences when a modality reports no match.

        The discount grows with the no-match confidence: a loud \"I don't know
        who this is\" carries more weight than a quiet one.
        """
        factor = 1.0 - 0.15 * _clamp01(confidence)
        for key in list(model._name_confidences):
            model._name_confidences[key] = _clamp01(model._name_confidences[key] * factor)

    def _recompute(
        self,
        model: PersonModel,
        *,
        was_status: IdentityStatus,
        was_name: str | None,
        now: str,
    ) -> None:
        """Re-derive lifecycle status from name confidences (Task 2.2)."""
        # An explicit rejection sticks against weak evidence; only strong
        # re-observation (>= RECOGNIZED) may override it.
        ranked = sorted(model._name_confidences.items(), key=lambda kv: kv[1], reverse=True)
        best_conf = ranked[0][1] if ranked else 0.0
        if model.identity_status == IdentityStatus.REJECTED and best_conf < _RECOGNIZED_FLOOR:
            return

        if not ranked:
            status = IdentityStatus.UNKNOWN
            confidence = model.confidence if model.canonical_name is None else 0.0
        else:
            best_name, best_conf = ranked[0]
            confidence = best_conf
            second = ranked[1][1] if len(ranked) > 1 else 0.0
            # Contradiction retention: two strong, close candidates → AMBIGUOUS.
            if (
                second >= _AMBIGUITY_FLOOR
                and best_conf - second <= _AMBIGUITY_DELTA
            ):
                status = IdentityStatus.AMBIGUOUS
                confidence = _clamp01(confidence * 0.8)  # lower, never force
            elif best_conf >= _CONFIRMED_FLOOR and len(model.modalities_seen) >= 2:
                status = IdentityStatus.CONFIRMED
            elif best_conf >= _RECOGNIZED_FLOOR:
                status = IdentityStatus.RECOGNIZED
            elif best_conf >= _CANDIDATE_FLOOR:
                status = IdentityStatus.CANDIDATE
            else:
                status = IdentityStatus.UNKNOWN
            model.canonical_name = best_name

        model.confidence = round(_clamp01(confidence), 4)
        status_changed = status != was_status
        model.identity_status = status
        if status_changed:
            event = self._event_for(model, status, was_status, was_name)
            if event["event_type"] in _CANONICAL_EVENTS:
                self._pending_events.append(event)

    def _event_for(
        self,
        model: PersonModel,
        status: IdentityStatus,
        was_status: IdentityStatus,
        was_name: str | None,
    ) -> dict[str, Any]:
        """Map a lifecycle transition to a recognition event (Task 2.4)."""
        if status == IdentityStatus.AMBIGUOUS:
            event_type = "identity.ambiguous"
        elif status == IdentityStatus.REJECTED:
            event_type = "identity.lost"
        elif was_status == IdentityStatus.REJECTED and status in (
            IdentityStatus.RECOGNIZED,
            IdentityStatus.CONFIRMED,
        ):
            event_type = "identity.reidentified"
        elif status in (IdentityStatus.RECOGNIZED, IdentityStatus.CONFIRMED):
            event_type = "identity.recognized"
        elif was_status in (IdentityStatus.RECOGNIZED, IdentityStatus.CONFIRMED) and status == IdentityStatus.UNKNOWN:
            event_type = "identity.lost"
        else:
            event_type = "identity.status_changed"
        return {
            "event_type": event_type,
            "person_id": model.person_id,
            "name": model.canonical_name,
            "confidence": model.confidence,
            "status": status.value,
        }

    # ---- lifecycle controls -------------------------------------------------

    def reject(self, person_id: str, *, reason: str = "explicit") -> bool:
        """Explicitly reject an identity (user correction / safety).

        The disputed identity claim is discarded (name confidences cleared) so
        stale strong evidence cannot silently re-recognize the person; only
        fresh strong observations can rebuild the identity (→ reidentified).
        """
        model = self._persons.get(person_id)
        if model is None:
            return False
        was = model.identity_status
        model.identity_status = IdentityStatus.REJECTED
        model.confidence = 0.0
        model._name_confidences.clear()
        self._pending_events.append(
            self._event_for(model, IdentityStatus.REJECTED, was, model.canonical_name)
        )
        return True

    def note_interaction(self, person_id: str, summary: str, *, cycle: int) -> None:
        model = self._persons.get(person_id)
        if model is None:
            return
        model.interaction_count += 1
        model.recent_interactions.append(
            {"cycle": cycle, "summary": summary, "at": utc_now_iso()}
        )
        model.recent_interactions = model.recent_interactions[-_MAX_RECENT_INTERACTIONS:]

    def learn_preference(self, person_id: str, kind: str, value: Any) -> None:
        model = self._persons.get(person_id)
        if model is None:
            return
        model.preferences[kind] = value

    def note_relationship(self, person_id: str, other_id: str, category: str) -> None:
        model = self._persons.get(person_id)
        if model is None:
            return
        model.known_relationships[other_id] = category

    # ---- queries ------------------------------------------------------------

    def person(self, person_id: str) -> PersonModel | None:
        return self._persons.get(person_id)

    def resolve(self, name: str) -> PersonModel | None:
        """Resolve a canonical name / alias / person_id to a person."""
        key = str(name).strip().lower()
        for model in self._persons.values():
            if model.person_id == key or model.canonical_name == key or key in model.aliases:
                return model
        return None

    def recognized_persons(self) -> list[PersonModel]:
        return [m for m in self._persons.values() if m.known]

    def all_persons(self) -> list[PersonModel]:
        return list(self._persons.values())

    def drain_events(self) -> list[dict[str, Any]]:
        events, self._pending_events = self._pending_events, []
        return events

    # ---- persistence --------------------------------------------------------

    def snapshot(self) -> dict[str, Any]:
        return {"persons": [m.snapshot() for m in self._persons.values()]}

    @classmethod
    def from_snapshot(cls, data: dict[str, Any] | None) -> "PersonRegistry":
        registry = cls()
        if not data:
            return registry
        for raw in data.get("persons", []):
            model = PersonModel.from_snapshot(raw)
            registry._persons[model.person_id] = model
        return registry
