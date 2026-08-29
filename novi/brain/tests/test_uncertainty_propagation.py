"""Phase 1b (north-star gap analysis): uncertainty propagates end-to-end.

docs/audits/NOVI_NORTH_STAR_GAP_ANALYSIS_2026-08-29.md §4 Phase 1b:
"Add σ to WorldEntity.state/WorldRelation, combine in quadrature on fusion,
expose in uncertainty_summary()."

Acceptance:
- fusing two observations yields σ smaller than either input (inverse-variance
  quadrature combine);
- uncertainty_summary() reports per-field σ for every entity/state field.
"""

from __future__ import annotations

import unittest

from novi.brain.fusion import ModalityObservation, MultimodalFusion, fuse_uncertainty
from novi.brain.world_model import HYPOTHESIZED, OBJECT, OBSERVED, WorldModel, WorldRelation


def _now(cycle: str) -> str:
    return f"2026-08-29T12:00:0{cycle}Z"


class WorldModelSigmaTests(unittest.TestCase):
    def test_update_entity_state_stores_sigma(self):
        world = WorldModel()
        world.add_entity("e1", OBJECT, labels=["cup"], epistemic_status=OBSERVED, confidence=0.9)
        ok = world.update_entity_state(
            "e1", "presence", "present", epistemic_status=OBSERVED,
            confidence=0.9, source="cam", timestamp=_now(0), sigma=0.08,
        )
        self.assertTrue(ok)
        entity = world.get_entity("e1")
        self.assertAlmostEqual(entity.state_sigma("presence"), 0.08)

    def test_sigma_defaults_to_one_minus_confidence(self):
        world = WorldModel()
        world.add_entity("e1", OBJECT, labels=["cup"], epistemic_status=OBSERVED, confidence=0.75)
        world.update_entity_state(
            "e1", "presence", "present", epistemic_status=OBSERVED,
            confidence=0.75, source="cam", timestamp=_now(0),
        )
        entity = world.get_entity("e1")
        self.assertAlmostEqual(entity.state_sigma("presence"), 0.25)

    def test_uncertainty_summary_reports_per_field_sigma(self):
        world = WorldModel()
        world.add_entity("e1", OBJECT, labels=["cup"], epistemic_status=OBSERVED)
        world.update_entity_state("e1", "presence", "present", epistemic_status=OBSERVED,
                                  confidence=0.9, source="cam", timestamp=_now(0), sigma=0.1)
        world.update_entity_state("e1", "location", "kitchen", epistemic_status=OBSERVED,
                                  confidence=0.8, source="cam", timestamp=_now(0), sigma=0.2)
        world.add_entity("e2", OBJECT, labels=["box"], epistemic_status=OBSERVED)
        world.update_entity_state("e2", "presence", "present", epistemic_status=OBSERVED,
                                  confidence=0.5, source="cam", timestamp=_now(0), sigma=0.5)
        summary = world.uncertainty_summary()
        self.assertIn("field_sigmas", summary)
        self.assertAlmostEqual(summary["field_sigmas"]["e1"]["presence"], 0.1)
        self.assertAlmostEqual(summary["field_sigmas"]["e1"]["location"], 0.2)
        self.assertAlmostEqual(summary["field_sigmas"]["e2"]["presence"], 0.5)

    def test_relation_carries_sigma(self):
        relation = WorldRelation(
            relation_id="r1", subject_id="e1", relation_type="near", object_id="e2",
            epistemic_status=OBSERVED, confidence=0.7, sigma=0.3,
        )
        snap = relation.snapshot()
        self.assertIn("sigma", snap)
        self.assertAlmostEqual(snap["sigma"], 0.3)

    def test_entity_snapshot_includes_sigma(self):
        world = WorldModel()
        world.add_entity("e1", OBJECT, labels=["cup"], epistemic_status=OBSERVED)
        world.update_entity_state("e1", "presence", "present", epistemic_status=OBSERVED,
                                  confidence=0.9, source="cam", timestamp=_now(0), sigma=0.1)
        snap = world.get_entity("e1").snapshot()
        self.assertAlmostEqual(snap["state"]["presence"]["sigma"], 0.1)

    def test_hypothetical_never_overwrites_sigma_that_is_real(self):
        world = WorldModel()
        world.add_entity("e1", OBJECT, labels=["cup"], epistemic_status=OBSERVED)
        world.update_entity_state("e1", "presence", "present", epistemic_status=OBSERVED,
                                  confidence=0.95, source="cam", timestamp=_now(0), sigma=0.05)
        # A hypothetical proposal does not overwrite the observed sigma.
        world.update_entity_state("e1", "presence", "maybe", epistemic_status=HYPOTHESIZED,
                                  confidence=0.4, source="guess", timestamp=_now(1), sigma=0.9)
        entity = world.get_entity("e1")
        self.assertEqual(entity.state_status("presence"), "OBSERVED")
        self.assertAlmostEqual(entity.state_sigma("presence"), 0.05)


class FusionSigmaTests(unittest.TestCase):
    def test_fusing_two_observations_yields_smaller_sigma(self):
        sigma = fuse_uncertainty([0.6, 0.4])
        self.assertLess(sigma, 0.6)
        self.assertLess(sigma, 0.4)
        # Inverse-variance quadrature: 1/sqrt(1/0.6^2 + 1/0.4^2) ~= 0.3336
        self.assertAlmostEqual(sigma, 1.0 / ((1 / 0.6**2 + 1 / 0.4**2) ** 0.5), places=3)

    def test_perfect_observation_dominates(self):
        self.assertAlmostEqual(fuse_uncertainty([0.0, 0.5]), 0.0)

    def test_single_sigma_is_itself(self):
        self.assertAlmostEqual(fuse_uncertainty([0.3]), 0.3)

    def test_fused_event_carries_sigma(self):
        fusion = MultimodalFusion()
        events = fusion.ingest([
            ModalityObservation(modality="vision", entity="cup", value="present",
                                confidence=0.9, captured_at="t1", received_at="t1",
                                source="cam", sigma=0.6),
            ModalityObservation(modality="audio", entity="cup", value="present",
                                confidence=0.8, captured_at="t1", received_at="t1",
                                source="mic", sigma=0.4),
        ])
        self.assertEqual(len(events), 1)
        fused = events[0]
        self.assertLess(fused.value_sigma, 0.6)
        self.assertLess(fused.value_sigma, 0.4)
        snap = fused.snapshot()
        self.assertIn("value_sigma", snap)

    def test_sigma_derived_from_confidence_when_absent(self):
        fusion = MultimodalFusion()
        events = fusion.ingest([
            ModalityObservation(modality="vision", entity="cup", value="present",
                                confidence=0.8, captured_at="t1", received_at="t1", source="cam"),
        ])
        # No explicit sigma: derive it honestly as 1 - confidence.
        self.assertAlmostEqual(events[0].value_sigma, 0.2)


class EngineSigmaTests(unittest.TestCase):
    def test_vision_pipeline_world_observation_propagates_field_sigma(self):
        from novi.brain.b2_perception import SpecialistPerception
        from novi.brain.engine import MacBrain, MacBrainConfig
        from novi.perception.detection import DeterministicObjectDetector
        from novi.perception.pipeline import PerceptionPipeline

        class Camera:
            def __init__(self) -> None:
                self.seq = 0

            def close(self) -> None:
                self.seq = self.seq

            def read(self) -> CameraFrame:
                self.seq += 1
                return CameraFrame(frame_id=f"f-{self.seq}", captured_at="2026-08-29T12:00:00Z",
                                   width=640, height=480, payload=b"x", metadata={})

        from novi.brain.io import CameraFrame

        pipeline = PerceptionPipeline(detector=DeterministicObjectDetector(scripted={
            "f-1": [("cup", 0.8, (10, 10, 50, 50))],
        }))
        brain = MacBrain(
            camera=Camera(),
            perception=SpecialistPerception(),
            perception_pipeline=pipeline,
            config=MacBrainConfig(curiosity_enabled=False),
        )
        brain.start()
        try:
            brain.step()
            entity = brain.unified_world.get_entity("track-1")
            self.assertIsNotNone(entity)
            # σ is derived and reported per field (1 - confidence = 0.2).
            self.assertAlmostEqual(entity.state_sigma("presence"), 0.2)
            self.assertAlmostEqual(brain.unified_world.uncertainty_summary()["field_sigmas"]["track-1"]["presence"], 0.2)
        finally:
            brain.stop()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
