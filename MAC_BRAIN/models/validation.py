"""Structured-output validation for local reasoning models.

Validates and coerces model output against a declared field schema, so an LLM's
JSON response is normalized into a safe, typed structure before it is trusted.
A failing output is rejected with a list of errors rather than silently used.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FieldSpec:
    required: bool = False
    types: Any = None  # a type or tuple of types
    enum: tuple | None = None
    default: Any = None


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]
    value: dict[str, Any]

    def snapshot(self) -> dict[str, Any]:
        return {"valid": self.valid, "errors": list(self.errors), "value": dict(self.value)}


def action_output_spec(allowed_actions: frozenset[str]) -> dict[str, FieldSpec]:
    """Schema for a bounded behavioral decision produced by a reasoning model."""
    return {
        "action": FieldSpec(required=True, types=str, enum=tuple(allowed_actions)),
        "parameters": FieldSpec(required=False, types=dict, default={}),
        "rationale": FieldSpec(required=False, types=str, default=""),
    }


class StructuredOutputValidator:
    def __init__(self, spec: dict[str, FieldSpec]) -> None:
        self.spec = spec

    def validate(self, raw: Any) -> ValidationResult:
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                return ValidationResult(False, ["output is not valid JSON"], {})
        if not isinstance(raw, dict):
            return ValidationResult(False, [f"expected object, got {type(raw).__name__}"], {})

        errors: list[str] = []
        value: dict[str, Any] = {}
        for field_name, spec in self.spec.items():
            present = field_name in raw and raw[field_name] is not None
            if not present:
                if spec.required:
                    errors.append(f"missing required field '{field_name}'")
                else:
                    value[field_name] = spec.default
                continue
            ok, coerced = self._coerce(raw[field_name], spec)
            if not ok:
                errors.append(f"field '{field_name}' failed validation: {raw[field_name]!r}")
                continue
            value[field_name] = coerced
        return ValidationResult(not errors, errors, value)

    def _coerce(self, item: Any, spec: FieldSpec) -> tuple[bool, Any]:
        if spec.enum is not None and item not in spec.enum:
            return False, item
        if spec.types is None:
            return True, item
        types = spec.types if isinstance(spec.types, tuple) else (spec.types,)
        if isinstance(item, types):
            return True, item
        # best-effort coercion
        if str in types and isinstance(item, (int, float)):
            return True, str(item)
        if float in types and isinstance(item, (int, float)):
            return True, float(item)
        if int in types:
            if isinstance(item, float) and item.is_integer():
                return True, int(item)
            if isinstance(item, str):
                try:
                    return True, int(item)
                except ValueError:
                    return False, item
        return False, item
