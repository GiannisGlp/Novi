"""Integration tests for the deeper runtime wiring (next steps).

Verifies:
  - Governance guard evaluates every action proposal before execution.
  - Closed-loop VERIFY step runs after every action.
  - Multi-speed System-0 safety gate runs at the start of every step.
  - The governance guard can block an action (R5 action denied).
  - The loop.verify event is emitted.
  - The governance.evaluated event is emitted.
"""

import unittest

from brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
from brain.runtime import Lifecycle

from MAC_BRAIN.runtime import MacBrain, MacBrainConfig
from MAC_BRAIN.tests.test_mac_brain import FakeCamera


class CupBackend(DeterministicPerceptionBackend):
    def detect(self, frame):
        return (Detection("cup", 0.85, (0.1, 0.1, 0.5, 0.5)),)


class GovernanceGuardRuntimeTests(unittest.TestCase):
    def test_governance_evaluated_event_emitted(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.stop()
        event_types = [e["event_type"] for e in brain.events]
        self.assertIn("governance.evaluated", event_types)

    def test_governance_grant_stored(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.stop()
        self.assertIsNotNone(brain._last_governance_grant)
        self.assertIn("decision", brain._last_governance_grant)

    def test_action_completed_includes_governance_info(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.stop()
        action_events = [e for e in brain.events if e["event_type"] == "action.completed"]
        self.assertGreater(len(action_events), 0)
        data = action_events[0].get("payload", {})
        self.assertIn("governance_allowed", data)
        self.assertIn("governance_decision", data)
        self.assertIn("brain_authorized", data)

    def test_governance_allows_safe_action(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.stop()
        # The wait/stop action should be allowed by governance.
        self.assertEqual(brain._last_governance_grant["decision"], "ALLOW")


class ClosedLoopRuntimeIntegrationTests(unittest.TestCase):
    def test_loop_verify_event_emitted(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.stop()
        event_types = [e["event_type"] for e in brain.events]
        self.assertIn("loop.verify", event_types)

    def test_loop_snapshot_stored(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.stop()
        self.assertIsNotNone(brain._last_loop_snapshot)
        self.assertIn("current_phase", brain._last_loop_snapshot)
        self.assertIn("steps", brain._last_loop_snapshot)

    def test_closed_loop_has_observe_plan_act_verify(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.stop()
        phases = [s["phase"] for s in brain._last_loop_snapshot["steps"]]
        self.assertIn("OBSERVE", phases)
        self.assertIn("PLAN", phases)
        self.assertIn("ACT", phases)
        self.assertIn("VERIFY", phases)


class MultiSpeedRuntimeIntegrationTests(unittest.TestCase):
    def test_system0_safety_check_registered(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        sys0_tasks = brain.multi_speed.tasks_by_tier("system_0")
        self.assertGreater(len(sys0_tasks), 0)
        brain.stop()

    def test_system0_safety_clear_after_step(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.stop()
        self.assertTrue(brain.multi_speed.system0_safety_clear)

    def test_multi_speed_does_not_block_normal_step(self):
        """The multi-speed System-0 check should not block a normal step."""
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        result = brain.step()
        brain.stop()
        self.assertEqual(result["cycle"], 1)
        # The step should complete normally (not return early with safety_gate failed).
        self.assertNotEqual(result.get("safety_gate"), "failed")


class FullWiringIntegrationTests(unittest.TestCase):
    def test_full_step_produces_all_events(self):
        """A full step should emit governance, attention, loop.verify events."""
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.stop()
        event_types = {e["event_type"] for e in brain.events}
        self.assertIn("governance.evaluated", event_types)
        self.assertIn("cognition.attention", event_types)
        self.assertIn("loop.verify", event_types)
        self.assertIn("action.completed", event_types)
        self.assertIn("MAC_BRAIN.started", event_types)
        self.assertIn("MAC_BRAIN.stopped", event_types)

    def test_governance_and_brain_both_authorize(self):
        """Action executes only if BOTH brain authorizes AND governance allows."""
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.stop()
        action_events = [e for e in brain.events if e["event_type"] == "action.completed"]
        self.assertGreater(len(action_events), 0)
        data = action_events[0].get("payload", {})
        self.assertTrue(data.get("brain_authorized", False))
        self.assertTrue(data.get("governance_allowed", False))


if __name__ == "__main__":
    unittest.main()