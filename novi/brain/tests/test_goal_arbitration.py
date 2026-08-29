"""Tests for goal management completion (06_AUTONOMY doc 02).

Covers: deterministic arbitration scoring with auditable records, safety-goal
dominance, urgency/deadline ranking, resource-aware postponement, background
goal caps, and restart revalidation (gate A-GOAL-01).
"""

from __future__ import annotations

import unittest

from novi.brain.autonomy import BoundedGoalController, Goal, GoalStatus


class MockBody:
    """Minimal body for the goal controller's step()."""

    def __init__(self, x: float = 0.0, y: float = 0.0, heading_deg: float = 0.0) -> None:
        self.x_m = x
        self.y_m = y
        self.heading_deg = heading_deg


def make_goals(n: int = 100, *, seed: int = 7) -> list[Goal]:
    """Deterministic mixed-priority goal population for A-GOAL-01."""
    goals: list[Goal] = []
    for i in range(n):
        goals.append(Goal(
            goal_id=f"goal-{i:03d}",
            kind="reach" if i % 3 else "investigate",
            target=(float(i % 10), float(i % 5)),
            priority=float((i * 37 % 11) / 2),           # 0.0..5.0
            max_steps=50,
            created_cycle=i,
            source="safety" if i % 17 == 0 else ("human" if i % 2 else "routine"),
            urgency=float((i * 13 % 10) / 10),           # 0.0..0.9
            deadline_cycle=0 if i % 7 else 100 - (i % 100),
            safety_relevant=(i % 17 == 0),
            resource_budget=float(0.5 + (i % 5) / 4),    # 0.5..1.5
        ))
    return goals


class ArbitrationTests(unittest.TestCase):
    def test_same_state_picks_same_winner(self):
        """A-GOAL-01: 100 mixed goals -> same winner for the same state."""
        c1 = BoundedGoalController()
        c2 = BoundedGoalController()
        for goal in make_goals(100):
            c1.enqueue(goal)
            c2.enqueue(goal)
        c1.step(MockBody(), cycle=0)
        c2.step(MockBody(), cycle=0)
        assert c1.active is not None and c2.active is not None
        self.assertEqual(c1.active.goal.goal_id, c2.active.goal.goal_id)
        self.assertEqual(c1.arbitration_key(c1.active.goal), c2.arbitration_key(c2.active.goal))

    def test_safety_goals_dominate_all_lower_authority_goals(self):
        """A-GOAL-01: safety goals must dominate every lower-authority goal."""
        c = BoundedGoalController()
        c.adopt(Goal.reach(1, 0, priority=5.0, goal_id="high-priority-nonsafety", source="human"))
        c.adopt(Goal.investigate("smoke", goal_id="safety-goal", source="safety", safety_relevant=True))
        assert c.active is not None
        self.assertEqual(c.active.goal.goal_id, "safety-goal")
        # The arbitration record explains why.
        self.assertTrue(c.arbitrations)
        record = c.arbitrations[-1]
        self.assertEqual(record.winner_goal_id, "safety-goal")
        self.assertEqual(record.basis, "safety")
        self.assertTrue(record.score_winner["safety_relevant"])
        self.assertFalse(record.score_loser["safety_relevant"])

    def test_urgency_beats_priority_tie(self):
        c = BoundedGoalController()
        c.enqueue(Goal.reach(1, 0, priority=2.0, urgency=0.1, goal_id="low-urgency"))
        c.enqueue(Goal.reach(1, 0, priority=2.0, urgency=0.9, goal_id="high-urgency"))
        c.step(MockBody(), cycle=0)
        assert c.active is not None
        self.assertEqual(c.active.goal.goal_id, "high-urgency")

    def test_deadline_pressure_breaks_urgency_tie(self):
        c = BoundedGoalController()
        c.enqueue(Goal.reach(1, 0, priority=1.0, urgency=0.5, goal_id="no-deadline"))
        c.enqueue(Goal.reach(1, 0, priority=1.0, urgency=0.5, deadline_cycle=5, goal_id="urgent-deadline"))
        c.step(MockBody(), cycle=0)
        assert c.active is not None
        self.assertEqual(c.active.goal.goal_id, "urgent-deadline")

    def test_arbitration_is_auditable(self):
        c = BoundedGoalController()
        c.enqueue(Goal.reach(1, 0, priority=3.0, goal_id="winner"))
        c.enqueue(Goal.reach(1, 0, priority=1.0, goal_id="loser"))
        c.step(MockBody(), cycle=0)
        assert c.active is not None
        self.assertEqual(c.active.goal.goal_id, "winner")
        # A real conflict (loser challenges the active winner) records the audit.
        c.enqueue(Goal.reach(2, 0, priority=0.5, goal_id="challenger"))
        c.step(MockBody(), cycle=1)
        self.assertTrue(c.arbitrations, "every arbitration decision must record why one goal won")
        for record in c.arbitrations:
            self.assertIn("priority", record.score_winner)
            self.assertIn("priority", record.score_loser)
            self.assertTrue(record.winner_goal_id != record.loser_goal_id)


class ResourceAndBackgroundTests(unittest.TestCase):
    def test_resource_constrained_postpones_low_value_goals(self):
        c = BoundedGoalController(resource_priority_floor=2.0)
        c.enqueue(Goal.reach(1, 0, priority=1.0, goal_id="low-value"))
        c.enqueue(Goal.reach(1, 0, priority=3.0, goal_id="high-value"))
        c.step(MockBody(), cycle=0, resource_constrained=True)
        assert c.active is not None
        self.assertEqual(c.active.goal.goal_id, "high-value", "low-value goal postponed while constrained")
        # Resources recover: the low-value goal is now promoted.
        c.step(MockBody(), cycle=1, resource_constrained=False)
        self.assertIsNotNone(c.active)

    def test_background_goals_are_capped(self):
        c = BoundedGoalController(max_background_goals=2)
        states = []
        for i in range(5):
            states.append(c.enqueue(Goal.investigate(
                f"thing-{i}", goal_id=f"bg-{i}", source="exploration",
            )))
        self.assertEqual(c.background_count, 2)
        # The overflow goals were blocked, not queued.
        blocked = [s for s in states if s.status is GoalStatus.BLOCKED]
        self.assertEqual(len(blocked), 3)
        self.assertTrue(all(s.block_reason == "background_goal_limit" for s in blocked))

    def test_explicit_goals_are_not_capped(self):
        c = BoundedGoalController(max_background_goals=1)
        for i in range(5):
            c.enqueue(Goal.reach(i, 0, goal_id=f"user-{i}", source="human"))
        self.assertEqual(c.background_count, 0)
        self.assertEqual(c.pending_count, 5)


class RevalidationTests(unittest.TestCase):
    def test_restored_goal_requires_revalidation(self):
        c = BoundedGoalController()
        c.adopt(Goal.reach(5, 0, goal_id="physical-goal"))
        c.step(MockBody(), cycle=0)
        assert c.active is not None
        self.assertEqual(c.active.goal.goal_id, "physical-goal")

        # Simulated restart: goal restored but physical preconditions unknown.
        self.assertTrue(c.mark_requires_revalidation("physical-goal"))
        self.assertIsNone(c.active)
        state = c.status_of("physical-goal")
        self.assertEqual(state, GoalStatus.BLOCKED)

        # It cannot be resumed or pursued until explicitly reaccepted.
        self.assertFalse(c.resume("physical-goal"))
        self.assertFalse(c.reaccept("other-goal"))
        self.assertTrue(c.reaccept("physical-goal"))
        self.assertEqual(c.status_of("physical-goal"), GoalStatus.PENDING)

    def test_revalidation_is_not_terminal(self):
        c = BoundedGoalController()
        c.adopt(Goal.reach(5, 0, goal_id="g"))
        c.cancel("g")
        self.assertFalse(c.mark_requires_revalidation("g"), "terminal goals cannot be revalidated")


if __name__ == "__main__":
    unittest.main()
