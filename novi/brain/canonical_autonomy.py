"""Canonical autonomy state machine (Phase 2b, P0 gap 4 of the 2026-08-29 plan).

Single source of truth for the plan-required autonomy states — consumed by
BOTH the engine's ``AutonomyStateMachine`` and the ``AutonomySupervisor``.

Plan states (docs/01-system-architecture/20 §Safety state machine):

    BOOT → SELF_TEST → SAFE_IDLE → READY → AUTONOMOUS → DEGRADED
                                             ↓            ↓
                              EMERGENCY_STOP ← FAULT →    RECOVERY

The two concrete machines historically evolved disjoint vocabularies (13
states each, none fully matching the plan). The unification contract is:

- ``CanonicalAutonomyState`` is the ONE canonical enum: every mandated
  plan state is a member, and every legacy concrete name survives as a
  DEPRECATED alias so existing consumers keep working;
- every concrete state of both machines projects TOTALLY (and typed) into
  a canonical member — adding a concrete state without a projection is a
  test failure (test_canonical_autonomy covers completeness);
- equivalent milestones project to the same canonical state, so the engine
  and the supervisor can always agree on state by projection;
- both machines expose ``canonical_state`` and ``request_canonical()``;
  invalid canonical transitions fail closed with an explicit rejection.

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

from enum import Enum
from typing import TYPE_CHECKING, Any, Final

if TYPE_CHECKING:  # pragma: no cover
    from .autonomy_state_machine import AutonomyStateMachineState
    from .autonomy_supervisor import AutonomyState as SupervisorState
    from .autonomy_supervisor import AutonomySupervisor


class IllegalAutonomyTransition(ValueError):
    """Explicit rejection for an illegal canonical autonomy transition.

    Raised (or recorded, by the machines) fail-closed: the state never
    changes on an illegal request.
    """


class CanonicalAutonomyState(str, Enum):
    """ONE canonical autonomy enum for engine and supervisor.

    The nine plan-mandated states are the members; every legacy concrete
    name from ``AutonomyStateMachineState`` and the supervisor's
    ``AutonomyState`` survives as a DEPRECATED alias (aliases compare
    identical to their canonical member and never appear in iteration).
    """

    BOOT = "BOOT"
    SELF_TEST = "SELF_TEST"
    SAFE_IDLE = "SAFE_IDLE"
    READY = "READY"
    AUTONOMOUS = "AUTONOMOUS"
    DEGRADED = "DEGRADED"
    FAULT = "FAULT"
    EMERGENCY_STOP = "EMERGENCY_STOP"
    RECOVERY = "RECOVERY"

    # -- DEPRECATED aliases: engine AutonomyStateMachineState names --
    BOOTING = "BOOT"  # DEPRECATED: use BOOT
    INITIALIZING = "SELF_TEST"  # DEPRECATED: use SELF_TEST
    OBSERVING = "AUTONOMOUS"  # DEPRECATED: use AUTONOMOUS
    AWARE = "AUTONOMOUS"  # DEPRECATED: use AUTONOMOUS
    INTERACTING = "AUTONOMOUS"  # DEPRECATED: use AUTONOMOUS
    PLANNING = "AUTONOMOUS"  # DEPRECATED: use AUTONOMOUS
    EXECUTING = "AUTONOMOUS"  # DEPRECATED: use AUTONOMOUS
    LEARNING = "AUTONOMOUS"  # DEPRECATED: use AUTONOMOUS
    MAINTENANCE = "AUTONOMOUS"  # DEPRECATED: use AUTONOMOUS
    SAFE_DEGRADED = "DEGRADED"  # DEPRECATED: use DEGRADED
    SHUTTING_DOWN = "SAFE_IDLE"  # DEPRECATED: use SAFE_IDLE
    FAULT_RECOVERY = "RECOVERY"  # DEPRECATED: use RECOVERY

    # -- DEPRECATED aliases: supervisor AutonomyState names --
    # (OBSERVING / PLANNING / EXECUTING already aliased above to AUTONOMOUS.)
    IDLE = "BOOT"  # DEPRECATED: use BOOT
    INTERPRETING = "AUTONOMOUS"  # DEPRECATED: use AUTONOMOUS
    GOAL_PENDING = "READY"  # DEPRECATED: use READY
    AWAITING_AUTHORITY = "READY"  # DEPRECATED: use READY
    VERIFYING = "AUTONOMOUS"  # DEPRECATED: use AUTONOMOUS
    RECOVERING = "RECOVERY"  # DEPRECATED: use RECOVERY
    PAUSED = "DEGRADED"  # DEPRECATED: use DEGRADED
    SAFE_STOP = "EMERGENCY_STOP"  # DEPRECATED: use EMERGENCY_STOP
    COMPLETED = "READY"  # DEPRECATED: use READY
    FAILED = "FAULT"  # DEPRECATED: use FAULT


CANONICAL_STATES: Final[tuple[str, ...]] = tuple(m.value for m in CanonicalAutonomyState)

#: Legal canonical transitions (source, destination). Anything else is
#: rejected fail-closed. EMERGENCY_STOP is reachable from every canonical
#: state; only explicit RECOVERY leaves it (never auto-resume).
CANONICAL_LEGAL_TRANSITIONS: Final[
    frozenset[tuple[CanonicalAutonomyState, CanonicalAutonomyState]]
] = frozenset({
    (CanonicalAutonomyState.BOOT, CanonicalAutonomyState.SELF_TEST),
    (CanonicalAutonomyState.BOOT, CanonicalAutonomyState.EMERGENCY_STOP),
    (CanonicalAutonomyState.SELF_TEST, CanonicalAutonomyState.SAFE_IDLE),
    (CanonicalAutonomyState.SELF_TEST, CanonicalAutonomyState.FAULT),
    (CanonicalAutonomyState.SELF_TEST, CanonicalAutonomyState.EMERGENCY_STOP),
    (CanonicalAutonomyState.SAFE_IDLE, CanonicalAutonomyState.READY),
    (CanonicalAutonomyState.SAFE_IDLE, CanonicalAutonomyState.EMERGENCY_STOP),
    (CanonicalAutonomyState.READY, CanonicalAutonomyState.AUTONOMOUS),
    (CanonicalAutonomyState.READY, CanonicalAutonomyState.DEGRADED),
    (CanonicalAutonomyState.READY, CanonicalAutonomyState.SAFE_IDLE),
    (CanonicalAutonomyState.READY, CanonicalAutonomyState.EMERGENCY_STOP),
    (CanonicalAutonomyState.AUTONOMOUS, CanonicalAutonomyState.DEGRADED),
    (CanonicalAutonomyState.AUTONOMOUS, CanonicalAutonomyState.READY),
    (CanonicalAutonomyState.AUTONOMOUS, CanonicalAutonomyState.FAULT),
    (CanonicalAutonomyState.AUTONOMOUS, CanonicalAutonomyState.EMERGENCY_STOP),
    (CanonicalAutonomyState.DEGRADED, CanonicalAutonomyState.AUTONOMOUS),
    (CanonicalAutonomyState.DEGRADED, CanonicalAutonomyState.READY),
    (CanonicalAutonomyState.DEGRADED, CanonicalAutonomyState.FAULT),
    (CanonicalAutonomyState.DEGRADED, CanonicalAutonomyState.EMERGENCY_STOP),
    (CanonicalAutonomyState.FAULT, CanonicalAutonomyState.RECOVERY),
    (CanonicalAutonomyState.FAULT, CanonicalAutonomyState.EMERGENCY_STOP),
    (CanonicalAutonomyState.RECOVERY, CanonicalAutonomyState.SAFE_IDLE),
    (CanonicalAutonomyState.RECOVERY, CanonicalAutonomyState.READY),
    (CanonicalAutonomyState.RECOVERY, CanonicalAutonomyState.EMERGENCY_STOP),
    (CanonicalAutonomyState.EMERGENCY_STOP, CanonicalAutonomyState.RECOVERY),
})


def _engine_map() -> dict[Any, CanonicalAutonomyState]:
    from .autonomy_state_machine import AutonomyStateMachineState as S

    return {
        S.BOOTING: CanonicalAutonomyState.BOOT,
        S.INITIALIZING: CanonicalAutonomyState.SELF_TEST,
        S.OBSERVING: CanonicalAutonomyState.AUTONOMOUS,
        S.AWARE: CanonicalAutonomyState.AUTONOMOUS,
        S.INTERACTING: CanonicalAutonomyState.AUTONOMOUS,
        S.PLANNING: CanonicalAutonomyState.AUTONOMOUS,
        S.EXECUTING: CanonicalAutonomyState.AUTONOMOUS,
        S.LEARNING: CanonicalAutonomyState.AUTONOMOUS,
        S.MAINTENANCE: CanonicalAutonomyState.AUTONOMOUS,
        S.SAFE_DEGRADED: CanonicalAutonomyState.DEGRADED,
        S.SHUTTING_DOWN: CanonicalAutonomyState.SAFE_IDLE,
        S.EMERGENCY_STOP: CanonicalAutonomyState.EMERGENCY_STOP,
        S.FAULT_RECOVERY: CanonicalAutonomyState.RECOVERY,
    }


def _supervisor_map() -> dict[Any, CanonicalAutonomyState]:
    from .autonomy_supervisor import AutonomyState as S

    return {
        S.IDLE: CanonicalAutonomyState.BOOT,
        S.OBSERVING: CanonicalAutonomyState.AUTONOMOUS,
        S.INTERPRETING: CanonicalAutonomyState.AUTONOMOUS,
        S.GOAL_PENDING: CanonicalAutonomyState.READY,
        S.PLANNING: CanonicalAutonomyState.AUTONOMOUS,
        S.AWAITING_AUTHORITY: CanonicalAutonomyState.READY,
        S.EXECUTING: CanonicalAutonomyState.AUTONOMOUS,
        S.VERIFYING: CanonicalAutonomyState.AUTONOMOUS,
        S.RECOVERING: CanonicalAutonomyState.RECOVERY,
        S.PAUSED: CanonicalAutonomyState.DEGRADED,
        S.SAFE_STOP: CanonicalAutonomyState.EMERGENCY_STOP,
        S.COMPLETED: CanonicalAutonomyState.READY,
        S.FAILED: CanonicalAutonomyState.FAULT,
    }


def project_engine_state(state: object) -> CanonicalAutonomyState:
    """Project an engine AutonomyStateMachineState into the canonical set."""
    if isinstance(state, CanonicalAutonomyState):
        return state
    try:
        return _engine_map()[getattr(state, "name", str(state))]
    except KeyError:
        pass
    try:
        return coerce_canonical(state)
    except IllegalAutonomyTransition:
        raise IllegalAutonomyTransition(
            f"unknown engine autonomy state: {state!r}"
        ) from None


def project_supervisor_state(state: object) -> CanonicalAutonomyState:
    """Project a supervisor AutonomyState into the canonical set."""
    if isinstance(state, CanonicalAutonomyState):
        return state
    try:
        return _supervisor_map()[getattr(state, "name", str(state))]
    except KeyError:
        pass
    try:
        return coerce_canonical(state)
    except IllegalAutonomyTransition:
        raise IllegalAutonomyTransition(
            f"unknown supervisor autonomy state: {state!r}"
        ) from None


def project_to_canonical(state: object) -> CanonicalAutonomyState:
    """Project any known autonomy state (either machine, canonical, string) to canonical."""
    return coerce_canonical(state)


def coerce_canonical(state: object) -> CanonicalAutonomyState:
    """Coerce an engine state, supervisor state, canonical member, or string to canonical.

    Raises IllegalAutonomyTransition (fail-closed) for anything unknown.
    """
    if isinstance(state, CanonicalAutonomyState):
        return state
    from .autonomy_state_machine import AutonomyStateMachineState as EngineState
    from .autonomy_supervisor import AutonomyState as SupervisorState

    if isinstance(state, EngineState):
        return project_engine_state(state)
    if isinstance(state, SupervisorState):
        return project_supervisor_state(state)
    if isinstance(state, str):
        try:
            return CanonicalAutonomyState(state)  # by value, e.g. "BOOT"
        except ValueError:
            pass
        try:
            return CanonicalAutonomyState[state]  # by name, incl. DEPRECATED aliases
        except KeyError:
            pass
    raise IllegalAutonomyTransition(f"unknown autonomy state: {state!r}")


def is_canonical_transition_legal(source: object, destination: object) -> bool:
    """True iff the canonical transition source -> destination is legal.

    Unknown states coerce-fail (IllegalAutonomyTransition): fail-closed.
    """
    src = coerce_canonical(source)
    dst = coerce_canonical(destination)
    return (src, dst) in CANONICAL_LEGAL_TRANSITIONS


def require_canonical_transition(
    source: object, destination: object
) -> CanonicalAutonomyState:
    """Return the coerced destination, or raise IllegalAutonomyTransition (explicit rejection)."""
    src = coerce_canonical(source)
    dst = coerce_canonical(destination)
    if (src, dst) not in CANONICAL_LEGAL_TRANSITIONS:
        raise IllegalAutonomyTransition(
            f"illegal canonical transition {src.value} -> {dst.value}"
        )
    return dst


def canonical_state_equivalent(a: object, b: object) -> bool:
    """True when two states (canonical, concrete, or string) are the same canonical state."""
    return coerce_canonical(a) == coerce_canonical(b)


def supervisor_concretes_for(destination: object) -> tuple[SupervisorState, ...]:
    """Supervisor concrete states projecting to a canonical state (definition order)."""
    from .autonomy_supervisor import AutonomyState as S

    dest = coerce_canonical(destination)
    return tuple(s for s in S if project_supervisor_state(s) == dest)


def engine_concretes_for(destination: object) -> tuple[AutonomyStateMachineState, ...]:
    """Engine concrete states projecting to a canonical state (definition order)."""
    from .autonomy_state_machine import AutonomyStateMachineState as S

    dest = coerce_canonical(destination)
    return tuple(s for s in S if project_engine_state(s) == dest)


def resolve_supervisor_request(
    current: object, destination: object
) -> tuple[str, Any]:
    """Route a canonical request against the supervisor's concrete table.

    Returns ``("noop", None)``, ``("emergency", None)``,
    ``("move", AutonomyState)`` or ``("reject", reason)`` — never raises
    for unknown/illegal input (fail-closed decisions, not exceptions).
    """
    from .autonomy_supervisor import _LEGAL_TRANSITIONS
    from .autonomy_supervisor import AutonomyState as S

    try:
        dest = coerce_canonical(destination)
    except IllegalAutonomyTransition as exc:
        return ("reject", str(exc))
    if not isinstance(current, S):
        return ("reject", f"cannot route from non-supervisor state {current!r}")
    current_canonical = project_supervisor_state(current)
    if dest == current_canonical:
        return ("noop", None)
    if dest is CanonicalAutonomyState.EMERGENCY_STOP:
        return ("emergency", None)
    if not is_canonical_transition_legal(current_canonical, dest):
        return (
            "reject",
            f"illegal canonical transition {current_canonical.value} -> {dest.value}",
        )
    for candidate in supervisor_concretes_for(dest):
        if (current, candidate) in _LEGAL_TRANSITIONS:
            return ("move", candidate)
    return (
        "reject",
        f"no concrete supervisor transition realizes "
        f"{current_canonical.value} -> {dest.value}",
    )


def request_supervisor_canonical(
    supervisor: AutonomySupervisor,
    destination: object,
    *,
    reason: str = "canonical_request",
    producer: str = "supervisor",
) -> bool:
    """Execute a canonical request on a supervisor.

    Fail-closed: an illegal, unknown, or unrealizable destination returns
    False with a TRANSITION_REJECTED audit event and no state change.
    """
    kind, payload = resolve_supervisor_request(supervisor.state, destination)
    if kind == "emergency":
        supervisor.emergency_stop(reason=reason)
        return True
    if kind == "move":
        return supervisor._transition(payload, reason=reason, producer=producer)
    if kind == "noop":
        return True
    supervisor._emit("TRANSITION_REJECTED", reason=payload, producer=producer)
    return False
