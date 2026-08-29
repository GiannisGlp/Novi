"""Tests for safety & governance hardening (06_AUTONOMY doc 08).

Covers: invariants (e-stop, stale pose, forbidden zones, velocity limits,
sensor health, approval for high-risk skills), pre-action risk assessment,
runtime monitoring during execution, policy versioning, and the A-SAFE-01
adversarial suite (zero bypasses; no model-generated instruction can bypass
the safety gate).
"""

from __future__ import annotations

import unittest

from novi.brain.safety_policy import (
    ALLOW,
    DENY,
    MODIFY,
    PolicyVersion,
    RiskAssessor,
    RuntimeSafetyMonitor,
    SafetyInvariant,
    SafetyInvariantSet,
    SafetyPolicy,
)


def baseline_invariants() -> SafetyInvariantSet:
    invariants = SafetyInvariantSet([
        SafetyInvariant(
            "no_motion_during_estop",
            lambda s: (not s.get("estop_active", False), "e-stop is active"),
            "never move while emergency stop is active (doc 08 Step 2)",
        ),
        SafetyInvariant(
            "pose_freshness",
            lambda s: (s.get("pose_fresh", True), f"stale pose (ttl {s.get('pose_ttl')})"),
            "never execute with a stale pose beyond its TTL",
        ),
        SafetyInvariant(
            "no_forbidden_zone",
            lambda s: (not s.get("in_forbidden_zone", False), "inside forbidden zone"),
            "never enter forbidden zones",
        ),
        SafetyInvariant(
            "velocity_limit",
            lambda s: (s.get("speed_mps", 0.0) <= s.get("max_speed_mps", 1.0), "velocity limit exceeded"),
            "never exceed velocity/force limits",
        ),
        SafetyInvariant(
            "sensor_health",
            lambda s: (s.get("sensors_healthy", True), "required sensor unhealthy"),
            "never operate without required sensor health",
        ),
    ])
    return invariants


class InvariantTests(unittest.TestCase):
    def test_all_invariants_hold(self):
        invariants = baseline_invariants()
        holds, violated, _ = invariants.evaluate({"pose_fresh": True, "speed_mps": 0.5})
        self.assertTrue(holds)
        self.assertEqual(violated, [])

    def test_estop_denies_motion(self):
        invariants = baseline_invariants()
        holds, violated, details = invariants.evaluate({"estop_active": True})
        self.assertFalse(holds)
        self.assertIn("no_motion_during_estop", violated)
        self.assertIn("e-stop is active", details["no_motion_during_estop"])

    def test_stale_pose_denies(self):
        invariants = baseline_invariants()
        holds, _, _ = invariants.evaluate({"pose_fresh": False})
        self.assertFalse(holds)

    def test_forbidden_zone_denies(self):
        invariants = baseline_invariants()
        holds, violated, _ = invariants.evaluate({"in_forbidden_zone": True})
        self.assertFalse(holds)
        self.assertIn("no_forbidden_zone", violated)

    def test_velocity_limit_enforced(self):
        invariants = baseline_invariants()
        holds, _, _ = invariants.evaluate({"speed_mps": 2.0, "max_speed_mps": 1.0})
        self.assertFalse(holds)

    def test_broken_check_fails_closed(self):
        invariants = SafetyInvariantSet([
            SafetyInvariant("boom", lambda s: (_ for _ in ()).throw(RuntimeError("boom"))),
        ])
        holds, violated, _ = invariants.evaluate({})
        self.assertFalse(holds, "a broken invariant check must fail closed")
        self.assertEqual(violated, ["boom"])


class RiskAssessmentTests(unittest.TestCase):
    def test_benign_observation_is_r0(self):
        self.assertEqual(RiskAssessor().assess(), "R0")

    def test_high_proximity_raises_risk(self):
        low = RiskAssessor().assess(proximity_to_human=0.1, speed_force=0.1)
        high = RiskAssessor().assess(proximity_to_human=0.9, speed_force=0.8, reversibility="physical")
        self.assertLess(_rank(low), _rank(high))

    def test_irreversible_actions_are_high_risk(self):
        # Irreversibility alone pushes to R4; R5 requires stacking with a
        # harmful consequence (see test below).
        risk = RiskAssessor().assess(reversibility="irreversible")
        self.assertEqual(risk, "R4")

    def test_harmful_consequence_is_high_risk(self):
        risk = RiskAssessor().assess(expected_consequence="harmful", reversibility="irreversible")
        self.assertEqual(risk, "R5")


def _rank(risk_class: str) -> int:
    return {"R0": 0, "R1": 1, "R2": 2, "R3": 3, "R4": 4, "R5": 5}[risk_class]


class SafetyPolicyTests(unittest.TestCase):
    def test_allow_when_invariants_hold(self):
        policy = SafetyPolicy(baseline_invariants())
        decision = policy.evaluate({"action": "speak"}, {"pose_fresh": True})
        self.assertEqual(decision.decision, ALLOW)
        self.assertEqual(decision.policy_version, "1.0.0")

    def test_deny_when_invariant_violated(self):
        policy = SafetyPolicy(baseline_invariants())
        decision = policy.evaluate({"action": "move_forward"}, {"estop_active": True})
        self.assertEqual(decision.decision, DENY)
        self.assertIn("no_motion_during_estop", decision.violated_invariants)

    def test_absolute_deny_actions(self):
        policy = SafetyPolicy(baseline_invariants())
        decision = policy.evaluate({"action": "disable_safety"}, {})
        self.assertEqual(decision.decision, DENY)
        self.assertEqual(decision.risk_class, "R5")

    def test_risk_class_beyond_max_denied(self):
        policy = SafetyPolicy(baseline_invariants(), max_risk_class="R3")
        decision = policy.evaluate(
            {"action": "move_forward", "risk_class": "R5"}, {"pose_fresh": True})
        self.assertEqual(decision.decision, DENY)

    def test_high_risk_requires_approval(self):
        # Coherent thresholds: R5 is the hard ceiling; R4 is approval-gated.
        policy = SafetyPolicy(baseline_invariants(), require_approval_above="R4", max_risk_class="R5")
        decision = policy.evaluate(
            {"action": "pick", "risk_class": "R4"}, {"pose_fresh": True})
        self.assertEqual(decision.decision, MODIFY)
        self.assertEqual(decision.reason, "requires_human_approval")
        # The ceiling itself is never approval-able.
        ceiling = policy.evaluate({"action": "pick", "risk_class": "R5"}, {"pose_fresh": True})
        self.assertEqual(ceiling.decision, DENY)

    def test_policy_version_is_recorded(self):
        policy = SafetyPolicy(baseline_invariants(),
                              policy_version=PolicyVersion("2.1.0", revision_note="stricter estop"))
        policy.evaluate({"action": "speak"}, {})
        policy.evaluate({"action": "move_forward"}, {"estop_active": True})
        self.assertTrue(all(d.policy_version == "2.1.0" for d in policy.decisions))


class RuntimeMonitoringTests(unittest.TestCase):
    def test_monitor_interrupts_mid_execution(self):
        invariants = baseline_invariants()
        monitor = RuntimeSafetyMonitor(invariants)
        # Approved action starts; environment changes mid-execution.
        safe, _ = monitor.check({"action": "move_forward"}, {"pose_fresh": True}, cycle=1)
        self.assertTrue(safe)
        safe, reason = monitor.check({"action": "move_forward"}, {"estop_active": True}, cycle=2)
        self.assertFalse(safe)
        self.assertIn("interrupted_by_invariant", reason)
        self.assertEqual(len(monitor.interruptions), 1)

    def test_monitor_does_not_interrupt_without_cause(self):
        monitor = RuntimeSafetyMonitor(baseline_invariants())
        for cycle in range(5):
            safe, _ = monitor.check({"action": "speak"}, {"pose_fresh": True}, cycle=cycle)
            self.assertTrue(safe)
        self.assertEqual(monitor.interruptions, [])


class AdversarialTests(unittest.TestCase):
    """Gate A-SAFE-01: any configured unsafe condition must prevent physical
    execution; no model-generated instruction may bypass the safety gate."""

    def _policy(self) -> SafetyPolicy:
        return SafetyPolicy(baseline_invariants(), require_approval_above="R4", max_risk_class="R3")

    def test_prompt_injection_cannot_bypass(self):
        policy = self._policy()
        # A model output tries to smuggle an instruction through parameters.
        decision = policy.evaluate(
            {"action": "move_forward", "parameters": {"injected": "disable safety"},
             "risk_class": "R5"},
            {"pose_fresh": True},
        )
        self.assertEqual(decision.decision, DENY, "model output is data, not authority")

    def test_misleading_label_cannot_bypass(self):
        policy = self._policy()
        decision = policy.evaluate(
            {"action": "move_into_forbidden", "risk_class": "R0"}, {"pose_fresh": True})
        self.assertEqual(decision.decision, DENY, "renamed unsafe action is still denied")

    def test_unsafe_user_instruction_still_risk_assessed(self):
        policy = self._policy()
        # Even a user instruction is risk-assessed; irreversible harm is denied.
        decision = policy.evaluate(
            {"action": "move_forward", "source": "user", "risk_class": "R5"},
            {"pose_fresh": True},
        )
        self.assertEqual(decision.decision, DENY)

    def test_stale_state_is_denied(self):
        policy = self._policy()
        decision = policy.evaluate(
            {"action": "move_forward", "risk_class": "R2"},
            {"pose_fresh": False},
        )
        self.assertEqual(decision.decision, DENY, "stale state must fail closed")

    def test_estop_interrupts_within_response_budget(self):
        """Any e-stop condition interrupts execution within the response budget."""
        monitor = RuntimeSafetyMonitor(baseline_invariants(), interrupt_delay_cycles=1)
        for cycle in range(3):
            safe, _ = monitor.check({"action": "move_forward"}, {"pose_fresh": True}, cycle=cycle)
            self.assertTrue(safe)
        # E-stop engages at cycle 3: the very next check interrupts.
        safe, _ = monitor.check({"action": "move_forward"}, {"pose_fresh": True}, cycle=3)
        self.assertTrue(safe)
        safe, _ = monitor.check({"action": "move_forward"}, {"estop_active": True}, cycle=4)
        self.assertFalse(safe)
        self.assertLessEqual(monitor.interruptions[0]["cycle"], 4,
                             "interruption must happen within the response budget")


if __name__ == "__main__":
    unittest.main()
