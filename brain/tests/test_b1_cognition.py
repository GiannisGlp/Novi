import unittest

from brain.b1_cognition import DeterministicCognition
from brain.b1_world import DeterministicWorld, TemporalWorldModel


class B1CognitionTests(unittest.TestCase):
    def test_builds_situation_from_observed_world(self) -> None:
        world = DeterministicWorld()
        model = TemporalWorldModel()
        world.advance()
        observations = world.observe()
        model.apply_many(observations)
        cognitive = DeterministicCognition().cycle(model.state, observations, cycle=world.cycle)
        self.assertEqual(cognitive.situation.cycle, 1)
        self.assertIn("alice", cognitive.situation.salient_entities)
        self.assertTrue(cognitive.situation.evidence)

    def test_reasoning_is_structured_and_provenanced(self) -> None:
        world = DeterministicWorld()
        model = TemporalWorldModel()
        world.advance()
        observations = world.observe()
        model.apply_many(observations)
        result = DeterministicCognition().cycle(model.state, observations, cycle=1).reasoning
        self.assertEqual(result.conclusion, "person_alice_is_relevant_to_current_situation")
        self.assertGreater(result.confidence, 0.9)
        self.assertTrue(result.provenance)
        self.assertEqual(result.provenance[0].source, observations[0].source)

    def test_uncertainty_reduces_reasoning_confidence(self) -> None:
        world = DeterministicWorld()
        model = TemporalWorldModel()
        world.advance()
        observations = tuple(
            type(item)(item.cycle, item.source, item.entity, item.location, item.state, 0.5, item.captured_cycle)
            for item in world.observe()
        )
        model.apply_many(observations)
        cognitive = DeterministicCognition().cycle(model.state, observations, cycle=1)
        self.assertIn("low_confidence:alice", cognitive.situation.uncertainty)
        self.assertLessEqual(cognitive.reasoning.confidence, 0.6)

    def test_cognition_does_not_execute_actions(self) -> None:
        world = DeterministicWorld()
        model = TemporalWorldModel()
        world.advance()
        observations = world.observe()
        model.apply_many(observations)
        cognitive = DeterministicCognition().cycle(model.state, observations, cycle=1)
        self.assertFalse(hasattr(cognitive, "action"))


if __name__ == "__main__":
    unittest.main()
