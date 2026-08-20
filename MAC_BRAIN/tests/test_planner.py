import tempfile
import unittest
from pathlib import Path

from brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception

from MAC_BRAIN.autonomy import Goal
from MAC_BRAIN.planner import Plan, Planner
from MAC_BRAIN.runtime import MacBrain, MacBrainConfig
from MAC_BRAIN.tests.test_mac_brain import FakeCamera


class PlannerTests(unittest.TestCase):
    def test_reach_goal_plan_has_typed_steps(self):
        plan = Planner().plan(Goal.reach(10, 0, goal_id="g1"))
        self.assertEqual(plan.goal_kind, "reach")
        self.assertEqual([s.kind for s in plan.steps], ["evaluate", "navigate", "verify"])
        self.assertTrue(all(s.expected_outcome for s in plan.steps))

    def test_investigate_goal_plan(self):
        plan = Planner().plan(Goal.investigate("lamp", goal_id="g2"))
        self.assertEqual([s.kind for s in plan.steps], ["locate", "track", "conclude"])

    def test_advance_moves_through_steps_and_completes(self):
        p = Planner()
        plan = p.plan(Goal.reach(10, 0, goal_id="g3"))
        p.start(plan)
        self.assertEqual(plan.current_step().kind, "evaluate")
        nxt = p.advance(plan)
        self.assertEqual(nxt.kind, "navigate")
        p.advance(plan)
        self.assertIsNone(p.advance(plan))  # last step completes the plan
        self.assertTrue(plan.complete)

    def test_fail_and_cancel(self):
        p = Planner()
        plan = p.plan(Goal.reach(10, 0, goal_id="g4"))
        p.start(plan)
        p.fail(plan)
        self.assertEqual(plan.status, "failed")
        plan2 = p.plan(Goal.reach(10, 0, goal_id="g5"))
        p.start(plan2)
        p.cancel(plan2)
        self.assertEqual(plan2.status, "cancelled")

    def test_replan_fresh(self):
        p = Planner()
        plan = p.plan(Goal.reach(10, 0, goal_id="g6"))
        replan = p.replan(Goal.reach(10, 0, goal_id="g6"))
        self.assertNotEqual(replan.plan_id, plan.plan_id)

    def test_roundtrip_snapshot(self):
        p = Planner()
        plan = p.plan(Goal.reach(10, 0, goal_id="g7"))
        p.start(plan)
        restored = Plan.from_snapshot(plan.snapshot())
        self.assertEqual(restored.goal_kind, "reach")
        self.assertEqual(restored.current_step().kind, "evaluate")


class BrainPlannerTests(unittest.TestCase):
    class PersonBackend(DeterministicPerceptionBackend):
        def detect(self, frame):
            return (Detection("person", 0.8, (0, 0, 1, 1)),)

    def _brain(self, store_path=None):
        return MacBrain(
            camera=FakeCamera(),
            perception=SpecialistPerception(self.PersonBackend()),
            store_path=store_path,
            config=MacBrainConfig(curiosity_enabled=False),
        )

    def test_set_goal_creates_plan_and_step_advances(self):
        brain = self._brain()
        brain.start()
        brain.set_goal(Goal.reach(10, 0, max_steps=10, goal_id="plan-goal"))
        first = brain.step()
        brain.step()
        brain.stop()
        self.assertIn("plan", first)
        self.assertEqual(first["plan"]["goal_kind"], "reach")
        self.assertIn("plan.created", [e["event_type"] for e in brain.events])
        self.assertIn("plan.step", [e["event_type"] for e in brain.events])

    def test_replan_goal(self):
        brain = self._brain()
        brain.start()
        brain.set_goal(Goal.reach(10, 0, goal_id="replan-goal"))
        plan = brain.replan_goal("replan-goal")
        brain.stop()
        self.assertIsNotNone(plan)
        self.assertIn("plan.replanned", [e["event_type"] for e in brain.events])

    def test_plan_persists_across_restart(self):
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td) / "b.db")
            b1 = self._brain(db)
            b1.start()
            b1.set_goal(Goal.reach(10, 0, max_steps=50, goal_id="persist-goal"))
            b1.step()
            b1.stop()
            b2 = self._brain(db)
            b2.start()
            self.assertIsNotNone(b2.goals.active)
            self.assertIsNotNone(b2.current_plan(), "plan should resume for a resumed goal")
            b2.stop()


if __name__ == "__main__":
    unittest.main()
