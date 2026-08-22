import unittest

from brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
from MAC_BRAIN.autonomy import BoundedGoalController, Goal, GoalStatus
from MAC_BRAIN.io import VirtualBody
from MAC_BRAIN.runtime import MacBrain
from MAC_BRAIN.tests.test_mac_brain import FakeCamera


class WidgetBackend(DeterministicPerceptionBackend):
    def detect(self, frame):
        return (Detection("widget", 0.9, (0, 0, 1, 1)),)


class BoundedInvestigateControllerTests(unittest.TestCase):
    def test_investigate_goal_observes_for_bounded_cycles_then_completes(self):
        body = VirtualBody()
        ctrl = BoundedGoalController()
        ctrl.adopt(Goal.investigate("mystery", max_steps=3))
        actions = []
        guard = 0
        while ctrl.has_active and guard < 20:
            cmd = ctrl.step(body)
            body.execute(cmd.action, **cmd.parameters)
            actions.append(cmd.action)
            guard += 1
        last = ctrl.history[-1]
        self.assertEqual(last.status, GoalStatus.COMPLETED)
        self.assertEqual(actions.count("observe"), 3)


class CuriosityBrainTests(unittest.TestCase):
    def test_novel_entity_auto_creates_investigate_goal(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(WidgetBackend()))
        brain.start()
        for _ in range(8):  # enough cycles for the bounded investigate goal to finish
            brain.step()
        brain.stop()
        self.assertTrue(any(e["event_type"] == "curiosity.triggered" for e in brain.events))
        # the spawned goal drives observation rather than a one-shot reaction
        self.assertEqual(len(brain.goals.history), 1)
        self.assertEqual(brain.goals.history[-1].goal.kind, "investigate")
        self.assertEqual(brain.goals.history[-1].status, GoalStatus.COMPLETED)

    def test_same_entity_does_not_respawn_goal(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(WidgetBackend()))
        brain.start()
        for _ in range(15):
            brain.step()
        brain.stop()
        triggers = [e for e in brain.events if e["event_type"] == "curiosity.triggered"]
        self.assertEqual(len(triggers), 1)

    def test_curiosity_does_not_interrupt_active_goal(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(WidgetBackend()))
        brain.start()
        brain.set_goal(Goal.reach(4.0, 0.0, max_steps=20))
        brain.step()  # novel widget appears while a reach goal is active
        brain.stop()
        triggers = [e for e in brain.events if e["event_type"] == "curiosity.triggered"]
        # active goal is pursued; curiosity does not spawn a second goal
        self.assertEqual(len(triggers), 0)
        self.assertEqual(len(brain.goals.history), 1)
        self.assertEqual(brain.goals.history[-1].goal.kind, "reach")


if __name__ == "__main__":
    unittest.main()
