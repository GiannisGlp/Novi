import unittest

from novi.brain.runtime import ActionProposal, BrainSupervisor, Lifecycle, SafetyViolation


class B0StageGateTests(unittest.TestCase):
    def test_integrated_runtime_foundation(self) -> None:
        brain = BrainSupervisor()
        brain.start()

        self.assertEqual(brain.lifecycle, Lifecycle.ACTIVE)

        outcome = brain.cycle()
        self.assertTrue(outcome.success)
        self.assertEqual(len(brain.body.executed), 1)

        event_types = [event.event_type for event in brain.events.events]
        self.assertIn("observation.received", event_types)
        self.assertIn("safety.decided", event_types)
        self.assertIn("action.completed", event_types)

        brain.safe_stop("integrated gate test")
        self.assertEqual(brain.lifecycle, Lifecycle.SAFE_STOP)
        brain.shutdown()
        self.assertEqual(brain.lifecycle, Lifecycle.SHUTTING_DOWN)

    def test_denied_action_cannot_cross_body_boundary(self) -> None:
        brain = BrainSupervisor()
        proposal = ActionProposal("disable_safety", {}, "stage gate", "gate-correlation")
        decision = brain.propose(proposal)
        self.assertFalse(decision.authorized)

        with self.assertRaises(SafetyViolation):
            brain.execute(proposal, decision)

        self.assertEqual(brain.body.executed, [])
        self.assertEqual(len(brain.body.rejected), 1)

    def test_scheduler_and_event_runtime_integrate(self) -> None:
        brain = BrainSupervisor()
        calls: list[str] = []
        brain.scheduler.register("sensor", lambda: calls.append("sensor"), priority=10)
        brain.scheduler.register("background", lambda: calls.append("background"), priority=1)

        self.assertEqual(brain.scheduler.run_once(), ("sensor", "background"))
        self.assertEqual(calls, ["sensor", "background"])
        self.assertEqual(brain.scheduler.run_count, 1)

        sequences = [event.sequence for event in brain.events.events]
        self.assertEqual(sequences, sorted(sequences))
        self.assertEqual(len(sequences), len(set(sequences)))


if __name__ == "__main__":
    unittest.main()
