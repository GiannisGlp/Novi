"""Explicit boundary states (plan 24, Phase 14).

Boundary states: NORMAL, REDUCE_CONTACT, DO_NOT_INTERRUPT, DO_NOT_PROBE,
TOPIC_LIMIT, PRIVACY_LIMIT, SAFETY_LIMIT.

Rules (plan §18):
  - "I don't want to talk about that." → record boundary → stop probing;
  - if Novi notices a potentially emotional signal but the user does not want
    discussion → respect boundary → continue task normally;
  - boundary memory is durable where appropriate and revocable.

Deterministic and hardware-free.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .affective_evidence import utc_now_iso


class BoundaryState(str, Enum):
    NORMAL = "NORMAL"
    REDUCE_CONTACT = "REDUCE_CONTACT"
    DO_NOT_INTERRUPT = "DO_NOT_INTERRUPT"
    DO_NOT_PROBE = "DO_NOT_PROBE"
    TOPIC_LIMIT = "TOPIC_LIMIT"
    PRIVACY_LIMIT = "PRIVACY_LIMIT"
    SAFETY_LIMIT = "SAFETY_LIMIT"


# boundary state → actions it blocks
_BLOCKED_ACTIONS: dict[BoundaryState, set[str]] = {
    BoundaryState.REDUCE_CONTACT: {"initiate", "interrupt"},
    BoundaryState.DO_NOT_INTERRUPT: {"interrupt"},
    BoundaryState.DO_NOT_PROBE: {"probe"},
    BoundaryState.TOPIC_LIMIT: {"probe", "initiate"},
    BoundaryState.PRIVACY_LIMIT: {"probe", "interrupt"},
    BoundaryState.SAFETY_LIMIT: {"probe", "initiate", "interrupt"},
}


@dataclass
class Boundary:
    person: str
    topic: str
    state: BoundaryState = BoundaryState.NORMAL
    recorded_at: str = field(default_factory=utc_now_iso)

    def snapshot(self) -> dict[str, Any]:
        return {
            "person": self.person,
            "topic": self.topic,
            "state": self.state.value,
            "recorded_at": self.recorded_at,
        }

    @classmethod
    def from_snapshot(cls, data: dict[str, Any]) -> "Boundary":
        try:
            state = BoundaryState(str(data.get("state", "NORMAL")))
        except ValueError:
            state = BoundaryState.NORMAL
        return cls(
            person=str(data.get("person", "")),
            topic=str(data.get("topic", "")),
            state=state,
            recorded_at=str(data.get("recorded_at", "")),
        )


class BoundaryManager:
    """Per-person, per-topic boundary registry; durable and revocable."""

    def __init__(self) -> None:
        self._boundaries: dict[tuple[str, str], Boundary] = {}

    def record(self, person: str, topic: str, state: BoundaryState) -> Boundary:
        boundary = Boundary(person=person, topic=topic, state=state)
        self._boundaries[(person, topic)] = boundary
        return boundary

    def revoke(self, person: str, topic: str) -> None:
        self._boundaries.pop((person, topic), None)

    def state_for(self, person: str, topic: str) -> BoundaryState:
        boundary = self._boundaries.get((person, topic))
        return boundary.state if boundary else BoundaryState.NORMAL

    def allows(self, person: str, topic: str, *, action: str) -> bool:
        """Whether an action is allowed under the current boundary (plan §18)."""
        state = self.state_for(person, topic)
        return action not in _BLOCKED_ACTIONS.get(state, set())

    def snapshot(self) -> list[dict[str, Any]]:
        return [b.snapshot() for b in self._boundaries.values()]

    @classmethod
    def from_snapshot(cls, rows: list[dict[str, Any]]) -> "BoundaryManager":
        manager = cls()
        for row in rows:
            boundary = Boundary.from_snapshot(row)
            manager._boundaries[(boundary.person, boundary.topic)] = boundary
        return manager
