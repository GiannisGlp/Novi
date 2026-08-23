"""Phase A1 (gap-audit plan 13): typed cognition is canonical in the loop.

Pins the wiring that makes the typed contracts the canonical per-cycle record:
  - Brain.step() emits cognition.typed on the event bus every cycle;
  - _last_typed_cognition holds the snapshot and the step result exposes
    typed_situation_id matching it;
  - the typed cycle is deterministic: same world + same observations + the
    same correlation id produce an identical typed snapshot;
  - the typed situation carries the same grounding (knowledge/goal/recall)
    context as the legacy cycle, so it is not a parallel debug view.
"""

import unittest

from novi.brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.tests.test_cognition_typed import _observations
from novi.brain.tests.test_mac_brain import FakeCamera


class CupBackend(DeterministicPerceptionBackend):
    def detect(self, frame):
        return (Detection("cup", 0.85, (0.1, 0.1, 0.5, 0.5)),)


def _brain() -> MacBrain:
    brain = MacBrain(
        camera=FakeCamera(),
        perception=SpecialistPerception(CupBackend()),
        config=MacBrainConfig(curiosity_enabled=False),
    )
    brain.start()
    return brain


class TypedCognitionInLoopTests(unittest.TestCase):
    def test_step_emits_cognition_typed(self):
        brain = _brain()
        try:
            brain.step()
            event_types = [e["event_type"] for e in brain.events]
            self.assertIn("cognition.typed", event_types)
        finally:
            brain.stop()

    def test_step_result_exposes_typed_situation_id(self):
        brain = _brain()
        try:
            result = brain.step()
            self.assertIsNotNone(brain._last_typed_cognition)
            typed_id = brain._last_typed_cognition["situation"]["id"]
            self.assertIsNotNone(typed_id)
            self.assertEqual(result["typed_situation_id"], typed_id)
        finally:
            brain.stop()

    def test_typed_snapshot_is_current_after_each_cycle(self):
        brain = _brain()
        try:
            first = brain.step()
            second = brain.step()
            self.assertEqual(first["cycle"], 1)
            self.assertEqual(second["cycle"], 2)
            # The cached snapshot always reflects the latest cycle.
            self.assertIn(
                f"-{second['cycle']}-",
                brain._last_typed_cognition["situation"]["id"],
            )
        finally:
            brain.stop()


class TypedCognitionDeterminismTests(unittest.TestCase):
    def test_same_inputs_same_correlation_id_identical_snapshot(self):
        """Same world + observations + correlation id ⇒ same situation id and
        same content. (Wall-clock created_at is intentionally excluded.)"""
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        try:
            brain._cycle = 7
            brain._cycle_correlation_id = "determinism-check"
            snap_a = brain.cognition_typed(_observations())
            snap_b = brain.cognition_typed(_observations())
            self.assertEqual(snap_a["situation"]["id"], snap_b["situation"]["id"])
            self.assertEqual(snap_a["situation"]["participants"], snap_b["situation"]["participants"])
            self.assertEqual(snap_a["situation"]["current_activity"], snap_b["situation"]["current_activity"])
            self.assertEqual(
                [p["id"] for p in snap_a["person_contexts"]],
                [p["id"] for p in snap_b["person_contexts"]],
            )
        finally:
            brain.stop()

    def test_grounding_context_reaches_the_typed_situation(self):
        """Passing goal/recall grounding must be visible in the typed record."""
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        try:
            brain._cycle = 3
            brain._cycle_correlation_id = "grounding-check"
            bare = brain.cognition_typed(_observations())
            grounded = brain.cognition_typed(
                _observations(),
                goal={"kind": "reach", "target": [8, 0], "priority": 1},
                recalled=({"memory_id": "m1", "text": "cup on the table"},),
            )
            # social_context.recalled is the recall count fed to the cycle.
            self.assertEqual(grounded["situation"]["social_context"].get("recalled"), 1)
            self.assertNotEqual(
                grounded["situation"]["social_context"],
                bare["situation"]["social_context"],
            )
        finally:
            brain.stop()


if __name__ == "__main__":
    unittest.main()
