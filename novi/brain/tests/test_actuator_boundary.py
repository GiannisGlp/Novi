"""Phase 2c (north-star gap analysis): the physical authority boundary.

docs/audits/NOVI_NORTH_STAR_GAP_ANALYSIS_2026-08-29.md §4 Phase 2c:
"Implement the physical authority boundary: actuator-command contract +
command compiler (bounds/allow-list/rate-limit/expiry) + watchdog."

Acceptance:
- an out-of-bounds model command is rejected at the boundary;
- an expired authorization cannot reach the actuator (watchdog + live check);
- unknown actions and over-budget rates are rejected with typed codes;
- every engine action reaches the body only as a compiled, expiring command.
"""

from __future__ import annotations

import unittest
from typing import Any

from novi.brain.actuator_boundary import ActuatorBoundary
from novi.brain.b2_perception import SpecialistPerception
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.governance_guard import REQUIRE_CONFIRMATION
from novi.brain.io import CameraFrame


class _Grant:
    def __init__(self, decision: str, grant_id: str, reason: str = "") -> None:
        self.decision = decision
        self.grant_id = grant_id
        self.reason = reason
        self.is_allowed = decision == "ALLOW"

    def snapshot(self) -> dict[str, Any]:
        return {"decision": self.decision, "grant_id": self.grant_id, "reason": self.reason}


class ConfirmationGuard:
    """Governance-guard stub: requires confirmation, then confirms."""

    def __init__(self, grant_id: str = "gg-1") -> None:
        self.grant_id = grant_id

    def evaluate(self, proposal) -> _Grant:
        return _Grant(REQUIRE_CONFIRMATION, self.grant_id, "policy requires a human yes")

    def confirm(self, grant_id: str) -> _Grant | None:
        if grant_id != self.grant_id:
            return None
        return _Grant("ALLOW", grant_id, "confirmed_by_operator")


class FrameCamera:
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


def _brain(actuator_boundary=None, governance_guard=None) -> MacBrain:
    return MacBrain(
        camera=FrameCamera(),
        perception=SpecialistPerception(QuietPerception()),
        actuator_boundary=actuator_boundary,
        governance_guard=governance_guard,
        config=MacBrainConfig(curiosity_enabled=False),
    )


class CompileTests(unittest.TestCase):
    def test_bounds_respected_command_compiles(self):
        b = ActuatorBoundary()
        result = b.compile(action="move_forward", parameters={"distance_m": 0.1}, cycle=3, correlation_id="c1")
        self.assertIsNone(result.rejection)
        self.assertIsNotNone(result.command)
        cmd = result.command
        self.assertEqual(cmd.action, "move_forward")
        self.assertEqual(cmd.issued_cycle, 3)
        self.assertEqual(cmd.expires_cycle, 3 + b.command_ttl_cycles)
        self.assertTrue(cmd.command_id.startswith("ac-"))

    def test_out_of_bounds_command_rejected(self):
        b = ActuatorBoundary()
        result = b.compile(action="move_forward", parameters={"distance_m": 999.0}, cycle=1)
        self.assertIsNone(result.command)
        self.assertEqual(result.rejection, "OUT_OF_BOUNDS")

    def test_unknown_action_rejected(self):
        b = ActuatorBoundary()
        result = b.compile(action="teleport", parameters={}, cycle=1)
        self.assertIsNone(result.command)
        self.assertEqual(result.rejection, "UNKNOWN_ACTION")

    def test_speak_length_bounded(self):
        b = ActuatorBoundary()
        result = b.compile(action="speak", parameters={"text": "x" * 5000}, cycle=1)
        self.assertIsNone(result.command)
        self.assertEqual(result.rejection, "OUT_OF_BOUNDS")

    def test_rate_limit_one_command_per_cycle(self):
        b = ActuatorBoundary(max_commands_per_cycle=1)
        first = b.compile(action="wait", parameters={}, cycle=7)
        self.assertIsNone(first.rejection)
        second = b.compile(action="observe", parameters={}, cycle=7)
        self.assertIsNone(second.command)
        self.assertEqual(second.rejection, "RATE_LIMITED")
        next_cycle = b.compile(action="observe", parameters={}, cycle=8)
        self.assertIsNone(next_cycle.rejection)


class ExpiryAndWatchdogTests(unittest.TestCase):
    def test_expired_command_cannot_reach_actuator(self):
        b = ActuatorBoundary(command_ttl_cycles=3)
        cmd = b.compile(action="move_forward", parameters={"distance_m": 0.1}, cycle=1).command
        self.assertTrue(b.is_live(cmd, cycle=1))
        self.assertTrue(b.is_live(cmd, cycle=3))
        self.assertFalse(b.is_live(cmd, cycle=4), "expired authorization must not reach the actuator")

    def test_watchdog_expires_stale_commands(self):
        b = ActuatorBoundary(command_ttl_cycles=2)
        cmd = b.compile(action="move_forward", parameters={"distance_m": 0.1}, cycle=0).command
        expired = b.watch(cycle=5)
        self.assertEqual(len(expired), 1)
        self.assertEqual(expired[0]["command_id"], cmd.command_id)
        self.assertEqual(expired[0]["code"], "EXPIRED")


class EngineBoundaryTests(unittest.TestCase):
    def test_every_executed_action_carries_compiled_command(self):
        brain = _brain()
        brain.start()
        try:
            result = brain.step()
            self.assertTrue(result["authorized"])
            events = [e["event_type"] for e in brain.events]
            self.assertIn("actuator.compiled", events)
            self.assertTrue(result["actuator"]["command_id"].startswith("ac-"))
        finally:
            brain.stop()

    def test_action_off_allow_list_rejected_at_boundary_chokepoint(self):
        # The boundary allow-list is runtime-owned: a command the boundary
        # does not authorize dies at the chokepoint (fail closed), even after
        # the supervisor + governance + safety gates said yes. Quiet cycles
        # deterministically propose wait/observe — off the injected list.
        tight = ActuatorBoundary(allowed_actions=frozenset({"move_forward", "turn_left", "turn_right"}))
        brain = _brain(actuator_boundary=tight)
        brain.start()
        try:
            result = brain.step()
            self.assertFalse(result["authorized"])
            self.assertEqual(result["actuator"]["rejection"], "UNKNOWN_ACTION")
            self.assertIsNone(result["actuator"]["command_id"])
            self.assertEqual(brain.body.last_action, "idle")
            events = [e["event_type"] for e in brain.events]
            self.assertIn("actuator.rejected", events)
            entries = brain.audit_entries(limit=10)
            self.assertTrue(any("actuator_boundary" in str(e.get("actor", "")) for e in entries))
        finally:
            brain.stop()

    def test_confirmed_pending_action_goes_through_boundary(self):
        # The real confirmation flow: governance guard requires confirmation,
        # the engine surfaces a pending request, and confirm_action executes
        # through the actuator boundary.
        brain = _brain(governance_guard=ConfirmationGuard())
        brain.start()
        try:
            # No confirmation yet -> confirm is a no-op fail-closed.
            self.assertFalse(brain.confirm_action("gg-1"))
            brain.step()
            self.assertIn("gg-1", brain._pending_confirmations)
            events = [e["event_type"] for e in brain.events]
            self.assertIn("governance.confirmation_required", events)
            # The granted, in-envelope action compiles and executes.
            self.assertTrue(brain.confirm_action("gg-1"))
            events = [e["event_type"] for e in brain.events]
            self.assertIn("governance.confirmed", events)
            self.assertIn("actuator.compiled", events)
        finally:
            brain.stop()

    def test_out_of_bounds_confirmed_action_refused_by_boundary(self):
        # Even a human-confirmed action cannot leave the compiled envelope:
        # the confirmation path re-runs the boundary before the actuator.
        # (Quiet cycles deterministically propose wait/observe — bound both.)
        bounds = {"observe": {"force_level": (0.0, 1.0)}, "wait": {"force_level": (0.0, 1.0)}}
        brain = _brain(
            actuator_boundary=ActuatorBoundary(bounds=bounds),
            governance_guard=ConfirmationGuard(),
        )
        brain.start()
        try:
            brain.step()
            pending = brain._pending_confirmations.get("gg-1")
            self.assertIsNotNone(pending)
            pending["parameters"] = {"force_level": 10}
            self.assertFalse(brain.confirm_action("gg-1"))
            self.assertEqual(brain.body.last_action, "idle")
            events = [e["event_type"] for e in brain.events]
            self.assertIn("actuator.rejected", events)
        finally:
            brain.stop()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
