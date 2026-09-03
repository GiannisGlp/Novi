"""Learning pipeline: knowledge promotion, user correction, routines (item 13).

Implements docs/06-soul/06_LEARNING_DEVELOPMENT_AND_ADAPTATION.md learning
principles (provenance, reviewable adaptation, safety boundaries) and
docs/03-cognition/02_WORLD_MODEL.md (Imagination Boundary — hypothetical states
never become factual):

  `KnowledgePromotionPipeline` — candidate triples accumulate evidence and
  confidence; they are promoted to the durable knowledge graph only past
  explicit thresholds, keeping provenance and epistemic status;
  `CorrectionRecord` — a user correction supersedes a knowledge triple with
  provenance, never silently deleting history;
  `RoutineDetector` — repeated event patterns become *candidate* routines with
  evidence counts (hypotheses, not facts);
  `CounterfactualEngine` — "what if" queries build hypothetical world slices
  flagged COUNTERFACTUAL/SIMULATED that never merge into observed state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .kgraph import EntityKnowledgeGraph as EntityGraph

OBSERVED = "OBSERVED"
INFERRED = "INFERRED"
PREDICTED = "PREDICTED"
SIMULATED = "SIMULATED"
VERIFIED = "VERIFIED"

_PROMOTABLE_EPISTEMIC = frozenset({OBSERVED, VERIFIED, INFERRED})
_NON_FACTUAL = frozenset({PREDICTED, SIMULATED})


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


# ---------------------------------------------------------------------------
# Knowledge promotion pipeline
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PromotionCandidate:
    """A proposed triple with accumulated evidence (never promoted silently)."""
    subject: str
    predicate: str
    object: str
    confidence: float
    evidence_count: int
    epistemic: str = OBSERVED
    sources: tuple[str, ...] = ()
    first_cycle: int = 0

    def snapshot(self) -> dict[str, Any]:
        return {
            "subject": self.subject, "predicate": self.predicate,
            "object": self.object, "confidence": round(self.confidence, 3),
            "evidence_count": self.evidence_count, "epistemic": self.epistemic,
            "sources": list(self.sources), "first_cycle": self.first_cycle,
        }


class KnowledgePromotionPipeline:
    """Promotes evidence-backed candidates into knowledge with thresholds.

    Candidates never become facts from a single observation; they accumulate
    evidence per (subject, predicate, object) and cross promote thresholds.
    SIMULATED/PREDICTED candidates (e.g. from simulation) cannot be promoted as
    facts — they stay hypothetical.
    """

    def __init__(
        self,
        *,
        promote_min_evidence: int = 3,
        promote_min_confidence: float = 0.7,
        record_exposure: bool = False,
        max_promotions: int = 1000,
    ) -> None:
        self.promote_min_evidence = promote_min_evidence
        self.promote_min_confidence = promote_min_confidence
        self.record_exposure = record_exposure
        self._max_promotions = max(1, int(max_promotions))
        self._candidates: dict[tuple[str, str, str], PromotionCandidate] = {}
        self._promotions: list[dict[str, Any]] = []
        self._dropped_promotions = 0
        self._promoted_keys: set[tuple[str, str, str]] = set()

    @property
    def dropped_promotions(self) -> int:
        """Promotion-ledger spills so far (bounded-memory accounting)."""
        return self._dropped_promotions

    def _store_promotion(self, entry: dict[str, Any]) -> None:
        self._promotions.append(entry)
        overflow = len(self._promotions) - self._max_promotions
        if overflow > 0:
            del self._promotions[:overflow]
            self._dropped_promotions += overflow

    def observe(
        self,
        subject: str,
        predicate: str,
        object: str,
        *,
        confidence: float,
        source: str = "",
        cycle: int = 0,
        epistemic: str = OBSERVED,
    ) -> PromotionCandidate:
        """Feed one observation; returns the (possibly updated) candidate."""
        key = (subject, predicate, object)
        existing = self._candidates.get(key)
        if existing is None:
            cand = PromotionCandidate(
                subject=subject, predicate=predicate, object=object,
                confidence=_clamp01(confidence), evidence_count=1,
                epistemic=epistemic, sources=(source,) if source else (),
                first_cycle=cycle,
            )
            self._candidates[key] = cand
            return cand
        overlap = max(0.0, 1.0 - _clamp01(confidence))
        new_conf = 1.0 - (1.0 - existing.confidence) * overlap
        new_epistemic = _merge_epistemic(existing.epistemic, epistemic)
        updated = PromotionCandidate(
            subject=subject, predicate=predicate, object=object,
            confidence=_clamp01(new_conf), evidence_count=existing.evidence_count + 1,
            epistemic=new_epistemic,
            sources=existing.sources + ((source,) if source else ()),
            first_cycle=existing.first_cycle,
        )
        self._candidates[key] = updated
        return updated

    def promote(self, candidate: PromotionCandidate, graph: EntityGraph, *, cycle: int = 0) -> bool:
        """Promote a candidate into the knowledge graph past thresholds.

        SIMULATED/PREDICTED candidates are never promoted as fact — they remain
        hypothetical (safety boundary: simulation never becomes fact).
        """
        if candidate.epistemic not in _PROMOTABLE_EPISTEMIC:
            return False
        if candidate.evidence_count < self.promote_min_evidence:
            return False
        if candidate.confidence < self.promote_min_confidence:
            return False
        key = (candidate.subject, candidate.predicate, candidate.object)
        if key in self._promoted_keys:
            return False  # already promoted; do not re-inflate evidence/confidence
        triple = graph.add(
            candidate.subject, candidate.predicate, candidate.object,
            confidence=candidate.confidence, source="|".join(candidate.sources) or "pipeline",
            cycle=cycle,
        )
        self._promoted_keys.add(key)
        self._store_promotion({
            "subject": candidate.subject, "predicate": candidate.predicate,
            "object": candidate.object, "confidence": round(candidate.confidence, 3),
            "evidence_count": candidate.evidence_count,
            "source": triple.source, "cycle": cycle,
        })
        return True

    def promote_all_ready(self, graph: EntityGraph, *, cycle: int = 0) -> int:
        count = 0
        for candidate in self._candidates.values():
            if self.promote(candidate, graph, cycle=cycle):
                count += 1
        return count

    def candidates(self) -> tuple[PromotionCandidate, ...]:
        return tuple(self._candidates.values())

    def promotions(self) -> list[dict[str, Any]]:
        return list(self._promotions)

    def snapshot(self) -> dict[str, Any]:
        return {
            "promote_min_evidence": self.promote_min_evidence,
            "promote_min_confidence": self.promote_min_confidence,
            "candidate_count": len(self._candidates),
            "candidates": [c.snapshot() for c in self._candidates.values()],
            "promotion_count": len(self._promotions),
            "promotions": list(self._promotions),
            "promoted_keys": sorted(self._promoted_keys),
            "dropped_promotions": self._dropped_promotions,
        }

    def from_snapshot(self, snapshot: dict[str, Any]) -> "KnowledgePromotionPipeline":
        """Phase 4c: restore promotion candidates/history after restart."""
        for c in snapshot.get("candidates", []):
            try:
                candidate = PromotionCandidate(
                    subject=str(c.get("subject", "")),
                    predicate=str(c.get("predicate", "")),
                    object=str(c.get("object", "")),
                    confidence=_clamp01(c.get("confidence", 0.0)),
                    evidence_count=int(c.get("evidence_count", 0)),
                    epistemic=str(c.get("epistemic", OBSERVED)),
                    sources=tuple(str(s) for s in c.get("sources", [])),
                    first_cycle=int(c.get("first_cycle", 0)),
                )
            except (TypeError, ValueError):
                continue
            key = (candidate.subject, candidate.predicate, candidate.object)
            self._candidates[key] = candidate
        for entry in snapshot.get("promotions", []):
            if isinstance(entry, dict) and entry:
                self._store_promotion(entry)
        self._promoted_keys.update(str(k) for k in snapshot.get("promoted_keys", []))
        return self


def _merge_epistemic(a: str, b: str) -> str:
    """Merged epistemic status: strongest wins; simulation never claims real."""
    if a == b:
        return a
    if a in _NON_FACTUAL or b in _NON_FACTUAL:
        return PREDICTED if (PREDICTED in (a, b)) else SIMULATED
    if VERIFIED in (a, b):
        return VERIFIED
    if OBSERVED in (a, b):
        return OBSERVED
    return INFERRED


# ---------------------------------------------------------------------------
# User correction with provenance
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CorrectionRecord:
    """An explicit user correction that supersedes a prior knowledge claim."""
    subject: str
    predicate: str
    old_object: str | None
    new_object: str
    person: str
    source: str
    cycle: int
    timestamp: str = ""

    def snapshot(self) -> dict[str, Any]:
        return {
            "subject": self.subject, "predicate": self.predicate,
            "old_object": self.old_object, "new_object": self.new_object,
            "corrected_by": self.person, "source": self.source,
            "cycle": self.cycle, "timestamp": self.timestamp,
        }


class UserCorrectionLog:
    """Append-only log of explicit user corrections with provenance.

    A correction supersedes (does not silently delete) earlier knowledge: the
    old triple's history stays visible under its new status.
    """

    def __init__(self, *, max_records: int = 1000) -> None:
        # The knowledge itself persists in the graph at authoritative
        # confidence; this log is the audit trail, bounded with a counter.
        self._max_records = max(1, int(max_records))
        self._records: list[CorrectionRecord] = []
        self._dropped_records = 0

    @property
    def dropped_records(self) -> int:
        return self._dropped_records

    def _store(self, record: CorrectionRecord) -> None:
        self._records.append(record)
        overflow = len(self._records) - self._max_records
        if overflow > 0:
            del self._records[:overflow]
            self._dropped_records += overflow

    def apply(self, record: CorrectionRecord, graph: EntityGraph) -> bool:
        """Apply a correction: add the corrected triple at authoritative confidence.

        The kgraph's confidence-based reconcile then marks the prior claim
        contradicted (evidence preserved, never silently deleted). The correction
        record itself carries full provenance (who/when/source).
        """
        prior = graph.leading(record.subject, record.predicate)
        changed = prior is not None and prior.object != record.new_object
        graph.add(
            record.subject, record.predicate, record.new_object,
            confidence=1.0,  # explicit user correction is authoritative
            source=record.source or "user_correction",
            cycle=record.cycle,
        )
        self._store(record)
        return changed

    def records(self) -> tuple[CorrectionRecord, ...]:
        return tuple(self._records)

    def snapshot(self) -> list[dict[str, Any]]:
        return [r.snapshot() for r in self._records]

    def restore(self, records: list[dict[str, Any]]) -> "UserCorrectionLog":
        """Phase 4c: reload persisted corrections (learning survives restart)."""
        for r in records or []:
            try:
                self._store(CorrectionRecord(
                    subject=str(r.get("subject", "")),
                    predicate=str(r.get("predicate", "")),
                    old_object=r.get("old_object"),
                    new_object=str(r.get("new_object", "")),
                    person=str(r.get("corrected_by", "")),
                    source=str(r.get("source", "")),
                    cycle=int(r.get("cycle", 0)),
                    timestamp=str(r.get("timestamp", "")),
                ))
            except (TypeError, ValueError):
                continue  # malformed record: skip, never crash the brain
        return self


# ---------------------------------------------------------------------------
# Routine detection
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RoutineHypothesis:
    """A candidate routine: repeated co-occurrence pattern, not a fact."""
    pattern: tuple[str, ...]
    occurrences: int
    confidence: float
    window_cycles: int

    def snapshot(self) -> dict[str, Any]:
        return {
            "pattern": list(self.pattern),
            "occurrences": self.occurrences,
            "confidence": round(self.confidence, 3),
            "window_cycles": self.window_cycles,
            "epistemic": "INFERRED",
        }


class RoutineDetector:
    """Detects repeated (consecutive) event patterns as candidate routines.

    Routines are hypotheses: they require repeated evidence and remain
    INFERRED (never promoted to fact without further confirmation).
    """

    def __init__(self, *, window: int = 3, min_occurrences: int = 2) -> None:
        self.window = window
        self.min_occurrences = min_occurrences
        self._history: list[tuple[int, set[str]]] = []  # (cycle, events)
        self._routines: dict[tuple[str, ...], RoutineHypothesis] = {}

    def observe(self, cycle: int, events: set[str]) -> None:
        self._history.append((cycle, set(events)))
        # _scan only ever reads the last `window` entries — trimming here is
        # lossless and keeps the detector O(window) forever.
        keep = max(1, self.window)
        if len(self._history) > keep:
            del self._history[:-keep]
        self._scan(cycle)

    def _scan(self, cycle: int) -> None:
        # Look at the last N cycles; a stable multi-cycle co-occurrence is a routine.
        recent = [ev for _, ev in self._history[-self.window:]]
        if len(recent) < self.window:
            return
        common = set.intersection(*recent)
        if not common:
            return
        pattern = tuple(sorted(common))
        existing = self._routines.get(pattern)
        if existing is None:
            self._routines[pattern] = RoutineHypothesis(
                pattern=pattern, occurrences=1,
                confidence=0.4, window_cycles=self.window,
            )
        else:
            self._routines[pattern] = RoutineHypothesis(
                pattern=pattern, occurrences=existing.occurrences + 1,
                confidence=_clamp01(0.4 + 0.15 * (existing.occurrences + 1)),
                window_cycles=self.window,
            )

    def routines(self, *, min_occurrences: int | None = None) -> tuple[RoutineHypothesis, ...]:
        threshold = self.min_occurrences if min_occurrences is None else min_occurrences
        return tuple(r for r in self._routines.values() if r.occurrences >= threshold)

    def snapshot(self) -> dict[str, Any]:
        return {
            "window": self.window,
            "routines": [r.snapshot() for r in self.routines()],
        }

    def from_snapshot(self, snapshot: dict[str, Any]) -> "RoutineDetector":
        """Phase 4c: restore learned routines so learning survives restart."""
        self.window = int(snapshot.get("window", self.window))
        for r in snapshot.get("routines", []):
            pattern = tuple(sorted(str(p) for p in r.get("pattern", [])))
            if not pattern:
                continue
            self._routines[pattern] = RoutineHypothesis(
                pattern=pattern,
                occurrences=int(r.get("occurrences", self.min_occurrences)),
                confidence=_clamp01(r.get("confidence", 0.4)),
                window_cycles=int(r.get("window_cycles", self.window)),
            )
        return self


# ---------------------------------------------------------------------------
# Counterfactual engine
# ---------------------------------------------------------------------------


class CounterfactualEngine:
    """Evaluates "what-if" questions without touching real world state.

    Each query produces a hypothetical slice labelled SIMULATED; results can
    inform planning but are never merged into observed/knowledge state.
    """

    def __init__(self, *, max_queries: int = 1000) -> None:
        self._max_queries = max(1, int(max_queries))
        self._queries: list[dict[str, Any]] = []
        self._dropped_queries = 0

    def _store(self, query: dict[str, Any]) -> None:
        """Append with a bound; spills counted (never silent)."""
        self._queries.append(query)
        overflow = len(self._queries) - self._max_queries
        if overflow > 0:
            del self._queries[:overflow]
            self._dropped_queries += overflow

    @property
    def dropped_queries(self) -> int:
        return self._dropped_queries

    def evaluate(
        self,
        *,
        premise: str,
        if_evidence: dict[str, Any],
        then_prediction: str,
        confidence: float = 0.4,
    ) -> dict[str, Any]:
        """Run a counterfactual: (premise, if_evidence) -> then_prediction."""
        hypothetical = {
            "premise": premise,
            "if_evidence": dict(if_evidence),
            "then_prediction": then_prediction,
            "confidence": _clamp01(confidence),
            "epistemic": SIMULATED,
            "status": "hypothetical",
        }
        self._store(hypothetical)
        return hypothetical

    def queries(self) -> tuple[dict[str, Any], ...]:
        return tuple(self._queries)

    def from_snapshot(self, data: dict[str, Any]) -> "CounterfactualEngine":
        """Phase 4c: restore persisted counterfactual queries."""
        for q in data.get("queries", []):
            if isinstance(q, dict) and q:
                self._store(q)
        return self

    def snapshot(self) -> dict[str, Any]:
        return {
            "query_count": len(self._queries),
            "queries": list(self._queries),
            "dropped_queries": self._dropped_queries,
        }
