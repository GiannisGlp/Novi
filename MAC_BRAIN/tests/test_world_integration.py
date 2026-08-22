"""Integration tests for WorldModel/ContextAssembler/AttentionRanker runtime
wiring (PERFECTING_PLAN Step 1 done-bar).

Verifies:
  - The runtime populates the unified WorldModel from perception detections.
  - Attention candidates are emitted as events during the step cycle.
  - The context assembler grounds dialogue in the world model.
  - Epistemic status is enforced at the world boundary (predictions ≠ facts).
  - The reference-resolution scenario (NVIDIA Exp 1) passes through the runtime.
"""

import unittest

from brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception

from MAC_BRAIN.runtime import MacBrain, MacBrainConfig
from MAC_BRAIN.tests.test_mac_brain import FakeCamera
from MAC_BRAIN.world_model import OBSERVED, UNKNOWN, PERSON, OBJECT


class CupBackend(DeterministicPerceptionBackend):
    """Detects a cup on the table."""
    def detect(self, frame):
        return (Detection("cup", 0.85, (0.1, 0.1, 0.5, 0.5)),)


class PersonCupBackend(DeterministicPerceptionBackend):
    """Detects a person and a cup."""
    def detect(self, frame):
        return (
            Detection("alice", 0.95, (0.0, 0.0, 0.3, 0.5)),
            Detection("cup", 0.85, (0.4, 0.4, 0.6, 0.6)),
        )


class WorldModelRuntimeIntegrationTests(unittest.TestCase):
    def test_unified_world_populated_after_step(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.stop()
        # The cup should be in the unified world model.
        entity = brain.unified_world.resolve("cup")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.entity_type, OBJECT)
        self.assertEqual(entity.epistemic_status, OBSERVED)

    def test_attention_candidates_emitted(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(PersonCupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.stop()
        # Attention candidates should have been emitted.
        event_types = [e["event_type"] for e in brain.events]
        self.assertIn("cognition.attention", event_types)
        # The brain should have stored the last attention candidates.
        self.assertGreater(len(brain._last_attention_candidates), 0)

    def test_person_detected_gets_person_type(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(PersonCupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.stop()
        alice = brain.unified_world.resolve("alice")
        self.assertIsNotNone(alice)
        self.assertEqual(alice.entity_type, PERSON)

    def test_world_model_snapshot_available(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.stop()
        snap = brain.unified_world.snapshot()
        self.assertGreater(len(snap.entities), 0)
        self.assertGreater(snap.world_version, 0)

    def test_world_context_assembled_in_compose_reply(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        # compose_reply with no llm_chat returns early, but the world context
        # is available via _assemble_world_context.
        ctx = brain._assemble_world_context("bring me that cup", "Alice")
        self.assertIsInstance(ctx, dict)
        # The unified world has the cup.
        self.assertGreater(len(ctx.get("visible_entities", [])), 0)
        brain.stop()

    def test_reference_resolution_through_runtime(self):
        """NVIDIA Exp 1: 'Bring me that cup' resolves to the cup entity."""
        from MAC_BRAIN.context_assembler import ContextAssembler, ContextRequest

        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()

        assembler = ContextAssembler()
        request = ContextRequest(
            speaker_label="Alice",
            utterance="bring me that cup",
            referenced_labels=("cup",),
            token_budget=5000,
        )
        result = assembler.resolve_reference(brain.unified_world, request, "that cup")
        brain.stop()
        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(result["label"], "cup")


class EpistemicDisciplineIntegrationTests(unittest.TestCase):
    """Verify epistemic status is enforced at the world boundary in the runtime."""

    def test_prediction_does_not_overwrite_observation(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        # The cup is observed with confidence 0.85.
        cup = brain.unified_world.resolve("cup")
        self.assertEqual(cup.epistemic_status, OBSERVED)
        # Now inject a prediction that the cup is elsewhere.
        from MAC_BRAIN.world_model import PREDICTED
        brain.unified_world.update_entity_state(
            cup.entity_id, "location", "other_room",
            epistemic_status=PREDICTED, confidence=0.9,
            source="prediction_model", timestamp="2026-01-01T12:00:00Z",
        )
        # The prediction should not overwrite the observed "presence" state.
        cup_after = brain.unified_world.resolve("cup")
        self.assertEqual(cup_after.state_value("presence"), "present")
        self.assertEqual(cup_after.state_status("presence"), OBSERVED)
        brain.stop()

    def test_contradiction_preserved_in_runtime(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        cup = brain.unified_world.resolve("cup")
        # Inject two conflicting observations about location.
        from MAC_BRAIN.world_model import OBSERVED as OBS
        brain.unified_world.update_entity_state(
            cup.entity_id, "location", "kitchen",
            epistemic_status=OBS, confidence=0.7,
            source="camera", timestamp="2026-01-01T10:00:00Z",
        )
        brain.unified_world.update_entity_state(
            cup.entity_id, "location", "living_room",
            epistemic_status=OBS, confidence=0.6,
            source="rfid", timestamp="2026-01-01T10:01:00Z",
        )
        self.assertGreaterEqual(len(brain.unified_world.contradictions), 1)
        brain.stop()


if __name__ == "__main__":
    unittest.main()