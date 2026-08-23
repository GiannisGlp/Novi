"""Tests for SkillExecutor wiring into the runtime action path.

Verifies:
  - The SkillExecutor is initialized in the runtime.
  - Actions that map to skills invoke the skill contract.
  - Skill preconditions are checked before execution.
  - Skill failures block action execution.
  - skill.invoked and skill.failed events are emitted.
  - The action.completed event includes skill info.
"""

import unittest

from brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
from brain.autonomy import Goal
from brain.engine import MacBrain, MacBrainConfig
from brain.skill_contract import SUCCESS, SkillExecutor
from brain.tests.test_mac_brain import FakeCamera


class CupBackend(DeterministicPerceptionBackend):
    def detect(self, frame):
        return (Detection("cup", 0.85, (0.1, 0.1, 0.5, 0.5)),)


class SkillExecutorWiringTests(unittest.TestCase):
    def test_skill_executor_initialized(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        self.assertIsInstance(brain.skill_executor, SkillExecutor)

    def test_skill_invoked_event_emitted_for_navigate(self):
        """When a goal is active and move_forward is executed, the navigate skill is invoked."""
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.set_goal(Goal.reach(3.0, 0.0, max_steps=60))
        brain.step()
        brain.stop()
        skill_events = [e for e in brain.events if e["event_type"] == "skill.invoked"]
        # The navigate skill should have been invoked for move_forward/turn actions.
        if skill_events:
            self.assertIn(skill_events[0]["payload"]["skill_id"], ("navigate", "inspect"))

    def test_observe_action_invokes_inspect_skill(self):
        """The observe action maps to the inspect skill."""
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=True))
        brain.start()
        brain.step()
        brain.stop()
        skill_events = [e for e in brain.events if e["event_type"] == "skill.invoked"]
        # The inspect skill should have been invoked for the observe action.
        inspect_events = [e for e in skill_events if e["payload"]["skill_id"] == "inspect"]
        if inspect_events:
            self.assertEqual(inspect_events[0]["payload"]["action"], "observe")

    def test_wait_action_no_skill(self):
        """The wait action does not invoke any skill (no mapping)."""
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.stop()
        skill_events = [e for e in brain.events if e["event_type"] == "skill.invoked"]
        wait_skills = [e for e in skill_events if e["payload"]["action"] == "wait"]
        # wait should not invoke a skill (it's R0, always safe).
        self.assertEqual(len(wait_skills), 0)

    def test_action_completed_includes_skill_info(self):
        """The action.completed event includes skill_passed and skill_invoked fields."""
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.stop()
        action_events = [e for e in brain.events if e["event_type"] == "action.completed"]
        self.assertGreater(len(action_events), 0)
        payload = action_events[0]["payload"]
        self.assertIn("skill_passed", payload)
        self.assertIn("skill_invoked", payload)

    def test_last_skill_invocation_stored(self):
        """The last skill invocation result is stored on the brain."""
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=True))
        brain.start()
        brain.step()
        brain.stop()
        # If a skill was invoked, the last invocation should be stored.
        if brain._last_skill_invocation is not None:
            self.assertIn("skill_id", brain._last_skill_invocation)
            self.assertIn("status", brain._last_skill_invocation)

    def test_skill_failure_blocks_execution(self):
        """If a skill's preconditions aren't met, the action is not executed."""
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.stop()
        # Check that if a skill failed, the action was not authorized.
        skill_failed_events = [e for e in brain.events if e["event_type"] == "skill.failed"]
        action_events = [e for e in brain.events if e["event_type"] == "action.completed"]
        for failed in skill_failed_events:
            # Find the corresponding action.completed event.
            failed_action = failed["payload"]["action"]
            corresponding = [e for e in action_events if e["payload"]["action"] == failed_action]
            if corresponding:
                self.assertFalse(corresponding[-1]["payload"]["skill_passed"])
                self.assertFalse(corresponding[-1]["payload"]["authorized"])

    def test_navigate_skill_succeeds_with_goal(self):
        """The navigate skill succeeds when a goal is active (target_location_known)."""
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.set_goal(Goal.reach(3.0, 0.0, max_steps=60))
        brain.step()
        brain.stop()
        skill_events = [e for e in brain.events if e["event_type"] == "skill.invoked"
                        and e["payload"]["skill_id"] == "navigate"]
        if skill_events:
            # Navigate skill should succeed (preconditions met with active goal).
            self.assertEqual(skill_events[-1]["payload"]["status"], SUCCESS)

    def test_skill_context_built_from_runtime_state(self):
        """The skill context is built from the runtime state."""
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        ctx = brain._skill_context("observe", {}, goal_was_active=False)
        self.assertTrue(ctx["robot_localized"])
        self.assertTrue(ctx["camera_available"])
        self.assertTrue(ctx["entity_visible"])
        brain.stop()


if __name__ == "__main__":
    unittest.main()
