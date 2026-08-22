"""Provenance validation for the typed cognition contracts (doc 26 §18).

Every derived object must be traceable: source → observation → evidence →
derived object. For model-derived results, input references + model ID/version +
runtime + timestamp + transformation → result. Missing provenance must cause
rejection for decision-relevant or durable objects.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from cognition.contracts.common import Provenance, ValidationIssue


class ProvenanceValidation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valid: bool
    issues: list[ValidationIssue] = Field(default_factory=list)


# Contract types that must never be written without provenance.
DECISION_RELEVANT_TYPES = frozenset({
    "Evidence",
    "WorldState",
    "SituationState",
    "AttentionCandidate",
    "IntentHypothesis",
    "Prediction",
    "CognitiveDecisionRecord",
    "CognitiveEvent",
})

# Contract types that may be transient/diagnostic and tolerate thin provenance.
TRANSIENT_TYPES = frozenset({"Observation"})


def _provenance_of(obj: dict[str, Any]) -> Provenance | None:
    raw = obj.get("provenance")
    if isinstance(raw, Provenance):
        return raw
    if isinstance(raw, dict):
        return Provenance.model_validate(raw)
    return None


def validate_provenance(obj: Any, *, durable: bool = True) -> ProvenanceValidation:
    """Validate that a canonical object carries a sufficient provenance chain.

    ``durable=True`` rejects objects with no provenance at all (doc 26 §18).
    """
    if hasattr(obj, "model_dump"):
        obj = obj.model_dump()
    if not isinstance(obj, dict):
        return ProvenanceValidation(
            valid=False,
            issues=[ValidationIssue(category="provenance_missing", message="expected an object")],
        )

    contract_type = obj.get("contract_type", "?")
    provenance = _provenance_of(obj)
    issues: list[ValidationIssue] = []

    if provenance is None:
        # Source field itself may carry the origin.
        if durable and contract_type in DECISION_RELEVANT_TYPES and obj.get("source", "system") == "system":
            issues.append(
                ValidationIssue(
                    category="provenance_missing",
                    message=f"{contract_type} has no provenance and no non-system source",
                    contract_type=contract_type,
                )
            )
        if not issues:
            return ProvenanceValidation(valid=True, issues=[])

    source = obj.get("source", "system")
    if provenance is not None:
        has_chain = bool(
            provenance.source_observation_ids
            or provenance.source_evidence_ids
            or provenance.source_object_ids
            or provenance.model_ref
        )
        if durable and contract_type in DECISION_RELEVANT_TYPES and not has_chain and source == "system":
            issues.append(
                ValidationIssue(
                    category="provenance_missing",
                    message=f"{contract_type} provenance has no traceable chain",
                    contract_type=contract_type,
                )
            )

        model_backed = provenance.model_ref is not None
        if model_backed and (provenance.model_version is None or provenance.transformation is None):
            issues.append(
                ValidationIssue(
                    category="provenance_missing",
                    message="model-derived object requires model_version and transformation",
                    contract_type=contract_type,
                )
            )

    return ProvenanceValidation(valid=not issues, issues=issues)
