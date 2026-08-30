"""Dataset validation pipeline (plan 23 §8, step 05).

Deterministic preprocessing chain:

    raw traces
     -> schema validation        (training.schemas)
     -> PII/privacy filter       (sanitizer.Sanitizer)
     -> malformed-example removal
     -> duplicate detection      (deduplicator)
     -> contradiction detection  (deduplicator)
     -> context completeness check
     -> quality scoring
     -> human review             (annotator)
     -> curated dataset

Rejection rules (plan §8) implemented here (dataset-level context):
- a referenced memory does not exist in the memory index;
- the response depends on missing context (memory summary, perception);
- the visual evidence is absent although the task/response requires it;
- the response makes unsupported perceptual claims;
- identity confidence is below the required threshold;
- the outcome label is unknown when the task requires an outcome.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable

from training.collection.sanitizer import Sanitizer
from training.schemas import validate_example

# Task types whose responses must be grounded in visual/perception evidence.
_EVIDENCE_REQUIRING_TASKS = frozenset({"memory_grounded_response", "dialogue_realization"})

# Perception claim verbs -> an unsupported claim if no evidence backs them.
_CLAIM_VERBS = re.compile(r"\b(i\s+)?(saw|see|noticed|detected|heard|observed)\b", re.IGNORECASE)

KNOWN_OUTCOMES = frozenset({
    "acknowledged", "corrected", "thanks", "follow_up", "ignored",
    "positive", "negative", "accepted", "rejected", "confused", "",
})

# Assistant-like phrasing (plan §10.3 bad examples) penalized by quality score.
ASSISTANT_PHRASES = (
    "i acknowledge", "i have detected", "i can confirm that", "i understand your",
    "it is nice to see", "i appreciate your", "as an ai", "certainly,", "absolutely,",
    "i am happy to", "let me know if",
)


def quality_score(example: dict[str, Any]) -> float:
    """Deterministic 0-1 quality heuristic (plan §8 'quality scoring')."""
    score = 0.0
    sit = example.get("situation") or {}
    person = sit.get("person") or {}
    if person.get("id") and float(person.get("confidence", 0.0)) >= 0.9:
        score += 0.2
    if sit.get("conversation", {}).get("topic") or sit.get("conversation", {}).get("input_event"):
        score += 0.15
    if sit.get("memory"):
        score += 0.15
    decision = example.get("decision") or {}
    if decision.get("dialogue_act"):
        score += 0.15
    if decision.get("reason"):
        score += 0.05
    response = example.get("response", "")
    if response:
        if 2 <= len(response) <= 300:
            score += 0.15
        low = response.lower()
        if not any(p in low for p in ASSISTANT_PHRASES):
            score += 0.15
    return round(max(0.0, min(1.0, score)), 3)


def _perception_evidence(example: dict[str, Any]) -> list[str]:
    return list((((example.get("situation") or {}).get("world") or {}).get("perception") or []))


def _claims_perception(response: str) -> bool:
    return bool(_CLAIM_VERBS.search(response or ""))


def validate_example_ctx(
    example: dict[str, Any],
    memory_index: Iterable[str] | None = None,
    identity_threshold: float = 0.9,
    require_outcome: bool = False,
) -> list[str]:
    """Dataset-level rejection reasons (plan §8). Schema-level checks included."""
    if not isinstance(example, dict):
        return ["malformed: not a dict"]
    errors = list(validate_example(example))
    known_memories = None if memory_index is None else set(memory_index)

    sit = example.get("situation") or {}
    # 1. Referenced memories must exist in the store (plan §8).
    #    Explicit empty index = "no memory may be referenced"; None = unchecked.
    for m in sit.get("memory") or []:
        mid = m.get("id", "")
        if mid and known_memories is not None and mid not in known_memories:
            errors.append(f"situation.memory: {mid!r} does not exist in the memory store")
        if not m.get("summary"):
            errors.append(f"situation.memory: {mid!r} has no summary (missing context)")

    # 2. Identity confidence below the required threshold (plan §8).
    person = sit.get("person") or {}
    if person and float(person.get("confidence", 0.0)) < identity_threshold:
        errors.append(f"person.confidence: {person.get('confidence')} below threshold {identity_threshold}")

    # 3. Visual evidence absent although required (plan §8).
    task = example.get("task", "")
    evidence = _perception_evidence(example)
    if task in _EVIDENCE_REQUIRING_TASKS and not evidence:
        errors.append("visual evidence absent but required by task")

    # 4. Unsupported perceptual claims (plan §8).
    response = example.get("response", "")
    if _claims_perception(response) and not evidence:
        errors.append("response makes unsupported perceptual claim without visual evidence")

    # 5. Outcome label unknown when required (plan §8). An empty label is
    #    "unknown" whenever the task demands an outcome.
    if require_outcome and example.get("outcome", "") not in KNOWN_OUTCOMES - {""}:
        errors.append(f"outcome: unknown outcome label {example.get('outcome')!r}")

    return errors


@dataclass
class ValidationReport:
    accepted: list[dict[str, Any]] = field(default_factory=list)
    rejected: list[tuple[Any, list[str]]] = field(default_factory=list)

    @property
    def rejected_count(self) -> int:
        return len(self.rejected)

    @property
    def accepted_count(self) -> int:
        return len(self.accepted)

    @property
    def total(self) -> int:
        return self.rejected_count + self.accepted_count

    @property
    def acceptance_rate(self) -> float:
        return self.accepted_count / self.total if self.total else 1.0


class DatasetValidator:
    """Runs dataset-level validation + quality scoring over a batch."""

    def __init__(
        self,
        memory_index: Iterable[str] | None = None,
        identity_threshold: float = 0.9,
        require_outcome: bool = False,
    ) -> None:
        # None = existence unchecked; an explicit set (even empty) is enforced.
        self._memory_index = None if memory_index is None else set(memory_index)
        self._identity_threshold = identity_threshold
        self._require_outcome = require_outcome

    def validate(self, examples: list[Any]) -> ValidationReport:
        report = ValidationReport()
        for ex in examples:
            if not isinstance(ex, dict):
                report.rejected.append((ex, ["malformed: not a dict"]))
                continue
            errors = validate_example_ctx(
                ex,
                memory_index=self._memory_index,
                identity_threshold=self._identity_threshold,
                require_outcome=self._require_outcome,
            )
            if errors:
                report.rejected.append((ex, errors))
            else:
                out = dict(ex)
                out["quality"] = quality_score(out)
                report.accepted.append(out)
        return report


@dataclass
class PipelineReport:
    sanitized: int = 0
    sanitized_kept: int = 0
    sanitized_dropped: int = 0
    validated_accepted: int = 0
    validated_rejected: int = 0
    duplicates_removed: int = 0
    contradictions_found: int = 0
    final: list[dict[str, Any]] = field(default_factory=list)
    rejected: list[tuple[Any, list[str]]] = field(default_factory=list)


def run_collection_pipeline(
    examples: list[dict[str, Any]],
    *,
    sanitizer: Sanitizer | None = None,
    memory_index: Iterable[str] | None = None,
    identity_threshold: float = 0.9,
    require_outcome: bool = False,
    near_dup_threshold: float = 0.8,
) -> PipelineReport:
    """End-to-end chain: sanitize -> validate -> dedup (plan §8).

    Contradictions are *reported* but not auto-dropped (human review decides,
    plan §8: contradiction detection is a review trigger, not a deletion).
    """
    from training.collection.deduplicator import find_contradictions, find_near_duplicates

    report = PipelineReport()
    sanitizer = sanitizer or Sanitizer()
    report.sanitized = len(examples)

    kept, sreport = sanitizer.sanitize_all(examples)
    report.sanitized_kept = len(kept)
    report.sanitized_dropped = report.sanitized - len(kept)

    validator = DatasetValidator(
        memory_index=memory_index,
        identity_threshold=identity_threshold,
        require_outcome=require_outcome,
    )
    vreport = validator.validate(kept)
    report.validated_accepted = vreport.accepted_count
    report.validated_rejected = vreport.rejected_count
    report.rejected = vreport.rejected

    candidates = vreport.accepted
    report.contradictions_found = len(find_contradictions(candidates))

    dup_groups = find_near_duplicates(candidates, threshold=near_dup_threshold)
    dropped_ids: set[str] = set()
    for group in dup_groups:
        # keep the first id of each pair, drop the rest deterministically
        for _keep_id, drop_id, _score in group:
            if drop_id not in dropped_ids:
                dropped_ids.add(drop_id)
    report.duplicates_removed = len(dropped_ids)
    report.final = [ex for ex in candidates if ex["example_id"] not in dropped_ids]
    return report
