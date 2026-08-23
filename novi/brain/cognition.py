"""Deepened cognition for the Mac Brain: beliefs/knowledge + prediction/expectation.

Implements docs/03-cognition 04/10 (reasoning engine + prediction & expectation)
as deterministic, model-independent capabilities:

  - `BeliefSystem` maintains per-entity/state beliefs with confidence that
    accumulate with evidence, detect contradictions, and refuse to silently flip
    an established belief on weak single evidence (repeated contradiction flips).
  - `ExpectationLearner` learns persistence expectations (what is typically
    present/stable) from experience and flags expectation violations when a
    steady pattern is contradicted.

Boundaries honored (docs/03-cognition):
  - Predictions are always marked as predicted and never overwrite observed state.
  - Predictions do not assume intent or infer sensitive facts from routine
    deviations. Prediction errors are learning signals, not overconfident facts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

CONTRADICTION_FLIP_EVIDENCE = 2

# Gap-audit Phase C1: evidence is weighted by how it was obtained before it is
# combined. A camera seeing something is stronger evidence than being told.
SOURCE_WEIGHTS = {
    "direct_sensor": 0.9,
    "model_inference": 0.6,
    "user_statement": 0.5,
}
DEFAULT_SOURCE = "direct_sensor"

# Contradictions weaken confidence multiplicatively (proportional doubt), so a
# near-certain belief loses more absolute confidence than a weak one.
CONTRADICTION_DECAY = 0.7


def source_weight(source: str) -> float:
    return SOURCE_WEIGHTS.get(str(source).lower(), SOURCE_WEIGHTS[DEFAULT_SOURCE])


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


@dataclass
class Belief:
    entity: str
    value: Any
    property: str = "presence"
    confidence: float = 0.2
    evidence_count: int = 1
    contradictions: int = 0
    first_observed: str = ""
    last_observed: str = ""
    last_source: str = ""

    def snapshot(self) -> dict[str, Any]:
        return {
            "entity": self.entity,
            "value": self.value,
            "property": self.property,
            "confidence": self.confidence,
            "evidence_count": self.evidence_count,
            "contradictions": self.contradictions,
            "last_source": self.last_source,
        }


class BeliefSystem:
    """Evidence-backed beliefs that resist silent, single-shot overwriting."""

    def __init__(self) -> None:
        self._beliefs: dict[tuple[str, str], Belief] = {}
        self._property_index: dict[str, dict[str, Any]] = {}

    def observe(
        self,
        entity: str,
        value: Any,
        *,
        confidence: float = 0.8,
        property: str = "presence",
        now: str = "",
        source: str = DEFAULT_SOURCE,
    ) -> Belief:
        """Fuse one observation into the belief (Bayesian noisy-OR).

        Confirming evidence combines as ``1 - (1-prior)*(1-evidence)`` where
        ``evidence`` is the raw confidence weighted by the source class
        (direct_sensor > model_inference > user_statement). Contradictions
        decay confidence multiplicatively and never silently flip the belief;
        only repeated contradiction flips it.
        """
        evidence = _clamp01(confidence) * source_weight(source)
        key = (entity, property)
        belief = self._beliefs.get(key)
        if belief is None:
            belief = Belief(entity=entity, value=value, property=property, confidence=_clamp01(evidence), evidence_count=1, first_observed=now, last_observed=now, last_source=str(source))
            self._beliefs[key] = belief
            return belief

        if belief.value == value:
            belief.evidence_count += 1
            # Noisy-OR: diminishing returns, asymptotic to 1, never decreases.
            belief.confidence = _clamp01(1.0 - (1.0 - belief.confidence) * (1.0 - evidence))
            belief.last_observed = now
            belief.last_source = str(source)
        else:
            belief.contradictions += 1
            belief.evidence_count += 1
            belief.last_observed = now
            belief.last_source = str(source)
            if belief.contradictions >= CONTRADICTION_FLIP_EVIDENCE:
                # repeated strong evidence flips the belief
                belief.value = value
                belief.confidence = _clamp01(evidence)
                belief.contradictions = 0
            else:
                # single contradiction weakens confidence proportionally
                # without silently flipping
                belief.confidence = _clamp01(belief.confidence * CONTRADICTION_DECAY)
        return belief

    def belief_for(self, entity: str, property: str = "presence") -> Belief | None:
        return self._beliefs.get((entity, property))

    def contradicts(self) -> int:
        return sum(1 for b in self._beliefs.values() if b.contradictions > 0)

    def snapshot(self) -> list[dict[str, Any]]:
        return [b.snapshot() for b in self._beliefs.values()]

    @classmethod
    def from_snapshot(cls, rows: list[dict[str, Any]]) -> "BeliefSystem":
        sys = cls()
        for row in rows:
            b = Belief(
                entity=row["entity"],
                value=row["value"],
                property=row.get("property", "presence"),
                confidence=row["confidence"],
                evidence_count=row["evidence_count"],
                contradictions=row["contradictions"],
                last_source=row.get("last_source", ""),
            )
            sys._beliefs[(b.entity, b.property)] = b
        return sys


@dataclass
class ExpectationViolation:
    entity: str
    kind: str  # e.g. "expected_present_now_absent"
    expectation_confidence: float

    def snapshot(self) -> dict[str, Any]:
        return {"entity": self.entity, "kind": self.kind, "expectation_confidence": self.expectation_confidence}


class ExpectationSystem:
    """Learns steady-state presence expectations and flags violations."""

    def __init__(self, consistency: int = 2) -> None:
        self._consecutive: dict[str, int] = {}
        self._violations: list[ExpectationViolation] = []
        self._seen_entities: set[str] = set()
        self.consistency = consistency

    def update(self, present: set[str]) -> None:
        self._seen_entities |= present
        for entity in list(self._seen_entities):
            if entity in present:
                self._consecutive[entity] = self._consecutive.get(entity, 0) + 1
            else:
                if self._consecutive.get(entity, 0) >= self.consistency:
                    self._violations.append(
                        ExpectationViolation(entity=entity, kind="expected_present_now_absent", expectation_confidence=_clamp01(self._consecutive[entity] / self.consistency))
                    )
                self._consecutive[entity] = 0

    def expects_present(self, entity: str) -> bool:
        return self._consecutive.get(entity, 0) >= self.consistency

    def pending_violations(self) -> list[ExpectationViolation]:
        return self._violations

    def drain_violations(self) -> list[ExpectationViolation]:
        out = self._violations
        self._violations = []
        return out

    def snapshot(self) -> dict[str, Any]:
        return {"consecutive": dict(self._consecutive), "seen": sorted(self._seen_entities)}

    @classmethod
    def from_snapshot(cls, data: dict[str, Any]) -> "ExpectationSystem":
        sys = cls()
        sys._consecutive = dict(data.get("consecutive", {}))
        sys._seen_entities = set(data.get("seen", []))
        return sys
