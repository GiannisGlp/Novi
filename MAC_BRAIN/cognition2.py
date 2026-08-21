"""Cognition 2.0: richer situation understanding + memory-grounded reasoning.

Extends the base ``DeterministicCognition`` (a salience classifier) into a
situation-understanding engine that grounds its reasoning in:

  - **knowledge-graph relations** relevant to the salient entities,
  - **active-goal context** (kind / target / distance / progress),
  - **recalled memories** retrieved before reasoning.

It produces a richer ``ReasoningResult`` carrying multiple candidate
**hypotheses** with confidence and **temporal/causal inferences**, and refines
the headline conclusion/confidence accordingly.

Boundaries (unchanged from docs/03-cognition):
  - Predictions are always marked as predicted and never overwrite observed state.
  - Inferences are hypotheses, not asserted facts; they never bypass Policy/Safety.
"""

from __future__ import annotations

from typing import Any, Iterable

from brain.b1_cognition import CognitiveState, DeterministicCognition, ReasoningResult, Situation
from brain.b1_world import SensorObservation, WorldModelState

# Predicates that carry a causal/temporal reading (subject likely <pred> object).
_CAUSAL_PREDICATES = {"moved", "opened", "closed", "entered", "left", "placed", "turned_on", "turned_off"}


class MacCognition(DeterministicCognition):
    """Situation-understanding cognition grounded in knowledge, goals, and memory."""

    def build_situation(
        self,
        state: WorldModelState,
        observations: Iterable[SensorObservation],
        *,
        cycle: int,
        knowledge: Any = (),
        goal: dict[str, Any] | None = None,
        recalled: Any = (),
    ) -> Situation:
        base = super().build_situation(state, observations, cycle=cycle)
        return Situation(
            cycle=base.cycle,
            entities=base.entities,
            salient_entities=base.salient_entities,
            recent_events=base.recent_events,
            uncertainty=base.uncertainty,
            evidence=base.evidence,
            relations=self._relevant_relations(base.salient_entities, knowledge),
            goal=goal,
            recalled=tuple(recalled),
        )

    @staticmethod
    def _relevant_relations(salient: tuple[str, ...], knowledge: Any) -> tuple[dict[str, Any], ...]:
        """Knowledge-graph triples whose subject or object is a salient entity."""
        if not knowledge:
            return ()
        salient_set = set(salient)
        out: list[dict[str, Any]] = []
        for triple in knowledge:
            subject = triple.get("subject")
            obj = triple.get("object")
            if subject in salient_set or obj in salient_set:
                out.append(
                    {
                        "subject": subject,
                        "predicate": triple.get("predicate"),
                        "object": obj,
                        "confidence": triple.get("confidence", 0.5),
                        "status": triple.get("status", "active"),
                    }
                )
        return tuple(out)

    def reason(self, situation: Situation) -> ReasoningResult:
        base = super().reason(situation)
        hypotheses = self._hypotheses(situation)
        inferences = self._inferences(situation)
        conclusion, confidence, basis = self._refine(base, situation, inferences)
        return ReasoningResult(
            conclusion=conclusion,
            confidence=confidence,
            basis=basis,
            provenance=situation.evidence,
            hypotheses=hypotheses,
            inferences=inferences,
        )

    def _hypotheses(self, situation: Situation) -> tuple[dict[str, Any], ...]:
        """Candidate explanations for the current situation, with confidence."""
        hyps: list[dict[str, Any]] = []
        for rel in situation.relations:
            hyps.append(
                {
                    "hypothesis": f"{rel['subject']} {rel['predicate']} {rel['object']}",
                    "confidence": round(rel.get("confidence", 0.5), 3),
                    "source": "knowledge",
                }
            )
        if situation.goal:
            hyps.append(
                {
                    "hypothesis": f"goal {situation.goal.get('kind')} toward {situation.goal.get('target')} is active",
                    "confidence": 0.9,
                    "source": "goal",
                }
            )
        if situation.recalled:
            hyps.append(
                {
                    "hypothesis": f"{len(situation.recalled)} relevant memories recalled",
                    "confidence": 0.6,
                    "source": "memory",
                }
            )
        return tuple(hyps)

    def _inferences(self, situation: Situation) -> tuple[str, ...]:
        """Temporal/causal inferences drawn from knowledge + goal context."""
        infs: list[str] = []
        for rel in situation.relations:
            predicate = rel.get("predicate")
            if predicate in _CAUSAL_PREDICATES:
                infs.append(f"{rel['subject']} likely {predicate} {rel['object']}")
        goal = situation.goal
        if goal and goal.get("distance_to_goal") is not None:
            distance = float(goal["distance_to_goal"])
            if distance < 0.5:
                infs.append("goal target reached")
            elif distance < 2.0:
                infs.append("approaching goal target")
        return tuple(infs)

    def _refine(self, base: ReasoningResult, situation: Situation, inferences: tuple[str, ...]) -> tuple[str, float, tuple[str, ...]]:
        """Refine the headline conclusion/confidence from the base result."""
        conclusion = base.conclusion
        confidence = base.confidence
        basis = list(base.basis)
        if inferences:
            conclusion = "causal_change_inferred"
            confidence = min(0.9, base.confidence + 0.1)
            basis = basis + list(inferences)
        goal = situation.goal
        if goal and goal.get("distance_to_goal") is not None and float(goal["distance_to_goal"]) < 2.0:
            conclusion = "goal_relevant_change"
            confidence = max(confidence, 0.85)
            basis = basis + ["active goal is near"]
        return conclusion, confidence, tuple(basis)

    def cycle(
        self,
        state: WorldModelState,
        observations: Iterable[SensorObservation],
        *,
        cycle: int,
        knowledge: Any = (),
        goal: dict[str, Any] | None = None,
        recalled: Any = (),
    ) -> CognitiveState:
        situation = self.build_situation(state, observations, cycle=cycle, knowledge=knowledge, goal=goal, recalled=recalled)
        return CognitiveState(situation=situation, reasoning=self.reason(situation))
