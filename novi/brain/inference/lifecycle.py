"""Runtime lifecycle state machines (plan 12, §18 Phase 13, §37 Phase 37).

Two validated state machines:

- ``ModelLifecycle`` — backend/model lifecycle:
  UNKNOWN, REGISTERED, VALIDATING, PREPARING, READY, LOADING, LOADED, RUNNING,
  DRAINING, UNLOADED, DEGRADED, FAILED (plan 12, §18).

  Invalid transitions (e.g. FAILED -> RUNNING) are rejected with
  ``LifecycleTransitionError``; ``shutdown``/``unload`` are idempotent.

- ``ModelResidency`` — residency policy states (plan 12, §37):
  NOT_PREPARED, PREPARED, COLD, WARM, ACTIVE, DRAINING. Residency becomes part
  of routing cost: the router may prefer a slightly less capable model if
  switching to a cold giant model would violate the request deadline.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class ModelLifecycle(str, Enum):
    UNKNOWN = "UNKNOWN"
    REGISTERED = "REGISTERED"
    VALIDATING = "VALIDATING"
    PREPARING = "PREPARING"
    READY = "READY"
    LOADING = "LOADING"
    LOADED = "LOADED"
    RUNNING = "RUNNING"
    DRAINING = "DRAINING"
    UNLOADED = "UNLOADED"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"


class ModelResidency(str, Enum):
    NOT_PREPARED = "NOT_PREPARED"
    PREPARED = "PREPARED"
    COLD = "COLD"
    WARM = "WARM"
    ACTIVE = "ACTIVE"
    DRAINING = "DRAINING"


#: Valid lifecycle transitions: (from, to) pairs.
_LIFECYCLE_EDGES: frozenset[tuple[ModelLifecycle, ModelLifecycle]] = frozenset(
    {
        (ModelLifecycle.UNKNOWN, ModelLifecycle.REGISTERED),
        (ModelLifecycle.REGISTERED, ModelLifecycle.VALIDATING),
        (ModelLifecycle.REGISTERED, ModelLifecycle.FAILED),
        (ModelLifecycle.VALIDATING, ModelLifecycle.PREPARING),
        (ModelLifecycle.VALIDATING, ModelLifecycle.READY),
        (ModelLifecycle.VALIDATING, ModelLifecycle.FAILED),
        (ModelLifecycle.PREPARING, ModelLifecycle.READY),
        (ModelLifecycle.PREPARING, ModelLifecycle.FAILED),
        (ModelLifecycle.READY, ModelLifecycle.LOADING),
        (ModelLifecycle.READY, ModelLifecycle.DEGRADED),
        (ModelLifecycle.READY, ModelLifecycle.UNLOADED),
        (ModelLifecycle.LOADING, ModelLifecycle.LOADED),
        (ModelLifecycle.LOADING, ModelLifecycle.FAILED),
        (ModelLifecycle.LOADING, ModelLifecycle.READY),
        (ModelLifecycle.LOADED, ModelLifecycle.RUNNING),
        (ModelLifecycle.LOADED, ModelLifecycle.READY),
        (ModelLifecycle.LOADED, ModelLifecycle.DRAINING),
        (ModelLifecycle.LOADED, ModelLifecycle.FAILED),
        (ModelLifecycle.RUNNING, ModelLifecycle.LOADED),
        (ModelLifecycle.RUNNING, ModelLifecycle.DRAINING),
        (ModelLifecycle.RUNNING, ModelLifecycle.DEGRADED),
        (ModelLifecycle.RUNNING, ModelLifecycle.FAILED),
        (ModelLifecycle.DRAINING, ModelLifecycle.UNLOADED),
        (ModelLifecycle.DRAINING, ModelLifecycle.READY),
        (ModelLifecycle.DRAINING, ModelLifecycle.FAILED),
        (ModelLifecycle.DEGRADED, ModelLifecycle.READY),
        (ModelLifecycle.DEGRADED, ModelLifecycle.FAILED),
        (ModelLifecycle.DEGRADED, ModelLifecycle.UNLOADED),
        (ModelLifecycle.UNLOADED, ModelLifecycle.REGISTERED),
        (ModelLifecycle.UNLOADED, ModelLifecycle.READY),
        (ModelLifecycle.FAILED, ModelLifecycle.UNLOADED),
        (ModelLifecycle.FAILED, ModelLifecycle.REGISTERED),
        (ModelLifecycle.FAILED, ModelLifecycle.READY),
    }
)

#: Valid residency transitions.
_RESIDENCY_EDGES: frozenset[tuple[ModelResidency, ModelResidency]] = frozenset(
    {
        (ModelResidency.NOT_PREPARED, ModelResidency.PREPARED),
        (ModelResidency.NOT_PREPARED, ModelResidency.COLD),
        (ModelResidency.PREPARED, ModelResidency.COLD),
        (ModelResidency.PREPARED, ModelResidency.WARM),
        (ModelResidency.PREPARED, ModelResidency.ACTIVE),
        (ModelResidency.COLD, ModelResidency.WARM),
        (ModelResidency.COLD, ModelResidency.ACTIVE),
        (ModelResidency.WARM, ModelResidency.ACTIVE),
        (ModelResidency.WARM, ModelResidency.COLD),
        (ModelResidency.ACTIVE, ModelResidency.WARM),
        (ModelResidency.ACTIVE, ModelResidency.DRAINING),
        (ModelResidency.DRAINING, ModelResidency.COLD),
        (ModelResidency.DRAINING, ModelResidency.NOT_PREPARED),
    }
)


class LifecycleTransitionError(Exception):
    """Raised when a lifecycle transition is not allowed."""

    def __init__(self, machine: str, current: Enum, target: Enum) -> None:
        super().__init__(f"invalid {machine} transition: {current.value} -> {target.value}")
        self.machine = machine
        self.current = current
        self.target = target


class LifecycleMachine:
    """Validated single-entity lifecycle state machine."""

    def __init__(
        self,
        *,
        machine_name: str,
        initial: Enum,
        edges: frozenset[tuple[Enum, Enum]],
        transitions: list[tuple[Enum, Enum]] | None = None,
    ) -> None:
        self.machine_name = machine_name
        self.state = initial
        self._edges = edges
        self._transitions: list[tuple[Enum, Enum]] = transitions or []

    def can(self, target: Enum) -> bool:
        return (self.state, target) in self._edges

    def transition(self, target: Enum) -> Enum:
        if not self.can(target):
            raise LifecycleTransitionError(self.machine_name, self.state, target)
        self._transitions.append((self.state, target))
        self.state = target
        return self.state

    def transition_to(self, target: Enum) -> Enum:
        """Advance to ``target`` walking a valid path (each hop is validated).

        Backends request the target state directly (e.g. LOADED); the machine
        walks a canonical BFS path so every intermediate transition remains a
        validated hop of the state graph.
        """
        if self.state is target:
            return target
        path = self._find_path(self.state, target)
        if path is None:
            raise LifecycleTransitionError(self.machine_name, self.state, target)
        for hop in path:
            self.transition(hop)
        return self.state

    def _find_path(self, start: Enum, goal: Enum) -> list[Enum] | None:
        from collections import deque

        queue: deque[tuple[Enum, list[Enum]]] = deque([(start, [])])
        visited = {start}
        while queue:
            current, path = queue.popleft()
            for src, dst in self._edges:
                if src is current and dst not in visited:
                    new_path = path + [dst]
                    if dst is goal:
                        return new_path
                    visited.add(dst)
                    queue.append((dst, new_path))
        return None

    def snapshot(self) -> dict[str, Any]:
        return {
            "machine": self.machine_name,
            "state": self.state.value,
            "transitions": [(a.value, b.value) for a, b in self._transitions],
        }


def new_model_lifecycle(initial: ModelLifecycle = ModelLifecycle.UNKNOWN) -> LifecycleMachine:
    return LifecycleMachine(
        machine_name="model_lifecycle",
        initial=initial,
        edges=_LIFECYCLE_EDGES,  # type: ignore[arg-type]
    )


def new_residency(initial: ModelResidency = ModelResidency.NOT_PREPARED) -> LifecycleMachine:
    return LifecycleMachine(
        machine_name="model_residency",
        initial=initial,
        edges=_RESIDENCY_EDGES,  # type: ignore[arg-type]
    )
