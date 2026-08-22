"""Tests for the full autonomy state machine.

Verifies:
  - All states are defined (BOOTING through EMERGENCY_STOP).
  - Transitions are explicit and invalid transitions are rejected.
  - Emergency conditions override normal operation.
  - State changes are observable and auditable.
  - The runtime drives transitions correctly (start → OBSERVING, step → AWARE, stop → SHUTTING_DOWN).
  - The step result includes autonomy state info.
"""

import unittest

from MAC_BRAIN.autonomy_state_machine import (
    AutonomyStateMachine, AutonomyStateMachineState as ASMState,
    TransitionRecord, Transition, CANONICAL_TRANSITIONS,
    BOOTING, INITIALIZING, OBSERVING, AWARE, INTERACTING, PLANNING,
    EXECUTING, LEARNING, MAINTENANCE, SAFE_DEGRADED,
    SHUTTING_DOWN, EMERGENCY_STOP, FAULT_RECOVERY,
)
from brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
from MAC_BRAIN.runtime import MacBrain, MacBrainConfig
from MAC_BRAIN.tests.test_mac_brain import FakeCamera


class CupBackend(DeterministicPerceptionBackend):
    def detect(self, frame):
        return (Detection("cup", 0.85, (0.1, 0.1, 0.5, 0.5)),)


class AutonomyStateMachineTests(unittest.TestCase):
    def test_initial_state_is_booting(self):
        sm = AutonomyStateMachine()
        self.assertEqual(sm.state, BOOTING)

    def test_all_states_defined(self):
        states = {s for s in ASMState}
        expected = {BOOTING, INITIALIZING, OBSERVING, AWARE, INTERACTING,
                    PLANNING, EXECUTING, LEARNING, MAINTENANCE, SAFE_DEGRADED,
                    SHUTTING_DOWN, EMERGENCY_STOP, FAULT_RECOVERY}
        self.assertEqual(states, expected)

    def test_boot_sequence(self):
        sm = AutonomyStateMachine()
        t1 = sm.transition("boot_complete")
        self.assertTrue(t1.accepted)
        self.assertEqual(sm.state, INITIALIZING)
        t2 = sm.transition("init_complete")
        self.assertTrue(t2.accepted)
        self.assertEqual(sm.state, OBSERVING)

    def test_invalid_transition_rejected(self):
        sm = AutonomyStateMachine()
        # Can't go from BOOTING to OBSERVING directly.
        t = sm.transition("significant_event")
        self.assertFalse(t.accepted)
        self.assertEqual(sm.state, BOOTING)

    def test_guard_failure_rejected(self):
        sm = AutonomyStateMachine()
        sm.transition("boot_complete")
        sm.transition("init_complete")
        # Guard fails.
        t = sm.transition("significant_event", guard_check=lambda: False)
        self.assertFalse(t.accepted)
        self.assertEqual(sm.state, OBSERVING)  # stayed

    def test_observing_to_aware(self):
        sm = AutonomyStateMachine()
        sm.transition("boot_complete")
        sm.transition("init_complete")
        t = sm.transition("significant_event")
        self.assertTrue(t.accepted)
        self.assertEqual(sm.state, AWARE)

    def test_aware_to_planning(self):
        sm = AutonomyStateMachine()
        sm.transition("boot_complete")
        sm.transition("init_complete")
        sm.transition("significant_event")
        t = sm.transition("planning_needed")
        self.assertTrue(t.accepted)
        self.assertEqual(sm.state, PLANNING)

    def test_aware_to_interacting(self):
        sm = AutonomyStateMachine()
        sm.transition("boot_complete")
        sm.transition("init_complete")
        sm.transition("significant_event")
        t = sm.transition("interaction_started")
        self.assertTrue(t.accepted)
        self.assertEqual(sm.state, INTERACTING)

    def test_planning_to_executing(self):
        sm = AutonomyStateMachine()
        sm._state = PLANNING
        t = sm.transition("plan_ready")
        self.assertTrue(t.accepted)
        self.assertEqual(sm.state, EXECUTING)

    def test_executing_to_observing(self):
        sm = AutonomyStateMachine()
        sm._state = EXECUTING
        t = sm.transition("action_completed")
        self.assertTrue(t.accepted)
        self.assertEqual(sm.state, OBSERVING)

    def test_emergency_stop_from_any_state(self):
        """Emergency conditions override normal operation."""
        for state in [OBSERVING, AWARE, INTERACTING, PLANNING, EXECUTING, LEARNING, MAINTENANCE, SAFE_DEGRADED]:
            sm = AutonomyStateMachine()
            sm._state = state
            t = sm.emergency_stop()
            self.assertTrue(t.accepted)
            self.assertEqual(sm.state, EMERGENCY_STOP)

    def test_emergency_stop_from_emergency_is_idempotent(self):
        sm = AutonomyStateMachine()
        sm._state = EMERGENCY_STOP
        t = sm.emergency_stop()
        self.assertTrue(t.accepted)
        self.assertEqual(sm.state, EMERGENCY_STOP)

    def test_shutdown_from_any_non_emergency_state(self):
        for state in [OBSERVING, AWARE, INTERACTING, PLANNING, EXECUTING, LEARNING, MAINTENANCE, SAFE_DEGRADED]:
            sm = AutonomyStateMachine()
            sm._state = state
            t = sm.shutdown()
            self.assertTrue(t.accepted)
            self.assertEqual(sm.state, SHUTTING_DOWN)

    def test_cannot_shutdown_from_emergency(self):
        sm = AutonomyStateMachine()
        sm._state = EMERGENCY_STOP
        t = sm.shutdown()
        self.assertFalse(t.accepted)
        self.assertEqual(sm.state, EMERGENCY_STOP)

    def test_transition_history_auditable(self):
        sm = AutonomyStateMachine()
        sm.transition("boot_complete")
        sm.transition("init_complete")
        sm.transition("significant_event")
        self.assertEqual(len(sm.transition_history), 3)
        self.assertTrue(all(t.accepted for t in sm.accepted_transitions))

    def test_rejected_transitions_tracked(self):
        sm = AutonomyStateMachine()
        sm.transition("invalid_event")  # no transition from BOOTING
        self.assertEqual(len(sm.rejected_transitions), 1)

    def test_available_events(self):
        sm = AutonomyStateMachine()
        events = sm.available_events()
        self.assertIn("boot_complete", events)
        self.assertNotIn("significant_event", events)  # not available from BOOTING

    def test_snapshot(self):
        sm = AutonomyStateMachine()
        sm.transition("boot_complete")
        snap = sm.snapshot()
        self.assertEqual(snap["state"], "INITIALIZING")
        self.assertIn("available_events", snap)
        self.assertIn("transition_count", snap)

    def test_is_operational(self):
        sm = AutonomyStateMachine()
        sm._state = OBSERVING
        self.assertTrue(sm.is_operational)
        sm._state = EMERGENCY_STOP
        self.assertFalse(sm.is_operational)

    def test_full_cycle(self):
        """Exercise a full state machine cycle deterministically."""
        sm = AutonomyStateMachine()
        # Boot.
        sm.transition("boot_complete")
        sm.transition("init_complete")
        self.assertEqual(sm.state, OBSERVING)
        # Detect something.
        sm.transition("significant_event")
        self.assertEqual(sm.state, AWARE)
        # Start planning.
        sm.transition("planning_needed")
        self.assertEqual(sm.state, PLANNING)
        # Execute.
        sm.transition("plan_ready")
        self.assertEqual(sm.state, EXECUTING)
        # Complete.
        sm.transition("action_completed")
        self.assertEqual(sm.state, OBSERVING)
        # Shutdown.
        sm.shutdown()
        self.assertEqual(sm.state, SHUTTING_DOWN)


class AutonomyStateMachineRuntimeIntegrationTests(unittest.TestCase):
    def test_state_machine_initialized(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        self.assertIsInstance(brain.autonomy_sm, AutonomyStateMachine)

    def test_start_transitions_to_observing(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        self.assertEqual(brain.autonomy_sm.state, OBSERVING)
        brain.stop()

    def test_stop_transitions_to_shutting_down(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.stop()
        self.assertEqual(brain.autonomy_sm.state, SHUTTING_DOWN)

    def test_step_transitions_to_aware_on_detection(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        # The state machine should have transitioned to AWARE during the step
        # (check via events), even if it returned to OBSERVING at the end.
        transition_events = [e for e in brain.events if e["event_type"] == "autonomy.transition"]
        aware_transitions = [e for e in transition_events if e["payload"]["destination"] == "AWARE"]
        self.assertGreater(len(aware_transitions), 0)
        brain.stop()

    def test_transition_events_emitted(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.stop()
        transition_events = [e for e in brain.events if e["event_type"] == "autonomy.transition"]
        self.assertGreater(len(transition_events), 0)

    def test_step_result_includes_autonomy_state(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        result = brain.step()
        brain.stop()
        self.assertIn("autonomy_state", result)
        self.assertIn("state", result["autonomy_state"])


if __name__ == "__main__":
    unittest.main()