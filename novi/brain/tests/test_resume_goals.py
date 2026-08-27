import tempfile
import unittest
from pathlib import Path

from novi.brain.autonomy import Goal
from novi.brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.tests.test_mac_brain import FakeCamera


class PersonBackend(DeterministicPerceptionBackend):
    def detect(self, frame):
        return (Detection("person", 0.8, (0, 0, 1, 1)),)


def make_brain(store_path):
    return MacBrain(camera=FakeCamera(), perception=SpecialistPerception(PersonBackend()), store_path=store_path, config=MacBrainConfig(curiosity_enabled=False))


class ResumeGoalTests(unittest.TestCase):
    def test_active_goal_resumes_after_restart(self):
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td) / "brain.db")
            b1 = make_brain(db)
            b1.start()
            b1.set_goal(Goal.reach(10, 0, max_steps=100, goal_id="reach-1"))
            for _ in range(3):
                b1.step()  # partial pursuit
            self.assertEqual(b1.goals.active.steps_taken, 3)
            b1.stop()

            b2 = make_brain(db)
            b2.start()
            self.assertIsNotNone(b2.goals.active, "active goal must be resumed after restart")
            self.assertEqual(b2.goals.active.goal.goal_id, "reach-1")
            self.assertEqual(b2.goals.active.steps_taken, 3, "resumed goal keeps its step budget")
            b2.stop()

    def test_mid_pursuit_kill_preserves_step_budget(self):
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td) / "brain.db")
            b1 = make_brain(db)
            b1.start()
            b1.set_goal(Goal.reach(10, 0, max_steps=100, goal_id="reach-kill"))
            for _ in range(4):
                b1.step()  # partial pursuit
            self.assertEqual(b1.goals.active.steps_taken, 4)
            # simulate SIGKILL: close the store WITHOUT the graceful stop() that
            # persists the active goal, so only per-cycle progress was saved.
            b1.memory.close()

            b2 = make_brain(db)
            b2.start()
            self.assertIsNotNone(b2.goals.active, "active goal must be resumed after a mid-pursuit kill")
            self.assertEqual(b2.goals.active.goal.goal_id, "reach-kill")
            self.assertEqual(b2.goals.active.steps_taken, 4, "mid-pursuit kill must preserve the step budget")
            b2.stop()

    def test_resumed_goal_keeps_pursuing_and_stays_bounded(self):
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td) / "brain.db")
            b1 = make_brain(db)
            b1.start()
            b1.set_goal(Goal.reach(20, 0, max_steps=5, goal_id="reach-2"))
            for _ in range(2):
                b1.step()
            b1.stop()

            b2 = make_brain(db)
            b2.start()
            actions = []
            for _ in range(5):
                step = b2.step()
                actions.append(step["action"])
                if not b2.goals.has_active:
                    break
            b2.stop()
            self.assertTrue(any(a in {"move_forward", "turn_left", "turn_right"} for a in actions), "resumed goal must keep moving")
            self.assertEqual(b2.goals.active, None, "bounded goal must not outlive its budget")

    def test_pending_goal_is_resumed(self):
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td) / "brain.db")
            b1 = make_brain(db)
            b1.start()
            b1.set_goal(Goal.reach(10, 0, priority=2.0, goal_id="reach-a"))
            b1.enqueue_goal(Goal.reach(10, 10, priority=1.0, goal_id="reach-b"))
            b1.stop()

            b2 = make_brain(db)
            b2.start()
            self.assertEqual(b2.goals.pending_count, 1)
            self.assertEqual(b2.goals.pending_goals[0].goal.goal_id, "reach-b")
            b2.stop()

    def test_terminal_goal_not_reinflated_as_active(self):
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td) / "brain.db")
            b1 = make_brain(db)
            b1.start()
            # a goal already completed (max_steps=0) is persisted as COMPLETED
            goal = Goal.reach(10, 0, max_steps=0, goal_id="reach-done")
            b1.set_goal(goal)
            b1.step()  # budget spent -> FAILED
            b1.stop()
            b2 = make_brain(db)
            b2.start()
            self.assertEqual(b2.goals.active, None)
            self.assertFalse(b2.goals.has_active)
            b2.stop()


    def test_body_pose_continues_after_restart(self):
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td) / "brain.db")
            b1 = make_brain(db)
            b1.start()
            b1.set_goal(Goal.reach(10, 0, max_steps=100, goal_id="reach-pos"))
            for _ in range(4):
                b1.step()  # moves ~2m along +x
            x_before = b1.body.x_m
            self.assertGreater(x_before, 0.0)
            b1.stop()

            b2 = make_brain(db)
            b2.start()
            self.assertAlmostEqual(b2.body.x_m, x_before, places=3, msg="body pose must be restored across restart")
            first = b2.step()
            self.assertEqual(first["action"], "move_forward")
            self.assertGreater(b2.body.x_m, x_before, msg="resumed goal continues from restored pose")
            b2.stop()


if __name__ == "__main__":
    unittest.main()
