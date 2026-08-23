import unittest

from novi.brain.b1_autonomy import ActionProposal
from novi.brain.b1_outcomes import DeterministicOutcomeEvaluator, DeterministicReplay


class B1OutcomeTests(unittest.TestCase):
    def proposal(self) -> ActionProposal:
        return ActionProposal(
            proposal_id="proposal-test",
            capability="observe.environment",
            semantic_intent="test",
            parameters={},
            constraints={},
            expected_effects={},
            risks={},
            requester_id="test",
            authorization_context={},
            expires_at="2099-01-01T00:00:00Z",
            idempotency_key="proposal-test",
            provenance={},
        )

    def test_matching_effects_succeed(self) -> None:
        proposal = self.proposal()
        result = DeterministicOutcomeEvaluator().evaluate(
            proposal,
            observed_effects=("observation_update",),
            expected_effects=("observation_update",),
        )
        self.assertEqual(result.status, "SUCCEEDED")
        self.assertFalse(result.discrepancies)

    def test_missing_expected_effect_diverges(self) -> None:
        proposal = self.proposal()
        result = DeterministicOutcomeEvaluator().evaluate(
            proposal,
            observed_effects=(),
            expected_effects=("observation_update",),
        )
        self.assertEqual(result.status, "DIVERGED")
        self.assertEqual(result.discrepancies, ("observation_update",))

    def test_replay_is_append_only_and_deterministic(self) -> None:
        proposal = self.proposal()
        outcome = DeterministicOutcomeEvaluator().evaluate(proposal, observed_effects=("ok",))
        replay = DeterministicReplay()
        replay.record(1, outcome)
        replay.record(2, outcome)
        self.assertEqual(replay.count, 2)
        self.assertEqual(replay.replay()[0].proposal_id, "proposal-test")
        self.assertEqual(replay.replay()[1].outcome_status, "SUCCEEDED")


if __name__ == "__main__":
    unittest.main()
