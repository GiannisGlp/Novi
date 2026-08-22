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


class GoalLifecycleTests(unittest.TestCase):
    """Full goal lifecycle (gap-analysis Step 3, item 21).

    Canonical authority: docs/02-autonomy/04 §Goal Lifecycle —
    candidate → validated → queued → active → (paused/blocked/superseded) →
    (completed/failed/cancelled/expired), with resumability.
    """

    def test_pause_resume_keeps_budget(self) -> None:
        ctrl = BoundedGoalController()
        g = Goal.reach(10.0, 0.0, max_steps=100)
        state = ctrl.adopt(g)
        body = VirtualBody()
        ctrl.step(body)  # 1 step taken
        self.assertTrue(ctrl.pause(g.goal_id, reason="user_interruption"))
        self.assertEqual(ctrl.status_of(g.goal_id), GoalStatus.PAUSED)
        self.assertFalse(ctrl.has_active)
        self.assertEqual(ctrl.step(body).action, "wait")  # paused → no command
        self.assertEqual(state.steps_taken, 1)  # budget preserved
        self.assertTrue(ctrl.resume(g.goal_id))
        cmd = ctrl.step(body)
        self.assertIn(cmd.action, {"turn_left", "turn_right", "move_forward"})
        self.assertEqual(state.steps_taken, 2)

    def test_block_unblock(self) -> None:
        ctrl = BoundedGoalController()
        g = Goal.reach(5.0, 0.0, max_steps=50)
        ctrl.adopt(g)
        self.assertTrue(ctrl.block(g.goal_id, reason="path_obstructed"))
        self.assertEqual(ctrl.status_of(g.goal_id), GoalStatus.BLOCKED)
        self.assertFalse(ctrl.has_active)
        # Resume returns it to PENDING and it is promoted on the next reconcile.
        self.assertTrue(ctrl.resume(g.goal_id))
        self.assertEqual(ctrl.status_of(g.goal_id), GoalStatus.ACTIVE)

    def test_cancel_is_terminal(self) -> None:
        ctrl = BoundedGoalController()
        g = Goal.reach(5.0, 0.0, max_steps=100)
        ctrl.adopt(g)
        self.assertTrue(ctrl.cancel(g.goal_id, reason="user_cancelled"))
        self.assertEqual(ctrl.status_of(g.goal_id), GoalStatus.CANCELLED)
        self.assertFalse(ctrl.has_active)
        self.assertFalse(ctrl.resume(g.goal_id))  # cancelled is terminal
        self.assertFalse(ctrl.pause(g.goal_id))

    def test_validity_expiry(self) -> None:
        body = VirtualBody()
        ctrl = BoundedGoalController()
        g = Goal.reach(10.0, 0.0, max_steps=100)
        ctrl.adopt(g)
        self.assertTrue(ctrl.set_validity(g.goal_id, expires_cycle=10))
        # At cycle 11 the goal must be expired, not pursued.
        cmd = ctrl.step(body, cycle=11)
        self.assertEqual(ctrl.status_of(g.goal_id), GoalStatus.EXPIRED)
        self.assertEqual(cmd.action, "stop")
        self.assertEqual(ctrl.history[-1].status, GoalStatus.EXPIRED)

    def test_status_of_unknown_goal_is_none(self) -> None:
        ctrl = BoundedGoalController()
        self.assertIsNone(ctrl.status_of("does-not-exist"))


class GoalConflictResolutionTests(unittest.TestCase):
    """Canonical conflict resolution (gap-analysis Step 3, item 21; doc 04 §Goal Conflicts)."""

    def test_higher_priority_same_kind_supersedes(self) -> None:
        ctrl = BoundedGoalController()
        low = ctrl.adopt(Goal.investigate("a", priority=1.0, max_steps=100))
        top = ctrl.enqueue(Goal.investigate("b", priority=9.0, max_steps=2))
        ctrl.step(VirtualBody())
        self.assertEqual(ctrl.active.goal.goal_id, top.goal.goal_id)
        self.assertEqual(ctrl.status_of(low.goal.goal_id), GoalStatus.SUPERSEDED)
        # Conflict recorded (doc 04: record the conflict and resolution).
        self.assertGreaterEqual(ctrl.conflict_resolution_count, 1)

    def test_lower_priority_challenger_rejected_and_queued(self) -> None:
        ctrl = BoundedGoalController()
        high = ctrl.adopt(Goal.investigate("a", priority=9.0, max_steps=100))
        low = ctrl.enqueue(Goal.investigate("b", priority=1.0, max_steps=2))
        ctrl.step(VirtualBody())
        self.assertEqual(ctrl.active.goal.goal_id, high.goal.goal_id)
        self.assertEqual(ctrl.status_of(low.goal.goal_id), GoalStatus.PENDING)
        self.assertEqual(ctrl.conflict_resolutions[-1].outcome, "rejected_challenger")

    def test_resource_constrained_pauses_lower_priority(self) -> None:
        """When resources are constrained, lower-priority non-critical goals are paused,
        not discarded (docs/02-autonomy/00 §Resources)."""
        ctrl = BoundedGoalController()
        low = ctrl.adopt(Goal.investigate("worker", priority=1.0, max_steps=100))
        high = ctrl.enqueue(Goal.investigate("critical", priority=9.0, max_steps=2))
        ctrl.step(VirtualBody(), cycle=1, resource_constrained=True)
        self.assertEqual(ctrl.active.goal.goal_id, high.goal.goal_id)
        # The lower-priority goal is paused, not lost — still resumable.
        self.assertEqual(ctrl.status_of(low.goal.goal_id), GoalStatus.PAUSED)
        self.assertFalse(ctrl.has_active and ctrl.active.goal.goal_id == low.goal.goal_id)
        self.assertEqual(ctrl.conflict_resolutions[-1].outcome, "paused_active")

    def test_explicit_reach_beats_curiosity(self) -> None:
        ctrl = BoundedGoalController()
        curiosity = ctrl.adopt(Goal.investigate("mystery", priority=3.0, max_steps=100))
        explicit = ctrl.enqueue(Goal.reach(2.0, 0.0, priority=1.0, max_steps=20))
        ctrl.step(VirtualBody())
        self.assertEqual(ctrl.active.goal.goal_id, explicit.goal.goal_id)
        self.assertEqual(ctrl.status_of(curiosity.goal.goal_id), GoalStatus.SUPERSEDED)

    def test_curiosity_does_not_displace_explicit_goal(self) -> None:
        ctrl = BoundedGoalController()
        explicit = ctrl.adopt(Goal.reach(2.0, 0.0, priority=1.0, max_steps=20))
        curiosity = ctrl.enqueue(Goal.investigate("mystery", priority=3.0, max_steps=2))
        ctrl.step(VirtualBody())
        self.assertEqual(ctrl.active.goal.goal_id, explicit.goal.goal_id)
        self.assertEqual(ctrl.status_of(curiosity.goal.goal_id), GoalStatus.PENDING)

    def test_resolutions_filter_by_goal(self) -> None:
        ctrl = BoundedGoalController()
        low = ctrl.adopt(Goal.investigate("a", priority=1.0, max_steps=100))
        ctrl.enqueue(Goal.investigate("b", priority=9.0, max_steps=2))
        ctrl.step(VirtualBody())
        related = ctrl.resolutions(goal_id=low.goal.goal_id)
        self.assertGreaterEqual(len(related), 1)
        self.assertIn(low.goal.goal_id, (related[0].active_goal_id, related[0].challenger_goal_id))


if __name__ == "__main__":
    unittest.main()
