from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from time import monotonic, time
from typing import Any, Callable
from uuid import uuid4


class Lifecycle(str, Enum):
    BOOTING = "BOOTING"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    RECOVERING = "RECOVERING"
    SAFE_STOP = "SAFE_STOP"
    SHUTTING_DOWN = "SHUTTING_DOWN"
    FAILED = "FAILED"


class RuntimeErrorBase(Exception):
    """Base error for Brain runtime failures."""


class InvalidLifecycleTransition(RuntimeErrorBase):
    pass


class SafetyViolation(RuntimeErrorBase):
    pass


class SchedulerError(RuntimeErrorBase):
    pass


class ActionRejected(RuntimeErrorBase):
    pass


@dataclass(frozen=True)
class RuntimeEvent:
    event_type: str
    payload: dict[str, Any]
    correlation_id: str = field(default_factory=lambda: str(uuid4()))
    causation_id: str | None = None
    sequence: int = 0
    wall_time: float = field(default_factory=time)
    monotonic_time: float = field(default_factory=monotonic)


@dataclass(frozen=True)
class Health:
    status: str = "UNKNOWN"
    detail: str = ""


@dataclass(frozen=True)
class Observation:
    source: str
    value: dict[str, Any]
    quality: float = 1.0
    sequence: int = 0


@dataclass(frozen=True)
class ActionProposal:
    action: str
    parameters: dict[str, Any]
    reason: str
    correlation_id: str


@dataclass(frozen=True)
class SafetyDecision:
    authorized: bool
    reason: str
    correlation_id: str


@dataclass(frozen=True)
class ActionOutcome:
    action: str
    success: bool
    detail: str
    correlation_id: str


@dataclass(frozen=True)
class ScheduledTask:
    name: str
    task: Callable[[], None]
    priority: int = 0


class EventBus:
    def __init__(self) -> None:
        self._events: list[RuntimeEvent] = []
        self._sequence = 0

    def publish(self, event_type: str, payload: dict[str, Any], *, correlation_id: str | None = None, causation_id: str | None = None) -> RuntimeEvent:
        self._sequence += 1
        event = RuntimeEvent(event_type, payload, correlation_id=correlation_id or str(uuid4()), causation_id=causation_id, sequence=self._sequence)
        self._events.append(event)
        return event

    @property
    def events(self) -> tuple[RuntimeEvent, ...]:
        return tuple(self._events)


class DeterministicScheduler:
    """Synchronous, deterministic Stage-0 scheduler with explicit priorities."""

    def __init__(self, events: EventBus | None = None) -> None:
        self._tasks: dict[str, ScheduledTask] = {}
        self._events = events
        self._run_count = 0

    def register(self, name: str, task: Callable[[], None], *, priority: int = 0) -> None:
        if not name:
            raise ValueError("scheduler task name must not be empty")
        if name in self._tasks:
            raise SchedulerError(f"scheduler task already registered: {name}")
        self._tasks[name] = ScheduledTask(name, task, priority)
        if self._events:
            self._events.publish("scheduler.task.registered", {"name": name, "priority": priority})

    def unregister(self, name: str) -> None:
        if name not in self._tasks:
            raise SchedulerError(f"scheduler task not registered: {name}")
        del self._tasks[name]
        if self._events:
            self._events.publish("scheduler.task.unregistered", {"name": name})

    def run_once(self) -> tuple[str, ...]:
        self._run_count += 1
        executed: list[str] = []
        ordered = sorted(self._tasks.values(), key=lambda item: (-item.priority, item.name))
        for item in ordered:
            try:
                item.task()
            except Exception as exc:
                if self._events:
                    self._events.publish("scheduler.task.failed", {"name": item.name, "error_type": type(exc).__name__, "detail": str(exc)})
                raise SchedulerError(f"scheduler task failed: {item.name}") from exc
            executed.append(item.name)
        if self._events:
            self._events.publish("scheduler.cycle.completed", {"run_count": self._run_count, "tasks": executed})
        return tuple(executed)

    @property
    def run_count(self) -> int:
        return self._run_count

    @property
    def task_names(self) -> tuple[str, ...]:
        return tuple(sorted(self._tasks))


class MockSafetyGateway:
    """Stage-0 safety boundary: deny-by-default for invalid or protected actions."""

    _allowed_actions = {"inspect"}
    _blocked_actions = {"unsafe_motor_override", "disable_safety", "emergency_stop_bypass"}

    def validate_proposal(self, proposal: ActionProposal) -> None:
        if not proposal.action:
            raise ActionRejected("action name is required")
        if not proposal.correlation_id:
            raise ActionRejected("correlation_id is required")
        if proposal.action in self._blocked_actions:
            raise ActionRejected("action is protected and cannot be bypassed")
        if proposal.action not in self._allowed_actions:
            raise ActionRejected(f"action is not authorized for Stage-0 body execution: {proposal.action}")

    def authorize(self, proposal: ActionProposal) -> SafetyDecision:
        try:
            self.validate_proposal(proposal)
        except ActionRejected as exc:
            return SafetyDecision(False, str(exc), proposal.correlation_id)
        return SafetyDecision(True, "authorized", proposal.correlation_id)


class MockBody:
    """Embodiment boundary that cannot execute without an explicit allow decision."""

    def __init__(self) -> None:
        self.executed: list[ActionOutcome] = []
        self.rejected: list[ActionOutcome] = []

    def execute(self, proposal: ActionProposal, decision: SafetyDecision) -> ActionOutcome:
        if not decision.authorized:
            outcome = ActionOutcome(proposal.action, False, decision.reason, proposal.correlation_id)
            self.rejected.append(outcome)
            raise SafetyViolation(decision.reason)
        outcome = ActionOutcome(proposal.action, True, "mock execution completed", proposal.correlation_id)
        self.executed.append(outcome)
        return outcome


class SyntheticSensor:
    def __init__(self) -> None:
        self._sequence = 0

    def read(self) -> Observation:
        self._sequence += 1
        return Observation(source="synthetic.environment", value={"entity": "test_object", "distance_m": 1.0, "state": "present"}, quality=1.0, sequence=self._sequence)


class BrainSupervisor:
    """Explicit lifecycle supervisor for the Stage-0 Brain runtime."""

    _allowed = {
        Lifecycle.BOOTING: {Lifecycle.INITIALIZING, Lifecycle.FAILED},
        Lifecycle.INITIALIZING: {Lifecycle.READY, Lifecycle.FAILED},
        Lifecycle.READY: {Lifecycle.ACTIVE, Lifecycle.SHUTTING_DOWN},
        Lifecycle.ACTIVE: {Lifecycle.DEGRADED, Lifecycle.SAFE_STOP, Lifecycle.SHUTTING_DOWN},
        Lifecycle.DEGRADED: {Lifecycle.RECOVERING, Lifecycle.SAFE_STOP, Lifecycle.SHUTTING_DOWN},
        Lifecycle.RECOVERING: {Lifecycle.ACTIVE, Lifecycle.FAILED},
        Lifecycle.SAFE_STOP: {Lifecycle.SHUTTING_DOWN},
        Lifecycle.SHUTTING_DOWN: set(),
        Lifecycle.FAILED: {Lifecycle.SHUTTING_DOWN},
    }

    _healthy_states = {Lifecycle.READY, Lifecycle.ACTIVE}

    def __init__(self) -> None:
        self.lifecycle = Lifecycle.BOOTING
        self.health = Health("STARTING", "booting")
        self.events = EventBus()
        self.scheduler = DeterministicScheduler(self.events)
        self.sensor = SyntheticSensor()
        self.safety = MockSafetyGateway()
        self.body = MockBody()
        self.last_observation: Observation | None = None
        self.last_outcome: ActionOutcome | None = None

    def transition(self, target: Lifecycle, detail: str = "") -> RuntimeEvent:
        if target not in self._allowed[self.lifecycle]:
            raise InvalidLifecycleTransition(f"{self.lifecycle.value} -> {target.value}")
        previous = self.lifecycle
        self.lifecycle = target
        status = "HEALTHY" if target in self._healthy_states else target.value
        self.health = Health(status, detail or target.value.lower())
        return self.events.publish("lifecycle.changed", {"from": previous.value, "to": target.value, "detail": detail})

    def start(self) -> None:
        if self.lifecycle is not Lifecycle.BOOTING:
            raise InvalidLifecycleTransition(f"cannot start from {self.lifecycle.value}")
        self.transition(Lifecycle.INITIALIZING)
        self.events.publish("runtime.readying", {})
        self.transition(Lifecycle.READY)
        self.transition(Lifecycle.ACTIVE)

    def degrade(self, detail: str) -> None:
        self.transition(Lifecycle.DEGRADED, detail)

    def recover(self, detail: str = "recovery complete") -> None:
        self.transition(Lifecycle.RECOVERING, "recovery started")
        self.transition(Lifecycle.ACTIVE, detail)

    def fail(self, detail: str) -> None:
        if self.lifecycle not in {Lifecycle.BOOTING, Lifecycle.INITIALIZING, Lifecycle.RECOVERING}:
            raise InvalidLifecycleTransition(f"cannot fail from {self.lifecycle.value}")
        self.transition(Lifecycle.FAILED, detail)

    def safe_stop(self, detail: str = "safety stop requested") -> None:
        if self.lifecycle not in {Lifecycle.ACTIVE, Lifecycle.DEGRADED}:
            raise InvalidLifecycleTransition(f"cannot safe-stop from {self.lifecycle.value}")
        self.transition(Lifecycle.SAFE_STOP, detail)

    def propose(self, proposal: ActionProposal) -> SafetyDecision:
        decision = self.safety.authorize(proposal)
        self.events.publish("safety.decided", {"authorized": decision.authorized, "reason": decision.reason}, correlation_id=decision.correlation_id)
        return decision

    def execute(self, proposal: ActionProposal, decision: SafetyDecision) -> ActionOutcome:
        outcome = self.body.execute(proposal, decision)
        self.last_outcome = outcome
        self.events.publish("action.completed", {"action": outcome.action, "success": outcome.success, "detail": outcome.detail}, correlation_id=outcome.correlation_id, causation_id=proposal.correlation_id)
        return outcome

    def cycle(self) -> ActionOutcome:
        if self.lifecycle is not Lifecycle.ACTIVE:
            raise RuntimeErrorBase(f"cannot cycle while {self.lifecycle.value}")
        observation = self.sensor.read()
        self.last_observation = observation
        observed = self.events.publish("observation.received", {"source": observation.source, "value": observation.value, "quality": observation.quality, "sequence": observation.sequence})
        proposal = ActionProposal(action="inspect", parameters={"entity": observation.value["entity"]}, reason="synthetic observation requires inspection", correlation_id=observed.correlation_id)
        self.events.publish("action.proposed", {"action": proposal.action, "parameters": proposal.parameters}, correlation_id=proposal.correlation_id, causation_id=observed.correlation_id)
        decision = self.propose(proposal)
        return self.execute(proposal, decision)

    def shutdown(self) -> None:
        if self.lifecycle is Lifecycle.SHUTTING_DOWN:
            return
        if self.lifecycle in {Lifecycle.READY, Lifecycle.ACTIVE, Lifecycle.DEGRADED, Lifecycle.SAFE_STOP, Lifecycle.FAILED}:
            self.transition(Lifecycle.SHUTTING_DOWN)
            return
        raise InvalidLifecycleTransition(f"cannot shutdown from {self.lifecycle.value}")

    def run(self, cycles: int = 1) -> tuple[ActionOutcome, ...]:
        if cycles < 0:
            raise ValueError("cycles must be >= 0")
        self.start()
        outcomes = tuple(self.cycle() for _ in range(cycles))
        self.shutdown()
        return outcomes
