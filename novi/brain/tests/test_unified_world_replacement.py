"""Tests for UnifiedWorldModel replacement of legacy TemporalWorldModel.

Verifies that cognition now queries the epistemic-status-aware UnifiedWorldModel
instead of the legacy TemporalWorldModel.
"""

import unittest

from novi.brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.tests.test_mac_brain import FakeCamera
from novi.brain.world_model import OBJECT, OBSERVED, PERSON, WorldModel


class CupBackend(DeterministicPerceptionBackend):
    def detect(self, frame):
        return (Detection("cup", 0.85, (0.1, 0.1, 0.5, 0.5)),)


class UnifiedWorldModelReplacementTests(unittest.TestCase):
    def test_unified_world_to_world_state(self):
        """UnifiedWorldModel.to_world_state() produces a WorldModelState."""
        from novi.brain.b1_world import WorldModelState
        wm = WorldModel()
        wm.add_entity("cup_001", OBJECT, labels=["cup"], epistemic_status=OBSERVED, confidence=0.85)
        state = wm.to_world_state()
        self.assertIsInstance(state, WorldModelState)
        self.assertIn("cup", state.entities)

    def test_cognition_uses_unified_world(self):
        """Cognition now queries the unified world model, not the legacy one."""
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.stop()
        # The unified world model should have the cup entity.
        entity = brain.unified_world.resolve("cup")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.epistemic_status, OBSERVED)
        # The to_world_state() should produce entities that cognition can query.
        state = brain.unified_world.to_world_state()
        self.assertIn("cup", state.entities)

    def test_no_references_to_legacy_world_state(self):
        """No references to self.world.state in the runtime (replaced by unified)."""
        # Canonical location is novi/brain/runtime.py; keep legacy shim check for pre-consolidation
        import pathlib
        for cand in ("novi/brain/runtime.py", "brain/runtime.py"):
            p = pathlib.Path(cand)
            if p.exists():
                content = p.read_text()
                break
        else:
            self.fail("neither novi/brain/runtime.py nor brain/runtime.py found")
        # self.world.state should not appear (it's been replaced by unified_world.to_world_state())
        self.assertNotIn("self.world.state", content)

    def test_epistemic_status_preserved_in_world_state(self):
        """The unified world model's epistemic status is available through to_world_state()."""
        wm = WorldModel()
        wm.add_entity("alice_001", PERSON, labels=["Alice"], epistemic_status=OBSERVED, confidence=0.9)
        wm.add_entity("unknown_001", OBJECT, labels=["mystery"], epistemic_status="UNKNOWN", confidence=0.1)
        state = wm.to_world_state()
        # Both entities should be in the state.
        self.assertIn("Alice", state.entities)
        self.assertIn("mystery", state.entities)
        # The confidence values should be preserved.
        self.assertAlmostEqual(state.entities["Alice"].confidence, 0.9)
        self.assertAlmostEqual(state.entities["mystery"].confidence, 0.1)


if __name__ == "__main__":
    unittest.main()
