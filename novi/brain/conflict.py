"""Conflict handling state machine (plan 24, Phase 12).

NORMAL → CORRECTION → DISAGREEMENT → TENSION → REPAIR → RESOLUTION.

Rules (plan §16):
  - never become defensive;
  - never blame the user for Novi's misunderstanding;
  - distinguish disagreement from hostility;
  - ask clarifying questions when needed;
  - stop arguing when evidence does not justify continued disagreement;
  - preserve factual honesty.

Deterministic and hardware-free: a pure transition function.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class ConflictState(str, Enum):
    NORMAL = "NORMAL"
    CORRECTION = "CORRECTION"
    DISAGREEMENT = "DISAGREEMENT"
    TENSION = "TENSION"
    REPAIR = "REPAIR"
    RESOLUTION = "RESOLUTION"


# event → {from_state: to_state}; missing entries keep the current state.
_TRANSITIONS: dict[str, dict[ConflictState, ConflictState]] = {
    "user_correction": {
        ConflictState.NORMAL: ConflictState.CORRECTION,
        ConflictState.DISAGREEMENT: ConflictState.CORRECTION,
        ConflictState.REPAIR: ConflictState.CORRECTION,
        ConflictState.RESOLUTION: ConflictState.CORRECTION,
    },
    "contradiction": {
        ConflictState.NORMAL: ConflictState.DISAGREEMENT,
        ConflictState.CORRECTION: ConflictState.DISAGREEMENT,
        ConflictState.RESOLUTION: ConflictState.DISAGREEMENT,
    },
    "user_rejection": {
        # stop arguing when the user rejects — never escalate to hostility
        ConflictState.DISAGREEMENT: ConflictState.REPAIR,
        ConflictState.CORRECTION: ConflictState.TENSION,
        ConflictState.NORMAL: ConflictState.CORRECTION,
    },
    "novi_error": {
        ConflictState.TENSION: ConflictState.REPAIR,
        ConflictState.NORMAL: ConflictState.CORRECTION,
    },
    "repeated_misunderstanding": {
        ConflictState.CORRECTION: ConflictState.TENSION,
        ConflictState.DISAGREEMENT: ConflictState.TENSION,
        ConflictState.NORMAL: ConflictState.CORRECTION,
    },
    "successful_clarification": {
        ConflictState.NORMAL: ConflictState.RESOLUTION,
        ConflictState.CORRECTION: ConflictState.RESOLUTION,
        ConflictState.DISAGREEMENT: ConflictState.RESOLUTION,
        ConflictState.TENSION: ConflictState.RESOLUTION,
        ConflictState.REPAIR: ConflictState.RESOLUTION,
    },
}


class ConflictStateMachine:
    """Tracks the conflict state and applies plan §16 transition rules."""

    def __init__(self) -> None:
        self.state = ConflictState.NORMAL

    def transition(self, event: str) -> ConflictState:
        """Apply an event; returns the new state."""
        table = _TRANSITIONS.get(event)
        if table is not None:
            self.state = table.get(self.state, self.state)
        return self.state

    def snapshot(self) -> dict[str, Any]:
        return {"state": self.state.value}

    @classmethod
    def from_snapshot(cls, data: dict[str, Any]) -> "ConflictStateMachine":
        machine = cls()
        try:
            machine.state = ConflictState(str(data.get("state", "NORMAL")))
        except ValueError:
            machine.state = ConflictState.NORMAL
        return machine
