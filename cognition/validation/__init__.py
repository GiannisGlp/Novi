"""Validation layer for the typed cognition contracts (doc 26 §5, §17, §18)."""

from cognition.validation.cross_contract import (
    CrossContractValidation,
    validate_cross_contract,
)
from cognition.validation.provenance import ProvenanceValidation, validate_provenance
from cognition.validation.semantic import SemanticContext, SemanticValidation, validate_semantic
from cognition.validation.structural import (
    StructuralValidation,
    parse_object,
    validate_many,
    validate_structurally,
)

__all__ = [
    "StructuralValidation",
    "parse_object",
    "validate_many",
    "validate_structurally",
    "SemanticContext",
    "SemanticValidation",
    "validate_semantic",
    "ProvenanceValidation",
    "validate_provenance",
    "CrossContractValidation",
    "validate_cross_contract",
]


def validate_full(
    obj: object,
    *,
    ctx: SemanticContext | None = None,
    durable: bool = True,
) -> tuple[StructuralValidation, SemanticValidation, ProvenanceValidation, CrossContractValidation]:
    """Run the full validation pipeline: structural → semantic → provenance → cross-contract.

    Returns a tuple of (structural, semantic, provenance, cross_contract) results.
    """
    contract_type = getattr(obj, "contract_type", None)
    if contract_type is None and isinstance(obj, dict):
        contract_type = obj.get("contract_type")

    if contract_type is None:
        return (
            StructuralValidation(valid=False, issues=[]),
            SemanticValidation(valid=False, issues=[]),
            ProvenanceValidation(valid=False, issues=[]),
            CrossContractValidation(valid=False, issues=[]),
        )

    structural = validate_structurally(contract_type, obj)
    if not structural.valid:
        return (
            structural,
            SemanticValidation(valid=False, issues=[]),
            ProvenanceValidation(valid=False, issues=[]),
            CrossContractValidation(valid=False, issues=[]),
        )

    semantic = validate_semantic(structural.value, ctx)
    provenance = validate_provenance(structural.value, durable=durable)
    cross = validate_cross_contract(structural.value)
    return structural, semantic, provenance, cross


__all__ += ["validate_full"]
