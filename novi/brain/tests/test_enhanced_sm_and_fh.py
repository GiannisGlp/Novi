"""Tests for enhanced autonomy state machine and failure handler.

Verifies the improvements made during the review:
  - State machine transition table validation (completeness).
  - New transitions (AWARE→OBSERVING, INTERACTING→PLANNING, EXECUTING→INTERACTING, etc.).
  - Side effects on transitions.
  - Emergency/shutdown reachable from ALL states including BOOTING, INITIALIZING, FAULT_RECOVERY.
  - Configurable recovery thresholds per severity.
  - Condition-check recovery (recovery gated by a callable).
  - Component-level degradation tracking.
  - Per-category recovery tracking.
"""

import unittest

from novi.brain.autonomy_state_machine import (
    AWARE,
    BOOTING,
    CANONICAL_TRANSITIONS,
    EMERGENCY_STOP,
    EXECUTING,
    FAULT_RECOVERY,
    INITIALIZING,
    INTERACTING,
    LEARNING,
    MAINTENANCE,
    OBSERVING,
    PLANNING,
    SAFE_DEGRADED,
    SHUTTING_DOWN,
    AutonomyStateMachine,
)
from novi.brain.autonomy_state_machine import (
    AutonomyStateMachineState as ASMState,
)
from novi.brain.failure_modes import (
    MODEL_UNAVAILABLE,
    PERCEPTION_UNCERTAINTY,
    TOOL_FAILURE,
    DegradedMode,
    FailureHandler,
)


class TransitionTableValidationTests(unittest.TestCase):
    def test_validate_table_passes(self):
        """The transition table should pass validation."""
        sm = AutonomyStateMachine()
        result = sm.validate_table()
        self.assertTrue(result["valid"], f"Validation failed: {result}")
        self.assertEqual(result["states_without_outgoing"], [])
        self.assertEqual(result["missing_emergency_from"], [])
        self.assertEqual(result["missing_shutdown_from"], [])
        self.assertEqual(result["missing_observing_return_from"], [])

    def test_every_state_has_outgoing_transition(self):
        """Every state should have at least one outgoing transition."""
        all_states = set(ASMState)
        states_with_outgoing = {t.source for t in CANONICAL_TRANSITIONS}
        orphaned = all_states - states_with_outgoing
        self.assertEqual(orphaned, set(), f"States without outgoing transitions: {orphaned}")

    def test_emergency_reachable_from_all_operational_states(self):
        """EMERGENCY_STOP should be reachable from every operational state."""
        operational = {OBSERVING, AWARE, INTERACTING, PLANNING, EXECUTING,
                       LEARNING, MAINTENANCE, SAFE_DEGRADED, FAULT_RECOVERY,
                       BOOTING, INITIALIZING}
        for state in operational:
            sm = AutonomyStateMachine()
            sm._state = state
            t = sm.transition("emergency")
            self.assertTrue(t.accepted, f"Emergency not reachable from {state.value}")
            self.assertEqual(sm.state, EMERGENCY_STOP)

    def test_shutdown_reachable_from_all_non_emergency_states(self):
        """SHUTTING_DOWN should be reachable from every non-emergency state."""
        non_emergency = {OBSERVING, AWARE, INTERACTING, PLANNING, EXECUTING,
                         LEARNING, MAINTENANCE, SAFE_DEGRADED, FAULT_RECOVERY,
                         BOOTING, INITIALIZING}
        for state in non_emergency:
            sm = AutonomyStateMachine()
            sm._state = state
            t = sm.transition("shutdown_requested")
            self.assertTrue(t.accepted, f"Shutdown not reachable from {state.value}")
            self.assertEqual(sm.state, SHUTTING_DOWN)

    def test_total_transition_count_increased(self):
        """The enhanced table should have more transitions than the original."""
        # Original had ~40 transitions; enhanced should have significantly more.
        self.assertGreater(len(CANONICAL_TRANSITIONS), 50)


class NewTransitionsTests(unittest.TestCase):
    def test_aware_to_observing_not_significant(self):
        """AWARE → OBSERVING when event is no longer significant."""
        sm = AutonomyStateMachine()
        sm._state = AWARE
        t = sm.transition("no_longer_significant")
        self.assertTrue(t.accepted)
        self.assertEqual(sm.state, OBSERVING)

    def test_booting_to_fault_recovery(self):
        """BOOTING → FAULT_RECOVERY on boot failure."""
        sm = AutonomyStateMachine()
        t = sm.transition("boot_failed")
        self.assertTrue(t.accepted)
        self.assertEqual(sm.state, FAULT_RECOVERY)

    def test_interacting_to_planning(self):
        """INTERACTING → PLANNING when user requests something."""
        sm = AutonomyStateMachine()
        sm._state = INTERACTING
        t = sm.transition("planning_needed")
        self.assertTrue(t.accepted)
        self.assertEqual(sm.state, PLANNING)

    def test_executing_to_interacting(self):
        """EXECUTING → INTERACTING when person engages during execution."""
        sm = AutonomyStateMachine()
        sm._state = EXECUTING
        t = sm.transition("interaction_started")
        self.assertTrue(t.accepted)
        self.assertEqual(sm.state, INTERACTING)

    def test_executing_to_learning(self):
        """EXECUTING → LEARNING when learning opportunity arises after action."""
        sm = AutonomyStateMachine()
        sm._state = EXECUTING
        t = sm.transition("learning_opportunity")
        self.assertTrue(t.accepted)
        self.assertEqual(sm.state, LEARNING)

    def test_learning_to_aware(self):
        """LEARNING → AWARE when learning reveals something significant."""
        sm = AutonomyStateMachine()
        sm._state = LEARNING
        t = sm.transition("significant_event")
        self.assertTrue(t.accepted)
        self.assertEqual(sm.state, AWARE)

    def test_planning_to_safe_degraded(self):
        """PLANNING → SAFE_DEGRADED when component unavailable."""
        sm = AutonomyStateMachine()
        sm._state = PLANNING
        t = sm.transition("degradation_detected")
        self.assertTrue(t.accepted)
        self.assertEqual(sm.state, SAFE_DEGRADED)

    def test_executing_to_safe_degraded(self):
        """EXECUTING → SAFE_DEGRADED when component unavailable."""
        sm = AutonomyStateMachine()
        sm._state = EXECUTING
        t = sm.transition("degradation_detected")
        self.assertTrue(t.accepted)
        self.assertEqual(sm.state, SAFE_DEGRADED)

    def test_observing_to_learning(self):
        """OBSERVING → LEARNING during idle background learning."""
        sm = AutonomyStateMachine()
        sm._state = OBSERVING
        t = sm.transition("learning_opportunity")
        self.assertTrue(t.accepted)
        self.assertEqual(sm.state, LEARNING)

    def test_observing_to_maintenance(self):
        """OBSERVING → MAINTENANCE for periodic diagnostics."""
        sm = AutonomyStateMachine()
        sm._state = OBSERVING
        t = sm.transition("maintenance_needed")
        self.assertTrue(t.accepted)
        self.assertEqual(sm.state, MAINTENANCE)

    def test_fault_recovery_to_booting(self):
        """FAULT_RECOVERY → BOOTING for full restart."""
        sm = AutonomyStateMachine()
        sm._state = FAULT_RECOVERY
        t = sm.transition("full_restart")
        self.assertTrue(t.accepted)
        self.assertEqual(sm.state, BOOTING)

    def test_shutting_down_to_booting(self):
        """SHUTTING_DOWN → BOOTING for restart."""
        sm = AutonomyStateMachine()
        sm._state = SHUTTING_DOWN
        t = sm.transition("restart_requested")
        self.assertTrue(t.accepted)
        self.assertEqual(sm.state, BOOTING)

    def test_safe_degraded_to_maintenance(self):
        """SAFE_DEGRADED → MAINTENANCE for diagnostics during degradation."""
        sm = AutonomyStateMachine()
        sm._state = SAFE_DEGRADED
        t = sm.transition("maintenance_needed")
        self.assertTrue(t.accepted)
        self.assertEqual(sm.state, MAINTENANCE)

    def test_safe_degraded_to_learning(self):
        """SAFE_DEGRADED → LEARNING for limited consolidation."""
        sm = AutonomyStateMachine()
        sm._state = SAFE_DEGRADED
        t = sm.transition("learning_opportunity")
        self.assertTrue(t.accepted)
        self.assertEqual(sm.state, LEARNING)


class SideEffectsTests(unittest.TestCase):
    def test_transitions_have_side_effects(self):
        """Most transitions should have non-empty side effects."""
        with_effects = sum(1 for t in CANONICAL_TRANSITIONS if t.side_effects)
        without_effects = sum(1 for t in CANONICAL_TRANSITIONS if not t.side_effects)
        # The majority should have side effects.
        self.assertGreater(with_effects, without_effects)

    def test_emergency_transition_has_stop_all_actions(self):
        """Emergency transitions should include stop_all_actions side effect."""
        sm = AutonomyStateMachine()
        sm._state = EXECUTING
        t = sm.emergency_stop()
        self.assertIn("stop_all_actions", t.side_effects)
        self.assertIn("preserve_state", t.side_effects)
        self.assertIn("audit", t.side_effects)

    def test_shutdown_transition_has_cleanup(self):
        """Shutdown transitions should include cleanup and persist_state."""
        sm = AutonomyStateMachine()
        sm._state = OBSERVING
        t = sm.shutdown()
        self.assertIn("cleanup", t.side_effects)
        self.assertIn("persist_state", t.side_effects)

    def test_execution_transition_has_dispatch_action(self):
        """AWARE → EXECUTING should include dispatch_action."""
        sm = AutonomyStateMachine()
        sm._state = AWARE
        t = sm.transition("execution_ready")
        self.assertIn("dispatch_action", t.side_effects)

    def test_action_completed_has_record_outcome(self):
        """EXECUTING → OBSERVING should include record_outcome."""
        sm = AutonomyStateMachine()
        sm._state = EXECUTING
        t = sm.transition("action_completed")
        self.assertIn("record_outcome", t.side_effects)
        self.assertIn("update_world_state", t.side_effects)


class ConfigurableRecoveryThresholdsTests(unittest.TestCase):
    def test_default_thresholds(self):
        fh = FailureHandler()
        # Default: warning=3, error=5, critical=10, info=1
        fh.report_failure(PERCEPTION_UNCERTAINTY, severity="warning", component="perception")
        self.assertFalse(fh.attempt_recovery())
        self.assertFalse(fh.attempt_recovery())
        self.assertTrue(fh.attempt_recovery())  # 3rd attempt succeeds

    def test_error_severity_threshold_is_5(self):
        fh = FailureHandler()
        fh.report_failure(PERCEPTION_UNCERTAINTY, severity="error", component="perception")
        for _ in range(4):
            self.assertFalse(fh.attempt_recovery())
        self.assertTrue(fh.attempt_recovery())  # 5th attempt succeeds

    def test_critical_severity_threshold_is_10(self):
        fh = FailureHandler()
        fh.report_failure(TOOL_FAILURE, severity="critical", component="skill")
        for _ in range(9):
            self.assertFalse(fh.attempt_recovery())
        self.assertTrue(fh.attempt_recovery())  # 10th attempt succeeds

    def test_info_severity_threshold_is_1(self):
        fh = FailureHandler()
        fh.report_failure(PERCEPTION_UNCERTAINTY, severity="info", component="perception")
        self.assertTrue(fh.attempt_recovery())  # 1st attempt succeeds

    def test_custom_thresholds(self):
        """Custom recovery thresholds can be configured."""
        fh = FailureHandler(recovery_thresholds={"warning": 1, "error": 2, "critical": 3, "info": 1})
        fh.report_failure(PERCEPTION_UNCERTAINTY, severity="warning", component="perception")
        self.assertTrue(fh.attempt_recovery())  # 1st attempt succeeds (custom threshold)


class ConditionCheckRecoveryTests(unittest.TestCase):
    def test_recovery_blocked_by_condition_check(self):
        """Recovery is blocked when condition_check returns False."""
        fh = FailureHandler()
        fh.report_failure(MODEL_UNAVAILABLE, severity="warning", component="reasoning")
        for _ in range(3):
            # Even after threshold is met, condition_check blocks recovery.
            self.assertFalse(fh.attempt_recovery(condition_check=lambda: False))

    def test_recovery_allowed_when_condition_met(self):
        """Recovery succeeds when condition_check returns True after threshold."""
        fh = FailureHandler()
        fh.report_failure(MODEL_UNAVAILABLE, severity="warning", component="reasoning")
        self.assertFalse(fh.attempt_recovery(condition_check=lambda: True))
        self.assertFalse(fh.attempt_recovery(condition_check=lambda: True))
        self.assertTrue(fh.attempt_recovery(condition_check=lambda: True))  # 3rd + condition met

    def test_condition_check_without_threshold_not_enough(self):
        """Condition check alone is not enough; threshold must also be met."""
        fh = FailureHandler()
        fh.report_failure(MODEL_UNAVAILABLE, severity="error", component="reasoning")  # threshold=5
        # Even with condition=True, threshold not met.
        for _ in range(4):
            self.assertFalse(fh.attempt_recovery(condition_check=lambda: True))
        self.assertTrue(fh.attempt_recovery(condition_check=lambda: True))  # 5th + condition met


class ComponentTrackingTests(unittest.TestCase):
    def test_degraded_components_tracked(self):
        """The handler tracks which components are degraded."""
        fh = FailureHandler()
        fh.report_failure(PERCEPTION_UNCERTAINTY, component="perception", message="test")
        fh.report_failure(MODEL_UNAVAILABLE, component="reasoning", message="test")
        self.assertIn("perception", fh.degraded_components)
        self.assertIn("reasoning", fh.degraded_components)

    def test_clear_component(self):
        """clear_component removes a component from the degraded set."""
        fh = FailureHandler()
        fh.report_failure(PERCEPTION_UNCERTAINTY, component="perception", message="test")
        fh.report_failure(MODEL_UNAVAILABLE, component="reasoning", message="test")
        fh.clear_component("perception")
        self.assertNotIn("perception", fh.degraded_components)
        self.assertIn("reasoning", fh.degraded_components)

    def test_clearing_all_components_returns_to_normal(self):
        """Clearing all degraded components returns to normal mode."""
        fh = FailureHandler()
        fh.report_failure(PERCEPTION_UNCERTAINTY, component="perception", message="test")
        fh.report_failure(MODEL_UNAVAILABLE, component="reasoning", message="test")
        self.assertTrue(fh.is_degraded)
        fh.clear_component("perception")
        self.assertTrue(fh.is_degraded)  # reasoning still degraded
        fh.clear_component("reasoning")
        self.assertFalse(fh.is_degraded)
        self.assertEqual(fh.degraded_mode, DegradedMode.NORMAL)

    def test_snapshot_includes_degraded_components(self):
        fh = FailureHandler()
        fh.report_failure(PERCEPTION_UNCERTAINTY, component="perception", message="test")
        snap = fh.snapshot()
        self.assertIn("degraded_components", snap)
        self.assertIn("perception", snap["degraded_components"])

    def test_failures_by_component(self):
        fh = FailureHandler()
        fh.report_failure(PERCEPTION_UNCERTAINTY, component="perception", message="a")
        fh.report_failure(MODEL_UNAVAILABLE, component="reasoning", message="b")
        fh.report_failure(PERCEPTION_UNCERTAINTY, component="perception", message="c")
        self.assertEqual(len(fh.failures_by_component("perception")), 2)
        self.assertEqual(len(fh.failures_by_component("reasoning")), 1)


class TransitionsFromStateTests(unittest.TestCase):
    def test_transitions_from_observing(self):
        sm = AutonomyStateMachine()
        transitions = sm.transitions_from(OBSERVING)
        events = {t.event for t in transitions}
        self.assertIn("significant_event", events)
        self.assertIn("person_detected", events)
        self.assertIn("goal_set", events)
        self.assertIn("learning_opportunity", events)
        self.assertIn("maintenance_needed", events)
        self.assertIn("emergency", events)
        self.assertIn("shutdown_requested", events)

    def test_transitions_from_executing(self):
        sm = AutonomyStateMachine()
        transitions = sm.transitions_from(EXECUTING)
        events = {t.event for t in transitions}
        self.assertIn("action_completed", events)
        self.assertIn("action_failed", events)
        self.assertIn("interaction_started", events)
        self.assertIn("learning_opportunity", events)
        self.assertIn("degradation_detected", events)
        self.assertIn("emergency", events)


if __name__ == "__main__":
    unittest.main()
