"""Canonical autonomy state machine (Phase 2b, P0 gap 4 of the 2026-08-29 plan).

Single source of truth for the plan-required autonomy states — consumed by
BOTH the engine's ``AutonomyStateMachine`` and the ``AutonomySupervisor``.

Plan states (docs/01-system-architecture/20 §Safety state machine):

    BOOT → SELF_TEST → SAFE_IDLE → READY → AUTONOMOUS → DEGRADED
                                             ↓            ↓
                              EMERGENCY_STOP ← FAULT →    RECOVERY

The two concrete machines historically evolved disjoint vocabularies (13
states each, none fully matching the plan). Full replaces are risky; the
unification contract here is:

- every concrete state projects TOTALY (and typed) into a canonical state —
  adding a concrete state without a projection is a test failure
  (test_canonical_autonomy covers completeness);
- equivalent milestones project to the same canonical state, so the engine
  and the supervisor can always agree on state by projection.

Semantics of the canonical set:
- BOOT: powered, not yet validated.
- SELF_TEST: bring-up checks running.
- SAFE_IDLE: validated, no task authority (also: shutting down).
- READY: capable, awaiting/goal-holding authority.
- AUTONOMOUS: the perception→cognition→action loop is operating.
- DEGRADED: operating in a reduced/restricted capacity.
- FAULT: a subsystem failed and needs recovery intent.
- EMERGENCY_STOP: latched safe minimum; motion forbidden.
- RECOVERY: restoring toward normal operation.
"""

from __future__ import annotations

from typing import Final

CANONICAL_STATES: Final[tuple[str, ...]] = (
    "BOOT",
    "SELF_TEST",
    "SAFE_IDLE",
    "READY",
    "AUTONOMOUS",
    "DEGRADED",
    "FAULT",
    "EMERGENCY_STOP",
    "RECOVERY",
)

_BOOT: Final = "BOOT"
_SELF_TEST: Final = "SELF_TEST"
_SAFE_IDLE: Final = "SAFE_IDLE"
_READY: Final = "READY"
_AUTONOMOUS: Final = "AUTONOMOUS"
_DEGRADED: Final = "DEGRADED"
_FAULT: Final = "FAULT"
_ESTOP: Final = "EMERGENCY_STOP"
_RECOVERY: Final = "RECOVERY"


def _engine_map() -> dict[str, str]:
    from .autonomy_state_machine import AutonomyStateMachineState as S

    return {
        S.BOOTING: _BOOT,
        S.INITIALIZING: _SELF_TEST,
        S.OBSERVING: _AUTONOMOUS,
        S.AWARE: _AUTONOMOUS,
        S.INTERACTING: _AUTONOMOUS,
        S.PLANNING: _AUTONOMOUS,
        S.EXECUTING: _AUTONOMOUS,
        S.LEARNING: _AUTONOMOUS,
        S.MAINTENANCE: _AUTONOMOUS,
        S.SAFE_DEGRADED: _DEGRADED,
        S.SHUTTING_DOWN: _SAFE_IDLE,
        S.EMERGENCY_STOP: _ESTOP,
        S.FAULT_RECOVERY: _RECOVERY,
    }


def _supervisor_map() -> dict[str, str]:
    from .autonomy_supervisor import AutonomyState as S

    return {
        S.IDLE: _BOOT,
        S.OBSERVING: _AUTONOMOUS,
        S.INTERPRETING: _AUTONOMOUS,
        S.GOAL_PENDING: _READY,
        S.PLANNING: _AUTONOMOUS,
        S.AWAITING_AUTHORITY: _READY,
        S.EXECUTING: _AUTONOMOUS,
        S.VERIFYING: _AUTONOMOUS,
        S.RECOVERING: _RECOVERY,
        S.PAUSED: _DEGRADED,
        S.SAFE_STOP: _ESTOP,
        S.COMPLETED: _READY,
        S.FAILED: _FAULT,
    }


def project_engine_state(state: object) -> str:
    """Project an engine AutonomyStateMachineState into the canonical set."""
    return _engine_map()[getattr(state, "name", str(state))]


def project_supervisor_state(state: object) -> str:
    """Project a supervisor AutonomyState into the canonical set."""
    return _supervisor_map()[getattr(state, "name", str(state))]


def canonical_state_equivalent(a: str, b: str) -> bool:
    """True when two canonical labels are the same plan-canonical state."""
    return a == b
