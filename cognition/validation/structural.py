"""Structural validation for the typed cognition contracts (doc 26 §5, §17).

Structural validation checks that a raw payload parses as the canonical typed
object (Pydantic validation) and that references resolve against a supplied
context. It is the first stage of the strict validation policy:

    raw input → parse → structural → semantic → provenance → cross-contract
"""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from cognition.contracts.common import ValidationIssue
from cognition.contracts.schemas import CANONICAL_MODELS

T = TypeVar("T", bound=BaseModel)


class StructuralValidation(BaseModel):
    """Result of parsing one or more payloads against a canonical object."""

    model_config = ConfigDict(extra="forbid")

    valid: bool
    value: Any = None  # dict (single) or list[dict] (many)
    issues: list[ValidationIssue] = Field(default_factory=list)


def _issues_from_pydantic(exc: ValidationError, contract_type: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for err in exc.errors():
        path = ".".join(str(p) for p in err.get("loc", ()))
        issues.append(
            ValidationIssue(
                category="field_invalid",
                message=f"{path}: {err.get('msg', 'invalid')}",
                contract_type=contract_type,
                field_path=path or None,
            )
        )
    return issues


def validate_structurally(contract_type: str, raw: Any) -> StructuralValidation:
    """Parse ``raw`` as the canonical ``contract_type`` object.

    Returns a StructuralValidation with either the typed value (as a dict) or
    machine-readable issues (doc 26 §23 categories).
    """
    model_cls = CANONICAL_MODELS.get(contract_type)
    if model_cls is None:
        return StructuralValidation(
            valid=False,
            issues=[ValidationIssue(
                category="schema_invalid",
                message=f"unknown contract_type {contract_type!r}",
                contract_type=contract_type,
            )],
        )

    if isinstance(raw, model_cls):
        return StructuralValidation(valid=True, value=raw.model_dump())

    try:
        instance = model_cls.model_validate(raw)
    except ValidationError as exc:
        return StructuralValidation(valid=False, issues=_issues_from_pydantic(exc, contract_type))

    return StructuralValidation(valid=True, value=instance.model_dump())


def validate_many(contract_type: str, items: list[Any]) -> StructuralValidation:
    """Validate a list of raw items against one canonical model type."""
    if not isinstance(items, list):
        return StructuralValidation(
            valid=False,
            issues=[ValidationIssue(category="schema_invalid", message="expected a list")],
        )
    value: list[dict[str, Any]] = []
    issues: list[ValidationIssue] = []
    for i, item in enumerate(items):
        result = validate_structurally(contract_type, item)
        if result.valid:
            value.append(result.value)  # type: ignore[arg-type]
        else:
            issues.extend(
                ValidationIssue(
                    category=issue.category,
                    message=f"item[{i}]: {issue.message}",
                    contract_type=contract_type,
                    field_path=issue.field_path,
                )
                for issue in result.issues
            )
    return StructuralValidation(valid=not issues, value=value, issues=issues)


def parse_object(model: type[T], raw: Any) -> T:
    """Parse and return a typed instance, raising on invalid input."""
    return model.model_validate(raw)
