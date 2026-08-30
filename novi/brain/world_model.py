"""Unified World Model for the Mac Brain (PERFECTING_PLAN Step 1).

A time-aware, uncertainty-aware entity/relation graph with explicit epistemic
status on every node and relation, contradictions preserved (never silently
overwritten), and snapshots for debug/replay.

Canonical authority: docs/03-cognition/02_WORLD_MODEL.md

Key invariants enforced at this boundary:
  - Every entity/relation carries an EpistemicStatus (OBSERVED/INFERRED/PREDICTED/
    VERIFIED/UNKNOWN).
  - Predictions and hypothetical states never overwrite current observed state.
  - Contradictory evidence is preserved until resolved, expires, or is
    superseded by stronger evidence.
  - The WorldModel never overrides authoritative live telemetry with memory.
  - The WorldModel never directly commands actuators.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence
from uuid import uuid4

# ---------------------------------------------------------------------------
# Epistemic status (docs/03-cognition/02 §Epistemic State)
# ---------------------------------------------------------------------------

OBSERVED = "OBSERVED"
INFERRED = "INFERRED"
FUSED = "FUSED"
REMEMBERED = "REMEMBERED"
PREDICTED = "PREDICTED"
SIMULATED = "SIMULATED"
COUNTERFACTUAL = "COUNTERFACTUAL"
HYPOTHESIZED = "HYPOTHESIZED"
VERIFIED = "VERIFIED"
UNKNOWN = "UNKNOWN"

# Evidence classes maintained by Novi (docs/NOVI_NVIDIA_ROBOT_LEARNING_COGNITION_AUTONOMY_RESEARCH.md
# research 18: OBSERVED / INFERRED / PREDICTED / SIMULATED / COUNTERFACTUAL /
# HYPOTHESIZED / VERIFIED), extended with FUSED/REMEMBERED/UNKNOWN by the domain
# authority (docs/03-cognition/02 §Epistemic State).
ALL_EPISTEMIC_STATUSES = frozenset({
    OBSERVED, INFERRED, FUSED, REMEMBERED, PREDICTED, SIMULATED,
    COUNTERFACTUAL, HYPOTHESIZED, VERIFIED, UNKNOWN,
})

# Statuses that represent the *current real* world (as opposed to hypothetical).
_REAL_STATUSES = frozenset({OBSERVED, INFERRED, FUSED, REMEMBERED, VERIFIED, UNKNOWN})

# Statuses that must never overwrite current observed state.
_HYPOTHETICAL_STATUSES = frozenset({PREDICTED, SIMULATED, COUNTERFACTUAL, HYPOTHESIZED})


def _is_real(status: str) -> bool:
    return status in _REAL_STATUSES


def _clamp_sigma(sigma: float) -> float:
    """Clamp a measurement uncertainty σ into [0, 1]."""
    return max(0.0, min(1.0, float(sigma)))


def _is_hypothetical(status: str) -> bool:
    return status in _HYPOTHETICAL_STATUSES


# ---------------------------------------------------------------------------
# Entity types (docs/03-cognition/02 §Core Entity Types)
# ---------------------------------------------------------------------------

PERSON = "person"
ANIMAL = "animal"
ROBOT = "robot"
OBJECT = "object"
ROOM = "room"
BUILDING = "building"
PLACE = "place"
DEVICE = "device"
VEHICLE = "vehicle"
ACTIVITY = "activity"
EVENT = "event"
CONCEPT = "concept"
ORGANIZATION = "organization"
PROJECT = "project"

ALL_ENTITY_TYPES = frozenset({
    PERSON, ANIMAL, ROBOT, OBJECT, ROOM, BUILDING, PLACE, DEVICE,
    VEHICLE, ACTIVITY, EVENT, CONCEPT, ORGANIZATION, PROJECT,
})


# ---------------------------------------------------------------------------
# Entity lifecycle (docs/03-cognition/14 §Lifecycle)
# ---------------------------------------------------------------------------

CANDIDATE = "candidate"
ACTIVE = "active"
STALE = "stale"
SUPERSEDED = "superseded"
ARCHIVED = "archived"

LIFECYCLE_STATES = frozenset({CANDIDATE, ACTIVE, STALE, SUPERSEDED, ARCHIVED})


# ---------------------------------------------------------------------------
# Provenance (docs/03-cognition/14 §Provenance)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Provenance:
    """Source trace for any derived world-state element."""
    source: str
    transformation: str = "direct"  # direct | inference | fusion | memory | prediction | simulation
    model_or_tool: str = ""
    timestamp: str = ""
    confidence: float = 1.0
    verification_status: str = "unverified"  # unverified | verified | contradicted | expired

    def snapshot(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "transformation": self.transformation,
            "model_or_tool": self.model_or_tool,
            "timestamp": self.timestamp,
            "confidence": round(self.confidence, 4),
            "verification_status": self.verification_status,
        }


# ---------------------------------------------------------------------------
# WorldEntity
# ---------------------------------------------------------------------------

@dataclass
class WorldEntity:
    """A typed entity in the world model with epistemic status and lifecycle.

    Identity is a stable internal ID; labels/aliases are display names.
    State is a dict of field -> (value, epistemic_status, confidence) so that
    observed and inferred states are never collapsed.
    """
    entity_id: str
    entity_type: str
    labels: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    epistemic_status: str = UNKNOWN
    confidence: float = 0.0
    provenance: Provenance | None = None
    lifecycle: str = CANDIDATE
    state: dict[str, tuple[Any, str, float]] = field(default_factory=dict)
    # state field -> (value, epistemic_status, confidence)
    # Phase 1b: per-field measurement uncertainty (σ ∈ [0, 1], 0 = certain),
    # kept in a parallel dict so the (value, status, confidence) tuples stay
    # compatible. When a caller supplies no σ it defaults to 1 - confidence.
    sigma: dict[str, float] = field(default_factory=dict)
    # Phase 1c: live metric reference into the SpatialMap coordinate space,
    # e.g. {"frame": "map", "x": 1.0, "y": 0.5} for the robot self-entity —
    # bridges the semantic world model to frames/regions/visibility.
    spatial_ref: dict[str, Any] | None = None
    created_at: str = ""
    last_updated_at: str = ""
    privacy_class: str = "unclassified"

    def label(self) -> str:
        return self.labels[0] if self.labels else self.entity_id

    def state_value(self, field_name: str) -> Any | None:
        entry = self.state.get(field_name)
        return entry[0] if entry else None

    def state_status(self, field_name: str) -> str | None:
        entry = self.state.get(field_name)
        return entry[1] if entry else None

    def state_sigma(self, field_name: str) -> float | None:
        """Phase 1b: the measurement uncertainty σ (∈ [0,1]) of a state field."""
        return self.sigma.get(field_name)

    def set_state(self, field_name: str, value: Any, *, status: str, confidence: float, provenance: Provenance | None = None, sigma: float | None = None) -> None:
        """Set a state field with explicit epistemic status.

        Hypothetical statuses (PREDICTED/SIMULATED/COUNTERFACTUAL) are stored
        alongside but never overwrite a real (OBSERVED/VERIFIED) value for the
        same field.
        """
        existing = self.state.get(field_name)
        if existing is not None:
            old_value, old_status, _ = existing
            # A hypothetical update never overwrites a real value.
            if _is_hypothetical(status) and _is_real(old_status):
                return  # preserve the real state
            # An older real observation never regresses a newer one.
            # (Freshness is handled by the WorldModel.update method via timestamps.)
        self.state[field_name] = (value, status, max(confidence, 0.0))
        # Phase 1b: store the measurement σ (default: 1 - confidence).
        self.sigma[field_name] = _clamp_sigma(sigma if sigma is not None else 1.0 - max(confidence, 0.0))
        if provenance is not None:
            self.provenance = provenance
        # Promote epistemic status: VERIFIED > OBSERVED > INFERRED/FUSED > UNKNOWN
        if _is_real(status) and self.epistemic_status == UNKNOWN:
            self.epistemic_status = status

    def snapshot(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "labels": list(self.labels),
            "aliases": list(self.aliases),
            "epistemic_status": self.epistemic_status,
            "confidence": round(self.confidence, 4),
            "provenance": self.provenance.snapshot() if self.provenance else None,
            "lifecycle": self.lifecycle,
            "state": {
                k: {"value": v[0], "epistemic_status": v[1], "confidence": round(v[2], 4),
                    "sigma": round(self.sigma.get(k, round(1.0 - v[2], 4)), 4)}
                for k, v in self.state.items()
            },
            "spatial_ref": dict(self.spatial_ref) if self.spatial_ref else None,
            "created_at": self.created_at,
            "last_updated_at": self.last_updated_at,
            "privacy_class": self.privacy_class,
        }


# ---------------------------------------------------------------------------
# WorldRelation
# ---------------------------------------------------------------------------

@dataclass
class WorldRelation:
    """A typed, timestamped, confidence-aware relation between two entities."""
    relation_id: str
    subject_id: str
    relation_type: str
    object_id: str
    epistemic_status: str = UNKNOWN
    confidence: float = 0.0
    # Phase 1b: measurement uncertainty σ ∈ [0,1] (defaults to 1 - confidence).
    sigma: float = 0.0
    provenance: Provenance | None = None
    valid_from: str = ""
    valid_until: str | None = None  # None = still valid
    verification_status: str = "unverified"

    def __post_init__(self) -> None:
        self.sigma = _clamp_sigma(self.sigma)

    def is_active(self) -> bool:
        return self.valid_until is None

    def snapshot(self) -> dict[str, Any]:
        return {
            "relation_id": self.relation_id,
            "subject_id": self.subject_id,
            "relation_type": self.relation_type,
            "object_id": self.object_id,
            "epistemic_status": self.epistemic_status,
            "confidence": round(self.confidence, 4),
            "sigma": round(self.sigma, 4),
            "provenance": self.provenance.snapshot() if self.provenance else None,
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
            "verification_status": self.verification_status,
        }


# ---------------------------------------------------------------------------
# Contradiction record
# ---------------------------------------------------------------------------

@dataclass
class Contradiction:
    """Preserved contradiction between two pieces of evidence."""
    contradiction_id: str
    entity_id: str
    field_name: str
    claim_a: tuple[Any, str, float]  # (value, epistemic_status, confidence)
    claim_b: tuple[Any, str, float]
    source_a: str = ""
    source_b: str = ""
    resolution: str = "unresolved"  # unresolved | resolved_a | resolved_b | expired
    created_at: str = ""

    def snapshot(self) -> dict[str, Any]:
        return {
            "contradiction_id": self.contradiction_id,
            "entity_id": self.entity_id,
            "field_name": self.field_name,
            "claim_a": {"value": self.claim_a[0], "epistemic_status": self.claim_a[1], "confidence": round(self.claim_a[2], 4)},
            "claim_b": {"value": self.claim_b[0], "epistemic_status": self.claim_b[1], "confidence": round(self.claim_b[2], 4)},
            "source_a": self.source_a,
            "source_b": self.source_b,
            "resolution": self.resolution,
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# WorldModelSnapshot
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WorldModelSnapshot:
    """Immutable snapshot of the world model for debug/replay."""
    snapshot_id: str
    created_at: str
    world_version: int
    entities: tuple[dict[str, Any], ...]
    relations: tuple[dict[str, Any], ...]
    active_events: tuple[dict[str, Any], ...]
    contradictions: tuple[dict[str, Any], ...]
    uncertainty_summary: dict[str, Any]
    provenance_summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "created_at": self.created_at,
            "world_version": self.world_version,
            "entities": list(self.entities),
            "relations": list(self.relations),
            "active_events": list(self.active_events),
            "contradictions": list(self.contradictions),
            "uncertainty_summary": self.uncertainty_summary,
            "provenance_summary": self.provenance_summary,
        }


# ---------------------------------------------------------------------------
# WorldModel — the unified current-state graph
# ---------------------------------------------------------------------------

class WorldModel:
    """Unified, time-aware, uncertainty-aware world-state graph.

    The single coherent "current world state" the whole brain queries.
    Pieces (kgraph, temporal, cognition2) feed into this via ``update_entity``
    and ``add_relation``.
    """

    def __init__(self) -> None:
        self._entities: dict[str, WorldEntity] = {}
        self._relations: dict[str, WorldRelation] = {}
        self._contradictions: list[Contradiction] = []
        self._active_events: list[dict[str, Any]] = []
        self._world_version: int = 0
        self._label_index: dict[str, str] = {}  # label -> entity_id
        # Freshness policy (doc 03 Step 2): (entity_id, field) ->
        # (observed_cycle, ttl_cycles). 0 ttl = never expires.
        self._field_ttl: dict[tuple[str, str], tuple[int, int]] = {}
        # Pairs already reported expired (idempotency for expire_stale).
        self._expired_fields: set[tuple[str, str]] = set()

    # ---- entity management ----

    def add_entity(
        self,
        entity_id: str,
        entity_type: str,
        *,
        labels: Sequence[str] | None = None,
        aliases: Sequence[str] | None = None,
        epistemic_status: str = UNKNOWN,
        confidence: float = 0.0,
        provenance: Provenance | None = None,
        privacy_class: str = "unclassified",
        created_at: str = "",
    ) -> WorldEntity:
        if entity_type not in ALL_ENTITY_TYPES:
            raise ValueError(f"unknown entity type: {entity_type!r}")
        if epistemic_status not in ALL_EPISTEMIC_STATUSES:
            raise ValueError(f"unknown epistemic status: {epistemic_status!r}")
        if entity_id in self._entities:
            entity = self._entities[entity_id]
            if labels:
                for lbl in labels:
                    if lbl not in entity.labels:
                        entity.labels.append(lbl)
                    self._label_index[lbl.lower()] = entity_id
            if aliases:
                for alias in aliases:
                    if alias not in entity.aliases:
                        entity.aliases.append(alias)
            return entity
        entity = WorldEntity(
            entity_id=entity_id,
            entity_type=entity_type,
            labels=list(labels) if labels else [],
            aliases=list(aliases) if aliases else [],
            epistemic_status=epistemic_status,
            confidence=confidence,
            provenance=provenance,
            privacy_class=privacy_class,
            created_at=created_at,
            last_updated_at=created_at,
        )
        self._entities[entity_id] = entity
        for lbl in entity.labels:
            self._label_index[lbl.lower()] = entity_id
        for alias in entity.aliases:
            self._label_index[alias.lower()] = entity_id
        self._world_version += 1
        return entity

    def get_entity(self, entity_id: str) -> WorldEntity | None:
        return self._entities.get(entity_id)

    def resolve(self, label_or_id: str) -> WorldEntity | None:
        """Resolve a label, alias, or entity_id to a WorldEntity."""
        if label_or_id in self._entities:
            return self._entities[label_or_id]
        return self._entities.get(self._label_index.get(label_or_id.lower(), ""))

    def update_entity_state(
        self,
        entity_id: str,
        field_name: str,
        value: Any,
        *,
        epistemic_status: str,
        confidence: float,
        source: str,
        timestamp: str = "",
        sigma: float | None = None,
    ) -> bool:
        """Update a single state field on an entity with epistemic discipline.

        Returns True if the update was applied, False if it was rejected
        (e.g. a hypothetical tried to overwrite a real value, or a stale
        observation tried to regress a newer one).

        Phase 1b: an explicit σ (measurement uncertainty ∈ [0,1]) may be
        attached; it defaults to 1 - confidence when omitted.
        """
        entity = self._entities.get(entity_id)
        if entity is None:
            return False
        if epistemic_status not in ALL_EPISTEMIC_STATUSES:
            raise ValueError(f"unknown epistemic status: {epistemic_status!r}")

        existing = entity.state.get(field_name)
        prov = Provenance(source=source, timestamp=timestamp, confidence=confidence)

        # Check for contradiction: two *real* claims with different values.
        if existing is not None and _is_real(epistemic_status) and _is_real(existing[1]):
            old_value, old_status, old_conf = existing
            if old_value != value:
                # Preserve the contradiction rather than overwrite.
                contradiction = Contradiction(
                    contradiction_id=str(uuid4()),
                    entity_id=entity_id,
                    field_name=field_name,
                    claim_a=existing,
                    claim_b=(value, epistemic_status, confidence),
                    source_a=entity.provenance.source if entity.provenance else "",
                    source_b=source,
                    created_at=timestamp,
                )
                self._contradictions.append(contradiction)
                # The higher-confidence (or, on a tie, the newer) claim becomes
                # the current state; the loser stays preserved as history
                # (doc 03 Step 3: belief revision chooses while preserving evidence).
                # Phase 1c: an equal-freshness tie (same or newer stamp, e.g.
                # same-microsecond re-observations from a body's own resolver)
                # also supersedes — equal timestamp is at least as fresh, so
                # the later perception is the newer one.
                newer_than_current = (
                    confidence == old_conf
                    and (
                        not bool(entity.last_updated_at)
                        or (bool(timestamp) and timestamp >= entity.last_updated_at)
                    )
                )
                if confidence > old_conf or newer_than_current:
                    entity.set_state(field_name, value, status=epistemic_status, confidence=confidence, provenance=prov, sigma=sigma)
                    entity.confidence = max(entity.confidence, confidence)
                    entity.last_updated_at = timestamp
                    self._world_version += 1
                    return True
                return False  # keep the old, preserve the contradiction

        # Stale check: don't let an older timestamp regress a newer one.
        if (
            existing is not None
            and timestamp
            and entity.last_updated_at
            and timestamp < entity.last_updated_at
            and _is_real(epistemic_status)
            and _is_real(existing[1])
        ):
            return False

        entity.set_state(field_name, value, status=epistemic_status, confidence=confidence, provenance=prov, sigma=sigma)
        entity.confidence = max(entity.confidence, confidence)
        entity.last_updated_at = timestamp
        if _is_real(epistemic_status):
            entity.lifecycle = ACTIVE
        self._world_version += 1
        return True

    def set_entity_lifecycle(self, entity_id: str, lifecycle: str) -> None:
        if lifecycle not in LIFECYCLE_STATES:
            raise ValueError(f"unknown lifecycle: {lifecycle!r}")
        entity = self._entities.get(entity_id)
        if entity is not None:
            entity.lifecycle = lifecycle
            self._world_version += 1

    def set_entity_spatial_ref(self, entity_id: str, spatial_ref: dict[str, Any] | None) -> bool:
        """Attach/update an entity's live metric reference into a coordinate
        frame (e.g. {"frame": "map", "x": 1.0, "y": 0.5}).

        Plan 22 Task 1.4 (spatial identity): persistent entities carry a
        spatial_ref so spatial reasoning never depends on semantic-only
        location strings.
        """
        entity = self._entities.get(entity_id)
        if entity is None:
            return False
        entity.spatial_ref = dict(spatial_ref) if spatial_ref else None
        self._world_version += 1
        return True

    # ---- freshness / TTL policy (doc 03 Step 2) ----

    def set_field_ttl(self, entity_id: str, field_name: str, *, ttl_cycles: int, observed_cycle: int = 0) -> bool:
        """Declare how long a state field stays fresh (0 = never expires).

        A person's location may expire quickly; a room name may remain stable.
        The planner must never treat expired data as current.
        """
        if entity_id not in self._entities:
            return False
        self._field_ttl[(entity_id, field_name)] = (max(0, int(observed_cycle)), max(0, int(ttl_cycles)))
        return True

    def freshness_of(self, entity_id: str, field_name: str, *, cycle: int) -> str:
        """fresh | stale | unknown — never lets callers assume freshness."""
        policy = self._field_ttl.get((entity_id, field_name))
        if policy is None:
            return "unknown"
        observed_cycle, ttl_cycles = policy
        if ttl_cycles == 0:
            return "fresh"
        return "fresh" if cycle <= observed_cycle + ttl_cycles else "stale"

    def expire_stale(self, *, cycle: int) -> list[tuple[str, str]]:
        """Expire state fields past their TTL; mark their entities STALE.

        Returns the list of (entity_id, field_name) pairs that expired in this
        call (idempotent: an already-expired pair is not reported twice).
        """
        expired: list[tuple[str, str]] = []
        for (entity_id, field_name), (observed_cycle, ttl_cycles) in self._field_ttl.items():
            if ttl_cycles and cycle > observed_cycle + ttl_cycles:
                pair = (entity_id, field_name)
                if pair not in self._expired_fields:
                    self._expired_fields.add(pair)
                    entity = self._entities.get(entity_id)
                    if entity is not None and entity.lifecycle != STALE:
                        entity.lifecycle = STALE
                        self._world_version += 1
                    expired.append(pair)
        return expired

    # ---- relation management ----

    def add_relation(
        self,
        subject_id: str,
        relation_type: str,
        object_id: str,
        *,
        epistemic_status: str = UNKNOWN,
        confidence: float = 0.0,
        source: str = "",
        timestamp: str = "",
        valid_from: str = "",
    ) -> WorldRelation:
        if epistemic_status not in ALL_EPISTEMIC_STATUSES:
            raise ValueError(f"unknown epistemic status: {epistemic_status!r}")
        relation_id = f"{subject_id}:{relation_type}:{object_id}"
        # If the same relation already exists, reinforce it.
        if relation_id in self._relations:
            rel = self._relations[relation_id]
            rel.confidence = min(1.0, rel.confidence + confidence * 0.1)
            rel.provenance = Provenance(source=source, timestamp=timestamp, confidence=rel.confidence)
            self._world_version += 1
            return rel
        rel = WorldRelation(
            relation_id=relation_id,
            subject_id=subject_id,
            relation_type=relation_type,
            object_id=object_id,
            epistemic_status=epistemic_status,
            confidence=confidence,
            provenance=Provenance(source=source, timestamp=timestamp, confidence=confidence),
            valid_from=valid_from or timestamp,
        )
        self._relations[relation_id] = rel
        self._world_version += 1
        return rel

    def get_relation(self, subject_id: str, relation_type: str, object_id: str) -> WorldRelation | None:
        return self._relations.get(f"{subject_id}:{relation_type}:{object_id}")

    def relations_for(self, entity_id: str) -> tuple[WorldRelation, ...]:
        return tuple(
            r for r in self._relations.values()
            if (r.subject_id == entity_id or r.object_id == entity_id) and r.is_active()
        )

    # ---- events ----

    def add_event(self, event: dict[str, Any]) -> None:
        self._active_events.append(event)
        self._world_version += 1

    def clear_events(self) -> None:
        self._active_events.clear()

    # ---- contradictions ----

    @property
    def contradictions(self) -> tuple[Contradiction, ...]:
        return tuple(self._contradictions)

    def resolve_contradiction(self, contradiction_id: str, resolution: str) -> bool:
        for c in self._contradictions:
            if c.contradiction_id == contradiction_id:
                c.resolution = resolution
                return True
        return False

    # ---- queries ----

    @property
    def world_version(self) -> int:
        return self._world_version

    @property
    def entities(self) -> dict[str, WorldEntity]:
        return dict(self._entities)

    @property
    def relations(self) -> dict[str, WorldRelation]:
        return dict(self._relations)

    def visible_entities(self, location: str | None = None) -> tuple[WorldEntity, ...]:
        """Entities currently present, optionally filtered by location."""
        out: list[WorldEntity] = []
        for entity in self._entities.values():
            if entity.lifecycle in (ARCHIVED, SUPERSEDED):
                continue
            if location is not None:
                loc = entity.state_value("location")
                if loc != location:
                    continue
            out.append(entity)
        return tuple(out)

    def uncertainty_summary(self) -> dict[str, Any]:
        """Summary of current uncertainty across the world model.

        Phase 1b: includes per-field measurement σ for every entity that has
        state fields ("field_sigmas": entity_id -> field -> σ ∈ [0,1]).
        """
        by_status: dict[str, int] = {}
        uncertain_entities: list[str] = []
        field_sigmas: dict[str, dict[str, float]] = {}
        for entity in self._entities.values():
            by_status[entity.epistemic_status] = by_status.get(entity.epistemic_status, 0) + 1
            if entity.epistemic_status in (UNKNOWN, INFERRED):
                uncertain_entities.append(entity.entity_id)
            sigmas = {
                field: round(entity.state_sigma(field), 4)
                for field in entity.state
                if entity.state_sigma(field) is not None
            }
            if sigmas:
                field_sigmas[entity.entity_id] = sigmas
        return {
            "total_entities": len(self._entities),
            "by_epistemic_status": by_status,
            "uncertain_entities": uncertain_entities,
            "unresolved_contradictions": sum(1 for c in self._contradictions if c.resolution == "unresolved"),
            "field_sigmas": field_sigmas,
        }

    def provenance_summary(self) -> dict[str, Any]:
        sources: dict[str, int] = {}
        for entity in self._entities.values():
            if entity.provenance:
                sources[entity.provenance.source] = sources.get(entity.provenance.source, 0) + 1
        for rel in self._relations.values():
            if rel.provenance:
                sources[rel.provenance.source] = sources.get(rel.provenance.source, 0) + 1
        return {"sources": sources, "total_sources": len(sources)}

    # ---- snapshot ----

    def snapshot(self, *, snapshot_id: str | None = None, created_at: str = "") -> WorldModelSnapshot:
        return WorldModelSnapshot(
            snapshot_id=snapshot_id or str(uuid4()),
            created_at=created_at,
            world_version=self._world_version,
            entities=tuple(e.snapshot() for e in self._entities.values()),
            relations=tuple(r.snapshot() for r in self._relations.values()),
            active_events=tuple(dict(e) for e in self._active_events),
            contradictions=tuple(c.snapshot() for c in self._contradictions),
            uncertainty_summary=self.uncertainty_summary(),
            provenance_summary=self.provenance_summary(),
        )

    # ---- serialization ----

    def to_dict(self) -> dict[str, Any]:
        return {
            "world_version": self._world_version,
            "entities": {eid: e.snapshot() for eid, e in self._entities.items()},
            "relations": {rid: r.snapshot() for rid, r in self._relations.items()},
            "contradictions": [c.snapshot() for c in self._contradictions],
            "active_events": list(self._active_events),
        }

    # ---- compatibility bridge for legacy cognition ----

    def to_world_state(self) -> Any:
        """Return a WorldModelState-compatible object for legacy cognition code.

        Converts the unified world model's entities to WorldEntityState objects
        that MacCognition.build_situation() and MacCognition.cycle() can query.
        This bridges the epistemic-status-aware UnifiedWorldModel to the
        existing cognition interface without rewriting cognition.
        """
        from novi.brain.b1_world import WorldEntityState, WorldModelState

        entities: dict[str, WorldEntityState] = {}
        for entity_id, entity in self._entities.items():
            if entity.lifecycle in ("archived", "superseded"):
                continue
            # Use the label as the entity key (matching legacy convention).
            key = entity.label() if entity.labels else entity_id
            location = entity.state_value("location")
            state = entity.state_value("presence") or entity.state_value("state") or "present"
            confidence = entity.confidence
            # Use the world_version as a proxy for last_observed_cycle.
            last_cycle = self._world_version
            entities[key] = WorldEntityState(
                entity=key,
                location=location,
                state=str(state) if state else "present",
                confidence=confidence,
                last_observed_cycle=last_cycle,
            )
        return WorldModelState(entities=entities)
