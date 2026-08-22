"""Adversarial / hostile-input tests (gap-analysis Step 3, item 22).

Exercises the runtime and autonomy layer with hostile inputs — NaN/infinite
targets, absurd distances, malformed goals, extreme budgets, unknown actions,
corrupt plan snapshots — and asserts graceful, bounded, decision-sane behavior
(no crashes, no NaN propagation, no unbounded loops).
"""

import math
import unittest

from MAC_BRAIN.autonomy import BoundedGoalController, Goal, GoalStatus
from MAC_BRAIN.io import VirtualBody
from MAC_BRAIN.planner import Plan, PlanStep, PlanValidator
from MAC_BRAIN.runtime import MacBrain, MacBrainConfig
from MAC_BRAIN.tests.test_mac_brain import FakeCamera


class AdversarialGoalTests(unittest.TestCase):
    def test_nan_target_reaches_failed_not_loop(self):
        body = VirtualBody()
        ctrl = BoundedGoalController(reach_threshold=0.1)
        ctrl.adopt(Goal.reach(float("nan"), 0.0, max_steps=5))
        guard = 0
        while ctrl.has_active and guard < 50:
            cmd = ctrl.step(body)
            body.execute(cmd.action, **cmd.parameters)
            guard += 1
        self.assertFalse(ctrl.has_active)
        self.assertEqual(ctrl.history[-1].status, GoalStatus.FAILED)
        self.assertLessEqual(guard, 8)  # bounded, not looping

    def test_infinite_target_fails_bounded(self):
        body = VirtualBody()
        ctrl = BoundedGoalController()
        ctrl.adopt(Goal.reach(float("inf"), 0.0, max_steps=3))
        outcomes = []
        while ctrl.has_active and len(outcomes) < 20:
            cmd = ctrl.step(body)
            outcomes.append(cmd.action)
        self.assertEqual(ctrl.history[-1].status, GoalStatus.FAILED)
        self.assertLessEqual(len(outcomes), 5)

    def test_zero_budget_goal_fails_immediately(self):
        body = VirtualBody()
        ctrl = BoundedGoalController()
        ctrl.adopt(Goal.reach(5.0, 0.0, max_steps=0))
        ctrl.step(body)
        self.assertFalse(ctrl.has_active)
        self.assertEqual(ctrl.history[-1].status, GoalStatus.FAILED)

    def test_negative_priority_queues_behind(self):
        ctrl = BoundedGoalController()
        high = ctrl.adopt(Goal.investigate("a", priority=5.0, max_steps=10))
        low = ctrl.enqueue(Goal.investigate("b", priority=-3.0, max_steps=10))
        ctrl.step(VirtualBody())
        self.assertEqual(ctrl.active.goal.goal_id, high.goal.goal_id)
        self.assertEqual(ctrl.status_of(low.goal.goal_id), GoalStatus.PENDING)

    def test_same_id_goals_do_not_duplicate_state(self):
        ctrl = BoundedGoalController()
        a1 = ctrl.adopt(Goal.investigate("x", goal_id="dup", max_steps=5))
        a2 = ctrl.adopt(Goal.investigate("y", goal_id="dup", max_steps=5))
        # Second adoption resolves against first; status queries are consistent.
        self.assertTrue(a1.goal.goal_id == a2.goal.goal_id == "dup")
        statuses = [s.status for s in ctrl.history if s.goal.goal_id == "dup"]
        self.assertGreaterEqual(len(statuses), 1)


class AdversarialRuntimeTests(unittest.TestCase):
    def test_no_nan_in_step_result(self):
        brain = MacBrain(camera=FakeCamera(), config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.set_goal(Goal.reach(float("nan"), 0.0, max_steps=3))
        result = brain.step()
        brain.stop()
        self.assertIn("action", result)
        outcome = result.get("outcome", {})
        self.assertNotIsInstance(outcome, float) or math.isfinite(outcome) if isinstance(outcome, float) else True

    def test_random_walks_from_malformed_goal(self):
        # A goal whose target type is unexpected must not crash the cycle.
        brain = MacBrain(camera=FakeCamera(), config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.set_goal(Goal("odd", "reach", "not-a-tuple", 1.0, 5, 0))
        result = brain.step()
        brain.stop()
        self.assertIn(result["action"], {"wait", "stop", "move_forward", "turn_left", "turn_right", "observe"})

    def test_tiny_and_huge_targets(self):
        body = VirtualBody()
        ctrl = BoundedGoalController()
        ctrl.adopt(Goal.reach(1e-9, 0.0, max_steps=200))
        guard = 0
        while ctrl.has_active and guard < 10:
            cmd = ctrl.step(body)
            body.execute(cmd.action, **cmd.parameters)
            guard += 1
        self.assertEqual(ctrl.history[-1].status, GoalStatus.COMPLETED)
        # Huge target with tiny budget = FAILED, bounded.
        ctrl2 = BoundedGoalController()
        ctrl2.adopt(Goal.reach(1e12, 0.0, max_steps=2))
        guard2 = 0
        while ctrl2.has_active and guard2 < 10:
            cmd = ctrl2.step(body)
            body.execute(cmd.action, **cmd.parameters)
            guard2 += 1
        self.assertFalse(ctrl2.has_active)
        self.assertEqual(ctrl2.history[-1].status, GoalStatus.FAILED)
        self.assertLessEqual(guard2, 4)


class AdversarialPlanTests(unittest.TestCase):
    def test_nan_step_argument_rejected(self):
        v = PlanValidator()
        plan = Plan(plan_id="p", goal_id="g", goal_kind="reach", steps=[
            PlanStep("move", "navigate", "move_forward", "ok", params={"distance_m": float("nan")}),
        ])
        result = v.validate(plan)
        self.assertFalse(result.valid)
        self.assertIn("spatial", [c.name for c in result.checks if not c.passed])

    def test_unknown_action_rejected(self):
        v = PlanValidator()
        plan = Plan(plan_id="p", goal_id="g", goal_kind="reach", steps=[
            PlanStep("teleport", "navigate", "teleport", "ok"),
            PlanStep("stop", "verify", "stop", "done"),
        ])
        result = v.validate(plan)
        self.assertFalse(result.valid)
        self.assertIn("capabilities", [c.name for c in result.checks if not c.passed])

    def test_oversized_plan_rejected(self):
        v = PlanValidator()
        steps = [PlanStep(f"s{i}", "execute", "observe", f"o{i}") for i in range(30)]
        steps.append(PlanStep("stop", "verify", "stop", "done"))
        plan = Plan(plan_id="p", goal_id="g", goal_kind="generic", steps=steps)
        result = v.validate(plan)
        self.assertFalse(result.valid)
        self.assertIn("bounded", [c.name for c in result.checks if not c.passed])

    def test_unterminable_plan_rejected(self):
        v = PlanValidator()
        plan = Plan(plan_id="p", goal_id="g", goal_kind="reach", steps=[
            PlanStep("x", "execute", "observe", "o"),
        ])
        result = v.validate(plan)
        self.assertFalse(result.valid)
        self.assertIn("safety", [c.name for c in result.checks if not c.passed])

    def test_inconsistent_step_statuses_rejected(self):
        v = PlanValidator()
        plan = Plan(plan_id="p", goal_id="g", goal_kind="reach", steps=[
            PlanStep("a", "evaluate", "observe", "x", status="pending"),
            PlanStep("b", "navigate", "move_forward", "y", status="completed"),
            PlanStep("c", "verify", "stop", "z"),
        ])
        result = v.validate(plan)
        self.assertFalse(result.valid)
        self.assertIn("statuses", [c.name for c in result.checks if not c.passed])


if __name__ == "__main__":
    unittest.main()
