"""Deterministic prediction engine for the Mac Brain (gap-audit plan Phase D4).

Predicts which entities will persist into the next cycle from observation
streaks, then scores those predictions against the next cycle's observations.
Prediction error drives expectation handling and is measurable: the engine
logs a rolling ``prediction_accuracy`` to its MetricRegistry (audit lever 4).

Boundaries honored (docs/03-cognition 10):
  - Predictions are always marked as predicted and never overwrite observed
    state — this module does not write to the unified world model at all.
  - Prediction errors are learning signals, not overconfident facts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

PENDING = "pending"
CONFIRMED = "confirmed"
VIOLATED = "violated"


@dataclass
class Prediction:
    entity: str
    kind: str  # "persist": expected present next cycle
    confidence: float
    made_at_cycle: int
    status: str = PENDING

    def snapshot(self) -> dict[str, Any]:
        return {
            "entity": self.entity,
            "kind": self.kind,
            "confidence": round(self.confidence, 3),
            "made_at_cycle": self.made_at_cycle,
            "status": self.status,
        }


@dataclass
class AccuracyTracker:
    """Rolling prediction accuracy over a bounded window, with outcomes."""

    window: int = 50
    _results: list[tuple[float, bool]] = field(default_factory=list)

    def record(self, confidence: float, hit: bool) -> None:
        self._results.append((max(0.0, min(1.0, float(confidence))), bool(hit)))
        if len(self._results) > self.window:
            self._results.pop(0)

    def accuracy(self) -> float | None:
        if not self._results:
            return None
        return sum(1.0 for _, hit in self._results if hit) / len(self._results)

    def pairs(self) -> list[tuple[float, bool]]:
        """(confidence, came_true) pairs for the calibration harness."""
        return list(self._results)


class PredictionEngine:
    """Streak-based persistence predictor (deterministic, model-free)."""

    def __init__(self, *, min_observations: int = 2, confidence_cap: float = 0.95) -> None:
        self.min_observations = max(1, int(min_observations))
        self.confidence_cap = max(0.0, min(1.0, confidence_cap))
        self._streaks: dict[str, int] = {}
        self._pending: list[Prediction] = []
        self.accuracy = AccuracyTracker()

    def observe(self, present: set[str], cycle: int) -> tuple[list[Prediction], list[Prediction], list[Prediction]]:
        """Ingest one cycle's observed entities.

        Returns ``(new_predictions, confirmed, violated)``:
          - new: persist-predictions for the next cycle;
          - confirmed/violated: outcomes of last cycle's predictions, scored
            against this cycle's observations and fed into the accuracy tracker.
        """
        confirmed: list[Prediction] = []
        violated: list[Prediction] = []
        for pred in self._pending:
            if pred.entity in present:
                pred.status = CONFIRMED
                confirmed.append(pred)
            else:
                pred.status = VIOLATED
                violated.append(pred)
            self.accuracy.record(pred.confidence, pred.status == CONFIRMED)
        self._pending = []

        for entity in sorted(present):
            self._streaks[entity] = self._streaks.get(entity, 0) + 1
        for entity in list(self._streaks):
            if entity not in present:
                self._streaks.pop(entity)
        new_predictions: list[Prediction] = []
        for entity in sorted(present):
            streak = self._streaks.get(entity, 0)
            if streak >= self.min_observations:
                conf = min(self.confidence_cap, 1.0 - 1.0 / (streak + 1))
                p = Prediction(entity=entity, kind="persist", confidence=conf, made_at_cycle=cycle)
                self._pending.append(p)
                new_predictions.append(p)
        return new_predictions, confirmed, violated

    def pending_count(self) -> int:
        return len(self._pending)

    def snapshot(self) -> dict[str, Any]:
        acc = self.accuracy.accuracy()
        return {
            "streaks": dict(sorted(self._streaks.items())),
            "pending": [p.snapshot() for p in self._pending],
            "accuracy": None if acc is None else round(acc, 4),
        }


@dataclass
class SequencePrediction:
    """A temporal-sequence prediction: after ``source`` appears, ``target``
    tends to appear within ``window`` cycles (causal/sequence learning, plan P4)."""

    source: str
    target: str
    kind: str = "sequence"
    confidence: float = 0.5
    made_at_cycle: int = 0
    status: str = PENDING

    def snapshot(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "kind": self.kind,
            "confidence": round(self.confidence, 3),
            "made_at_cycle": self.made_at_cycle,
            "status": self.status,
        }


class SequencePredictor:
    """Learns temporal sequences: after A appears, B tends to appear within k cycles.

    Distinct from ``RoutineDetector`` (concurrent co-occurrence) and from
    ``PredictionEngine`` (persistence). This is the causal/sequence lever
    (plan P4): it learns A→B precedence from the event log, predicts B when A
    is observed, and scores the prediction against the next ``window`` cycles.
    Violations are learning signals (surprise) — never facts.
    """

    def __init__(self, *, window: int = 3, min_observations: int = 2, confidence_cap: float = 0.9) -> None:
        self.window = max(1, int(window))
        self.min_observations = max(1, int(min_observations))
        self.confidence_cap = max(0.0, min(1.0, confidence_cap))
        self._recent: list[tuple[int, set[str]]] = []  # prior cycles (cycle, entities)
        self._cooccur: dict[tuple[str, str], int] = {}  # (A, B) -> A-then-B count
        self._pending: list[SequencePrediction] = []
        self.accuracy = AccuracyTracker()

    def observe(self, present: set[str], cycle: int) -> tuple[list[SequencePrediction], list[SequencePrediction], list[SequencePrediction]]:
        """Ingest one cycle's observed entities.

        Returns ``(new_predictions, confirmed, violated)`` for sequence
        predictions, mirroring ``PredictionEngine.observe``.
        """
        # 1. Score pending sequence predictions against this cycle.
        confirmed: list[SequencePrediction] = []
        violated: list[SequencePrediction] = []
        still_pending: list[SequencePrediction] = []
        for pred in self._pending:
            if pred.target in present:
                pred.status = CONFIRMED
                confirmed.append(pred)
                self.accuracy.record(pred.confidence, True)
            elif cycle - pred.made_at_cycle > self.window:
                pred.status = VIOLATED
                violated.append(pred)
                self.accuracy.record(pred.confidence, False)
            else:
                still_pending.append(pred)
        self._pending = still_pending

        # 2. Learn A→B precedence: for each B present now, count each A that
        #    appeared in a strictly-prior cycle within the window.
        for b in present:
            for c, ents in self._recent:
                if cycle - c > self.window:
                    continue
                for a in ents:
                    if a != b:
                        key = (a, b)
                        self._cooccur[key] = self._cooccur.get(key, 0) + 1

        # 3. Predict: for each A present now, predict each B whose A→B count
        #    meets the threshold (dedup by target already pending).
        pending_targets = {p.target for p in self._pending}
        new_predictions: list[SequencePrediction] = []
        for a in present:
            for (src, tgt), count in self._cooccur.items():
                if src != a or count < self.min_observations:
                    continue
                if tgt in pending_targets:
                    continue
                conf = min(self.confidence_cap, 1.0 - 1.0 / (count + 1))
                p = SequencePrediction(source=a, target=tgt, confidence=conf, made_at_cycle=cycle)
                self._pending.append(p)
                pending_targets.add(tgt)
                new_predictions.append(p)

        # 4. Maintain the prior-cycle history.
        self._recent.append((cycle, set(present)))
        if len(self._recent) > self.window + 1:
            self._recent.pop(0)

        return new_predictions, confirmed, violated

    def pending_count(self) -> int:
        return len(self._pending)

    def snapshot(self) -> dict[str, Any]:
        acc = self.accuracy.accuracy()
        return {
            "cooccurrences": {f"{a}->{b}": n for (a, b), n in sorted(self._cooccur.items())},
            "pending": [p.snapshot() for p in self._pending],
            "accuracy": None if acc is None else round(acc, 4),
        }
