"""Tests for canonical observation admission into the world model.

Plan 22 Phase 1 Tasks 1.2–1.4:
- a scripted frame through MacBrain.step() creates an OBSERVED person/object
  entity in the world model consumed by cognition and dialogue (1.2);
- confidence/uncertainty (sigma) propagate into world state (1.3);
- persistent entities carry a spatial_ref from metric observation locations
  (1.4).
"""

from __future__ import annotations

import unittest

from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.observation import (
    EPISTEMIC_HYPOTHETICAL,
    EPISTEMIC_OBSERVED,
    EPISTEMIC_UNKNOWN,
    apply_observation_to_world,
    make_observation,
)
from novi.brain.world_model import WorldModel


class ApplyObservationToWorldTest(unittest.TestCase):
    def setUp(self) -> None:
        self.world = WorldModel()

    def _obs(self, candidate="mug", confidence=0.85, entity_id="track-1", **kw):
        return make_observation(
            source="f-1",
            modality="vision",
            entity_candidate=candidate,
            confidence=confidence,
            provenance="frame:f-1",
            entity_id=entity_id,
            **kw,
        )

    def test_creates_observed_entity_with_sigma(self) -> None:
        obs = self._obs(confidence=0.85, attributes={"bbox_px": [0, 0, 10, 10]})
        entity_id = apply_observation_to_world(self.world, obs, source="cam")
        self.assertEqual(entity_id, "track-1")
        entity = self.world.resolve("track-1")
        self.assertIsNotNone(entity)
        assert entity is not None
        self.assertEqual(entity.entity_type, "object")
        self.assertEqual(entity.epistemic_status, EPISTEMIC_OBSERVED)
        self.assertEqual(entity.state_value("presence"), "present")
        # Task 1.3: measurement uncertainty propagates (sigma = 1 - confidence).
        sigma = entity.state_sigma("presence")
        self.assertIsNotNone(sigma)
        self.assertAlmostEqual(sigma or 0.0, 0.15)
        self.assertEqual(list(entity.state_value("bbox_px")), [0, 0, 10, 10])

    def test_person_candidate_gets_person_type(self) -> None:
        obs = self._obs(candidate="vano", confidence=0.97)
        apply_observation_to_world(self.world, obs, source="cam")
        self.assertEqual(self.world.resolve("track-1").entity_type, "person")  # type: ignore[union-attr]

    def test_low_confidence_is_unknown_not_observed(self) -> None:
        obs = self._obs(confidence=0.3)
        apply_observation_to_world(self.world, obs, source="cam")
        entity = self.world.resolve("track-1")
        self.assertEqual(entity.epistemic_status, EPISTEMIC_UNKNOWN)  # type: ignore[union-attr]

    def test_label_merges_never_forks(self) -> None:
        apply_observation_to_world(self.world, self._obs(candidate="mug"), source="cam")
        apply_observation_to_world(self.world, self._obs(candidate="coffee mug"), source="cam")
        entity = self.world.resolve("track-1")
        self.assertEqual(entity.labels, ["mug", "coffee mug"])  # type: ignore[union-attr]

    def test_metric_location_sets_spatial_ref(self) -> None:
        obs = self._obs(location={"frame": "camera", "x": 1.2, "y": 0.4})
        apply_observation_to_world(self.world, obs, source="cam")
        entity = self.world.resolve("track-1")
        self.assertEqual(entity.spatial_ref, {"frame": "camera", "x": 1.2, "y": 0.4})  # type: ignore[union-attr]

    def test_hypothetical_rejected_unless_allowed(self) -> None:
        obs = self._obs(epistemic_status=EPISTEMIC_HYPOTHETICAL, confidence=0.9)
        self.assertIsNone(apply_observation_to_world(self.world, obs, source="cam"))
        self.assertIsNone(self.world.resolve("track-1"))
        # The explicit grounding path may admit candidates (never overwriting
        # observed state — that rule lives in WorldModel.update_entity_state).
        entity_id = apply_observation_to_world(
            self.world, obs, source="cam", allow_hypothetical=True
        )
        self.assertEqual(entity_id, "track-1")
        self.assertIsNotNone(self.world.resolve("track-1"))

    def test_observation_without_entity_id_not_admitted(self) -> None:
        obs = make_observation(
            source="s", modality="vision", entity_candidate="x",
            confidence=0.9, provenance="p",
        )
        self.assertIsNone(apply_observation_to_world(self.world, obs, source="cam"))


class EngineCanonicalObservationAcceptanceTest(unittest.TestCase):
    """Task 1.2 acceptance: a scripted frame through MacBrain.step() creates an
    OBSERVED entity in the world model consumed by cognition and dialogue."""

    def test_scripted_pipeline_frame_creates_observed_entity_with_sigma(self) -> None:
        from novi.brain.b2_perception import DeterministicPerceptionBackend, SpecialistPerception
        from novi.brain.io import CameraFrame
        from novi.brain.tests.test_mac_brain import FakeCamera
        from novi.perception.detection import DeterministicObjectDetector
        from novi.perception.pipeline import PerceptionPipeline

        class ScriptedCamera(FakeCamera):
            def read(self):
                self.sequence += 1
                return CameraFrame(
                    frame_id=f"f-{self.sequence}",
                    captured_at="2026-08-30T12:00:00Z",
                    width=640,
                    height=480,
                    payload=b"frame",
                    metadata={"backend": "test"},
                )

        detector = DeterministicObjectDetector(
            scripted={"f-1": [("mug", 0.85, (10, 10, 300, 300))]}
        )
        pipeline = PerceptionPipeline(detector=detector)
        brain = MacBrain(
            camera=ScriptedCamera(),
            perception=SpecialistPerception(DeterministicPerceptionBackend()),
            config=MacBrainConfig(curiosity_enabled=False, perception_every_n_cycles=1),
        )
        brain.perception_pipeline = pipeline
        brain.start()
        try:
            brain.step()
            # Track-stable entity admitted into the unified world model.
            entity = brain.unified_world.resolve("track-1")
            self.assertIsNotNone(entity)
            assert entity is not None
            self.assertEqual(entity.entity_type, "object")
            self.assertEqual(entity.epistemic_status, EPISTEMIC_OBSERVED)
            # Task 1.3: sigma present on the admitted state.
            sigma = entity.state_sigma("presence")
            self.assertIsNotNone(sigma)
            self.assertAlmostEqual(sigma or 0.0, 0.15)
            # Task 1.2: the same world model is consumed by dialogue context.
            ctx = brain._assemble_world_context("what do you see?", person="")
            self.assertIsInstance(ctx, dict)
            self.assertGreater(len(ctx.get("visible_entities", [])), 0)
        finally:
            brain.stop()


if __name__ == "__main__":
    unittest.main()
