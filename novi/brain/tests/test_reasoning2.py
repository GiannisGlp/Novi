"""Reasoning 2.0: deliberative action selection + reflection / self-correction.

Verifies the situation-aware DeliberativeReasoningProvider and the
ReflectionEngine, plus their wiring into the runtime (reflection events and
self-correction feeding the next decision).
"""

import unittest

from novi.brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
from novi.brain.models.reasoning import DeliberativeReasoningProvider
from novi.brain.reflection import ReflectionEngine
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.tests.test_mac_brain import FakeCamera


class DeliberativeReasoningTests(unittest.TestCase):
    def setUp(self):
        self.p = DeliberativeReasoningProvider()

    def test_no_salience_waits(self):
        intent = self.p.decide(conclusion="no_high_salience_change_detected", confidence=0.7, situation={}, recall=())
        self.assertEqual(intent.action, "wait")

    def test_causal_change_inspects(self):
        intent = self.p.decide(conclusion="causal_change_inferred", confidence=0.8, situation={"inferences": ["alice likely moved door"]}, recall=())
        self.assertEqual(intent.action, "inspect")

    def test_person_observes(self):
        intent = self.p.decide(conclusion="person_alice_is_relevant_to_current_situation", confidence=0.9, situation={}, recall=())
        self.assertEqual(intent.action, "observe")

    def test_self_correction_avoids_ineffective_action(self):
        # last action was wait and it was ineffective -> prefer observe instead
        situation = {"reflection": {"action": "wait", "effective": False}}
        intent = self.p.decide(conclusion="no_high_salience_change_detected", confidence=0.7, situation=situation, recall=())
        self.assertNotEqual(intent.action, "wait")
        self.assertEqual(intent.action, "observe")


class ReflectionEngineTests(unittest.TestCase):
    def test_record_and_assess(self):
        e = ReflectionEngine()
        e.record(cycle=1, action="wait", intent="no_salience", effective=True)
        e.record(cycle=2, action="inspect", intent="causal", effective=False)
        self.assertFalse(e.last().effective)
        self.assertTrue(e.recent_ineffective(window=2))
        self.assertEqual(len(e.snapshot()), 2)

    def test_from_snapshot_roundtrip(self):
        e = ReflectionEngine()
        e.record(cycle=1, action="wait", intent="x", effective=True)
        e2 = ReflectionEngine.from_snapshot(e.snapshot())
        self.assertEqual(e2.last().action, "wait")
        self.assertTrue(e2.last().effective)


class AliceBackend(DeterministicPerceptionBackend):
    def detect(self, frame):
        return (Detection("alice", 0.9, (0.0, 0.0, 1.0, 1.0)),)


class ReflectionRuntimeTests(unittest.TestCase):
    def test_step_emits_reflection_and_feeds_next_decision(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(AliceBackend()), config=MacBrainConfig())
        brain.start()
        try:
            brain.step()
            brain.step()
            reflections = [e for e in brain.events if e["event_type"] == "reasoning.reflection"]
            self.assertTrue(reflections)
            self.assertIn("effective", reflections[-1]["payload"])
            self.assertIn("action", reflections[-1]["payload"])
            # the reflection engine holds the latest assessment
            self.assertIsNotNone(brain.reflection.last())
        finally:
            brain.stop()


if __name__ == "__main__":
    unittest.main()
