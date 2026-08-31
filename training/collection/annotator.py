"""Human annotation workflow (plan 23 §9, step 07).

Annotations cover: dialogue act, memory relevance, initiative appropriateness,
grounding correctness, naturalness, verbosity, certainty, user intent,
conversation state, social context and outcome quality.

Multiple reviewers are required for high-impact examples; `AnnotationWorkflow`
enforces a reviewer quorum and attaches a deterministic consensus once reached.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from statistics import mean
from typing import Any

from training.schemas import validate_annotation

# Fields reviewers score (1-5 or boolean/probability). The emotional fields
# (plan 24 §31) score the affective reading and the response's proportionality,
# boundary respect, and timing.
_SCORED_FIELDS = (
    "naturalness", "verbosity", "certainty", "outcome_quality", "memory_relevance",
    "emotional_accuracy", "proportionality", "boundary_respect", "timing",
)
_BOOL_FIELDS = ("initiative_appropriate", "grounding_correct")
_NOMINAL_FIELDS = ("dialogue_act", "user_intent", "conversation_state", "social_context")


def annotate_example(example: dict[str, Any], annotation: dict[str, Any]) -> dict[str, Any]:
    """Attach one reviewer annotation to an example (mutates a copy)."""
    errors = validate_annotation(annotation)
    if errors:
        raise ValueError(f"invalid annotation: {errors}")
    if annotation.get("example_id") != example.get("example_id"):
        raise ValueError(
            f"annotation example_id {annotation.get('example_id')!r} does not match "
            f"example {example.get('example_id')!r}"
        )
    out = dict(example)
    out.setdefault("annotations", []).append(annotation)
    return out


def _majority(values: list[Any]) -> Any:
    if not values:
        return None
    return Counter(values).most_common(1)[0][0]


def consensus(annotations: list[dict[str, Any]]) -> dict[str, Any]:
    """Deterministic consensus over reviewer annotations (majority per field)."""
    n = len(annotations) or 1
    fields: dict[str, Any] = {}
    agreements: list[float] = []
    for f in _SCORED_FIELDS:
        values = [a.get(f) for a in annotations if a.get(f) is not None]
        if not values:
            continue
        fields[f] = round(mean(values), 3) if f == "memory_relevance" else _majority(values)
        agreements.append(Counter(values).most_common(1)[0][1] / n)
    for f in _BOOL_FIELDS:
        values = [a.get(f) for a in annotations if a.get(f) is not None]
        if not values:
            continue
        fields[f] = _majority(values)
        agreements.append(Counter(values).most_common(1)[0][1] / n)
    for f in _NOMINAL_FIELDS:
        values = [a.get(f) for a in annotations if a.get(f)]
        if not values:
            continue
        fields[f] = _majority(values)
        agreements.append(Counter(values).most_common(1)[0][1] / n)
    return {
        "fields": fields,
        "reviewer_count": n,
        "agreement_rate": round(mean(agreements), 3) if agreements else 1.0,
    }


def inter_annotator_agreement(pair: list[dict[str, Any]]) -> float:
    """Pairwise agreement rate across annotatable fields (0-1)."""
    if len(pair) < 2:
        return 1.0
    a, b = pair[0], pair[1]
    keys = list({*a.keys(), *b.keys()} - {"annotation_id", "reviewer_id", "example_id"})
    keys = [k for k in keys if a.get(k) is not None or b.get(k) is not None]
    if not keys:
        return 1.0
    agree = sum(1 for k in keys if a.get(k) == b.get(k))
    return round(agree / len(keys), 3)


@dataclass
class AnnotationWorkflow:
    min_reviewers: int = 2

    def is_ready(self, example: dict[str, Any]) -> bool:
        return len(example.get("annotations") or []) >= self.min_reviewers

    def annotate(self, example: dict[str, Any], annotation: dict[str, Any]) -> dict[str, Any]:
        out = annotate_example(example, annotation)
        if self.is_ready(out):
            out["annotation_consensus"] = consensus(out["annotations"])
        return out
