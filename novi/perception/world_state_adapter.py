"""GroundingOutcome -> world-model admission (plan Step 18).

Converts a perception GroundingOutcome into world-model calls with full
epistemic discipline:

- ASSOCIATED observations (matched to a track) update that track's entity
  with OBSERVED state (bbox_px, bbox_norm, frame_id, query);
- CANDIDATE observations become new CANDIDATE entities with HYPOTHESIZED
  status — proposals that can never overwrite observed state (the brain's
  update_entity_state enforces this);
- every call carries provenance (source=locate_anything, model@revision).

The adapter is protocol-based: it needs only the documented world-model
surface (add_entity / update_entity_state / resolve), so tests use a fake
and the concrete WorldModel wiring stays the brain's call. A failed or
no-object grounding result admits NOTHING (fail-closed: absence is never
inferred from a failure).

Entity ids: associated -> `track-<id>` (or caller-supplied mapping via
`entity_id_for`); candidates -> `la-<observation_id>`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol, runtime_checkable

from novi.perception.grounding import (
    GroundingObservation,
    GroundingResult,
    PointObservation,
)
from novi.perception.grounding_association import GroundingAssociation, GroundingOutcome

OBSERVED = "OBSERVED"
HYPOTHESIZED = "HYPOTHESIZED"

_BOX_FIELDS = ("bbox_px", "bbox_norm", "frame_id", "query")
_POINT_FIELDS = ("point_px", "point_norm", "frame_id", "query")


@dataclass(frozen=True)
class _Provenance:
    """Provenance record shaped like the brain's Provenance (snapshot-compatible)."""

    source: str
    transformation: str = "direct"
    model_or_tool: str = ""
    timestamp: str = ""
    confidence: float = 1.0
    verification_status: str = "unverified"

    def snapshot(self) -> dict:
        return {
            "source": self.source,
            "transformation": self.transformation,
            "model_or_tool": self.model_or_tool,
            "timestamp": self.timestamp,
            "confidence": round(self.confidence, 4),
            "verification_status": self.verification_status,
        }


@runtime_checkable
class WorldModelSurface(Protocol):
    """The documented brain WorldModel surface the adapter needs."""

    def add_entity(self, entity_id, entity_type, *, labels=None, epistemic_status="UNKNOWN", confidence=0.0, provenance=None, created_at="", **kwargs): ...

    def update_entity_state(self, entity_id, field_name, value, *, epistemic_status, confidence, source, timestamp="") -> bool: ...

    def resolve(self, label_or_id): ...


@dataclass(frozen=True)
class AdmitSummary:
    created: int  # entities created
    updates: int  # associated entities updated
    candidates: int  # candidate entities created (hypothetical proposals)


def _provenance(obs: GroundingObservation | PointObservation) -> _Provenance:
    return _Provenance(
        source="locate_anything",
        transformation="direct",
        model_or_tool=f"{obs.model_id}@{obs.model_revision}",
        timestamp=obs.timestamp,
        confidence=1.0,
    )


def _state_values(obs: GroundingObservation | PointObservation) -> dict[str, object]:
    if isinstance(obs, GroundingObservation):
        return {
            "bbox_px": obs.pixel_box,
            "bbox_norm": obs.source_box,
            "frame_id": obs.frame_id,
            "query": obs.query,
        }
    return {
        "point_px": obs.pixel_point,
        "point_norm": obs.source_point,
        "frame_id": obs.frame_id,
        "query": obs.query,
    }


def admit_grounding_outcome(
    world: WorldModelSurface,
    outcome: GroundingOutcome,
    *,
    entity_type: str = "object",
    entity_id_for: Callable[[GroundingAssociation], str] | None = None,
) -> AdmitSummary:
    """Admit a grounding outcome into the world model. Returns a summary."""
    result: GroundingResult = outcome.result
    if not result.success or result.no_object:
        return AdmitSummary(created=0, updates=0, candidates=0)

    created = 0
    updated_entities: set[str] = set()
    candidates = 0

    for assoc in outcome.associations:
        obs = assoc.observation
        if assoc.status == "associated" and assoc.track_id is not None:
            entity_id = entity_id_for(assoc) if entity_id_for is not None else f"track-{assoc.track_id}"
            if world.resolve(entity_id) is None:
                world.add_entity(
                    entity_id,
                    entity_type,
                    labels=[obs.label],
                    epistemic_status=OBSERVED,
                    confidence=1.0,
                    provenance=_provenance(obs),
                    created_at=obs.timestamp,
                )
                created += 1
            for field, value in _state_values(obs).items():
                world.update_entity_state(
                    entity_id,
                    field,
                    value,
                    epistemic_status=OBSERVED,
                    confidence=1.0,
                    source="locate_anything",
                    timestamp=obs.timestamp,
                )
            updated_entities.add(entity_id)
        else:
            entity_id = f"la-{obs.observation_id}"
            world.add_entity(
                entity_id,
                entity_type,
                labels=[obs.label],
                epistemic_status=HYPOTHESIZED,
                confidence=0.5,
                provenance=_provenance(obs),
                created_at=obs.timestamp,
            )
            candidates += 1
            for field, value in _state_values(obs).items():
                world.update_entity_state(
                    entity_id,
                    field,
                    value,
                    epistemic_status=HYPOTHESIZED,
                    confidence=0.5,
                    source="locate_anything",
                    timestamp=obs.timestamp,
                )

    return AdmitSummary(created=created, updates=len(updated_entities), candidates=candidates)
