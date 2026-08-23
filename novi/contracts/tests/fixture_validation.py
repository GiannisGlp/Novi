#!/usr/bin/env python3
"""Generate deterministic structural fixtures from the canonical schemas and validate them.

The generator is schema-driven so adding a new required field makes the fixture
validation fail until the fixture-generation rules understand its type. This
prevents hand-written fixtures from silently drifting away from the schemas.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[3]
REGISTRY = ROOT / "novi" / "contracts" / "registry.json"


def value_for(schema: dict[str, Any], field: str) -> Any:
    if "const" in schema:
        return schema["const"]
    if "default" in schema:
        return schema["default"]
    if "enum" in schema and schema["enum"]:
        return schema["enum"][0]
    typ = schema.get("type")
    if typ == "string":
        if schema.get("format") == "date-time":
            return "2026-01-01T00:00:00Z"
        return f"fixture-{field}"
    if typ == "integer":
        return schema.get("minimum", 0)
    if typ == "number":
        return schema.get("minimum", 0)
    if typ == "boolean":
        return True
    if typ == "array":
        item = value_for(schema.get("items", {}), field)
        count = schema.get("minItems", 1)
        return [item for _ in range(count)]
    if typ == "object":
        return {
            key: value_for(value_schema, key)
            for key, value_schema in schema.get("properties", {}).items()
            if key in schema.get("required", [])
        }
    return {}


def positive(schema: dict[str, Any]) -> dict[str, Any]:
    return {
        field: value_for(schema.get("properties", {}).get(field, {}), field)
        for field in schema.get("required", [])
    }


def main() -> int:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    failures: list[str] = []
    positive_count = negative_count = 0
    checker = FormatChecker()

    for entry in registry["contracts"]:
        contract_id = entry["contract_id"]
        schema_path = ROOT / "novi" / "contracts" / entry["schema"]
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema, format_checker=checker)
        instance = positive(schema)

        errors = list(validator.iter_errors(instance))
        if errors:
            failures.append(f"positive fixture rejected for {contract_id}: {errors[0].message}")
        else:
            positive_count += 1

        # Required-field negative case: remove the first required field.
        required = schema.get("required", [])
        if required:
            broken = dict(instance)
            removed = required[0]
            broken.pop(removed, None)
            if not list(validator.iter_errors(broken)):
                failures.append(f"missing-required negative accepted for {contract_id}: {removed}")
            else:
                negative_count += 1

        # Unexpected-property negative case where additionalProperties is false.
        if schema.get("additionalProperties") is False:
            broken = dict(instance)
            broken["__fixture_unexpected_property__"] = True
            if not list(validator.iter_errors(broken)):
                failures.append(f"extra-property negative accepted for {contract_id}")
            else:
                negative_count += 1

    if failures:
        print("FIXTURE VALIDATION: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("FIXTURE VALIDATION: PASS")
    print(f"Positive fixtures validated: {positive_count}/{len(registry['contracts'])}")
    print(f"Negative cases validated: {negative_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
