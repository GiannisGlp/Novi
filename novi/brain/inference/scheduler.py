"""Inference scheduler (plan 12, §20 Phase 15).

The scheduler sits between the router and the backend and prevents competing
large-model requests from exhausting resources. Inputs considered: priority,
deadline, estimated memory, estimated duration, model residency, current load.

Queue classes: CRITICAL, HIGH, NORMAL, LOW, BACKGROUND (per-priority FIFO,
deadline-ordered within a class).

Cancellation is cooperative at request boundaries — preemption is NOT
implemented (plan 12, §20). When a high-priority request arrives while a
BACKGROUND request is running, the configured arrival policy applies:

    wait | queue | cancel_background | switch_model | smaller_fallback

``cancel_background`` marks running BACKGROUND requests cancelled at their next
cooperative boundary; it never interrupts mid-generation.
"""

from __future__ import annotations

import heapq
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .cancellation import CancellationToken
from .request import InferenceRequest, RequestPriority

#: Scheduler arrival policies for high-priority requests during background work.
ARRIVAL_POLICIES = ("wait", "queue", "cancel_background", "switch_model", "smaller_fallback")

#: Map priority -> scheduler queue class (same set, ordered).
_QUEUE_ORDER: tuple[RequestPriority, ...] = (
    RequestPriority.CRITICAL,
    RequestPriority.HIGH,
    RequestPriority.NORMAL,
    RequestPriority.LOW,
    RequestPriority.BACKGROUND,
)


@dataclass
class ScheduledRequest:
    """A request accepted by the scheduler."""

    request: InferenceRequest
    enqueued_at: float = field(default_factory=time.monotonic)
    estimated_memory_bytes: int = 0
    estimated_duration_ms: float = 0.0
    token: CancellationToken = field(default_factory=CancellationToken)
    state: str = "queued"  # queued | running | done | cancelled | failed
    backend_id: str = ""
    deadline_monotonic: float = 0.0

    @property
    def request_id(self) -> str:
        return self.request.request_id

    @property
    def priority(self) -> RequestPriority:
        return self.request.priority

    def cancel(self, reason: str = "scheduler_cancel") -> None:
        if self.state == "queued":
            self.state = "cancelled"
        elif self.state == "running":
            self.token.cancel(reason)
            self.state = "cancelling"
        self.token.cancel(reason)

    def as_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "priority": self.priority.value,
            "state": self.state,
            "model_hint": self.request.model_hint,
            "enqueued_at": self.enqueued_at,
            "estimated_memory_bytes": self.estimated_memory_bytes,
            "estimated_duration_ms": self.estimated_duration_ms,
            "deadline_monotonic": self.deadline_monotonic,
        }


class InferenceScheduler:
    """Priority-class, deadline-aware scheduler with cooperative cancellation."""

    def __init__(
        self,
        *,
        max_concurrent: int = 1,
        arrival_policy: str = "queue",
        deadline_ms: float = 30_000.0,
        cancel_running: Callable[[str], None] | None = None,
    ) -> None:
        if arrival_policy not in ARRIVAL_POLICIES:
            raise ValueError(f"invalid arrival_policy {arrival_policy!r}; choose from {ARRIVAL_POLICIES}")
        self.max_concurrent = max(1, int(max_concurrent))
        self.arrival_policy = arrival_policy
        self.deadline_ms = float(deadline_ms)
        #: invoked when a running request should be cooperatively cancelled
        self.cancel_running = cancel_running or (lambda request_id: None)
        self._queues: dict[RequestPriority, list[tuple[float, int, ScheduledRequest]]] = {p: [] for p in _QUEUE_ORDER}
        self._seq = 0
        self._running: dict[str, ScheduledRequest] = {}
        self._completed: dict[str, ScheduledRequest] = {}
        self._lock = threading.RLock()  # reentrant: wait_for_slot -> acquire
        self._cv = threading.Condition(self._lock)
        self._recent_cancellations: list[str] = []

    # ------------------------------------------------------------- submission
    def submit(
        self,
        request: InferenceRequest,
        *,
        estimated_memory_bytes: int = 0,
        estimated_duration_ms: float = 0.0,
    ) -> ScheduledRequest:
        """Submit a request. Returns the scheduled wrapper (never blocks)."""
        now = time.monotonic()
        deadline = request.deadline
        deadline_monotonic = 0.0
        if deadline is not None:
            # datetime -> monotonic approx via wall-clock delta
            import datetime as _dt

            now_utc = _dt.datetime.now(_dt.timezone.utc)
            delta = (deadline - now_utc).total_seconds()
            deadline_monotonic = now + max(0.0, delta)
        elif request.latency_budget_ms:
            deadline_monotonic = now + request.latency_budget_ms / 1000.0
        else:
            deadline_monotonic = now + self.deadline_ms / 1000.0
        sched = ScheduledRequest(
            request=request,
            estimated_memory_bytes=int(estimated_memory_bytes),
            estimated_duration_ms=float(estimated_duration_ms),
            deadline_monotonic=deadline_monotonic,
        )
        with self._lock:
            if self.arrival_policy == "cancel_background" and request.priority.rank > RequestPriority.NORMAL.rank:
                self._cancel_running_background(request)
            heapq.heappush(self._queues[request.priority], (sched.deadline_monotonic, self._seq, sched))
            self._seq += 1
            self._cv.notify_all()
        return sched

    def _cancel_running_background(self, incoming: InferenceRequest) -> None:
        """Policy: cancel running BACKGROUND work at its next boundary."""
        victims = [s for s in self._running.values() if s.priority is RequestPriority.BACKGROUND]
        for victim in victims:
            victim.cancel(f"high_priority_arrival:{incoming.request_id}")
            self._recent_cancellations.append(victim.request_id)
            self.cancel_running(victim.request_id)

    # ---------------------------------------------------------------- running
    def acquire(self) -> ScheduledRequest | None:
        """Pop the highest-priority eligible request, or None when empty."""
        with self._lock:
            if len(self._running) >= self.max_concurrent:
                return None
            for priority in _QUEUE_ORDER:
                queue = self._queues[priority]
                while queue:
                    _, _, sched = heapq.heappop(queue)
                    if sched.state == "cancelled":
                        continue
                    if self._past_deadline(sched):
                        sched.state = "failed"
                        self._completed[sched.request_id] = sched
                        continue
                    sched.state = "running"
                    self._running[sched.request_id] = sched
                    return sched
            return None

    def _past_deadline(self, sched: ScheduledRequest) -> bool:
        now = time.monotonic()
        return sched.deadline_monotonic > 0.0 and now > sched.deadline_monotonic

    def release(self, request_id: str, *, success: bool = True) -> None:
        """Mark a running request finished and free its slot."""
        with self._lock:
            sched = self._running.pop(request_id, None)
            if sched is not None:
                sched.state = "done" if success else "failed"
                self._completed[request_id] = sched
            self._cv.notify_all()

    def cancel(self, request_id: str, reason: str = "scheduler_cancel") -> bool:
        """Cancel a queued or running request; returns False if unknown."""
        with self._lock:
            sched = self._running.get(request_id)
            if sched is not None:
                sched.cancel(reason)
                self.cancel_running(request_id)
                self._recent_cancellations.append(request_id)
                return True
            for queue in self._queues.values():
                for _, _, candidate in queue:
                    if candidate.request_id == request_id and candidate.state == "queued":
                        candidate.state = "cancelled"
                        return True
        return False

    # ------------------------------------------------------------ observability
    @property
    def running_count(self) -> int:
        with self._lock:
            return len(self._running)

    def queue_depth(self) -> dict[str, int]:
        with self._lock:
            return {p.value: sum(1 for _, _, s in q if s.state == "queued") for p, q in self._queues.items()}

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "max_concurrent": self.max_concurrent,
                "arrival_policy": self.arrival_policy,
                "queue_depth": {
                    p.value: sum(1 for _, _, s in q if s.state == "queued") for p, q in self._queues.items()
                },
                "running": [s.as_dict() for s in self._running.values()],
                "recent_cancellations": self._recent_cancellations[-20:],
            }

    def wait_for_slot(self, timeout: float = 30.0) -> ScheduledRequest | None:
        """Block until a slot is free, then acquire. Returns None on timeout."""
        with self._lock:
            deadline = time.monotonic() + timeout
            while True:
                sched = self.acquire()
                if sched is not None:
                    return sched
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return None
                self._cv.wait(timeout=remaining)
