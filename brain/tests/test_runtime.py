import unittest

from brain.runtime import (
    ActionProposal,
    BrainSupervisor,
    InvalidLifecycleTransition,
    Lifecycle,
    SafetyViolation,
)


class BrainRuntimeTests(unittest.TestCase):
    def test_start_reaches_active(self) -> None:
        brain = BrainSupervisor()
        brain.start()
        self.assertEqual(brain.lifecycle, Lifecycle.ACTIVE)
        self.assertEqual(brain.health.status, "HEALTHY")

    def test_invalid_transition_is_rejected(self) -> None:
        brain = BrainSupervisor()
        with self.assertRaises(InvalidLifecycleTransition):
            brain.transition(Lifecycle.ACTIVE)

    def test_closed_cycle_is_deterministic(self) -> None:
        brain = BrainSupervisor()
        outcome = brain.run(1)[0]
        self.assertTrue(outcome.success)
        self.assertEqual(outcome.action, "inspect")
        self.assertEqual(brain.lifecycle, Lifecycle.SHUTTING_DOWN)
        self.assertEqual(len(brain.events.events), 5)

    def test_safety_cannot_be_bypassed(self) -> None:
        brain = BrainSupervisor()
        proposal = ActionProposal(
            action="disable_safety",
            parameters={},
            reason="test",
            correlation_id="test-correlation",
        )
        decision = brain.safety.authorize(proposal)
        self.assertFalse(decision.authorized)
        with self.assertRaises(SafetyViolation):
            brain.body.execute(proposal, decision)


if __name__ == "__main__":
    unittest.main()
