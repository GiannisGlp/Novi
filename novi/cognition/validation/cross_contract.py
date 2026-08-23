"""Cross-contract validation for ownership boundaries (doc 26 §17, §21).

The core ownership invariants:

- Cognition cannot create an authorization grant.
- Cognition cannot create a physical action command.
- Cognition cannot create a Soul-authoritative personality mutation.
- Privacy classification cannot be silently downgraded.

These are enforced in addition to structural/semantic/provenance validation and
must become automated tests (doc 26 §21 invariants).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from novi.cognition.contracts.common import ValidationIssue

# Subjects that only non-Cognition domains may author.
FORBIDDEN_CONTRACT_TYPES = frozenset({
    "AuthorizationDecision",
    "SafetyDecision",
    "ActionExecution",
    "ActionOutcome",
    "ActionProposal",
    "SoulState",
})

# Fields whose presence would indicate Cognition overstepping ownership.
FORBIDDEN_FIELD_MARKERS = (
    "authorization",
    "grant",
    "permission",
    "command",
    "actuator",
    "motor",
)


class CrossContractValidation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valid: bool
    issues: list[ValidationIssue] = Field(default_factory=list)


def validate_cross_contract(obj: Any) -> CrossContractValidation:
    """Verify that a cognitive object does not violate ownership boundaries."""
    if hasattr(obj, "model_dump"):
        obj = obj.model_dump()
    if not isinstance(obj, dict):
        return CrossContractValidation(
            valid=False,
            issues=[ValidationIssue(category="schema_invalid", message="expected an object")],
        )

    contract_type = obj.get("contract_type", "?")
    issues: list[ValidationIssue] = []

    if contract_type in FORBIDDEN_CONTRACT_TYPES:
        issues.append(
            ValidationIssue(
                category="ownership_violation",
                message=f"Cognition cannot author {contract_type}",
                contract_type=contract_type,
            )
        )

    # Cognitives objects must not carry authorization/command semantics.
    dumped = json_dump(obj)
    lowered = dumped.lower()
    if "authoriz" in lowered and "grant" in lowered:
        issues.append(
            ValidationIssue(
                category="ownership_violation",
                message="cognitive object contains authorization-grant semantics",
                contract_type=contract_type,
            )
        )

    # Privacy downgrade check: fields that are sensitive-biometric must remain
    # classified; a "none"/"inherited" classification on a person-bound object
    # with identity data is a violation.
    privacy = obj.get("privacy")
    sensitive_markers = ("identity_confidence", "biometric", "relationship_category", "person_ref")
    has_sensitive = any(marker in lowered for marker in sensitive_markers)
    if has_sensitive and isinstance(privacy, dict):
        classification = privacy.get("classification", "inherited")
        if classification in ("none", "inherited"):
            issues.append(
                ValidationIssue(
                    category="privacy_invalid",
                    message="person-sensitive cognitive data requires an explicit privacy classification",
                    contract_type=contract_type,
                    field_path="privacy.classification",
                )
            )

    return CrossContractValidation(valid=not issues, issues=issues)


def json_dump(obj: dict[str, Any]) -> str:
    import json

    def _default(o: Any) -> str:
        return str(o)

    return json.dumps(obj, default=_default)
