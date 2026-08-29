"""Phase 2a (north-star gap analysis): the safety boundary becomes the
production action path.

docs/audits/NOVI_NORTH_STAR_GAP_ANALYSIS_2026-08-29.md §4 Phase 2a:
"Route action execution through AutonomySupervisor + SafetyPolicy. Insert
SafetyPolicy.evaluate() + RuntimeSafetyMonitor.check() around body.execute()."

Acceptance:
- SafetyPolicy.evaluate() gates every engine action before skill execution
  (invariant violation / risk overshoot / absolute-deny => not executed);
- RuntimeSafetyMonitor.check() surrounds body.execute(): a previously
  approved action whose world state turns unsafe is interrupted (fail
  closed, emergency-stop transition);
- the default path (R0/R1 actions, healthy state) is behaviorally unchanged;
- STOP / monitor-interrupt transition the autonomy state machine.
"""

from __future__ import annotations

import unittest
from typing import Any

from novi.brain.autonomy_state_machine import AutonomyStateMachineState as ASMState
from novi.brain.b2_perception import SpecialistPerception
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.io import CameraFrame
from novi.brain.safety_policy import (
    PolicyVersion,
    RuntimeSafetyMonitor,
    SafetyInvariantSet,
    SafetyPolicy,
)


class FrameCamera:
    """Camera yielding frames with unique provenance-carrying ids."""

    def __init__(self) -> None:
        self.sequence = 0

    def close(self) -> None:
        self.sequence = self.sequence

    def read(self) -> CameraFrame:
        self.sequence += 1
        return CameraFrame(
            frame_id=f"f-{self.sequence}",
            captured_at="2026-08-29T12:00:00Z",
            width=2,
            height=2,
            payload=b"frame",
            metadata={"backend": "test"},
        )


class QuietPerception:
    def detect(self, frame):
        return ()

    def depth(self, frame):
        return None

    def segment(self, frame):
        return None


def _brain(safety_policy=None, safety_monitor=None) -> MacBrain:
    return MacBrain(
        camera=FrameCamera(),
        perception=SpecialistPerception(QuietPerception()),
        safety_policy=safety_policy,
        safety_monitor=safety_monitor,
        config=MacBrainConfig(curiosity_enabled=False),
    )


class AlwaysViolated:
    """An invariant set whose every evaluation fails closed."""

    def evaluate(self, state):
        return False, ["test_invariant"], {"test_invariant": "forced for test"}


class FlipFlopInvariant:
    """Passes on the first N evaluations, then fails (models a world change)."""

    name = "world_changed"

    def __init__(self, allow_evaluations: int) -> None:
        self._remaining = allow_evaluations

    def holds(self, state):
        if self._remaining > 0:
            self._remaining -= 1
            return True, ""
        return False, "state flipped mid-run"


class StopDecisionPolicy:
    """A crafted policy that always answers STOP."""

    class _Decision:
        decision = "STOP"
        reason = "test_estop"
        allowed = False
        violated_invariants: tuple[str, ...] = ()
        decision_id = "sd-test-stop"
        risk_class = "R5"

        def snapshot(self) -> dict[str, Any]:
            return {"decision": "STOP", "reason": "test_estop", "decision_id": "sd-test-stop"}

    def evaluate(self, proposal, world_state):
        return self._Decision()


class SafetyGateTests(unittest.TestCase):
    def test_safety_gate_present_by_default(self):
        brain = _brain()
        brain.start()
        try:
            result = brain.step()
            self.assertTrue(result["authorized"])
            self.assertTrue(result["safety"]["allowed"])
            self.assertEqual(result["safety"]["decision"], "ALLOW")
            # A quiet cycle proposes "observe" -> R0; virtual-body motions are
            # R1. Both are inside the policy's default R3 budget.
            self.assertIn(result["safety"]["risk_class"], ("R0", "R1"))
            events = [e["event_type"] for e in brain.events]
            self.assertIn("safety.evaluated", events)
        finally:
            brain.stop()

    def test_invariant_violation_denies_execution(self):
        policy = SafetyPolicy(AlwaysViolated())
        brain = _brain(safety_policy=policy)
        brain.start()
        try:
            result = brain.step()
            self.assertFalse(result["authorized"])
            self.assertFalse(result["safety"]["allowed"])
            self.assertEqual(result["safety"]["decision"], "DENY")
            self.assertIn("test_invariant", result["safety"]["violated"])
            events = [e["event_type"] for e in brain.events]
            self.assertIn("safety.blocked", events)
            # The body must not have been actuated.
            self.assertEqual(brain.body.last_action, "idle")
        finally:
            brain.stop()

    def test_stop_decision_triggers_emergency_stop(self):
        brain = _brain(safety_policy=StopDecisionPolicy())
        brain.start()
        try:
            result = brain.step()
            self.assertFalse(result["authorized"])
            self.assertEqual(brain.autonomy_sm.state, ASMState.EMERGENCY_STOP)
        finally:
            brain.stop()

    def test_monitor_interrupts_when_world_turns_unsafe(self):
        # The policy's own invariants (baseline) keep passing; the *monitor*'s
        # invariants accept only the FIRST post-execution check and then flip
        # (models the world changing mid-run): cycle 1 executes safely, cycle
        # 2's post-execution check interrupts.
        monitor = RuntimeSafetyMonitor(SafetyInvariantSet([FlipFlopInvariant(allow_evaluations=1)]))
        brain = _brain(safety_monitor=monitor)
        brain.start()
        try:
            first = brain.step()
            self.assertTrue(first["authorized"])
            self.assertEqual(len(monitor.interruptions), 0, "first cycle is safe")
            brain.step()
            self.assertEqual(
                len(monitor.interruptions), 1,
                "the world turning unsafe must interrupt the previously-approved action",
            )
            self.assertEqual(brain.autonomy_sm.state, ASMState.EMERGENCY_STOP)
            events = [e["event_type"] for e in brain.events]
            self.assertIn("safety.interrupted", events)
        finally:
            brain.stop()

    def test_policy_version_is_recorded(self):
        policy = SafetyPolicy(AlwaysViolated(), policy_version=PolicyVersion(version="9.9.9-test"))
        brain = _brain(safety_policy=policy)
        brain.start()
        try:
            brain.step()
            self.assertEqual(policy.decisions[0].policy_version, "9.9.9-test")
            self.assertTrue(policy.decisions[0].decision_id.startswith("sd-"))
        finally:
            brain.stop()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
