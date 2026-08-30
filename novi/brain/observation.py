"""Canonical observation contract (plan 22, Phase 1, Task 1.1).

Every perception result — camera tracks, face/speaker identity, grounding
outcomes — normalizes into one :class:`Observation` shape so the brain's
world model, memory, attention and dialogue policy all consume the same
evidence vocabulary.

Epistemic discipline (plan §2.5): a recognition result is evidence, never an
absolute fact. Every observation carries confidence, uncertainty (sigma),
provenance, timestamp and an epistemic status. Fusion (Task 1.3) may combine
independent observations into higher confidence / lower uncertainty but must
never manufacture certainty.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

EPISTEMIC_OBSERVED = "OBSERVED"
EPISTEMIC_UNKNOWN = "UNKNOWN"
EPISTEMIC_INFERRED = "INFERRED"
EPISTEMIC_FUSED = "FUSED"
EPISTEMIC_HYPOTHETICAL = "HYPOTHETICAL"

_EPISTEMIC_STATUSES = frozenset(
    {
        EPISTEMIC_OBSERVED,
        EPISTEMIC_UNKNOWN,
        EPISTEMIC_INFERRED,
        EPISTEMIC_FUSED,
        EPISTEMIC_HYPOTHETICAL,
    }
)

# Fusion never crosses this ceiling without stronger evidence (Task 1.3).
_FUSION_CEILING = 0.995


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_observation_id() -> str:
    return f"obs-{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True)
class Observation:
    """One normalized perception result."""

    observation_id: str
    timestamp: str
    source: str
    modality: str
    entity_candidate: str
    attributes: dict[str, Any] = field(default_factory=dict)
    location: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    uncertainty: float = 1.0  # sigma ∈ [0, 1]; 0 = certain
    provenance: str = ""
    epistemic_status: str = EPISTEMIC_OBSERVED
    identity_candidate: str = ""
    entity_id: str | None = None  # stable identity (e.g. track-3) when known

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "timestamp": self.timestamp,
            "source": self.source,
            "modality": self.modality,
            "entity_candidate": self.entity_candidate,
            "identity_candidate": self.identity_candidate,
            "attributes": dict(self.attributes),
            "location": dict(self.location),
            "confidence": round(self.confidence, 4),
            "uncertainty": round(self.uncertainty, 4),
            "provenance": self.provenance,
            "epistemic_status": self.epistemic_status,
            "entity_id": self.entity_id,
        }

    def with_epistemic_status(self, status: str) -> "Observation":
        return Observation(
            observation_id=self.observation_id,
            timestamp=self.timestamp,
            source=self.source,
            modality=self.modality,
            entity_candidate=self.entity_candidate,
            attributes=self.attributes,
            location=self.location,
            confidence=self.confidence,
            uncertainty=self.uncertainty,
            provenance=self.provenance,
            epistemic_status=status,
            identity_candidate=self.identity_candidate,
            entity_id=self.entity_id,
        )


def make_observation(
    *,
    source: str,
    modality: str,
    entity_candidate: str,
    confidence: float,
    provenance: str,
    timestamp: str | None = None,
    attributes: dict[str, Any] | None = None,
    location: dict[str, Any] | None = None,
    epistemic_status: str = EPISTEMIC_OBSERVED,
    identity_candidate: str = "",
    entity_id: str | None = None,
    uncertainty: float | None = None,
) -> Observation:
    """Factory with defaults; validates epistemic status and clamps confidence."""
    if epistemic_status not in _EPISTEMIC_STATUSES:
        raise ValueError(f"invalid epistemic status: {epistemic_status!r}")
    conf = _clamp01(confidence)
    return Observation(
        observation_id=new_observation_id(),
        timestamp=timestamp or utc_now_iso(),
        source=source,
        modality=modality,
        entity_candidate=entity_candidate,
        attributes=dict(attributes or {}),
        location=dict(location or {}),
        confidence=conf,
        uncertainty=_clamp01(uncertainty if uncertainty is not None else 1.0 - conf),
        provenance=provenance,
        epistemic_status=epistemic_status,
        identity_candidate=identity_candidate,
        entity_id=entity_id,
    )


def observation_from_world_observation(wo: Any) -> list[Observation]:
    """Normalize a perception-pipeline WorldObservation (tracks) into Observations.

    Accepts any object exposing ``frame_id`` and ``tracks`` (each track with
    ``track_id``, ``label``, ``last_confidence``). Track-stable entity ids
    (`track-<id>`) carry identity across frames (plan 20 admission rule).
    """
    observations: list[Observation] = []
    frame_id = getattr(wo, "frame_id", "frame")
    captured_at = getattr(wo, "captured_at", None) or utc_now_iso()
    for track in getattr(wo, "tracks", []) or []:
        confidence = _clamp01(getattr(track, "last_confidence", 0.0))
        status = EPISTEMIC_OBSERVED if confidence >= 0.5 else EPISTEMIC_UNKNOWN
        observations.append(
            Observation(
                observation_id=new_observation_id(),
                timestamp=captured_at,
                source=str(frame_id),
                modality="vision",
                entity_candidate=str(getattr(track, "label", "unknown")),
                attributes={"bbox_px": list(getattr(track, "bbox", ()))},
                location={},
                confidence=confidence,
                uncertainty=1.0 - confidence,
                provenance=f"frame:{frame_id}",
                epistemic_status=status,
                entity_id=f"track-{getattr(track, 'track_id', '?')}",
            )
        )
    return observations


def observation_from_grounding(g: Any) -> Observation:
    """Normalize a grounding outcome (GroundingObservation/PointObservation).

    Grounding outcomes are hypothetical candidates until the world model
    admits them: they can never overwrite observed state (plan §2.5).
    """
    confidence = _clamp01(getattr(g, "confidence", None) or 0.0)
    return Observation(
        observation_id=getattr(g, "observation_id", None) or new_observation_id(),
        timestamp=getattr(g, "timestamp", None) or utc_now_iso(),
        source=str(getattr(g, "frame_id", "grounding")),
        modality="grounding",
        entity_candidate=str(getattr(g, "label", "unknown")),
        attributes={"query": getattr(g, "query", "")},
        location=dict(getattr(g, "location", {}) or {}),
        confidence=confidence,
        uncertainty=1.0 - confidence,
        provenance=str(getattr(g, "provenance", "grounding")),
        epistemic_status=EPISTEMIC_HYPOTHETICAL,
        entity_id=getattr(g, "entity_id", None),
    )


def fuse_observations(a: Observation, b: Observation) -> Observation | None:
    """Combine two independent observations of the same candidate (Task 1.3).

    Rules:
    - entity candidates must agree (a conflict is preserved, not smoothed away);
    - provenance must differ (duplicates are not independent evidence);
    - confidence combines by noisy-or but is capped below certainty;
    - uncertainty shrinks with agreement but never reaches 0.
    """
    if a.entity_candidate != b.entity_candidate:
        return None
    if a.identity_candidate and b.identity_candidate and a.identity_candidate != b.identity_candidate:
        return None
    if a.provenance == b.provenance and a.source == b.source:
        return None
    ca, cb = a.confidence, b.confidence
    fused_conf = min(_FUSION_CEILING, 1.0 - (1.0 - ca) * (1.0 - cb))
    fused_sigma = min(a.uncertainty, b.uncertainty) * (1.0 - 0.5 * min(ca, cb))
    return Observation(
        observation_id=new_observation_id(),
        timestamp=utc_now_iso(),
        source=f"{a.source}+{b.source}",
        modality=f"{a.modality}+{b.modality}",
        entity_candidate=a.entity_candidate,
        attributes={**a.attributes, **b.attributes},
        location=a.location or b.location,
        confidence=fused_conf,
        uncertainty=fused_sigma,
        provenance=f"{a.provenance}+{b.provenance}",
        epistemic_status=EPISTEMIC_FUSED,
        identity_candidate=a.identity_candidate or b.identity_candidate,
        entity_id=a.entity_id or b.entity_id,
    )


# World-model entity types (mirrors novi.brain.world_model constants).
_WM_PERSON = "person"
_WM_PLACE = "place"
_WM_BUILDING = "building"
_WM_OBJECT = "object"


def apply_observation_to_world(
    world: Any,
    obs: Observation,
    *,
    source: str,
    timestamp: str | None = None,
    allow_hypothetical: bool = False,
) -> str | None:
    """Admit one canonical Observation into the unified WorldModel.

    Preserves the plan-20/21 admission semantics exactly: track-stable entity
    ids; OBSERVED when confidence >= 0.5 else UNKNOWN; labels merge (never
    fork); ``presence`` + ``bbox_px`` state fields carry the measurement sigma.
    Additionally (plan 22 Task 1.4) an observation with a metric ``location``
    attaches a ``spatial_ref`` to the entity.

    Hypothetical observations (grounding candidates) are admitted only with
    ``allow_hypothetical=True`` — the explicit grounding path owns that; the
    camera path never lets candidates overwrite observed state (§2.5).

    Returns the admitted entity id, or None when the observation cannot be
    admitted (no stable entity_id, or hypothetical without permission).
    """
    from .kgraph import infer_entity_type

    if obs.epistemic_status == EPISTEMIC_HYPOTHETICAL and not allow_hypothetical:
        return None
    entity_id = obs.entity_id
    if not entity_id:
        return None
    now = timestamp or obs.timestamp or utc_now_iso()
    entity_type = infer_entity_type(obs.entity_candidate)
    wm_type = {
        "person": _WM_PERSON,
        "place": _WM_PLACE,
        "building": _WM_BUILDING,
    }.get(entity_type, _WM_OBJECT)
    confident = obs.confidence >= 0.5
    status = EPISTEMIC_OBSERVED if confident else EPISTEMIC_UNKNOWN

    existing = world.resolve(entity_id)
    if existing is None:
        world.add_entity(
            entity_id,
            wm_type,
            labels=[obs.entity_candidate],
            epistemic_status=status,
            confidence=obs.confidence,
            created_at=now,
        )
    elif obs.entity_candidate not in existing.labels:
        # Same physical object under a refined label: merge, never fork.
        world.add_entity(entity_id, wm_type, labels=[obs.entity_candidate])
    world.update_entity_state(
        entity_id,
        "presence",
        "present",
        epistemic_status=status,
        confidence=obs.confidence,
        source=source,
        timestamp=now,
        sigma=obs.uncertainty,
    )
    bbox = obs.attributes.get("bbox_px")
    if bbox:
        world.update_entity_state(
            entity_id,
            "bbox_px",
            list(bbox),
            epistemic_status=status,
            confidence=obs.confidence,
            source=source,
            timestamp=now,
            sigma=obs.uncertainty,
        )
    if obs.location:
        setter = getattr(world, "set_entity_spatial_ref", None)
        if setter is not None:
            setter(entity_id, dict(obs.location))
    return entity_id
