from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from .runtime import ActionProposal, BrainSupervisor, Lifecycle, SafetyViolation


@dataclass(frozen=True)
class SimulatedObservation:
    cycle: int
    entity: str
    distance_m: float
    state: str


@dataclass(frozen=True)
class Situation:
    entity: str
    state: str
    distance_m: float
    familiar: bool


@dataclass(frozen=True)
class Goal:
    name: str
    priority: int


@dataclass(frozen=True)
class Experience:
    cycle: int
    entity: str
    action: str
    success: bool


@dataclass
class SimulationState:
    world: dict[str, Situation] = field(default_factory=dict)
    active_goals: list[Goal] = field(default_factory=list)
    experiences: list[Experience] = field(default_factory=list)
    cycle: int = 0


class PerceptionPort(Protocol):
    def interpret(self, observation: SimulatedObservation) -> Situation: ...


class CognitionPort(Protocol):
    def update(self, situation: Situation) -> None: ...
    def current(self, entity: str) -> Situation | None: ...


class MemoryPort(Protocol):
    def remember(self, experience: Experience) -> None: ...
    def recall(self, entity: str) -> tuple[Experience, ...]: ...


class AutonomyPort(Protocol):
    def choose_goal(self, situation: Situation, memory: tuple[Experience, ...]) -> Goal: ...
    def propose(self, goal: Goal, situation: Situation, correlation_id: str) -> ActionProposal: ...


class SimulatedPerception:
    def interpret(self, observation: SimulatedObservation) -> Situation:
        return Situation(
            entity=observation.entity,
            state=observation.state,
            distance_m=observation.distance_m,
            familiar=observation.entity == "test_object",
        )


class SimulatedCognition:
    def __init__(self, state: SimulationState) -> None:
        self.state = state

    def update(self, situation: Situation) -> None:
        self.state.world[situation.entity] = situation

    def current(self, entity: str) -> Situation | None:
        return self.state.world.get(entity)


class SimulatedMemory:
    def __init__(self, state: SimulationState) -> None:
        self.state = state

    def remember(self, experience: Experience) -> None:
        self.state.experiences.append(experience)

    def recall(self, entity: str) -> tuple[Experience, ...]:
        return tuple(item for item in self.state.experiences if item.entity == entity)


class SimulatedAutonomy:
    def __init__(self, state: SimulationState) -> None:
        self.state = state

    def choose_goal(self, situation: Situation, memory: tuple[Experience, ...]) -> Goal:
        name = "inspect_familiar_entity" if situation.familiar else "observe_unknown_entity"
        goal = Goal(name=name, priority=10 if situation.familiar else 5)
        self.state.active_goals = [goal]
        return goal

    def propose(self, goal: Goal, situation: Situation, correlation_id: str) -> ActionProposal:
        return ActionProposal(
            action="inspect",
            parameters={"entity": situation.entity, "goal": goal.name},
            reason="B1 simulated autonomy selected inspection",
            correlation_id=correlation_id,
        )


class ClosedSimulatedLoop:
    """First deterministic multi-cycle Brain loop built on the B0 runtime boundary."""

    def __init__(self, brain: BrainSupervisor | None = None) -> None:
        self.brain = brain or BrainSupervisor()
        self.state = SimulationState()
        self.perception = SimulatedPerception()
        self.cognition = SimulatedCognition(self.state)
        self.memory = SimulatedMemory(self.state)
        self.autonomy = SimulatedAutonomy(self.state)

    def observe(self) -> SimulatedObservation:
        self.state.cycle += 1
        return SimulatedObservation(
            cycle=self.state.cycle,
            entity="test_object",
            distance_m=max(0.5, 1.0 - (self.state.cycle - 1) * 0.1),
            state="present",
        )

    def step(self) -> Experience:
        if self.brain.lifecycle is not Lifecycle.ACTIVE:
            raise RuntimeError(f"closed loop requires ACTIVE Brain, got {self.brain.lifecycle.value}")

        observation = self.observe()
        self.brain.events.publish(
            "simulation.observation",
            {"cycle": observation.cycle, "entity": observation.entity, "distance_m": observation.distance_m, "state": observation.state},
        )

        situation = self.perception.interpret(observation)
        self.brain.events.publish(
            "perception.interpreted",
            {"entity": situation.entity, "state": situation.state, "distance_m": situation.distance_m, "familiar": situation.familiar},
        )
        self.cognition.update(situation)
        self.brain.events.publish("cognition.world.updated", {"entity": situation.entity})

        memories = self.memory.recall(situation.entity)
        goal = self.autonomy.choose_goal(situation, memories)
        self.brain.events.publish(
            "autonomy.goal.selected",
            {"goal": goal.name, "priority": goal.priority, "memory_count": len(memories)},
        )

        correlation_id = self.brain.events.publish("autonomy.action.requested", {"goal": goal.name}).correlation_id
        proposal = self.autonomy.propose(goal, situation, correlation_id)
        self.brain.events.publish(
            "action.proposed",
            {"action": proposal.action, "parameters": proposal.parameters},
            correlation_id=proposal.correlation_id,
        )

        decision = self.brain.propose(proposal)
        try:
            outcome = self.brain.execute(proposal, decision)
        except SafetyViolation:
            experience = Experience(observation.cycle, situation.entity, proposal.action, False)
            self.memory.remember(experience)
            raise

        experience = Experience(observation.cycle, situation.entity, outcome.action, outcome.success)
        self.memory.remember(experience)
        self.brain.events.publish(
            "memory.experience.stored",
            {"cycle": experience.cycle, "entity": experience.entity, "action": experience.action, "success": experience.success},
            correlation_id=experience.cycle.__str__(),
        )
        return experience

    def run(self, cycles: int = 3) -> tuple[Experience, ...]:
        if cycles <= 0:
            raise ValueError("cycles must be > 0")
        self.brain.start()
        experiences = tuple(self.step() for _ in range(cycles))
        self.brain.shutdown()
        return experiences
