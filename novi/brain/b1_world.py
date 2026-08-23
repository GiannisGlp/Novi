from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class GroundTruthEntity:
    entity: str
    location: str | None
    state: str
    present: bool = True


@dataclass(frozen=True)
class GroundTruthEvent:
    cycle: int
    event_type: str
    entity: str
    from_location: str | None = None
    to_location: str | None = None


@dataclass(frozen=True)
class SensorObservation:
    cycle: int
    source: str
    entity: str
    location: str | None
    state: str
    confidence: float
    captured_cycle: int


@dataclass(frozen=True)
class WorldEntityState:
    entity: str
    location: str | None
    state: str
    confidence: float
    last_observed_cycle: int


@dataclass
class WorldModelState:
    entities: dict[str, WorldEntityState] = field(default_factory=dict)
    correlated_events: list[str] = field(default_factory=list)
    stale_observations: list[SensorObservation] = field(default_factory=list)


class DeterministicWorld:
    """Ground-truth world plus deterministic sensor observations."""

    def __init__(self) -> None:
        self.cycle = 0
        self.entities: dict[str, GroundTruthEntity] = {
            "alice": GroundTruthEntity("alice", "kitchen", "present"),
            "door": GroundTruthEntity("door", "hallway", "closed"),
            "object_a": GroundTruthEntity("object_a", "table", "stationary"),
        }
        self.events: list[GroundTruthEvent] = []

    def advance(self) -> tuple[GroundTruthEvent, ...]:
        self.cycle += 1
        generated: list[GroundTruthEvent] = []
        if self.cycle == 1:
            generated.append(GroundTruthEvent(1, "person_entered_room", "alice", "kitchen", "living_room"))
            self.entities["alice"] = GroundTruthEntity("alice", "living_room", "present")
        elif self.cycle == 2:
            generated.append(GroundTruthEvent(2, "door_opened", "door"))
            self.entities["door"] = GroundTruthEntity("door", "hallway", "open")
        elif self.cycle == 3:
            generated.append(GroundTruthEvent(3, "object_moved", "object_a", "table", "shelf"))
            self.entities["object_a"] = GroundTruthEntity("object_a", "shelf", "moved")
        elif self.cycle == 4:
            generated.append(GroundTruthEvent(4, "person_left_room", "alice", "living_room", "hallway"))
            self.entities["alice"] = GroundTruthEntity("alice", "hallway", "present")
        elif self.cycle == 5:
            generated.append(GroundTruthEvent(5, "door_closed", "door"))
            self.entities["door"] = GroundTruthEntity("door", "hallway", "closed")
        elif self.cycle == 6:
            generated.append(GroundTruthEvent(6, "person_entered_room", "alice", "hallway", "living_room"))
            self.entities["alice"] = GroundTruthEntity("alice", "living_room", "present")
        self.events.extend(generated)
        return tuple(generated)

    def observe(self) -> tuple[SensorObservation, ...]:
        observations: list[SensorObservation] = []
        for entity in self.entities.values():
            if not entity.present:
                continue
            confidence = 0.95 if entity.entity == "alice" else 0.99
            observations.append(SensorObservation(self.cycle, "sim.camera", entity.entity, entity.location, entity.state, confidence, self.cycle))
        if self.cycle in {1, 2}:
            observations.append(SensorObservation(self.cycle, "sim.door", "door", "hallway", self.entities["door"].state, 0.99, self.cycle))
        return tuple(observations)


class TemporalWorldModel:
    """Current-state model that rejects older observations from regressing state."""

    def __init__(self) -> None:
        self.state = WorldModelState()

    def apply(self, observation: SensorObservation) -> bool:
        current = self.state.entities.get(observation.entity)
        if current and observation.captured_cycle < current.last_observed_cycle:
            self.state.stale_observations.append(observation)
            return False
        self.state.entities[observation.entity] = WorldEntityState(
            observation.entity,
            observation.location,
            observation.state,
            observation.confidence,
            observation.captured_cycle,
        )
        return True

    def apply_many(self, observations: Iterable[SensorObservation]) -> int:
        return sum(self.apply(observation) for observation in observations)

    def current(self, entity: str) -> WorldEntityState | None:
        return self.state.entities.get(entity)

    def correlate(self, events: Iterable[GroundTruthEvent]) -> tuple[str, ...]:
        correlated: list[str] = []
        for event in events:
            key = f"{event.cycle}:{event.event_type}:{event.entity}"
            if key not in self.state.correlated_events:
                self.state.correlated_events.append(key)
                correlated.append(key)
        return tuple(correlated)


@dataclass(frozen=True)
class B1WorldScenarioResult:
    final_world: dict[str, WorldEntityState]
    correlated_events: tuple[str, ...]
    stale_count: int
    observation_count: int


def run_world_scenario(cycles: int = 6) -> B1WorldScenarioResult:
    if cycles <= 0:
        raise ValueError("cycles must be > 0")
    world = DeterministicWorld()
    model = TemporalWorldModel()
    observation_count = 0
    for _ in range(cycles):
        events = world.advance()
        model.correlate(events)
        observations = world.observe()
        observation_count += len(observations)
        model.apply_many(observations)
    model.apply(SensorObservation(cycles + 1, "sim.replay", "alice", "kitchen", "present", 0.5, 1))
    return B1WorldScenarioResult(dict(model.state.entities), tuple(model.state.correlated_events), len(model.state.stale_observations), observation_count)
