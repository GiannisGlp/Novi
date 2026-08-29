"""Behavior-tree semantics for the Mac Brain (06_AUTONOMY doc 05 Step 4).

Explicit control nodes — sequence, selector/fallback, retry (bounded), timeout,
condition, action, recovery — with explicit, recoverable execution state.

Rules enforced here:
- **Bounded**: a ``TreeRunner`` enforces a cycle budget; ``RetryNode`` retries
  at most ``max_retries`` times; ``TimeoutNode`` aborts after ``max_cycles``.
- **Verifiable**: ``ActionNode`` runs preconditions before executing and
  postcondition verification after (doc 05 Steps 5-6). An action whose
  preconditions fail is NEVER executed.
- **Recoverable**: ``RecoveryNode`` maps a failure class to a strategy
  (retry / refresh_perception / replan / alternative_skill / ask_user /
  safe_stop) — it never blindly repeats a failed action (doc 05 Step 7).
- **Learned**: ``OutcomeMemory`` records executions with context so future
  planning can prefer skills with demonstrated success (doc 05 Step 8).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Protocol


class Status(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RUNNING = "RUNNING"


@dataclass
class BTContext:
    """Per-run context: cycle, world state, outcome memory, parameters."""
    cycle: int = 0
    world: dict[str, Any] = field(default_factory=dict)
    memory: "OutcomeMemory | None" = None
    params: dict[str, Any] = field(default_factory=dict)
    started_cycle: int = 0

    def cycles_elapsed(self) -> int:
        return self.cycle - self.started_cycle


@dataclass(frozen=True)
class PostconditionCheck:
    """Verification of an action's expected effect (doc 05 Step 6)."""
    method: str
    passed: bool
    measured: dict[str, Any] = field(default_factory=dict)
    threshold: dict[str, Any] = field(default_factory=dict)
    error: str = ""


class Node(Protocol):
    def tick(self, ctx: BTContext) -> Status: ...
    def reset(self) -> None: ...


# ---------------------------------------------------------------------------
# Leaf nodes
# ---------------------------------------------------------------------------


class ActionNode:
    """Executes one skill/action with precondition + postcondition discipline.

    ``precondition(ctx)`` must return (ok, reason); if not ok, the action is
    NOT executed (FAILURE) — the A-PLAN-01 invariant. ``execute(ctx)`` returns
    the observed outcome; ``postcondition(ctx, outcome)`` verifies the effect.
    """

    def __init__(
        self,
        name: str,
        *,
        precondition: Callable[[BTContext], tuple[bool, str]] | None = None,
        execute: Callable[[BTContext], Any],
        postcondition: Callable[[BTContext, Any], PostconditionCheck] | None = None,
    ) -> None:
        self.name = name
        self.precondition = precondition
        self.execute = execute
        self.postcondition = postcondition
        self.precondition_failures = 0
        self.executions = 0
        self.verifications: list[PostconditionCheck] = []

    def tick(self, ctx: BTContext) -> Status:
        if self.precondition is not None:
            ok, reason = self.precondition(ctx)
            if not ok:
                self.precondition_failures += 1
                ctx.world.setdefault("last_failure", {})["reason"] = reason
                return Status.FAILURE
        outcome = self.execute(ctx)
        self.executions += 1
        if self.postcondition is not None:
            check = self.postcondition(ctx, outcome)
            self.verifications.append(check)
            if not check.passed:
                # A multi-cycle action that is still making progress reports
                # RUNNING (e.g. navigation mid-route); a TimeoutNode bounds it.
                if outcome.get("in_progress"):
                    return Status.RUNNING
                ctx.world.setdefault("last_failure", {})["reason"] = check.error or "postcondition_failed"
                return Status.FAILURE
        return Status.SUCCESS

    def reset(self) -> None:
        pass


class ConditionNode:
    def __init__(self, name: str, predicate: Callable[[BTContext], bool]) -> None:
        self.name = name
        self.predicate = predicate

    def tick(self, ctx: BTContext) -> Status:
        return Status.SUCCESS if self.predicate(ctx) else Status.FAILURE

    def reset(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Control nodes
# ---------------------------------------------------------------------------


class Sequence:
    """All children must succeed; state is explicit and resumable."""

    def __init__(self, children: list[Node], name: str = "sequence") -> None:
        self.children = children
        self.name = name
        self._index = 0

    def tick(self, ctx: BTContext) -> Status:
        while self._index < len(self.children):
            status = self.children[self._index].tick(ctx)
            if status is Status.RUNNING:
                return Status.RUNNING
            if status is Status.FAILURE:
                self._index = 0
                return Status.FAILURE
            self._index += 1
        self._index = 0
        return Status.SUCCESS

    def reset(self) -> None:
        self._index = 0
        for child in self.children:
            child.reset()


class Selector:
    """First succeeding child wins (fallback semantics)."""

    def __init__(self, children: list[Node], name: str = "selector") -> None:
        self.children = children
        self.name = name
        self._index = 0

    def tick(self, ctx: BTContext) -> Status:
        while self._index < len(self.children):
            status = self.children[self._index].tick(ctx)
            if status is Status.RUNNING:
                return Status.RUNNING
            if status is Status.SUCCESS:
                self._index = 0
                return Status.SUCCESS
            self._index += 1
        self._index = 0
        return Status.FAILURE

    def reset(self) -> None:
        self._index = 0
        for child in self.children:
            child.reset()


class RetryNode:
    """Retries a child a bounded number of times after FAILURE (doc 05 Step 7)."""

    def __init__(self, child: Node, max_retries: int, name: str = "retry") -> None:
        self.child = child
        self.max_retries = max_retries
        self.name = name
        self._attempts = 0

    def tick(self, ctx: BTContext) -> Status:
        status = self.child.tick(ctx)
        if status is Status.FAILURE and self._attempts < self.max_retries:
            self._attempts += 1
            self.child.reset()
            return Status.RUNNING
        self._attempts = 0
        return status

    def reset(self) -> None:
        self._attempts = 0
        self.child.reset()


class TimeoutNode:
    """Aborts a child after a bounded number of cycles."""

    def __init__(self, child: Node, max_cycles: int, name: str = "timeout") -> None:
        self.child = child
        self.max_cycles = max_cycles
        self.name = name
        self._start_cycle: int | None = None

    def tick(self, ctx: BTContext) -> Status:
        if self._start_cycle is None:
            self._start_cycle = ctx.cycle
        if ctx.cycle - self._start_cycle > self.max_cycles:
            self._start_cycle = None
            self.child.reset()
            return Status.FAILURE
        status = self.child.tick(ctx)
        if status in (Status.SUCCESS, Status.FAILURE):
            self._start_cycle = None
        return status

    def reset(self) -> None:
        self._start_cycle = None
        self.child.reset()


class RecoveryNode:
    """Maps a failure to a recovery strategy (doc 05 Step 7 / doc 07 Step 4).

    Strategies: retry | refresh_perception | replan | alternative_skill |
    ask_user | safe_stop. ``replan_factory`` rebuilds the subtree (replan);
    ``fallback`` is tried first (alternative_skill). safe_stop returns a
    terminal FAILURE without re-executing.
    """

    def __init__(
        self,
        child: Node,
        *,
        strategy: str = "retry",
        max_retries: int = 2,
        fallback: Node | None = None,
        replan_factory: Callable[[], Node] | None = None,
        name: str = "recovery",
    ) -> None:
        self.child = child
        self.strategy = strategy
        self.max_retries = max_retries
        self.fallback = fallback
        self.replan_factory = replan_factory
        self.name = name
        self._attempts = 0
        self.recovery_events: list[dict[str, Any]] = []

    def tick(self, ctx: BTContext) -> Status:
        status = self.child.tick(ctx)
        if status is Status.SUCCESS or status is Status.RUNNING:
            return status

        # FAILURE -> strategy.
        if self.strategy == "safe_stop":
            self._record(ctx, "safe_stop")
            return Status.FAILURE
        if self.strategy == "ask_user":
            self._record(ctx, "ask_user")
            return Status.FAILURE  # bounded: the operator must act externally
        if self.strategy == "replan" and self.replan_factory is not None:
            self.child.reset()
            self.child = self.replan_factory()
            self._record(ctx, "replan")
            return Status.RUNNING
        if self.strategy == "alternative_skill" and self.fallback is not None:
            status = self.fallback.tick(ctx)
            self._record(ctx, "alternative_skill", status.value)
            return status
        # retry / refresh_perception: bounded retries on the same child.
        if self._attempts < self.max_retries:
            self._attempts += 1
            self.child.reset()
            self._record(ctx, self.strategy)
            return Status.RUNNING
        self._attempts = 0
        return Status.FAILURE

    def _record(self, ctx: BTContext, strategy: str, detail: str = "") -> None:
        self.recovery_events.append({
            "cycle": ctx.cycle, "strategy": strategy, "detail": detail,
        })

    def reset(self) -> None:
        self._attempts = 0
        self.child.reset()
        if self.fallback is not None:
            self.fallback.reset()


# ---------------------------------------------------------------------------
# Runner and outcome memory
# ---------------------------------------------------------------------------


class TreeRunner:
    """Runs a behavior tree to SUCCESS/FAILURE within a cycle budget."""

    def __init__(self, root: Node, *, max_cycles: int = 100) -> None:
        self.root = root
        self.max_cycles = max_cycles

    def run(self, ctx: BTContext) -> tuple[Status, int]:
        ctx.started_cycle = ctx.cycle
        while ctx.cycles_elapsed() <= self.max_cycles:
            status = self.root.tick(ctx)
            if status is Status.RUNNING:
                ctx.cycle += 1
                continue
            return status, ctx.cycles_elapsed()
        self.root.reset()
        return Status.FAILURE, ctx.cycles_elapsed()


@dataclass
class OutcomeRecord:
    skill_id: str
    outcome: str                    # SUCCESS | FAILURE
    verification: str               # PASS | FAIL | UNVERIFIED
    context: dict[str, Any]
    cycle: int

    def snapshot(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id, "outcome": self.outcome,
            "verification": self.verification, "context": dict(self.context),
            "cycle": self.cycle,
        }


class OutcomeMemory:
    """Skill outcome memory with context (doc 05 Step 8).

    Records successful and failed executions — not merely success counts — so
    future planning can prefer skills with demonstrated success in similar
    contexts.
    """

    def __init__(self, max_records: int = 1000) -> None:
        self._records: list[OutcomeRecord] = []
        self._max = max_records

    def record(self, *, skill_id: str, outcome: str, verification: str,
               context: dict[str, Any], cycle: int) -> None:
        self._records.append(OutcomeRecord(skill_id, outcome, verification, dict(context), cycle))
        if len(self._records) > self._max:
            self._records = self._records[-self._max:]

    def success_rate(self, skill_id: str, *, context_filter: dict[str, Any] | None = None) -> float | None:
        records = [r for r in self._records if r.skill_id == skill_id]
        if context_filter:
            records = [r for r in records
                       if all(r.context.get(k) == v for k, v in context_filter.items())]
        if not records:
            return None
        return sum(1 for r in records if r.outcome == "SUCCESS") / len(records)

    def records_for(self, skill_id: str) -> tuple[OutcomeRecord, ...]:
        return tuple(r for r in self._records if r.skill_id == skill_id)

    def count(self) -> int:
        return len(self._records)
