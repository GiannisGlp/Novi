import unittest

from novi.brain.autonomy import BoundedGoalController, Goal, GoalStatus
from novi.brain.engine import MacBrain
from novi.brain.io import VirtualBody
from novi.brain.tests.test_mac_brain import FakeCamera


class GoalSchedulerTests(unittest.TestCase):
    def test_highest_priority_queued_goal_runs_first(self):
        ctrl = BoundedGoalController()
        low = Goal.investigate("low", priority=1.0, max_steps=2)
        high = Goal.investigate("high", priority=5.0, max_steps=2)
        ctrl.enqueue(low)
        ctrl.enqueue(high)
        body = VirtualBody()
        self.assertEqual(ctrl.pending_count, 2)
        ctrl.step(body)
        # higher-priority goal promoted to active
        self.assertEqual(ctrl.active.goal.goal_id, high.goal_id)
        self.assertEqual(ctrl.pending_count, 1)

    def test_lower_priority_goal_runs_after_higher_completes(self):
        ctrl = BoundedGoalController()
        low = Goal.investigate("low", priority=1.0, max_steps=2)
        high = Goal.investigate("high", priority=5.0, max_steps=2)
        ctrl.enqueue(low)
        ctrl.enqueue(high)
        body = VirtualBody()
        active_sequence = []
        for _ in range(8):
            ctrl.step(body)
            active_sequence.append(ctrl.active.goal.goal_id if ctrl.active else None)
        self.assertEqual(active_sequence[0], high.goal_id)
        self.assertIn(low.goal_id, active_sequence)

    def test_higher_priority_queued_goal_supersedes_active(self):
        ctrl = BoundedGoalController()
        body = VirtualBody()
        low = Goal.investigate("low", priority=1.0, max_steps=100)
        ctrl.adopt(low)
        high = Goal.investigate("high", priority=9.0, max_steps=2)
        ctrl.enqueue(high)
        ctrl.step(body)
        self.assertEqual(ctrl.active.goal.goal_id, high.goal_id)
        low_state = next(s for s in ctrl.history if s.goal.goal_id == low.goal_id)
        self.assertEqual(low_state.status, GoalStatus.SUPERSEDED)

    def test_queued_lower_priority_does_not_supersede_higher_active(self):
        ctrl = BoundedGoalController()
        body = VirtualBody()
        high = Goal.investigate("high", priority=9.0, max_steps=100)
        ctrl.adopt(high)
        low = Goal.investigate("low", priority=1.0, max_steps=2)
        ctrl.enqueue(low)
        ctrl.step(body)
        # still running the higher-priority active goal
        self.assertEqual(ctrl.active.goal.goal_id, high.goal_id)


class BrainSchedulingTests(unittest.TestCase):
    def test_enqueue_goal_emits_queued_event(self):
        brain = MacBrain(camera=FakeCamera())
        brain.start()
        brain.enqueue_goal(Goal.investigate("thing", priority=2.0))
        brain.stop()
        self.assertTrue(any(e["event_type"] == "goal.queued" for e in brain.events))
        self.assertEqual(brain.goals.pending_count, 1)

    def test_high_priority_enqueue_supersedes_active_low_priority(self):
        brain = MacBrain(camera=FakeCamera())
        brain.start()
        brain.set_goal(Goal.investigate("a", priority=1.0, max_steps=100, goal_id="low"))
        brain.enqueue_goal(Goal.investigate("b", priority=9.0, max_steps=2, goal_id="high"))
        brain.step()
        brain.stop()
        # after the step, the higher-priority goal superseded and is active
        self.assertEqual(brain.goals.active.goal.goal_id, "high")
        superseded = [s for s in brain.goals.history if s.goal.goal_id == "low"]
        self.assertEqual(superseded[0].status, GoalStatus.SUPERSEDED)


if __name__ == "__main__":
    unittest.main()
