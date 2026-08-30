"""Persistent object identity (plan 22, Phase 3).

Tasks:
- 3.1 ObjectEntity — canonical fields incl. appearance signature and opaque
  instance-embedding ref (never the embedding itself in ordinary memory);
- 3.2 instance re-identification — distinguishing "a mug" from "Vano's black
  mug" from "that same black mug we saw yesterday" requires stable instance
  identity across frames and absences;
- 3.3 lifecycle — DETECTED → TRACKED → IDENTIFIED → PERSISTENT, with LOST /
  REACQUIRED / RETIRED;
- 3.4 event semantics — object.detected / recognized / moved / disappeared /
  reappeared / state_changed. Events are *evidence for salience*, never
  speech by themselves (plan §7: dialogue salience decides whether an event
  becomes speech).

Re-identification is deliberately conservative: without visual embeddings the
appearance signature is a deterministic proxy (class + size bucket + optional
attributes), so instance confidence stays honest and below certainty.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

_MAX_HISTORY = 16


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ObjectStatus(str, Enum):
    DETECTED = "DETECTED"
    TRACKED = "TRACKED"
    IDENTIFIED = "IDENTIFIED"
    PERSISTENT = "PERSISTENT"
    LOST = "LOST"
    REACQUIRED = "REACQUIRED"
    RETIRED = "RETIRED"


def _signature(*, cls: str, size_bucket: str, attributes: dict[str, Any]) -> str:
    """Deterministic appearance signature (Task 3.2).

    A bucket of the bounding-box area plus stable attributes. Without real
    embeddings two look-alike instances can collide — that is why re-
    identification confidence is bounded below certainty.
    """
    stable = {k: v for k, v in sorted(attributes.items()) if isinstance(v, (str, int, float, bool))}
    return f"{cls.lower()}|{size_bucket}|{stable}"


def _size_bucket(bbox: tuple[Any, Any, Any, Any] | list[Any] | None) -> str:
    if not bbox or len(bbox) < 4:
        return "?"
    try:
        w = max(0.0, float(bbox[2]) - float(bbox[0]))
        h = max(0.0, float(bbox[3]) - float(bbox[1]))
        area = w * h
    except (TypeError, ValueError):
        return "?"
    if area <= 0:
        return "?"
    if area < 500:
        return "tiny"
    if area < 5000:
        return "small"
    if area < 50000:
        return "medium"
    return "large"


@dataclass
class ObjectEntity:
    object_id: str
    cls: str
    status: ObjectStatus = ObjectStatus.DETECTED
    appearance_signature: str = ""
    instance_embedding_ref: str | None = None  # opaque ref, never the vector
    owner_candidate: str | None = None
    first_seen: str = ""
    last_seen: str = ""
    usual_location: str = ""
    current_location: str = ""
    state: str = "present"
    confidence: float = 0.0
    history: list[dict[str, Any]] = field(default_factory=list)
    relationships: dict[str, str] = field(default_factory=dict)  # other object/person id -> relation
    last_seen_cycle: int = 0
    lost_at_cycle: int | None = None

    def snapshot(self) -> dict[str, Any]:
        return {
            "object_id": self.object_id,
            "class": self.cls,
            "status": self.status.value,
            "appearance_signature": self.appearance_signature,
            "instance_embedding_ref": self.instance_embedding_ref,
            "owner_candidate": self.owner_candidate,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "usual_location": self.usual_location,
            "current_location": self.current_location,
            "state": self.state,
            "confidence": round(self.confidence, 4),
            "history": list(self.history),
            "relationships": dict(self.relationships),
            "last_seen_cycle": self.last_seen_cycle,
            "lost_at_cycle": self.lost_at_cycle,
        }


class ObjectRegistry:
    """Single canonical registry of persistent object instances (plan §2.2)."""

    def __init__(self) -> None:
        self._objects: dict[str, ObjectEntity] = {}
        self._pending_events: list[dict[str, Any]] = []

    # ---- observation -------------------------------------------------------

    def observe(
        self,
        *,
        entity_id: str,
        cls: str,
        confidence: float,
        cycle: int,
        location: str = "",
        bbox: tuple[Any, Any, Any, Any] | list[Any] | None = None,
        attributes: dict[str, Any] | None = None,
        embedding_ref: str | None = None,
        owner_candidate: str | None = None,
        now: str | None = None,
    ) -> ObjectEntity:
        """Register one sighting.

        A known ``entity_id`` re-identifies the same instance (TRACKED →
        IDENTIFIED → PERSISTENT). An unknown id is matched by appearance
        signature against known instances (REACQUIRED) or created fresh
        (DETECTED). Location changes are recorded and surfaced as
        ``object.moved`` events (Example B in plan §1).
        """
        now = now or utc_now_iso()
        conf = _clamp01(confidence)
        sig = _signature(cls=cls, size_bucket=_size_bucket(bbox), attributes=attributes or {})
        existing = self._objects.get(entity_id)

        if existing is None:
            existing = self._match_by_signature(sig)
            if existing is not None and existing.status in (
                ObjectStatus.PERSISTENT,
                ObjectStatus.IDENTIFIED,
                ObjectStatus.LOST,
            ):
                # Instance re-identification: same appearance seen before.
                self._pending_events.append(
                    self._event("object.reappeared" if existing.status == ObjectStatus.LOST else "object.recognized", existing, now)
                )
                existing.status = ObjectStatus.REACQUIRED
                existing.last_seen = now
                existing.last_seen_cycle = cycle
                existing.confidence = _clamp01(conf * 0.9)  # conservative
                existing.lost_at_cycle = None
                self._record(existing, location, now, cycle)
                return existing
            entity = ObjectEntity(
                object_id=entity_id,
                cls=cls,
                status=ObjectStatus.DETECTED,
                appearance_signature=sig,
                instance_embedding_ref=embedding_ref,
                owner_candidate=owner_candidate,
                first_seen=now,
                last_seen=now,
                current_location=location,
                usual_location=location,
                confidence=conf,
                last_seen_cycle=cycle,
            )
            self._objects[entity_id] = entity
            self._pending_events.append(self._event("object.detected", entity, now))
            return entity

        # Known instance: update state.
        was_status = existing.status
        if was_status in (ObjectStatus.LOST, ObjectStatus.RETIRED):
            existing.status = ObjectStatus.REACQUIRED
            existing.lost_at_cycle = None
            self._pending_events.append(self._event("object.reappeared", existing, now))
        elif existing.confidence >= 0.8 and existing.last_seen_cycle and cycle - existing.last_seen_cycle > 2:
            existing.status = ObjectStatus.PERSISTENT
        elif was_status == ObjectStatus.DETECTED:
            existing.status = ObjectStatus.TRACKED
        elif was_status == ObjectStatus.TRACKED and conf >= 0.7:
            existing.status = ObjectStatus.IDENTIFIED

        moved = bool(location) and existing.current_location and location != existing.current_location
        existing.current_location = location or existing.current_location
        existing.last_seen = now
        existing.last_seen_cycle = cycle
        existing.confidence = _clamp01(max(existing.confidence, conf))
        if embedding_ref:
            existing.instance_embedding_ref = embedding_ref
        if owner_candidate:
            existing.owner_candidate = owner_candidate
        if moved:
            self._pending_events.append(self._event("object.moved", existing, now))
        self._record(existing, location, now, cycle)
        return existing

    def _match_by_signature(self, sig: str) -> ObjectEntity | None:
        """Tentative instance re-identification by appearance (Task 3.2)."""
        for obj in self._objects.values():
            if obj.appearance_signature == sig and obj.status != ObjectStatus.RETIRED:
                return obj
        return None

    def _record(self, obj: ObjectEntity, location: str, now: str, cycle: int) -> None:
        obj.history.append({"at": now, "cycle": cycle, "location": location, "state": obj.state})
        obj.history = obj.history[-_MAX_HISTORY:]
        # usual_location = most frequent recent location
        if location:
            counts: dict[str, int] = {}
            for h in obj.history:
                if h["location"]:
                    counts[h["location"]] = counts.get(h["location"], 0) + 1
            if counts:
                obj.usual_location = max(counts.items(), key=lambda kv: kv[1])[0]

    def _event(self, event_type: str, obj: ObjectEntity, now: str) -> dict[str, Any]:
        return {
            "event_type": event_type,
            "object_id": obj.object_id,
            "class": obj.cls,
            "status": obj.status.value,
            "confidence": obj.confidence,
            "location": obj.current_location,
            "at": now,
        }

    # ---- lifecycle controls -------------------------------------------------

    def expire_missing(self, *, cycle: int, max_age_cycles: int = 10) -> list[dict[str, Any]]:
        """Mark instances not seen for ``max_age_cycles`` as LOST (once)."""
        emitted: list[dict[str, Any]] = []
        for obj in self._objects.values():
            if obj.status in (ObjectStatus.LOST, ObjectStatus.RETIRED):
                continue
            if cycle - obj.last_seen_cycle > max_age_cycles:
                obj.status = ObjectStatus.LOST
                obj.lost_at_cycle = cycle
                evt = self._event("object.disappeared", obj, utc_now_iso())
                self._pending_events.append(evt)
                emitted.append(evt)
        return emitted

    def retire(self, object_id: str) -> bool:
        obj = self._objects.get(object_id)
        if obj is None:
            return False
        obj.status = ObjectStatus.RETIRED
        return True

    def note_relationship(self, object_id: str, other_id: str, relation: str) -> None:
        obj = self._objects.get(object_id)
        if obj is not None:
            obj.relationships[other_id] = relation

    # ---- queries ------------------------------------------------------------

    def object(self, object_id: str) -> ObjectEntity | None:
        return self._objects.get(object_id)

    def resolve(self, cls: str, location: str = "") -> ObjectEntity | None:
        """Resolve the most likely known instance of a class (and location)."""
        best = None
        for obj in self._objects.values():
            if obj.cls.lower() != str(cls).lower() or obj.status == ObjectStatus.RETIRED:
                continue
            if location and obj.current_location == location:
                return obj
            if best is None or obj.confidence > best.confidence:
                best = obj
        return best

    def known_instances(self, cls: str | None = None) -> list[ObjectEntity]:
        objs = [
            o for o in self._objects.values()
            if o.status not in (ObjectStatus.RETIRED, ObjectStatus.LOST)
        ]
        if cls:
            objs = [o for o in objs if o.cls.lower() == str(cls).lower()]
        return objs

    def drain_events(self) -> list[dict[str, Any]]:
        events, self._pending_events = self._pending_events, []
        return events

    # ---- persistence --------------------------------------------------------

    def snapshot(self) -> dict[str, Any]:
        return {"objects": [o.snapshot() for o in self._objects.values()]}

    @classmethod
    def from_snapshot(cls, data: dict[str, Any] | None) -> "ObjectRegistry":
        registry = cls()
        if not data:
            return registry
        for raw in data.get("objects", []):
            obj = ObjectEntity(
                object_id=str(raw.get("object_id", "") or uuid.uuid4().hex[:12]),
                cls=str(raw.get("class", "object")),
                status=ObjectStatus(raw.get("status", ObjectStatus.DETECTED.value)),
                appearance_signature=str(raw.get("appearance_signature", "")),
                instance_embedding_ref=raw.get("instance_embedding_ref"),
                owner_candidate=raw.get("owner_candidate"),
                first_seen=str(raw.get("first_seen", "")),
                last_seen=str(raw.get("last_seen", "")),
                usual_location=str(raw.get("usual_location", "")),
                current_location=str(raw.get("current_location", "")),
                state=str(raw.get("state", "present")),
                confidence=_clamp01(float(raw.get("confidence", 0.0))),
                history=list(raw.get("history", [])),
                relationships=dict(raw.get("relationships", {})),
                last_seen_cycle=int(raw.get("last_seen_cycle", 0)),
                lost_at_cycle=raw.get("lost_at_cycle"),
            )
            registry._objects[obj.object_id] = obj
        return registry
