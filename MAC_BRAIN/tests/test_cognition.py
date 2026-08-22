import tempfile
import unittest
from pathlib import Path

from brain.b2_perception import SpecialistPerception
from MAC_BRAIN.cognition import BeliefSystem, ExpectationSystem
from MAC_BRAIN.runtime import MacBrain, MacBrainConfig
from MAC_BRAIN.storage import DurableMemoryStore
from MAC_BRAIN.tests.test_mac_brain import FakeCamera, PersonBackend


class BeliefTests(unittest.TestCase):
    def test_evidence_accumulates_confidence(self):
        bs = BeliefSystem()
        b1 = bs.observe("alice", True, confidence=0.8)
        c1 = b1.confidence
        b2 = bs.observe("alice", True, confidence=0.8)
        self.assertGreater(b2.confidence, c1)
        self.assertEqual(bs.belief_for("alice").evidence_count, 2)

    def test_single_contradiction_does_not_flip_established_belief(self):
        bs = BeliefSystem()
        for _ in range(3):
            bs.observe("lamp", True, confidence=0.9)
        stable = bs.belief_for("lamp").value
        bs.observe("lamp", False, confidence=0.9)  # single contradicting observation
        self.assertEqual(bs.belief_for("lamp").value, stable)
        self.assertEqual(bs.belief_for("lamp").contradictions, 1)
        self.assertLess(bs.belief_for("lamp").confidence, 0.9)

    def test_repeated_contradiction_flips_belief(self):
        bs = BeliefSystem()
        for _ in range(3):
            bs.observe("lamp", True, confidence=0.9)
        bs.observe("lamp", False, confidence=0.9)
        bs.observe("lamp", False, confidence=0.9)  # second strong contradiction -> flip
        self.assertEqual(bs.belief_for("lamp").value, False)
        self.assertEqual(bs.belief_for("lamp").contradictions, 0)

    def test_contradicts_reports_count(self):
        bs = BeliefSystem()
        bs.observe("a", True, confidence=0.9)
        bs.observe("a", False, confidence=0.9)
        self.assertEqual(bs.contradicts(), 1)


class ExpectationTests(unittest.TestCase):
    def test_steady_presence_then_absence_is_violation(self):
        es = ExpectationSystem(consistency=2)
        for _ in range(2):
            es.update({"lamp"})
        self.assertTrue(es.expects_present("lamp"))
        es.update(set())  # absence after steady presence -> violation
        v = es.drain_violations()
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0].kind, "expected_present_now_absent")
        self.assertEqual(v[0].entity, "lamp")

    def test_no_violation_without_steady_state(self):
        es = ExpectationSystem(consistency=3)
        es.update({"lamp"})
        es.update(set())
        self.assertEqual(es.drain_violations(), [])
        self.assertFalse(es.expects_present("lamp"))

    def test_violations_are_predicted_not_factual(self):
        es = ExpectationSystem(consistency=2)
        for _ in range(2):
            es.update({"alice"})
        es.update(set())
        v = es.drain_violations()[0]
        self.assertIn("expected", v.kind)  # explicitly a prediction/expectation, not observation


class DurableCognitionTests(unittest.TestCase):
    def test_beliefs_and_expectations_persist(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "cog.db"
            store = DurableMemoryStore(db)
            bs = BeliefSystem()
            for _ in range(3):
                bs.observe("lamp", True, confidence=0.9)
            es = ExpectationSystem(consistency=2)
            for _ in range(2):
                es.update({"lamp"})
            store.save_beliefs(bs.snapshot())
            store.save_expectations(es.snapshot())
            store.close()
            reopened = DurableMemoryStore(db)
            bs2 = BeliefSystem.from_snapshot(reopened.load_beliefs())
            es2 = ExpectationSystem.from_snapshot(reopened.load_expectations())
            self.assertEqual(bs2.belief_for("lamp").value, True)
            self.assertTrue(es2.expects_present("lamp"))
            reopened.close()


class BrainCognitionTests(unittest.TestCase):
    def test_brain_updates_beliefs_and_emits_prediction(self):
        camera = FakeCamera()
        brain = MacBrain(camera=camera, perception=SpecialistPerception(PersonBackend()), config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        for _ in range(3):
            brain.step()
        brain.stop()
        self.assertIn("cognition.completed", [e["event_type"] for e in brain.events])
        self.assertEqual(brain.beliefs.belief_for("person").value, True)


if __name__ == "__main__":
    unittest.main()
