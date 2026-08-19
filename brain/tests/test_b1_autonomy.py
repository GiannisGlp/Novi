import unittest

from brain.b1_autonomy import DeterministicAutonomy
from brain.b1_cognition import DeterministicCognition
from brain.b1_world import DeterministicWorld, TemporalWorldModel


class B1AutonomyTests(unittest.TestCase):
    def _cognitive_state(self):
        world = DeterministicWorld()
        model = TemporalWorldModel()
        world.advance()
        observations = world.observe()
        model.apply_many(observations)
        return DeterministicCognition().cycle(model.state, observations, cycle=world.cycle)

    def test_produces_canonical_action_proposal(self) -> None:
        proposal = DeterministicAutonomy().propose(self._cognitive_state())
        self.assertTrue(proposal.proposal_id.startswith("proposal-"))
        self.assertEqual(proposal.requester_id, "brain.b1")
        self.assertEqual(proposal.semantic_intent, "person_alice_is_relevant_to_current_situation")
        self.assertIn("requires_safety_authorization", proposal.constraints)

    def test_proposal_is_deterministic_for_same_cognitive_input(self) -> None:
        cognitive = self._cognitive_state()
        first = DeterministicAutonomy().propose(cognitive)
        second = DeterministicAutonomy().propose(cognitive)
        self.assertEqual(first.proposal_id, second.proposal_id)
        self.assertEqual(first.idempotency_key, second.idempotency_key)
        self.assertEqual(first.semantic_intent, second.semantic_intent)

    def test_proposal_cannot_directly_execute_actions(self) -> None:
        proposal = DeterministicAutonomy().propose(self._cognitive_state())
        self.assertFalse(hasattr(proposal, "execute"))
        self.assertTrue(proposal.constraints["no_direct_motor_control"])
        self.assertTrue(proposal.constraints["requires_safety_authorization"])

    def test_proposal_preserves_cognition_provenance(self) -> None:
        cognitive = self._cognitive_state()
        proposal = DeterministicAutonomy().propose(cognitive)
        self.assertEqual(proposal.provenance["cognition_cycle"], cognitive.situation.cycle)
        self.assertEqual(proposal.provenance["reasoning_conclusion"], cognitive.reasoning.conclusion)
        self.assertEqual(proposal.provenance["evidence_count"], len(cognitive.reasoning.provenance))


if __name__ == "__main__":
    unittest.main()
