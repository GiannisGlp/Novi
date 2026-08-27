"""Foundational cognition data model + deterministic fast-path (Stage B1).

This module is **not** the canonical cognition. It provides:

- the foundational **data types** the richer cognition builds on — ``Situation``,
  ``ReasoningResult``, ``CognitiveState``, ``EvidenceRef``; and
- ``DeterministicCognition``, the deterministic **fast-path** salience classifier
  (and its ``SPEECH_ENTITY`` constant).

The canonical, deliberative cognition is ``MacCognition`` in ``cognition2.py``,
which subclasses ``DeterministicCognition`` and adds knowledge/goal/memory-grounded
reasoning. The deterministic classifier here is the fast path, not the authority;
new cognition work targets ``cognition2.py`` / ``cognition_typed.py``, not this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .b1_world import SensorObservation, WorldEntityState, WorldModelState


@dataclass(frozen=True)
class EvidenceRef:
    source: str
    entity: str
    captured_cycle: int
    confidence: float


@dataclass(frozen=True)
class Situation:
    cycle: int
    entities: tuple[WorldEntityState, ...]
    salient_entities: tuple[str, ...]
    recent_events: tuple[str, ...]
    uncertainty: tuple[str, ...]
    evidence: tuple[EvidenceRef, ...]
    # Cognition 2.0: richer context used to ground understanding.
    relations: tuple[dict[str, Any], ...] = ()          # knowledge-graph triples relevant to salient entities
    goal: dict[str, Any] | None = None                  # active goal context (kind/target/distance/progress)
    recalled: tuple[dict[str, Any], ...] = ()           # memories retrieved before reasoning


@dataclass(frozen=True)
class ReasoningResult:
    conclusion: str
    confidence: float
    basis: tuple[str, ...]
    provenance: tuple[EvidenceRef, ...]
    # Cognition 2.0: multiple candidate explanations + temporal/causal inferences.
    hypotheses: tuple[dict[str, Any], ...] = ()
    inferences: tuple[str, ...] = ()


@dataclass(frozen=True)
class CognitiveState:
    situation: Situation
    reasoning: ReasoningResult


class DeterministicCognition:
    """Initial bounded cognition implementation behind the Cognition domain boundary."""

    SPEECH_ENTITY = "speech"

    def build_situation(self, state: WorldModelState, observations: Iterable[SensorObservation], *, cycle: int) -> Situation:
        observations = tuple(observations)
        evidence = tuple(EvidenceRef(item.source, item.entity, item.captured_cycle, item.confidence) for item in observations)
        entities = tuple(sorted(state.entities.values(), key=lambda item: item.entity))
        salient = {entity.entity for entity in entities if entity.entity == "alice" or entity.state in {"open", "moved"}}
        # Speech is a transient event carried by the observation list, not a
        # persistent world entity, so it is surfaced through the current cycle only.
        if any(obs.entity == self.SPEECH_ENTITY for obs in observations):
            salient.add(self.SPEECH_ENTITY)
        salient_tuple = tuple(sorted(salient))
        uncertainty = tuple(sorted(f"low_confidence:{entity.entity}" for entity in entities if entity.confidence < 0.7))
        return Situation(cycle, entities, salient_tuple, tuple(state.correlated_events[-3:]), uncertainty, evidence)

    def reason(self, situation: Situation) -> ReasoningResult:
        if self.SPEECH_ENTITY in situation.salient_entities:
            conclusion = "human_speech_observed"
            confidence = 0.8
            basis = ("a person spoke to Novi",)
        elif "alice" in situation.salient_entities:
            conclusion = "person_alice_is_relevant_to_current_situation"
            confidence = 0.95
            basis = ("alice is present in current world state",)
        elif situation.salient_entities:
            conclusion = "environmental_change_is_relevant"
            confidence = 0.8
            basis = ("salient environmental state detected",)
        else:
            conclusion = "no_high_salience_change_detected"
            confidence = 0.7
            basis = ("no salient entity or state change detected",)
        if situation.uncertainty:
            confidence = min(confidence, 0.6)
            basis = basis + ("uncertainty is present",)
        return ReasoningResult(conclusion, confidence, basis, situation.evidence)

    def cycle(self, state: WorldModelState, observations: Iterable[SensorObservation], *, cycle: int) -> CognitiveState:
        situation = self.build_situation(state, observations, cycle=cycle)
        return CognitiveState(situation=situation, reasoning=self.reason(situation))
