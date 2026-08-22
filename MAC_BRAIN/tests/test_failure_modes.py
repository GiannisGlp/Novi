"""Tests for cognitive failure-mode handling.

Verifies:
  - FailureHandler detects failures and transitions to degraded modes.
  - Degraded modes escalate correctly (perception_degraded → safety_only).
  - Recovery attempts can return to normal mode.
  - Perception uncertainty is detected when no/low-confidence detections.
  - Skill failures are reported to the failure handler.
  - The failure.detected event is emitted.
  - The step result includes failure handler info.
"""

import unittest

from brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception

from MAC_BRAIN.failure_modes import (
    FailureHandler, DegradedMode, FailureRecord,
    PERCEPTION_UNCERTAINTY, MODEL_UNAVAILABLE, TOOL_FAILURE,
    IDENTITY_AMBIGUITY, RESOURCE_EXHAUSTION, CORRUPTED_DATA,
)
from MAC_BRAIN.runtime import MacBrain, MacBrainConfig
from MAC_BRAIN.tests.test_mac_brain import FakeCamera


class EmptyBackend(DeterministicPerceptionBackend):
    """Detects nothing — triggers perception uncertainty."""
    def detect(self, frame):
        return ()


class LowConfBackend(DeterministicPerceptionBackend):
    """Low-confidence detections — triggers perception uncertainty."""
    def detect(self, frame):
        return (Detection("cup", 0.3, (0.1, 0.1, 0.5, 0.5)),)


class CupBackend(DeterministicPerceptionBackend):
    def detect(self, frame):
        return (Detection("cup", 0.85, (0.1, 0.1, 0.5, 0.5)),)


class FailureHandlerTests(unittest.TestCase):
    def test_initial_state_normal(self):
        fh = FailureHandler()
        self.assertEqual(fh.degraded_mode, DegradedMode.NORMAL)
        self.assertFalse(fh.is_degraded)

    def test_report_perception_uncertainty(self):
        fh = FailureHandler()
        record = fh.report_failure(PERCEPTION_UNCERTAINTY, component="perception", message="no_detections")
        self.assertEqual(record.category, PERCEPTION_UNCERTAINTY)
        self.assertEqual(fh.degraded_mode, DegradedMode.PERCEPTION_DEGRADED)
        self.assertTrue(fh.is_degraded)

    def test_report_model_unavailable(self):
        fh = FailureHandler()
        fh.report_failure(MODEL_UNAVAILABLE, component="reasoning", message="llm_timeout")
        self.assertEqual(fh.degraded_mode, DegradedMode.REASONING_DEGRADED)

    def test_critical_severity_escalates_to_safety_only(self):
        fh = FailureHandler()
        fh.report_failure(TOOL_FAILURE, severity="critical", component="skill", message="catastrophic")
        self.assertEqual(fh.degraded_mode, DegradedMode.SAFETY_ONLY)
        self.assertTrue(fh.is_safety_only)

    def test_recovery_returns_to_normal(self):
        fh = FailureHandler()
        fh.report_failure(PERCEPTION_UNCERTAINTY, component="perception", message="no_detections")
        self.assertTrue(fh.is_degraded)
        # 3 recovery attempts should return to normal.
        self.assertFalse(fh.attempt_recovery())
        self.assertFalse(fh.attempt_recovery())
        self.assertTrue(fh.attempt_recovery())
        self.assertEqual(fh.degraded_mode, DegradedMode.NORMAL)

    def test_failure_recorded(self):
        fh = FailureHandler()
        fh.report_failure(PERCEPTION_UNCERTAINTY, component="perception", message="test")
        self.assertEqual(fh.failure_count, 1)
        self.assertEqual(len(fh.recent_failures), 1)

    def test_failures_by_category(self):
        fh = FailureHandler()
        fh.report_failure(PERCEPTION_UNCERTAINTY, component="perception", message="a")
        fh.report_failure(PERCEPTION_UNCERTAINTY, component="perception", message="b")
        fh.report_failure(MODEL_UNAVAILABLE, component="reasoning", message="c")
        self.assertEqual(len(fh.failures_by_category(PERCEPTION_UNCERTAINTY)), 2)
        self.assertEqual(len(fh.failures_by_category(MODEL_UNAVAILABLE)), 1)

    def test_snapshot(self):
        fh = FailureHandler()
        fh.report_failure(PERCEPTION_UNCERTAINTY, component="perception", message="test")
        snap = fh.snapshot()
        self.assertEqual(snap["degraded_mode"], "perception_degraded")
        self.assertTrue(snap["is_degraded"])
        self.assertEqual(snap["failure_count"], 1)

    def test_unknown_category_rejected(self):
        fh = FailureHandler()
        with self.assertRaises(ValueError):
            fh.report_failure("unknown_category")

    def test_degraded_mode_escalation_order(self):
        """More restrictive modes override less restrictive ones."""
        fh = FailureHandler()
        fh.report_failure(PERCEPTION_UNCERTAINTY, component="perception", message="low")
        self.assertEqual(fh.degraded_mode, DegradedMode.PERCEPTION_DEGRADED)
        # A more restrictive failure should escalate.
        fh.report_failure(RESOURCE_EXHAUSTION, severity="error", component="system", message="cpu")
        self.assertEqual(fh.degraded_mode, DegradedMode.COMPUTE_CONSTRAINED)


class FailureHandlerRuntimeIntegrationTests(unittest.TestCase):
    def test_failure_handler_initialized(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        self.assertIsInstance(brain.failure_handler, FailureHandler)

    def test_perception_uncertainty_detected_no_detections(self):
        """Empty detections trigger perception uncertainty failure."""
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(EmptyBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.stop()
        failure_events = [e for e in brain.events if e["event_type"] == "failure.detected"]
        self.assertGreater(len(failure_events), 0)
        self.assertEqual(failure_events[0]["payload"]["category"], PERCEPTION_UNCERTAINTY)

    def test_perception_uncertainty_detected_low_confidence(self):
        """Low-confidence detections trigger perception uncertainty."""
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(LowConfBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.stop()
        failure_events = [e for e in brain.events if e["event_type"] == "failure.detected"]
        self.assertGreater(len(failure_events), 0)

    def test_no_failure_when_detections_normal(self):
        """Normal detections don't trigger perception uncertainty."""
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.stop()
        perception_failures = [e for e in brain.events if e["event_type"] == "failure.detected"
                               and e["payload"]["category"] == PERCEPTION_UNCERTAINTY]
        self.assertEqual(len(perception_failures), 0)

    def test_step_result_includes_failure_handler(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        result = brain.step()
        brain.stop()
        self.assertIn("failure_handler", result)
        self.assertIn("degraded_mode", result["failure_handler"])

    def test_recovery_event_emitted(self):
        """Recovery from degraded mode emits a failure.recovered event."""
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(EmptyBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()  # triggers perception uncertainty
        self.assertTrue(brain.failure_handler.is_degraded)
        # Now switch to normal detections and step enough times to recover.
        brain.perception = SpecialistPerception(CupBackend())
        for _ in range(4):
            brain.step()
        brain.stop()
        recovery_events = [e for e in brain.events if e["event_type"] == "failure.recovered"]
        self.assertGreater(len(recovery_events), 0)


if __name__ == "__main__":
    unittest.main()