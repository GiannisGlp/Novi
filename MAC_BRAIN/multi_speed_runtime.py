"""Multi-Speed Runtime for the Mac Brain (PERFECTING_PLAN Step 3).

Implements the System 0/1/2/3 multi-speed runtime with a deterministic System-0
safety/reactivity tier that never waits on an LLM.

Canonical authority:
  - docs/02-novi-brain (multi-speed System 0/1/2/3)
  - docs/02-autonomy/07_AUTONOMY_STATE_MACHINE.md
  - PERFECTING_PLAN/05_GAP_ANALYSIS_BRAIN.md

System tiers:
  System 0: deterministic safety/reactivity — immediate, never waits on LLM.
  System 1: fast reactive decisions (bounded, < 100ms).
  System 2: deliberative reasoning (bounded, < 5s).
  System 3: deep planning/reflection (bounded, background).

The autonomy state machine: idle/active/degraded with interruption/resume.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

# ---------------------------------------------------------------------------
# System tiers
# ---------------------------------------------------------------------------

SYSTEM_0 = "system_0"  # deterministic safety/reactivity
SYSTEM_1 = "system_1"  # fast reactive
SYSTEM_2 = "system_2"  # deliberative
SYSTEM_3 = "system_3"  # deep planning

ALL_SYSTEM_TIERS = frozenset({SYSTEM_0, SYSTEM_1, SYSTEM_2, SYSTEM_3})


# ---------------------------------------------------------------------------
# Autonomy state machine (docs/02-autonomy/07)
# ---------------------------------------------------------------------------

class AutonomyState(str, Enum):
    IDLE = "idle"
    ACTIVE = "active"
    DEGRADED = "degraded"
    SAFE_MINIMUM = "safe_minimum"
    INTERRUPTED = "interrupted"


# Resource modes (docs/02-novi-brain)
class ResourceMode(str, Enum):
    FULL = "full"
    DEGRADED = "degraded"
    REACTIVE_ONLY = "reactive_only"
    SAFE_MINIMUM = "safe_minimum"


# ---------------------------------------------------------------------------
# SystemTask — one scheduled task at a given tier
# ---------------------------------------------------------------------------

@dataclass
class SystemTask:
    """A scheduled task at a given system tier."""
    task_id: str
    tier: str
    name: str
    handler: Callable[[dict[str, Any]], Any] | None = None
    priority: float = 0.0
    max_latency_ms: float = float("inf")
    last_result: Any = None
    last_run_cycle: int = -1
    enabled: bool = True

    def snapshot(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "tier": self.tier,
            "name": self.name,
            "priority": self.priority,
            "max_latency_ms": self.max_latency_ms,
            "enabled": self.enabled,
            "last_run_cycle": self.last_run_cycle,
        }


# ---------------------------------------------------------------------------
# MultiSpeedRuntime
# ---------------------------------------------------------------------------

class MultiSpeedRuntime:
    """Multi-speed runtime with System-0 safety tier that never waits on an LLM.

    System 0 tasks always run first and can gate (interrupt, pause, or stop)
    higher-tier tasks. System 1/2/3 tasks run after System 0 clears safety.
    """

    def __init__(self) -> None:
        self._tasks: dict[str, SystemTask] = {}
        self.state: AutonomyState = AutonomyState.IDLE
        self.resource_mode: ResourceMode = ResourceMode.FULL
        self._system0_safety_clear: bool = True
        self._cycle: int = 0
        self._interrupted_tasks: set[str] = set()

    # ---- task registration ----

    def register(
        self,
        tier: str,
        name: str,
        handler: Callable[[dict[str, Any]], Any] | None = None,
        *,
        priority: float = 0.0,
        max_latency_ms: float = float("inf"),
    ) -> SystemTask:
        if tier not in ALL_SYSTEM_TIERS:
            raise ValueError(f"unknown system tier: {tier!r}")
        task_id = f"task:{tier}:{name}"
        task = SystemTask(
            task_id=task_id, tier=tier, name=name, handler=handler,
            priority=priority, max_latency_ms=max_latency_ms,
        )
        self._tasks[task_id] = task
        return task

    def unregister(self, task_id: str) -> bool:
        return self._tasks.pop(task_id, None) is not None

    def get_task(self, task_id: str) -> SystemTask | None:
        return self._tasks.get(task_id)

    # ---- state machine ----

    def set_state(self, state: AutonomyState) -> None:
        self.state = state

    def set_resource_mode(self, mode: ResourceMode) -> None:
        self.resource_mode = mode
        if mode == ResourceMode.SAFE_MINIMUM:
            self.state = AutonomyState.SAFE_MINIMUM
        elif mode == ResourceMode.DEGRADED:
            self.state = AutonomyState.DEGRADED

    def interrupt(self) -> None:
        """Interrupt all non-System-0 tasks (safety override)."""
        self._interrupted_tasks = {
            tid for tid, t in self._tasks.items() if t.tier != SYSTEM_0
        }
        self.state = AutonomyState.INTERRUPTED

    def resume(self) -> None:
        """Resume after an interruption."""
        self._interrupted_tasks.clear()
        self.state = AutonomyState.ACTIVE if self.resource_mode == ResourceMode.FULL else AutonomyState.DEGRADED

    # ---- execution ----

    def step(self, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Run one cycle of the multi-speed runtime.

        System 0 tasks run first (safety gating). If System 0 flags unsafe,
        higher tiers are interrupted/skipped.
        """
        context = context or {}
        self._cycle += 1
        results: dict[str, Any] = {}

        # ---- System 0: always runs, never waits on LLM ----
        system0_results = self._run_tier(SYSTEM_0, context)
        results["system_0"] = system0_results

        # Check System-0 safety gate.
        self._system0_safety_clear = all(
            r.get("safe", True) for r in system0_results.values() if isinstance(r, dict)
        )

        if not self._system0_safety_clear:
            # Safety gate failed — interrupt higher tiers.
            self.interrupt()
            results["system_1"] = {"interrupted": True}
            results["system_2"] = {"interrupted": True}
            results["system_3"] = {"interrupted": True}
            return results

        # ---- System 1: fast reactive (if not in safe minimum) ----
        if self.resource_mode != ResourceMode.SAFE_MINIMUM:
            results["system_1"] = self._run_tier(SYSTEM_1, context)

        # ---- System 2: deliberative (if full mode) ----
        if self.resource_mode == ResourceMode.FULL:
            results["system_2"] = self._run_tier(SYSTEM_2, context)

        # ---- System 3: deep planning (if full mode, background) ----
        if self.resource_mode == ResourceMode.FULL:
            results["system_3"] = self._run_tier(SYSTEM_3, context)

        return results

    def _run_tier(self, tier: str, context: dict[str, Any]) -> dict[str, Any]:
        """Run all enabled tasks at the given tier."""
        tier_results: dict[str, Any] = {}
        tier_tasks = sorted(
            (t for t in self._tasks.values() if t.tier == tier and t.enabled),
            key=lambda t: -t.priority,
        )
        for task in tier_tasks:
            if task.task_id in self._interrupted_tasks:
                tier_results[task.task_id] = {"interrupted": True}
                continue
            if task.handler is not None:
                try:
                    result = task.handler(context)
                    task.last_result = result
                    task.last_run_cycle = self._cycle
                    tier_results[task.task_id] = result
                except Exception as e:
                    tier_results[task.task_id] = {"error": str(e)}
            else:
                task.last_run_cycle = self._cycle
                tier_results[task.task_id] = {"executed": True}
        return tier_results

    # ---- queries ----

    @property
    def cycle(self) -> int:
        return self._cycle

    @property
    def system0_safety_clear(self) -> bool:
        return self._system0_safety_clear

    def tasks_by_tier(self, tier: str) -> tuple[SystemTask, ...]:
        return tuple(t for t in self._tasks.values() if t.tier == tier)

    def all_tasks(self) -> tuple[SystemTask, ...]:
        return tuple(self._tasks.values())

    def snapshot(self) -> dict[str, Any]:
        return {
            "cycle": self._cycle,
            "state": self.state.value,
            "resource_mode": self.resource_mode.value,
            "system0_safety_clear": self._system0_safety_clear,
            "tasks": [t.snapshot() for t in self._tasks.values()],
            "interrupted_tasks": list(self._interrupted_tasks),
        }
