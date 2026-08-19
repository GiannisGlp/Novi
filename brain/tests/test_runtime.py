import unittest

from brain.runtime import (
    ActionProposal,
    ActionRejected,
    BrainSupervisor,
    DeterministicScheduler,
    InvalidLifecycleTransition,
    Lifecycle,
    SafetyViolation,
    SchedulerError,
)


class BrainRuntimeTests(unittest.TestCase):
    def test_start_reaches_active(self) -> None:
        brain = BrainSupervisor()
        brain.start()
        self.assertEqual(brain.lifecycle, Lifecycle.ACTIVE)
        self.assertEqual(brain.health.status, "HEALTHY")

    def test_start_is_only_valid_from_booting(self) -> None:
        brain = BrainSupervisor()
        brain.start()
        with self.assertRaises(InvalidLifecycleTransition):
            brain.start()

    def test_invalid_transition_is_rejected(self) -> None:
        brain = BrainSupervisor()
        with self.assertRaises(InvalidLifecycleTransition):
            brain.transition(Lifecycle.ACTIVE)

    def test_degrade_and_recover(self) -> None:
        brain = BrainSupervisor()
        brain.start()
        brain.degrade("optional model unavailable")
        self.assertEqual(brain.lifecycle, Lifecycle.DEGRADED)
        self.assertEqual(brain.health.status, Lifecycle.DEGRADED.value)
        brain.recover()
        self.assertEqual(brain.lifecycle, Lifecycle.ACTIVE)
        self.assertEqual(brain.health.status, "HEALTHY")

    def test_safe_stop_requires_shutdown(self) -> None:
        brain = BrainSupervisor()
        brain.start()
        brain.safe_stop()
        self.assertEqual(brain.lifecycle, Lifecycle.SAFE_STOP)
        with self.assertRaises(Exception):
            brain.cycle()
        brain.shutdown()
        self.assertEqual(brain.lifecycle, Lifecycle.SHUTTING_DOWN)

    def test_failure_path_can_shutdown(self) -> None:
        brain = BrainSupervisor()
        brain.transition(Lifecycle.INITIALIZING)
        brain.fail("required component failed")
        self.assertEqual(brain.lifecycle, Lifecycle.FAILED)
        brain.shutdown()
        self.assertEqual(brain.lifecycle, Lifecycle.SHUTTING_DOWN)

    def test_closed_cycle_is_deterministic(self) -> None:
        brain = BrainSupervisor()
        outcome = brain.run(1)[0]
        self.assertTrue(outcome.success)
        self.assertEqual(outcome.action, "inspect")
        self.assertEqual(brain.lifecycle, Lifecycle.SHUTTING_DOWN)
        self.assertEqual(len(brain.events.events), 8)

    def test_scheduler_runs_priority_order(self) -> None:
        scheduler = DeterministicScheduler()
        calls: list[str] = []
        scheduler.register("low", lambda: calls.append("low"), priority=1)
        scheduler.register("high", lambda: calls.append("high"), priority=10)
        self.assertEqual(scheduler.run_once(), ("high", "low"))
        self.assertEqual(calls, ["high", "low"])
        self.assertEqual(scheduler.run_count, 1)

    def test_scheduler_rejects_duplicate_task_names(self) -> None:
        scheduler = DeterministicScheduler()
        scheduler.register("task", lambda: None)
        with self.assertRaises(SchedulerError):
            scheduler.register("task", lambda: None)

    def test_scheduler_failure_is_wrapped(self) -> None:
        scheduler = DeterministicScheduler()
        scheduler.register("broken", lambda: (_ for _ in ()).throw(ValueError("boom")))
        with self.assertRaises(SchedulerError):
            scheduler.run_once()

    def test_scheduler_emits_runtime_events(self) -> None:
        brain = BrainSupervisor()
        brain.scheduler.register("test", lambda: None, priority=5)
        brain.scheduler.run_once()
        event_types = [event.event_type for event in brain.events.events]
        self.assertIn("scheduler.task.registered", event_types)
        self.assertIn("scheduler.cycle.completed", event_types)

    def test_cycle_requires_active_state(self) -> None:
        brain = BrainSupervisor()
        with self.assertRaises(Exception):
            brain.cycle()

    def test_safety_denies_unknown_action(self) -> None:
        brain = BrainSupervisor()
        proposal = ActionProposal("move", {}, "test", "test-correlation")
        decision = brain.safety.authorize(proposal)
        self.assertFalse(decision.authorized)
        self.assertIn("not authorized", decision.reason)

    def test_safety_denies_protected_action(self) -> None:
        brain = BrainSupervisor()
        proposal = ActionProposal("disable_safety", {}, "test", "test-correlation")
        decision = brain.safety.authorize(proposal)
        self.assertFalse(decision.authorized)
        with self.assertRaises(SafetyViolation):
            brain.body.execute(proposal, decision)

    def test_safety_requires_action_name(self) -> None:
        brain = BrainSupervisor()
        proposal = ActionProposal("", {}, "test", "test-correlation")
        with self.assertRaises(ActionRejected):
            brain.safety.validate_proposal(proposal)

    def test_mock_body_cannot_execute_denied_proposal(self) -> None:
        brain = BrainSupervisor()
        proposal = ActionProposal("disable_safety", {}, "test", "test-correlation")
        decision = brain.propose(proposal)
        with self.assertRaises(SafetyViolation):
            brain.execute(proposal, decision)
        self.assertEqual(len(brain.body.executed), 0)
        self.assertEqual(len(brain.body.rejected), 1)

    def test_only_authorized_action_reaches_body(self) -> None:
        brain = BrainSupervisor()
        proposal = ActionProposal("inspect", {"entity": "test_object"}, "test", "test-correlation")
        decision = brain.propose(proposal)
        outcome = brain.execute(proposal, decision)
        self.assertTrue(outcome.success)
        self.assertEqual(len(brain.body.executed), 1)


if __name__ == "__main__":
    unittest.main()
