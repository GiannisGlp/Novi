"""Unified autonomy state machine tests.

The engine's ``AutonomyStateMachine`` and the ``AutonomySupervisor`` consume
ONE canonical enum (``CanonicalAutonomyState``): BOOT, SELF_TEST, SAFE_IDLE,
READY, AUTONOMOUS, DEGRADED, FAULT, EMERGENCY_STOP, RECOVERY.

Covers: every mandated state, every legal canonical transition,
illegal-transition rejection (fail-closed, explicit reason), and
engine/supervisor agreement. Socket-free and deterministic.
"""

from __future__ import annotations

import unittest
from dataclasses import dataclass
from typing import Any

from novi.brain.autonomy_state_machine import AutonomyStateMachine
from novi.brain.autonomy_state_machine import AutonomyStateMachineState as EngineState
from novi.brain.autonomy_supervisor import (
    ActionResult,
    AuthorizedAction,
    AutonomySupervisor,
    SimClock,
    VerificationResult,
)
from novi.brain.autonomy_supervisor import (
    AutonomyState as SupervisorState,
)
from novi.brain.canonical_autonomy import (
    CANONICAL_LEGAL_TRANSITIONS,
    CANONICAL_STATES,
    CanonicalAutonomyState,
    IllegalAutonomyTransition,
    canonical_state_equivalent,
    coerce_canonical,
    is_canonical_transition_legal,
    require_canonical_transition,
)
from novi.brain.governance_guard import ActionProposal, GovernanceGuard
from novi.brain.planner import Planner

# ---------------------------------------------------------------------------
# Deterministic fakes (no sockets, no threads, no wall-clock reads)
# ---------------------------------------------------------------------------


@dataclass
class FakeGoal:
    goal_id: str
    kind: str = "reach"
    target: tuple[float, float] = (10.0, 0.0)


class FakeGoalSource:
    def __init__(self, goals: list[FakeGoal] | None = None) -> None:
        self.goals = list(goals or [])
        self.completed: dict[str, str] = {}

    def active_goal(self, *, cycle: int) -> FakeGoal | None:
        for goal in self.goals:
            if goal.goal_id not in self.completed:
                return goal
        return None

    def complete_goal(self, goal_id: str, status: str, *, cycle: int) -> None:
        self.completed[goal_id] = status


class FakeWorld:
    def refresh(self, *, cycle: int) -> dict:
        return {}

    def expire_stale(self, *, cycle: int) -> list[str]:
        return []

    def needs_information(self, goal: FakeGoal, *, cycle: int) -> bool:
        return False


class FakeExecutor:
    def execute(self, action: AuthorizedAction, *, cycle: int) -> ActionResult:
        return ActionResult(
            result_id="res-1", action_ref=action.authorization_id,
            outcome="SUCCESS", cycle=cycle,
        )


class FakeVerifier:
    def verify(self, action: AuthorizedAction, result: ActionResult, *, cycle: int) -> VerificationResult:
        return VerificationResult(
            verification_id="ver-1", target_ref=action.authorization_id,
            method="fake", status="PASS", observed_evidence={},
        )


class FakeProposer:
    def propose(self, step: Any, *, goal_id: str, plan_id: str, cycle: int) -> ActionProposal:
        return ActionProposal(
            proposal_id=f"prop-{cycle}", action=step.action,
            parameters=dict(step.params), risk_class="R1",
            source="fake", rationale="unified test",
        )


def make_supervisor() -> AutonomySupervisor:
    return AutonomySupervisor(
        clock=SimClock(),
        executor=FakeExecutor(),
        verifier=FakeVerifier(),
        world=FakeWorld(),
        goals=FakeGoalSource(),
        planner=Planner(),
        proposer=FakeProposer(),
        guard=GovernanceGuard(),
    )


# ---------------------------------------------------------------------------
# (1) One canonical enum with every mandated state
# ---------------------------------------------------------------------------


class MandatedStatesTests(unittest.TestCase):
    def test_every_mandated_state_exists_with_exact_value(self):
        expected = (
            "BOOT", "SELF_TEST", "SAFE_IDLE", "READY", "AUTONOMOUS",
            "DEGRADED", "FAULT", "EMERGENCY_STOP", "RECOVERY",
        )
        self.assertEqual(tuple(m.value for m in CanonicalAutonomyState), expected)
        self.assertEqual(tuple(CANONICAL_STATES), expected)

    def test_iteration_yields_only_the_nine_canonical_members(self):
        self.assertEqual(len(list(CanonicalAutonomyState)), 9)


class DeprecatedAliasTests(unittest.TestCase):
    def test_engine_legacy_names_alias_canonical_members(self):
        cases = {
            "BOOTING": "BOOT", "INITIALIZING": "SELF_TEST",
            "OBSERVING": "AUTONOMOUS", "AWARE": "AUTONOMOUS",
            "INTERACTING": "AUTONOMOUS", "PLANNING": "AUTONOMOUS",
            "EXECUTING": "AUTONOMOUS", "LEARNING": "AUTONOMOUS",
            "MAINTENANCE": "AUTONOMOUS", "SAFE_DEGRADED": "DEGRADED",
            "SHUTTING_DOWN": "SAFE_IDLE", "FAULT_RECOVERY": "RECOVERY",
        }
        for old, canonical in cases.items():
            with self.subTest(old=old):
                self.assertIs(CanonicalAutonomyState[old], CanonicalAutonomyState(canonical))

    def test_supervisor_legacy_names_alias_canonical_members(self):
        cases = {
            "IDLE": "BOOT", "GOAL_PENDING": "READY",
            "AWAITING_AUTHORITY": "READY", "RECOVERING": "RECOVERY",
            "PAUSED": "DEGRADED", "SAFE_STOP": "EMERGENCY_STOP",
            "COMPLETED": "READY", "FAILED": "FAULT",
        }
        for old, canonical in cases.items():
            with self.subTest(old=old):
                self.assertIs(CanonicalAutonomyState[old], CanonicalAutonomyState(canonical))

    def test_coerce_accepts_members_concretes_and_strings(self):
        self.assertIs(coerce_canonical(CanonicalAutonomyState.BOOT), CanonicalAutonomyState.BOOT)
        self.assertIs(coerce_canonical("BOOT"), CanonicalAutonomyState.BOOT)
        self.assertIs(coerce_canonical("BOOTING"), CanonicalAutonomyState.BOOT)
        self.assertIs(coerce_canonical(EngineState.FAULT_RECOVERY), CanonicalAutonomyState.RECOVERY)
        self.assertIs(coerce_canonical(SupervisorState.SAFE_STOP), CanonicalAutonomyState.EMERGENCY_STOP)

    def test_coerce_rejects_unknown_fail_closed(self):
        with self.assertRaises(IllegalAutonomyTransition):
            coerce_canonical("BOGUS_STATE")


# ---------------------------------------------------------------------------
# (2) Legal transitions + fail-closed rejection at the canonical level
# ---------------------------------------------------------------------------


class CanonicalLegalTransitionTests(unittest.TestCase):
    def test_every_legal_transition_is_accepted(self):
        ordered = sorted(CANONICAL_LEGAL_TRANSITIONS, key=lambda p: (p[0].value, p[1].value))
        self.assertEqual(len(ordered), 25)
        for src, dst in ordered:
            with self.subTest(transition=f"{src.value}->{dst.value}"):
                self.assertTrue(is_canonical_transition_legal(src, dst))
                self.assertIs(require_canonical_transition(src, dst), dst)

    def test_every_mandated_state_participates(self):
        covered: set[str] = set()
        for src, dst in CANONICAL_LEGAL_TRANSITIONS:
            covered.add(src.value)
            covered.add(dst.value)
        self.assertEqual(covered, set(CANONICAL_STATES))

    def test_illegal_transitions_are_rejected(self):
        illegal = [
            (CanonicalAutonomyState.BOOT, CanonicalAutonomyState.AUTONOMOUS),
            (CanonicalAutonomyState.BOOT, CanonicalAutonomyState.READY),
            (CanonicalAutonomyState.AUTONOMOUS, CanonicalAutonomyState.BOOT),
            (CanonicalAutonomyState.AUTONOMOUS, CanonicalAutonomyState.SELF_TEST),
            (CanonicalAutonomyState.EMERGENCY_STOP, CanonicalAutonomyState.AUTONOMOUS),
            (CanonicalAutonomyState.EMERGENCY_STOP, CanonicalAutonomyState.BOOT),
            (CanonicalAutonomyState.RECOVERY, CanonicalAutonomyState.AUTONOMOUS),
            (CanonicalAutonomyState.FAULT, CanonicalAutonomyState.READY),
            (CanonicalAutonomyState.SELF_TEST, CanonicalAutonomyState.READY),
            (CanonicalAutonomyState.READY, CanonicalAutonomyState.FAULT),
            (CanonicalAutonomyState.SAFE_IDLE, CanonicalAutonomyState.AUTONOMOUS),
        ]
        for src, dst in illegal:
            with self.subTest(transition=f"{src.value}->{dst.value}"):
                self.assertFalse(is_canonical_transition_legal(src, dst))
                with self.assertRaises(IllegalAutonomyTransition):
                    require_canonical_transition(src, dst)

    def test_unknown_states_raise_fail_closed(self):
        with self.assertRaises(IllegalAutonomyTransition):
            is_canonical_transition_legal("BOGUS", CanonicalAutonomyState.BOOT)


# ---------------------------------------------------------------------------
# (3) Both machines consume the canonical enum (fail-closed)
# ---------------------------------------------------------------------------


class EngineCanonicalTests(unittest.TestCase):
    def test_engine_exposes_typed_canonical_state(self):
        sm = AutonomyStateMachine()
        self.assertIs(sm.canonical_state, CanonicalAutonomyState.BOOT)

    def test_engine_legal_canonical_request_succeeds(self):
        sm = AutonomyStateMachine()
        record = sm.request_canonical(CanonicalAutonomyState.SELF_TEST)
        self.assertTrue(record.accepted)
        self.assertEqual(sm.state, EngineState.INITIALIZING)
        self.assertIs(sm.canonical_state, CanonicalAutonomyState.SELF_TEST)

    def test_engine_illegal_canonical_request_rejected_fail_closed(self):
        sm = AutonomyStateMachine()
        record = sm.request_canonical(CanonicalAutonomyState.AUTONOMOUS)
        self.assertFalse(record.accepted)
        self.assertTrue(record.reason)
        self.assertEqual(sm.state, EngineState.BOOTING)  # unchanged
        self.assertIs(sm.canonical_state, CanonicalAutonomyState.BOOT)
        self.assertIn(record, sm.rejected_transitions)

    def test_engine_unknown_destination_rejected_fail_closed(self):
        sm = AutonomyStateMachine()
        record = sm.request_canonical("BOGUS_STATE")
        self.assertFalse(record.accepted)
        self.assertTrue(record.reason)
        self.assertEqual(sm.state, EngineState.BOOTING)

    def test_engine_emergency_stop_routes_fail_safe(self):
        sm = AutonomyStateMachine()
        record = sm.request_canonical(CanonicalAutonomyState.EMERGENCY_STOP)
        self.assertTrue(record.accepted)
        self.assertEqual(sm.state, EngineState.EMERGENCY_STOP)
        self.assertIs(sm.canonical_state, CanonicalAutonomyState.EMERGENCY_STOP)

    def test_engine_same_state_request_is_accepted_noop(self):
        sm = AutonomyStateMachine()
        record = sm.request_canonical("BOOT")
        self.assertTrue(record.accepted)
        self.assertEqual(sm.state, EngineState.BOOTING)

    def test_engine_snapshot_carries_canonical_state(self):
        sm = AutonomyStateMachine()
        snap = sm.snapshot()
        self.assertIs(snap["canonical_state"], sm.canonical_state)


class SupervisorCanonicalTests(unittest.TestCase):
    def test_supervisor_exposes_typed_canonical_state(self):
        sup = make_supervisor()
        self.assertIs(sup.canonical_state, CanonicalAutonomyState.BOOT)

    def test_supervisor_illegal_canonical_request_rejected_fail_closed(self):
        sup = make_supervisor()
        ok = sup.request_canonical(CanonicalAutonomyState.AUTONOMOUS, reason="t", producer="t")
        self.assertFalse(ok)
        self.assertIs(sup.state, SupervisorState.IDLE)  # unchanged
        self.assertIs(sup.canonical_state, CanonicalAutonomyState.BOOT)
        self.assertTrue(any(e.event_type == "TRANSITION_REJECTED" for e in sup.events))

    def test_supervisor_unknown_destination_rejected_fail_closed(self):
        sup = make_supervisor()
        ok = sup.request_canonical("BOGUS_STATE", reason="t", producer="t")
        self.assertFalse(ok)
        self.assertIs(sup.state, SupervisorState.IDLE)

    def test_supervisor_legal_realizable_request_succeeds(self):
        from novi.brain.canonical_autonomy import supervisor_concretes_for

        sup = make_supervisor()
        self.assertTrue(sup._transition(SupervisorState.GOAL_PENDING, reason="t", producer="t"))
        ok = sup.request_canonical(CanonicalAutonomyState.AUTONOMOUS, reason="t", producer="t")
        self.assertTrue(ok)
        self.assertIn(sup.state, supervisor_concretes_for(CanonicalAutonomyState.AUTONOMOUS))
        self.assertIs(sup.canonical_state, CanonicalAutonomyState.AUTONOMOUS)

    def test_supervisor_emergency_stop_routes_fail_safe(self):
        sup = make_supervisor()
        ok = sup.request_canonical(CanonicalAutonomyState.EMERGENCY_STOP, reason="t", producer="t")
        self.assertTrue(ok)
        self.assertIs(sup.state, SupervisorState.SAFE_STOP)
        self.assertIs(sup.canonical_state, CanonicalAutonomyState.EMERGENCY_STOP)

    def test_supervisor_same_state_request_is_accepted_noop(self):
        sup = make_supervisor()
        self.assertTrue(sup.request_canonical("BOOT", reason="t", producer="t"))
        self.assertIs(sup.state, SupervisorState.IDLE)

    def test_supervisor_snapshot_carries_canonical_state(self):
        sup = make_supervisor()
        self.assertIs(sup.snapshot()["canonical_state"], sup.canonical_state)


# ---------------------------------------------------------------------------
# (4) Engine and supervisor agree
# ---------------------------------------------------------------------------


class EngineSupervisorAgreementTests(unittest.TestCase):
    def test_boot_states_agree(self):
        self.assertIs(AutonomyStateMachine().canonical_state, make_supervisor().canonical_state)

    def test_emergency_stop_states_agree(self):
        sm = AutonomyStateMachine()
        sup = make_supervisor()
        sm.request_canonical(CanonicalAutonomyState.EMERGENCY_STOP)
        sup.request_canonical(CanonicalAutonomyState.EMERGENCY_STOP, reason="t", producer="t")
        self.assertIs(sm.canonical_state, CanonicalAutonomyState.EMERGENCY_STOP)
        self.assertIs(sup.canonical_state, CanonicalAutonomyState.EMERGENCY_STOP)
        self.assertEqual(sm.snapshot()["canonical_state"], sup.snapshot()["canonical_state"])

    def test_operating_states_agree(self):
        self.assertTrue(canonical_state_equivalent(EngineState.AWARE, SupervisorState.EXECUTING))
        self.assertTrue(canonical_state_equivalent("BOOTING", SupervisorState.IDLE))
        self.assertTrue(
            canonical_state_equivalent(EngineState.EMERGENCY_STOP, SupervisorState.SAFE_STOP)
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
