"""End-to-end autonomy scenarios (gap-analysis Step 3, item 22).

Scenario suite driving `MacBrain` through realistic multi-cycle situations:
goal pursuit, curiosity investigation, high-priority preemption,
resource-constrained pausing, confirmation flows, plan validation, and the
persistent audit trail — each asserts observable runtime state/events, not
just controller internals.
"""

import unittest

from brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
from brain.autonomy import Goal, GoalStatus
from brain.io import VirtualBody
from brain.engine import MacBrain, MacBrainConfig
from brain.tests.test_mac_brain import FakeCamera


class CatBackend(DeterministicPerceptionBackend):
    def detect(self, frame):
        return (Detection("cat", 0.9, (0, 0, 1, 1)),)


def brain_with_cat():
    return MacBrain(
        camera=FakeCamera(),
        perception=SpecialistPerception(CatBackend()),
        body=VirtualBody(),
        config=MacBrainConfig(curiosity_enabled=True),
    )


class ReachScenarioTests(unittest.TestCase):
    def test_autonomous_reach_completes(self):
        body = VirtualBody()
        brain = MacBrain(camera=FakeCamera(), body=body, config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.set_goal(Goal.reach(8.0, 0.0, max_steps=60, goal_id="scenario-reach"))
        for _ in range(40):
            brain.step()
        brain.stop()
        self.assertGreaterEqual(body.x_m, 7.5)
        terminal = [s for s in brain.goals.history if s.goal.goal_id == "scenario-reach"][-1]
        self.assertEqual(terminal.status, GoalStatus.COMPLETED)

    def test_plan_validated_event_emitted(self):
        brain = MacBrain(camera=FakeCamera(), config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.set_goal(Goal.reach(3.0, 0.0, goal_id="scenario-validated"))
        brain.stop()
        events = [e for e in brain.events if e["event_type"] == "plan.validated"]
        self.assertGreaterEqual(len(events), 1)
        self.assertTrue(events[0]["payload"]["valid"])

    def test_exhausted_budget_fails_goal(self):
        brain = MacBrain(camera=FakeCamera(), config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.set_goal(Goal.reach(1000.0, 0.0, max_steps=4, goal_id="scenario-fail"))
        for _ in range(6):
            brain.step()
        brain.stop()
        terminal = [s for s in brain.goals.history if s.goal.goal_id == "scenario-fail"][-1]
        self.assertEqual(terminal.status, GoalStatus.FAILED)


class CuriosityScenarioTests(unittest.TestCase):
    def test_curiosity_investigates_cat(self):
        brain = brain_with_cat()
        brain.start()
        for _ in range(20):
            brain.step()
        brain.stop()
        goals_created = [s for s in brain.goals.history + [brain.goals.active] if s is not None]
        investigate_ids = [s.goal.goal_id for s in goals_created if s.goal.kind == "investigate"]
        self.assertGreaterEqual(len(investigate_ids), 1)
        self.assertIn("goal.adopted", [e["event_type"] for e in brain.events])

    def test_curiosity_does_not_run_without_cat(self):
        brain = MacBrain(camera=FakeCamera(), config=MacBrainConfig(curiosity_enabled=True))
        brain.start()
        for _ in range(10):
            brain.step()
        brain.stop()
        investigate_ids = [s.goal.goal_id for s in (brain.goals.history + [brain.goals.active]) if s is not None and s.goal.kind == "investigate"]
        self.assertEqual(investigate_ids, [])


class PreemptionScenarioTests(unittest.TestCase):
    def test_high_priority_goal_preempts_low(self):
        body = VirtualBody()
        brain = MacBrain(camera=FakeCamera(), body=body, config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.set_goal(Goal.investigate("a", priority=1.0, max_steps=100, goal_id="low-p"))
        brain.enqueue_goal(Goal.investigate("b", priority=9.0, max_steps=2, goal_id="high-p"))
        brain.step()
        brain.stop()
        self.assertEqual(brain.goals.active.goal.goal_id, "high-p")
        low_state = [s for s in brain.goals.history if s.goal.goal_id == "low-p"][-1]
        self.assertEqual(low_state.status, GoalStatus.SUPERSEDED)
        self.assertGreaterEqual(brain.goals.conflict_resolution_count, 1)

    def test_resource_constrained_pause(self):
        body = VirtualBody()
        brain = MacBrain(camera=FakeCamera(), body=body, config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.set_goal(Goal.investigate("pickup", priority=1.0, max_steps=100, goal_id="worker"))
        brain.enqueue_goal(Goal.investigate("urgent", priority=9.0, max_steps=2, goal_id="urgent"))
        brain.step(resource_constrained=True)
        brain.stop()
        # Lower-priority goal is paused, not lost (doc 00 §Resources).
        worker = [s for s in brain.goals.history if s.goal.goal_id == "worker"][-1]
        self.assertEqual(worker.status, GoalStatus.PAUSED)
        self.assertEqual(brain.goals.active.goal.goal_id, "urgent")


class ConfirmationScenarioTests(unittest.TestCase):
    def test_confirmation_gated_action_held_then_confirmed(self):
        from brain.autonomy import Goal
        from brain.governance_guard import GovernanceGuard

        guard = GovernanceGuard(require_confirmation_above="R1")  # physical actions need confirmation
        brain = MacBrain(
            camera=FakeCamera(),
            body=VirtualBody(),
            config=MacBrainConfig(curiosity_enabled=False),
            governance_guard=guard,
        )
        brain.start()
        brain.set_goal(Goal.reach(3.0, 0.0, max_steps=30, goal_id="confirm-reach"))
        pending = None
        for _ in range(5):
            brain.step()
            if brain.pending_confirmations():
                pending = brain.pending_confirmations()
                break
        brain.stop()
        self.assertIsNotNone(pending, "confirmation request should have surfaced")
        grant_id = pending[0]["grant_id"]
        self.assertTrue(brain.confirm_action(grant_id))
        self.assertEqual(len(brain.pending_confirmations()), 0)
        self.assertIn("governance.confirmed", [e["event_type"] for e in brain.events])
        self.assertIn("action.completed", [e["event_type"] for e in brain.events])


class AuditScenarioTests(unittest.TestCase):
    def test_consequential_actions_are_audited(self):
        brain = MacBrain(camera=FakeCamera(), config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.set_goal(Goal.reach(3.0, 0.0, max_steps=10, goal_id="audit-goal"))
        for _ in range(3):
            brain.step()
        brain.stop()
        audit = brain.audit_entries()
        self.assertGreaterEqual(len(audit), 3)
        self.assertTrue(all(e["correlation_id"] for e in audit))
        by_goal = [e for e in audit if e["goal_id"] == "audit-goal"]
        self.assertGreaterEqual(len(by_goal), 1)


if __name__ == "__main__":
    unittest.main()
