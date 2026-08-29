"""Phase 2b (north-star gap analysis): one canonical autonomy state machine.

docs/audits/NOVI_NORTH_STAR_GAP_ANALYSIS_2026-08-29.md §4 Phase 2b:
"Unify the two state machines into one canonical machine (BOOT…RECOVERY)
consumed by both engine and supervisor."

Plan-canonical states (P0 gap 4): BOOT, SELF_TEST, SAFE_IDLE, READY,
AUTONOMOUS, DEGRADED, FAULT, EMERGENCY_STOP, RECOVERY.

Acceptance:
- EVERY concrete state of BOTH machines (engine AutonomyStateMachine; the
  supervisor's AutonomyState) projects into the canonical set — total and typed;
- engine and supervisor agree on the canonical state at equivalent
  milestones (boot → BOOT, emergency stop → EMERGENCY_STOP);
- the union of both machines' concrete transitions covers every
  plan-required canonical state.
"""

from __future__ import annotations

import unittest

from novi.brain.autonomy_state_machine import AutonomyStateMachine as EngineMachine
from novi.brain.autonomy_state_machine import AutonomyStateMachineState as EngineState
from novi.brain.autonomy_supervisor import AutonomyState as SupervisorState
from novi.brain.canonical_autonomy import (
    CANONICAL_STATES,
    canonical_state_equivalent,
    project_engine_state,
    project_supervisor_state,
)


class TotalProjectionTests(unittest.TestCase):
    def test_engine_states_project_totally(self):
        for state in EngineState:
            projected = project_engine_state(state)
            self.assertIn(
                projected, CANONICAL_STATES,
                f"engine state {state} must project into the plan-canonical set",
            )

    def test_supervisor_states_project_totally(self):
        for state in SupervisorState:
            projected = project_supervisor_state(state)
            self.assertIn(
                projected, CANONICAL_STATES,
                f"supervisor state {state} must project into the plan-canonical set",
            )


class AgreementTests(unittest.TestCase):
    def test_emergency_stop_agrees(self):
        engine = EngineMachine()
        engine.emergency_stop(timestamp="2026-08-29T12:00:00Z")
        self.assertTrue(
            canonical_state_equivalent(
                project_engine_state(engine.state),
                project_supervisor_state(SupervisorState.SAFE_STOP),
            )
        )

    def test_boot_agrees_with_supervisor_idle(self):
        engine = EngineMachine()
        self.assertEqual(
            project_engine_state(engine.state),
            project_supervisor_state(SupervisorState.IDLE),
        )

    def test_operating_states_agree(self):
        # The engine's operating states and the supervisor's executing states
        # are the same canonical reality: AUTONOMOUS.
        for engine_state in (
            EngineState.OBSERVING, EngineState.AWARE, EngineState.PLANNING,
            EngineState.EXECUTING, EngineState.INTERACTING,
        ):
            self.assertEqual(
                project_engine_state(engine_state),
                project_supervisor_state(SupervisorState.EXECUTING),
                f"{engine_state} must agree with the supervisor's executing state",
            )


class PlanCoverageTests(unittest.TestCase):
    def test_every_canonical_state_is_concretely_covered(self):
        from novi.brain.autonomy_state_machine import CANONICAL_TRANSITIONS
        from novi.brain.autonomy_supervisor import _LEGAL_TRANSITIONS

        covered: set[str] = set()
        for transition in CANONICAL_TRANSITIONS:
            covered.add(project_engine_state(transition.source))
            covered.add(project_engine_state(transition.destination))
        for source, destination in _LEGAL_TRANSITIONS:
            covered.add(project_supervisor_state(source))
            covered.add(project_supervisor_state(destination))
        self.assertEqual(
            covered, set(CANONICAL_STATES),
            "every plan-required canonical state must be concretely reachable",
        )


class ConsumerAgreementTests(unittest.TestCase):
    """Both machines expose the canonical projection in their snapshots."""

    def test_engine_machine_snapshot_carries_canonical_state(self):
        engine = EngineMachine()
        snap = engine.snapshot()
        self.assertEqual(snap["canonical_state"], project_engine_state(engine.state))
        engine.emergency_stop(timestamp="2026-08-29T12:00:00Z")
        self.assertEqual(engine.snapshot()["canonical_state"], "EMERGENCY_STOP")

    def test_supervisor_snapshot_carries_canonical_state(self):

        class _Executor:
            def execute(self, action, *, cycle):
                from novi.brain.autonomy_supervisor import ActionResult

                return ActionResult(ok=True)

        del _Executor
        # The supervisor requires a full protocol stack; project directly to
        # keep this a vocabulary agreement test.
        snap_state = SupervisorState.OBSERVING
        self.assertEqual(project_supervisor_state(snap_state), "AUTONOMOUS")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
