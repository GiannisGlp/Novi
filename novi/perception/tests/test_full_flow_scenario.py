"""L1 — Full-flow integration scenario (plan Definition of Done, deterministic).

Drives the ENTIRE Novi chain with real brain classes read-only
(WorldModel, PredictionEngine), the real durable ObservationRecorder, and
deterministic perception backends. No model, no hardware, no network.

Beats (the plan's closed loop):
  frame -> SSDLite (low confidence) -> escalation request (cognition stand-in)
  -> ground_frame -> typed observation -> track association
  -> world-state admission (OBSERVED entity)
  -> durable memory record -> prediction (streak) -> verified / violated
  -> deliberation (ambiguous candidates) -> promotion criterion
  -> cache/dedup -> re-observation verification
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pytest

from novi.brain.io import CameraFrame
from novi.brain.prediction import PredictionEngine
from novi.brain.world_model import WorldModel
from novi.integration.observation_recorder import ObservationRecorder
from novi.integration.recognition_store import RecognitionKind
from novi.perception.active_grounding import (
    EscalationSignal,
    GroundingCache,
    GroundingEscalationPolicy,
    GroundingRequestDeduplicator,
)
from novi.perception.detection import DeterministicObjectDetector
from novi.perception.deliberation_record import build_deliberation_record
from novi.perception.grounding import SpatialInferencePolicy, SpatialQuery
from novi.perception.grounding_verification import verify_grounding_agreement
from novi.perception.locate_anything import DeterministicLocateAnythingBackend
from novi.perception.pipeline import PerceptionPipeline
from novi.perception.prediction_verification import verify_predicted_presence
from novi.perception.spatial_memory_promotion import promotion_candidate
from novi.perception.tracking import ObjectTracker
from novi.perception.world_state_adapter import admit_grounding_outcome

W, H = 640, 480
CUP_BOX = (64, 96, 512, 288)  # pixel bbox used by both detector and grounding


def _frame(fid: str) -> CameraFrame:
    return CameraFrame(frame_id=fid, captured_at=f"t-{fid}", width=W, height=H, payload=b"")


def _query(fid: str, text: str = "locate the cup") -> SpatialQuery:
    return SpatialQuery(text=text, frame_id=fid, timestamp=f"t-{fid}")


@pytest.fixture()
def recorder(tmp_path: Path) -> Iterator[ObservationRecorder]:
    r = ObservationRecorder(tmp_path / "obs.db")
    yield r
    r.close()


@pytest.fixture()
def pipeline() -> PerceptionPipeline:
    detector = DeterministicObjectDetector(
        scripted={
            "f1": [("cup", 0.62, CUP_BOX)],  # low confidence -> escalation
            "f2": [("cup", 0.88, CUP_BOX)],
            "f3": [("cup", 0.90, CUP_BOX)],
        },
        confidence_floor=0.60,
    )
    grounding = DeterministicLocateAnythingBackend(
        scripted={
            ("f1", "locate the cup"): [("cup", (100, 200, 900, 800))],
            ("f2", "locate the cup"): [
                ("cup", (100, 200, 900, 800)),
                ("cup", (700, 200, 950, 800)),  # second candidate -> ambiguity
            ],
            ("f3", "locate the cup"): [("cup", (100, 200, 900, 800))],
        }
    )
    return PerceptionPipeline(
        detector=detector,
        grounding_backend=grounding,
        tracker=ObjectTracker(min_hits=2),
    )


class TestFullFlowScenario:
    def test_closed_loop_camera_to_memory(self, pipeline, recorder):
        world = WorldModel()
        engine = PredictionEngine(min_observations=2)
        cache = GroundingCache()
        dedup = GroundingRequestDeduplicator()
        policy = GroundingEscalationPolicy()

        # -- BEAT 1: frame arrives, SSDLite is uncertain --------------------
        obs1 = pipeline.process_frame(_frame("f1"))
        cup_det = next(d for d in obs1.detections if d.label == "cup")
        assert cup_det.confidence < 0.70  # low confidence

        # -- BEAT 2: escalation (cognition stand-in) fires a budgeted query --
        signal = EscalationSignal(frame_id="f1", low_confidence_labels=("cup",))
        requests = policy.evaluate(signal)
        assert len(requests) == 1
        assert requests[0].query == "locate the cup"
        assert requests[0].budget.max_retries >= 1

        # -- BEAT 3: ground_frame -> typed observation -> track association -
        outcome1 = pipeline.ground_frame(_frame("f1"), requests[0].query and _query("f1"), SpatialInferencePolicy())
        assert outcome1.result.success
        assert len(outcome1.associations) == 1
        assoc1 = outcome1.associations[0]
        assert assoc1.status == "associated"
        assert assoc1.track_id is not None
        track_id = assoc1.track_id

        # -- BEAT 4: world-state admission (real WorldModel) ----------------
        summary1 = admit_grounding_outcome(world, outcome1)
        assert summary1.updates == 1
        entity = world.get_entity(f"track-{track_id}")
        assert entity is not None
        assert entity.epistemic_status == "OBSERVED"
        assert entity.state_value("bbox_px") == CUP_BOX
        assert entity.state_value("frame_id") == "f1"

        # -- BEAT 5: durable memory (real ObservationRecorder) --------------
        recorder.record(
            kind=RecognitionKind.OBJECT,
            entity_ref="cup",
            place="desk",
            label="cup",
            bbox=CUP_BOX,
            frame_id="f1",
            provenance={"source": "locate_anything", "model": "nvidia/LocateAnything-3B@c32291ca"},
        )
        assert recorder.count() == 1
        assert recorder.last_sighting(RecognitionKind.OBJECT, "cup") is not None

        # -- BEAT 6: prediction streak -> confirmed -------------------------
        new0, conf0, viol0 = engine.observe({"cup"}, cycle=1)
        assert new0 == [] and conf0 == [] and viol0 == []
        new1, _, _ = engine.observe({"cup"}, cycle=2)
        assert [p.entity for p in new1] == ["cup"]  # streak >= 2 -> persist prediction

        # prediction verification (my seam) agrees:
        verification = verify_predicted_presence(outcome1.result, ("cup",))
        assert verification.as_present_set() == {"cup"}
        _, confirmed, _ = engine.observe(verification.as_present_set(), cycle=3)
        assert [p.entity for p in confirmed] == ["cup"]
        assert engine.accuracy.accuracy() == 1.0

        # -- BEAT 7: prediction violated when cup vanishes ------------------
        _, _, violated = engine.observe(set(), cycle=4)
        assert [p.entity for p in violated] == ["cup"]
        assert engine.accuracy.accuracy() < 1.0

        # -- BEAT 8: ambiguous frame -> deliberation record -----------------
        pipeline.process_frame(_frame("f2"))
        outcome2 = pipeline.ground_frame(_frame("f2"), _query("f2"), SpatialInferencePolicy())
        assert len(outcome2.result.observations) == 2
        first_id = outcome2.result.observations[0].observation_id
        second_id = outcome2.result.observations[1].observation_id
        record = build_deliberation_record(
            outcome2.result,
            selected_observation_id=first_id,
            reason="closest to the desk",
        )
        assert record.outcome == "selected"
        assert record.selected == first_id
        assert record.rejected == (second_id,)

        # candidates enter world state as HYPOTHESIZED (never overwrite):
        summary2 = admit_grounding_outcome(world, outcome2)
        assert summary2.candidates == 1
        candidate = world.get_entity(f"la-{second_id}")
        assert candidate is not None and candidate.epistemic_status == "HYPOTHESIZED"

        # -- BEAT 9: stable sightings -> promotion criterion ----------------
        pipeline.process_frame(_frame("f3"))
        outcome3 = pipeline.ground_frame(_frame("f3"), _query("f3"), SpatialInferencePolicy())
        history = [
            (outcome1.associations[0].observation, track_id),
            (outcome2.associations[0].observation, track_id),
            (outcome3.associations[0].observation, track_id),
        ]
        decision = promotion_candidate(history)
        assert decision.promote

        # -- BEAT 10: cache + dedup + re-observation verification -----------
        cache.put(outcome1.result)
        assert cache.get("f1", "locate the cup", outcome1.result.inference_mode) is outcome1.result
        dedup.remember("f1", "locate the cup")
        assert dedup.is_duplicate("f1", "locate the cup")
        assert not dedup.is_duplicate("f2", "locate the cup")

        verification_result = verify_grounding_agreement(outcome1.result, outcome3.result)
        assert verification_result.verified
        assert verification_result.best_iou == 1.0

        # -- final: the world knows the cup, memory remembers it ------------
        assert world.get_entity(f"track-{track_id}").state_value("bbox_px") == CUP_BOX
        assert recorder.count() >= 1
        assert engine.accuracy.pairs()  # both a confirmed and a violated outcome
