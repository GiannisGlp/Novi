"""Full Autonomy State Machine for the Mac Brain.

Defines deterministic lifecycle states for the autonomy runtime. Model outputs
may influence transitions, but cannot bypass transition guards.

Canonical authority: docs/02-autonomy/07_AUTONOMY_STATE_MACHINE.md

States:
  BOOTING → INITIALIZING → OBSERVING → AWARE
  AWARE → {INTERACTING, PLANNING, EXECUTING, LEARNING, MAINTENANCE, SAFE_DEGRADED}
  Terminal/recovery: SHUTTING_DOWN, EMERGENCY_STOP, FAULT_RECOVERY

Every transition has: source state, event/condition, guard, destination,
side effects, audit event.

Acceptance criteria:
  - all transitions are explicit;
  - invalid transitions are rejected;
  - emergency conditions override normal operation;
  - recovery revalidates world state;
  - state changes are observable and auditable;
  - simulation can deterministically exercise every state and transition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Sequence
from uuid import uuid4


# ---------------------------------------------------------------------------
# States (docs/02-autonomy/07)
# ---------------------------------------------------------------------------

class AutonomyStateMachineState(str, Enum):
    BOOTING = "BOOTING"
    INITIALIZING = "INITIALIZING"
    OBSERVING = "OBSERVING"
    AWARE = "AWARE"
    INTERACTING = "INTERACTING"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    LEARNING = "LEARNING"
    MAINTENANCE = "MAINTENANCE"
    SAFE_DEGRADED = "SAFE_DEGRADED"
    SHUTTING_DOWN = "SHUTTING_DOWN"
    EMERGENCY_STOP = "EMERGENCY_STOP"
    FAULT_RECOVERY = "FAULT_RECOVERY"


# Convenience aliases.
BOOTING = AutonomyStateMachineState.BOOTING
INITIALIZING = AutonomyStateMachineState.INITIALIZING
OBSERVING = AutonomyStateMachineState.OBSERVING
AWARE = AutonomyStateMachineState.AWARE
INTERACTING = AutonomyStateMachineState.INTERACTING
PLANNING = AutonomyStateMachineState.PLANNING
EXECUTING = AutonomyStateMachineState.EXECUTING
LEARNING = AutonomyStateMachineState.LEARNING
MAINTENANCE = AutonomyStateMachineState.MAINTENANCE
SAFE_DEGRADED = AutonomyStateMachineState.SAFE_DEGRADED
SHUTTING_DOWN = AutonomyStateMachineState.SHUTTING_DOWN
EMERGENCY_STOP = AutonomyStateMachineState.EMERGENCY_STOP
FAULT_RECOVERY = AutonomyStateMachineState.FAULT_RECOVERY


# ---------------------------------------------------------------------------
# Transition record (audit event)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TransitionRecord:
    """An audit record for a state machine transition."""
    transition_id: str
    source: str
    event: str
    guard: str  # guard condition that was checked
    destination: str
    side_effects: tuple[str, ...]
    timestamp: str
    accepted: bool = True
    reason: str = ""

    def snapshot(self) -> dict[str, Any]:
        return {
            "transition_id": self.transition_id,
            "source": self.source,
            "event": self.event,
            "guard": self.guard,
            "destination": self.destination,
            "side_effects": list(self.side_effects),
            "timestamp": self.timestamp,
            "accepted": self.accepted,
            "reason": self.reason,
        }


# ---------------------------------------------------------------------------
# Transition definition
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Transition:
    """A defined state machine transition."""
    source: AutonomyStateMachineState
    event: str
    destination: AutonomyStateMachineState
    guard: str = ""  # human-readable guard description
    side_effects: tuple[str, ...] = ()
    priority: int = 0  # higher = can interrupt lower


# ---------------------------------------------------------------------------
# Canonical transition table
# ---------------------------------------------------------------------------

# The canonical transitions. Emergency transitions have high priority and
# can interrupt any state.
CANONICAL_TRANSITIONS: tuple[Transition, ...] = (
    # Boot sequence.
    Transition(BOOTING, "boot_complete", INITIALIZING, guard="runtime_loaded"),
    Transition(INITIALIZING, "init_complete", OBSERVING, guard="sensors_verified"),
    Transition(INITIALIZING, "init_failed", FAULT_RECOVERY, guard="dependency_failure"),

    # Observing → AWARE (something happened).
    Transition(OBSERVING, "significant_event", AWARE, guard="event_is_significant"),
    Transition(OBSERVING, "person_detected", AWARE, guard="person_present"),
    Transition(OBSERVING, "goal_set", PLANNING, guard="goal_is_valid"),

    # AWARE → sub-states.
    Transition(AWARE, "interaction_started", INTERACTING, guard="person_engaged"),
    Transition(AWARE, "planning_needed", PLANNING, guard="goal_requires_planning"),
    Transition(AWARE, "execution_ready", EXECUTING, guard="action_authorized"),
    Transition(AWARE, "learning_opportunity", LEARNING, guard="evidence_available"),
    Transition(AWARE, "maintenance_needed", MAINTENANCE, guard="diagnostics_required"),
    Transition(AWARE, "degradation_detected", SAFE_DEGRADED, guard="component_unavailable"),

    # Sub-states → OBSERVING (return to passive).
    Transition(INTERACTING, "interaction_ended", OBSERVING, guard="person_disengaged"),
    Transition(PLANNING, "plan_ready", EXECUTING, guard="plan_is_valid"),
    Transition(PLANNING, "planning_aborted", OBSERVING, guard="goal_cancelled"),
    Transition(EXECUTING, "action_completed", OBSERVING, guard="outcome_verified"),
    Transition(EXECUTING, "action_failed", PLANNING, guard="recovery_needed"),
    Transition(LEARNING, "learning_complete", OBSERVING, guard="consolidation_done"),
    Transition(MAINTENANCE, "maintenance_complete", OBSERVING, guard="diagnostics_passed"),

    # Safe degraded → recovery.
    Transition(SAFE_DEGRADED, "component_recovered", OBSERVING, guard="component_available"),
    Transition(SAFE_DEGRADED, "component_still_degraded", SAFE_DEGRADED, guard="still_unavailable"),

    # Fault recovery.
    Transition(FAULT_RECOVERY, "recovery_complete", INITIALIZING, guard="system_repaired"),
    Transition(FAULT_RECOVERY, "recovery_failed", EMERGENCY_STOP, guard="unrecoverable"),

    # Emergency (can interrupt ANY state — priority 100).
    Transition(AWARE, "emergency", EMERGENCY_STOP, guard="safety_critical", priority=100),
    Transition(INTERACTING, "emergency", EMERGENCY_STOP, guard="safety_critical", priority=100),
    Transition(PLANNING, "emergency", EMERGENCY_STOP, guard="safety_critical", priority=100),
    Transition(EXECUTING, "emergency", EMERGENCY_STOP, guard="safety_critical", priority=100),
    Transition(LEARNING, "emergency", EMERGENCY_STOP, guard="safety_critical", priority=100),
    Transition(MAINTENANCE, "emergency", EMERGENCY_STOP, guard="safety_critical", priority=100),
    Transition(OBSERVING, "emergency", EMERGENCY_STOP, guard="safety_critical", priority=100),
    Transition(SAFE_DEGRADED, "emergency", EMERGENCY_STOP, guard="safety_critical", priority=100),

    # Shutdown (can interrupt any non-emergency state — priority 90).
    Transition(OBSERVING, "shutdown_requested", SHUTTING_DOWN, guard="shutdown_authorized", priority=90),
    Transition(AWARE, "shutdown_requested", SHUTTING_DOWN, guard="shutdown_authorized", priority=90),
    Transition(INTERACTING, "shutdown_requested", SHUTTING_DOWN, guard="shutdown_authorized", priority=90),
    Transition(PLANNING, "shutdown_requested", SHUTTING_DOWN, guard="shutdown_authorized", priority=90),
    Transition(EXECUTING, "shutdown_requested", SHUTTING_DOWN, guard="shutdown_authorized", priority=90),
    Transition(LEARNING, "shutdown_requested", SHUTTING_DOWN, guard="shutdown_authorized", priority=90),
    Transition(MAINTENANCE, "shutdown_requested", SHUTTING_DOWN, guard="shutdown_authorized", priority=90),
    Transition(SAFE_DEGRADED, "shutdown_requested", SHUTTING_DOWN, guard="shutdown_authorized", priority=90),

    # Emergency stop → fault recovery.
    Transition(EMERGENCY_STOP, "recovery_initiated", FAULT_RECOVERY, guard="recovery_authorized"),
)


# ---------------------------------------------------------------------------
# AutonomyStateMachine
# ---------------------------------------------------------------------------

class AutonomyStateMachine:
    """Full autonomy state machine with explicit transitions and audit events.

    All transitions are explicit. Invalid transitions are rejected. Emergency
    conditions override normal operation. State changes are observable and
    auditable.
    """

    def __init__(self) -> None:
        self._state: AutonomyStateMachineState = BOOTING
        self._transitions: list[TransitionRecord] = []
        self._transition_table: dict[tuple[AutonomyStateMachineState, str], Transition] = {}
        for t in CANONICAL_TRANSITIONS:
            self._transition_table[(t.source, t.event)] = t

    @property
    def state(self) -> AutonomyStateMachineState:
        return self._state

    @property
    def is_operational(self) -> bool:
        """True if the system is in a state that allows normal operation."""
        return self._state in (OBSERVING, AWARE, INTERACTING, PLANNING, EXECUTING, LEARNING, MAINTENANCE)

    @property
    def is_emergency(self) -> bool:
        return self._state == EMERGENCY_STOP

    @property
    def is_degraded(self) -> bool:
        return self._state == SAFE_DEGRADED

    @property
    def is_terminal(self) -> bool:
        return self._state in (SHUTTING_DOWN, EMERGENCY_STOP)

    def transition(
        self,
        event: str,
        *,
        guard_check: Callable[[], bool] | None = None,
        timestamp: str = "",
    ) -> TransitionRecord:
        """Attempt a state transition triggered by an event.

        Args:
            event: The event name (e.g. "boot_complete", "person_detected").
            guard_check: Optional callable that returns True if the guard
                         condition is satisfied. If None, the guard is assumed
                         to pass.
            timestamp: Optional timestamp for the audit record.

        Returns:
            A TransitionRecord (accepted or rejected).
        """
        key = (self._state, event)
        transition = self._transition_table.get(key)

        if transition is None:
            # Invalid transition — rejected.
            record = TransitionRecord(
                transition_id=str(uuid4()),
                source=self._state.value,
                event=event,
                guard="no_transition_defined",
                destination=self._state.value,
                side_effects=(),
                timestamp=timestamp,
                accepted=False,
                reason=f"no transition from {self._state.value} on event {event!r}",
            )
            self._transitions.append(record)
            return record

        # Check guard.
        guard_passed = True
        if guard_check is not None:
            guard_passed = guard_check()

        if not guard_passed:
            record = TransitionRecord(
                transition_id=str(uuid4()),
                source=self._state.value,
                event=event,
                guard=transition.guard,
                destination=self._state.value,
                side_effects=(),
                timestamp=timestamp,
                accepted=False,
                reason=f"guard failed: {transition.guard}",
            )
            self._transitions.append(record)
            return record

        # Execute transition.
        old_state = self._state
        self._state = transition.destination
        record = TransitionRecord(
            transition_id=str(uuid4()),
            source=old_state.value,
            event=event,
            guard=transition.guard,
            destination=transition.destination.value,
            side_effects=transition.side_effects,
            timestamp=timestamp,
            accepted=True,
        )
        self._transitions.append(record)
        return record

    def emergency_stop(self, *, timestamp: str = "") -> TransitionRecord:
        """Force an emergency stop from any state. Overrides normal operation."""
        if self._state == EMERGENCY_STOP:
            return TransitionRecord(
                transition_id=str(uuid4()),
                source=self._state.value, event="emergency",
                guard="already_in_emergency_stop", destination=self._state.value,
                side_effects=(), timestamp=timestamp, accepted=True,
                reason="already in EMERGENCY_STOP",
            )
        old_state = self._state
        self._state = EMERGENCY_STOP
        record = TransitionRecord(
            transition_id=str(uuid4()),
            source=old_state.value, event="emergency",
            guard="safety_critical", destination=EMERGENCY_STOP.value,
            side_effects=("stop_all_actions", "preserve_state", "audit"),
            timestamp=timestamp, accepted=True,
        )
        self._transitions.append(record)
        return record

    def shutdown(self, *, timestamp: str = "") -> TransitionRecord:
        """Initiate shutdown from any non-emergency state."""
        if self._state == EMERGENCY_STOP:
            return TransitionRecord(
                transition_id=str(uuid4()),
                source=self._state.value, event="shutdown_requested",
                guard="cannot_shutdown_from_emergency", destination=self._state.value,
                side_effects=(), timestamp=timestamp, accepted=False,
                reason="cannot shutdown from EMERGENCY_STOP",
            )
        old_state = self._state
        self._state = SHUTTING_DOWN
        record = TransitionRecord(
            transition_id=str(uuid4()),
            source=old_state.value, event="shutdown_requested",
            guard="shutdown_authorized", destination=SHUTTING_DOWN.value,
            side_effects=("cleanup", "persist_state", "audit"),
            timestamp=timestamp, accepted=True,
        )
        self._transitions.append(record)
        return record

    @property
    def transition_history(self) -> tuple[TransitionRecord, ...]:
        return tuple(self._transitions)

    @property
    def accepted_transitions(self) -> tuple[TransitionRecord, ...]:
        return tuple(t for t in self._transitions if t.accepted)

    @property
    def rejected_transitions(self) -> tuple[TransitionRecord, ...]:
        return tuple(t for t in self._transitions if not t.accepted)

    def available_events(self) -> tuple[str, ...]:
        """Events that are valid from the current state."""
        return tuple(
            event for (source, event) in self._transition_table
            if source == self._state
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "state": self._state.value,
            "is_operational": self.is_operational,
            "is_emergency": self.is_emergency,
            "is_degraded": self.is_degraded,
            "is_terminal": self.is_terminal,
            "available_events": list(self.available_events()),
            "transition_count": len(self._transitions),
            "accepted_count": len(self.accepted_transitions),
            "rejected_count": len(self.rejected_transitions),
            "recent_transitions": [t.snapshot() for t in self._transitions[-10:]],
        }