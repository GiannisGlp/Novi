"""Phase 1a (north-star gap analysis): vision pipeline wired into the engine.

docs/audits/NOVI_NORTH_STAR_GAP_ANALYSIS_2026-08-29.md §4 Phase 1a:
"Make PerceptionPipeline.process_frame/ground_frame the brain's perception
path, feeding WorldObservation/GroundingOutcome into WorldModel via the
already-built world_state_adapter.admit_grounding_outcome. Replace/augment
legacy _update_unified_world."

Acceptance:
- a MacBrain.step() run with a scripted pipeline produces OBSERVED
  world-model entities (track-stable ids) and HYPOTHESIZED candidates
  surfaced by context_assembler.assemble;
- grounding stays explicit (fail-closed without pipeline/backend/frame);
- the pipeline detections become the cycle's evidence for downstream
  consumers (memory admission, curiosity spawning).
"""

from __future__ import annotations

import unittest

from novi.brain.b2_perception import SpecialistPerception
from novi.brain.context_assembler import ContextRequest
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.io import CameraFrame
from novi.perception.detection import DeterministicObjectDetector
from novi.perception.grounding import (
    GroundingObservation,
    GroundingResult,
    SpatialInferenceMode,
    source_box_to_pixel_box,
)
from novi.perception.pipeline import PerceptionPipeline

W, H = 640, 480


class ScriptedFrameCamera:
    """Camera yielding 640x480 frames with unique provenance-carrying ids."""

    def __init__(self) -> None:
        self.sequence = 0
        self.closed = False

    def close(self) -> None:
        self.closed = True

    def read(self) -> CameraFrame:
        self.sequence += 1
        return CameraFrame(
            frame_id=f"f-{self.sequence}",
            captured_at="2026-08-29T12:00:00Z",
            width=W,
            height=H,
            payload=b"frame",
            metadata={"backend": "test"},
        )


class ScriptedSpatialBackend:
    """Scripted SpatialPerceptionBackend returning validated observations."""

    def __init__(self, observations: tuple[GroundingObservation, ...]) -> None:
        self._observations = observations

    def ground(self, frame, query, policy) -> GroundingResult:
        return GroundingResult(
            query=query.text,
            observations=tuple(self._observations),
            backend_status="ok",
            model_id="fake-grounding",
            model_revision="1",
            backend_version="0.1.0",
            inference_mode=policy.mode,
            frame_id=frame.frame_id,
            timestamp=query.timestamp,
            latency_ms=1.0,
            success=True,
        )


def _obs(observation_id: str, label: str, box: tuple[int, int, int, int]) -> tuple[GroundingObservation, tuple[int, int, int, int]]:
    """GroundingObservation from a pixel (x, y, w, h) box (mirrors the
    world-state adapter tests' canonical [0,1000] source-box construction),
    plus the canonical pixel box it converts back to."""
    source = (
        int(box[0] * 1000 / W),
        int(box[1] * 1000 / H),
        int((box[0] + box[2]) * 1000 / W),
        int((box[1] + box[3]) * 1000 / H),
    )
    return (
        GroundingObservation(
            observation_id=observation_id,
            query="the object",
            label=label,
            source_box=source,
            image_width=W,
            image_height=H,
            model_id="fake-grounding",
            model_revision="1",
            backend_version="0.1.0",
            inference_mode=SpatialInferenceMode.HYBRID,
            frame_id="f-1",
            timestamp="2026-08-29T12:00:01Z",
        ),
        source_box_to_pixel_box(*source, W, H),
    )


_CUP_FRAMES = {
    "f-1": [("cup", 0.9, (10, 10, 50, 50))],
    "f-2": [("cup", 0.95, (10, 10, 50, 50))],
}


def _pipeline(grounding_observations: tuple[GroundingObservation, ...] = ()) -> PerceptionPipeline:
    return PerceptionPipeline(
        detector=DeterministicObjectDetector(scripted=_CUP_FRAMES),
        grounding_backend=ScriptedSpatialBackend(grounding_observations) if grounding_observations else None,
    )


def _brain(pipeline: PerceptionPipeline | None, *, config: MacBrainConfig | None = None) -> MacBrain:
    return MacBrain(
        camera=ScriptedFrameCamera(),
        perception=SpecialistPerception(),
        perception_pipeline=pipeline,
        config=config or MacBrainConfig(curiosity_enabled=False),
    )


class TrackStableAdmissionTests(unittest.TestCase):
    """process_frame feeds the unified world model with track-stable entities."""

    def test_step_produces_observed_track_entity(self):
        brain = _brain(_pipeline())
        brain.start()
        try:
            result1 = brain.step()
            self.assertEqual(result1["detections"], ["cup"])
            track = brain.unified_world.get_entity("track-1")
            self.assertIsNotNone(track, "first frame should admit the track entity")
            self.assertEqual(track.epistemic_status, "OBSERVED")
            self.assertEqual(track.state_value("presence"), "present")
            self.assertEqual(track.state_value("bbox_px"), [10, 10, 50, 50])
            self.assertIn("cup", track.labels)
            # Legacy per-cycle det: ids must not appear for pipeline cycles.
            self.assertIsNone(brain.unified_world.get_entity("det:cup:1"))

            result2 = brain.step()
            self.assertEqual(result2["detections"], ["cup"])
            track = brain.unified_world.get_entity("track-1")
            self.assertIsNotNone(track)
            self.assertEqual(track.epistemic_status, "OBSERVED")
            self.assertEqual(track.state_value("bbox_px"), [10, 10, 50, 50])
            # Track-stable: no entity was re-created per cycle.
            self.assertIsNone(brain.unified_world.get_entity("det:cup:2"))
        finally:
            brain.stop()

    def test_no_entity_without_pipeline(self):
        brain = _brain(None)
        brain.start()
        try:
            brain.step()
            self.assertIsNone(brain.unified_world.get_entity("track-1"))
        finally:
            brain.stop()


class GroundingAdmissionTests(unittest.TestCase):
    """ground_frame -> admit_grounding_outcome -> OBSERVED/HYPOTHESIZED."""

    def test_ground_scene_fails_closed_without_pipeline(self):
        brain = _brain(None)
        brain.start()
        try:
            out = brain.ground_scene("the cup")
            self.assertFalse(out["grounded"])
            self.assertEqual(out["reason"], "no_vision_pipeline")
        finally:
            brain.stop()

    def test_ground_scene_without_grounding_backend_fails_closed(self):
        brain = _brain(_pipeline())
        brain.start()
        try:
            brain.step()
            out = brain.ground_scene("the cup")
            self.assertFalse(out["grounded"])
            self.assertEqual(out["reason"], "no_grounding_backend")
        finally:
            brain.stop()

    def test_ground_scene_before_any_step_fails_closed(self):
        pipeline = PerceptionPipeline(
            detector=DeterministicObjectDetector(scripted={}),
            grounding_backend=ScriptedSpatialBackend(()),
        )
        brain = _brain(pipeline)
        brain.start()
        try:
            out = brain.ground_scene("anything")
            self.assertFalse(out["grounded"])
            self.assertEqual(out["reason"], "no_frame")
        finally:
            brain.stop()

    def test_ground_scene_admits_associated_and_candidate(self):
        _obs_a, expected_px = _obs("o1", "red mug", (12, 12, 46, 46))
        _obs_b, _ = _obs("o2", "mystery blob", (400, 300, 40, 40))
        brain = _brain(_pipeline((_obs_a, _obs_b)))
        brain.start()
        try:
            brain.step()
            brain.step()
            out = brain.ground_scene("the mug")
            self.assertTrue(out["grounded"])
            self.assertEqual(out["updated"], 1, "the associated observation updates track-1")
            self.assertEqual(out["candidates"], 1, "the unmatched observation becomes a candidate")

            track = brain.unified_world.get_entity("track-1")
            self.assertEqual(track.state_status("bbox_px"), "OBSERVED")
            self.assertEqual(tuple(track.state_value("bbox_px")), expected_px)
            candidate = brain.unified_world.get_entity("la-o2")
            self.assertIsNotNone(candidate)
            self.assertEqual(candidate.epistemic_status, "HYPOTHESIZED")
            self.assertEqual(candidate.confidence, 0.5)
        finally:
            brain.stop()


class ContextSurfacingTests(unittest.TestCase):
    """Acceptance: OBSERVED entities and HYPOTHESIZED candidates are surfaced
    by context_assembler.assemble."""

    def test_assemble_surfaces_observed_and_hypothesized(self):
        obs_a, _ = _obs("o1", "red mug", (12, 12, 46, 46))
        obs_b, _ = _obs("o2", "mystery blob", (400, 300, 40, 40))
        brain = _brain(_pipeline((obs_a, obs_b)))
        brain.start()
        try:
            brain.step()
            brain.step()
            brain.ground_scene("the mug")
            package = brain.context_assembler.assemble(brain.unified_world, ContextRequest())
            statuses: dict[str, str] = {}
            for item in package.items:
                if item.kind == "entity" and isinstance(item.data, dict) and item.data.get("entity_id"):
                    statuses[item.data["entity_id"]] = item.epistemic_status
            self.assertEqual(statuses.get("track-1"), "OBSERVED")
            self.assertEqual(statuses.get("la-o2"), "HYPOTHESIZED")
        finally:
            brain.stop()


class InvestigateGoalGroundingTests(unittest.TestCase):
    """The loop closure: a curiosity investigate goal explicitly grounds its
    target against the current frame (grounding never runs implicitly)."""

    def test_investigate_goal_grounds_its_target_in_step(self):
        _obs_a, _ = _obs("o1", "red mug", (12, 12, 46, 46))
        brain = _brain(_pipeline((_obs_a,)), config=MacBrainConfig())
        brain.start()
        try:
            result = brain.step()
            # Curiosity spawned an investigate goal for the novel "cup" detection
            # and the goal's target was grounded in the same cycle.
            self.assertIsNotNone(brain.goals.active)
            self.assertEqual(brain.goals.active.goal.kind, "investigate")
            self.assertEqual(brain.goals.active.goal.target, "cup")
            self.assertIsNotNone(result.get("grounding"))
            self.assertEqual(result["grounding"]["updated"], 1)
            self.assertTrue(any(e["event_type"] == "perception.grounded" for e in brain.events))
        finally:
            brain.stop()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
