import unittest

from MAC_BRAIN.autonomy import BoundedGoalController, Goal, GoalStatus
from MAC_BRAIN.io import VirtualBody
from MAC_BRAIN.runtime import MacBrain
from MAC_BRAIN.tests.test_mac_brain import FakeCamera


class BoundedGoalControllerTests(unittest.TestCase):
    def test_reaches_target_directly_ahead(self) -> None:
        body = VirtualBody()
        ctrl = BoundedGoalController(move_distance=0.5, reach_threshold=0.1)
        ctrl.adopt(Goal.reach(10.0, 0.0, max_steps=100))
        guard = 0
        while ctrl.has_active and guard < 200:
            cmd = ctrl.step(body)
            body.execute(cmd.action, **cmd.parameters)
            guard += 1
        last = ctrl.history[-1]
        self.assertEqual(last.status, GoalStatus.COMPLETED)
        self.assertAlmostEqual(body.x_m, 10.0, delta=0.6)
        self.assertEqual(body.y_m, 0.0)

    def test_turns_toward_off_axis_target(self) -> None:
        body = VirtualBody()
        ctrl = BoundedGoalController(move_distance=0.5, reach_threshold=0.1)
        ctrl.adopt(Goal.reach(0.0, 10.0, max_steps=100))
        first = ctrl.step(body)  # target is 90deg CCW from heading 0
        self.assertEqual(first.action, "turn_left")
        body.execute(first.action, **first.parameters)
        self.assertGreater(body.heading_deg, 0.0)

    def test_goal_is_bounded_and_fails_on_budget_exhaustion(self) -> None:
        body = VirtualBody()
        ctrl = BoundedGoalController(move_distance=0.5, reach_threshold=0.1)
        ctrl.adopt(Goal.reach(1000.0, 0.0, max_steps=5))
        guard = 0
        while ctrl.has_active and guard < 100:
            cmd = ctrl.step(body)
            body.execute(cmd.action, **cmd.parameters)
            guard += 1
        self.assertFalse(ctrl.has_active)
        self.assertEqual(ctrl.history[-1].status, GoalStatus.FAILED)
        self.assertLessEqual(ctrl.history[-1].steps_taken, 6)

    def test_no_active_goal_returns_wait(self) -> None:
        ctrl = BoundedGoalController()
        cmd = ctrl.step(VirtualBody())
        self.assertEqual(cmd.action, "wait")


class GoalMovementBrainTests(unittest.TestCase):
    def test_goal_drives_multi_cycle_movement_through_brain(self) -> None:
        body = VirtualBody()
        brain = MacBrain(camera=FakeCamera(), body=body)
        brain.start()
        brain.set_goal(Goal.reach(10.0, 0.0, max_steps=100))
        for _ in range(30):
            brain.step()
        brain.stop()
        # reached target region and goal terminal
        self.assertGreaterEqual(body.x_m, 9.5)
        self.assertEqual(body.y_m, 0.0)
        terminal = brain.goals.history[-1]
        self.assertEqual(terminal.status, GoalStatus.COMPLETED)
        event_types = [e["event_type"] for e in brain.events]
        self.assertIn("goal.adopted", event_types)
        self.assertIn("goal.status", event_types)

    def test_goal_movement_is_authorized(self) -> None:
        body = VirtualBody()
        brain = MacBrain(camera=FakeCamera(), body=body)
        brain.start()
        brain.set_goal(Goal.reach(3.0, 0.0, max_steps=20))
        result = brain.step()
        brain.stop()
        # movement actions are authorized through the safety gateway
        self.assertIn(result["action"], {"move_forward", "turn_left", "turn_right", "stop", "wait"})
        self.assertTrue(result["authorized"])


if __name__ == "__main__":
    unittest.main()
