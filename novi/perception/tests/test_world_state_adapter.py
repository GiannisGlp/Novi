"""Tests: grounding -> world-state admission adapter (plan Step 18).

The adapter converts a GroundingOutcome into world-model calls:
- ASSOCIATED observations update the existing track's entity state (observed);
- CANDIDATE observations become CANDIDATE entities with HYPOTHESIZED status
  (proposals that never overwrite observed state — epistemic discipline);
- every call carries provenance (source=locate_anything, model revision).

The adapter is protocol-based: it needs only the documented world-model
surface (add_entity / update_entity_state / resolve), so tests use a fake
and the concrete WorldModel wiring is the brain's call.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from novi.perception.grounding import (
    GroundingObservation,
    GroundingResult,
    SpatialInferenceMode,
)
from novi.perception.grounding_association import (
    GroundingAssociation,
    GroundingOutcome,
    associate_grounding_to_tracks,
)
from novi.perception.tracking import Track
from novi.perception.world_state_adapter import (
    AdmitSummary,
    admit_grounding_outcome,
)

W, H = 640, 480


@dataclass
class FakeEntity:
    entity_id: str
    entity_type: str
    labels: list[str] = field(default_factory=list)
    epistemic_status: str = "UNKNOWN"
    lifecycle: str = "candidate"
    state: dict = field(default_factory=dict)


@dataclass
class FakeWorld:
    """Scripted world model implementing the documented surface."""

    entities: dict[str, FakeEntity] = field(default_factory=dict)
    add_calls: list[dict] = field(default_factory=list)
    update_calls: list[dict] = field(default_factory=list)
    resolves: dict[str, FakeEntity] = field(default_factory=dict)

    def add_entity(self, entity_id, entity_type, *, labels=None, epistemic_status="UNKNOWN", confidence=0.0, provenance=None, created_at="", **kw):
        self.add_calls.append(dict(entity_id=entity_id, entity_type=entity_type, labels=labels, status=epistemic_status, confidence=confidence, provenance=provenance))
        e = FakeEntity(entity_id=entity_id, entity_type=entity_type, labels=list(labels or []), epistemic_status=epistemic_status)
        self.entities[entity_id] = e
        return e

    def update_entity_state(self, entity_id, field_name, value, *, epistemic_status, confidence, source, timestamp=""):
        self.update_calls.append(dict(entity_id=entity_id, field=field_name, value=value, status=epistemic_status, source=source))
        if entity_id in self.entities:
            self.entities[entity_id].state[field_name] = (value, epistemic_status, confidence)
            return True
        return False

    def resolve(self, label_or_id):
        return self.resolves.get(label_or_id)


def _obs(observation_id: str, label: str, box=(100, 100, 200, 200)) -> GroundingObservation:
    return GroundingObservation(
        observation_id=observation_id,
        query="the cup",
        label=label,
        source_box=(int(box[0] * 1000 / W), int(box[1] * 1000 / H), int((box[0] + box[2]) * 1000 / W), int((box[1] + box[3]) * 1000 / H)),
        image_width=W,
        image_height=H,
        model_id="nvidia/LocateAnything-3B",
        model_revision="c32291ca",
        backend_version="0.1.0",
        inference_mode=SpatialInferenceMode.HYBRID,
        frame_id="f1",
        timestamp="t0",
    )


def _result(*obs) -> GroundingResult:
    return GroundingResult(
        query="the cup",
        observations=tuple(obs),
        backend_status="available",
        model_id="nvidia/LocateAnything-3B",
        model_revision="c32291ca",
        backend_version="0.1.0",
        inference_mode=SpatialInferenceMode.HYBRID,
        frame_id="f1",
        timestamp="t0",
        latency_ms=1.0,
        success=True,
    )


def _track(tid: int) -> Track:
    return Track(track_id=tid, label="cup", bbox=(90, 90, 220, 220), first_frame_id="f0", last_frame_id="f1", hits=3, confirmed=True)


class TestAdmitGroundingOutcome:
    def _outcome(self, observations, tracks) -> GroundingOutcome:
        return associate_grounding_to_tracks(_result(*observations), tracks, frame_id="f1", query="the cup")

    def test_associated_observation_updates_track_entity(self):
        world = FakeWorld()
        track = _track(7)
        world.resolves["track-7"] = FakeEntity(entity_id="track-7", entity_type="object", labels=["cup"], lifecycle="active")
        outcome = self._outcome([_obs("la-f1-0", "cup")], [track])
        summary = admit_grounding_outcome(world, outcome, entity_id_for=lambda a: f"track-{a.track_id}")
        assert summary.updates == 1
        assert summary.candidates == 0
        fields = {c["field"] for c in world.update_calls}
        assert {"bbox_px", "bbox_norm", "frame_id", "query"} <= fields
        assert all(c["status"] == "OBSERVED" for c in world.update_calls)
        assert all(c["source"] == "locate_anything" for c in world.update_calls)

    def test_candidate_observation_creates_hypothetical_entity(self):
        world = FakeWorld()
        outcome = self._outcome([_obs("la-f1-0", "cup")], [])  # no tracks -> candidate
        summary = admit_grounding_outcome(world, outcome)
        assert summary.candidates == 1
        assert summary.updates == 0
        call = world.add_calls[0]
        assert call["entity_type"] == "object"
        assert call["status"] == "HYPOTHESIZED"
        assert call["entity_id"].startswith("la-")
        assert call["labels"] == ["cup"]
        assert call["provenance"] is not None
        assert call["provenance"].source == "locate_anything"
        assert call["provenance"].model_or_tool == "nvidia/LocateAnything-3B@c32291ca"

    def test_missing_associated_entity_is_created_then_updated(self):
        world = FakeWorld()
        track = _track(7)
        outcome = self._outcome([_obs("la-f1-0", "cup")], [track])
        summary = admit_grounding_outcome(world, outcome, entity_id_for=lambda a: f"track-{a.track_id}")
        assert summary.created == 1
        assert summary.updates == 1
        assert world.add_calls[0]["entity_id"] == "track-7"

    def test_no_object_result_admits_nothing(self):
        world = FakeWorld()
        result = GroundingResult(
            query="q", observations=(), backend_status="available", model_id="m", model_revision="r",
            backend_version="0.1.0", inference_mode=SpatialInferenceMode.HYBRID, frame_id="f1",
            timestamp="t0", latency_ms=1.0, success=True, no_object=True,
        )
        outcome = associate_grounding_to_tracks(result, [], frame_id="f1", query="q")
        summary = admit_grounding_outcome(world, outcome)
        assert summary == AdmitSummary(created=0, updates=0, candidates=0)

    def test_failed_result_admits_nothing(self):
        world = FakeWorld()
        result = GroundingResult(
            query="q", observations=(), backend_status="available", model_id="m", model_revision="r",
            backend_version="0.1.0", inference_mode=SpatialInferenceMode.HYBRID, frame_id="f1",
            timestamp="t0", latency_ms=1.0, success=False, validation_errors=("boom",),
        )
        outcome = associate_grounding_to_tracks(result, [], frame_id="f1", query="q")
        summary = admit_grounding_outcome(world, outcome)
        assert summary == AdmitSummary(created=0, updates=0, candidates=0)
