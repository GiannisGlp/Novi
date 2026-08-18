#!/usr/bin/env python3
"""Generate deterministic positive/negative contract fixtures from registry schemas."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "contracts" / "registry.json"
FIXTURES = ROOT / "contracts" / "tests" / "fixtures"


def value_for_property(prop: dict):
    if "const" in prop:
        return prop["const"]
    if "default" in prop:
        return prop["default"]
    if prop.get("format") == "date-time":
        return "2026-01-01T00:00:00Z"

    kind = prop.get("type")
    if kind == "string":
        return "fixture-value" if prop.get("minLength", 0) == 0 else "fixture-value"
    if kind == "integer":
        return max(1, prop.get("minimum", 1))
    if kind == "number":
        return max(1.0, prop.get("minimum", 1.0))
    if kind == "boolean":
        return True
    if kind == "array":
        count = max(1, prop.get("minItems", 0))
        item_schema = prop.get("items", {"type": "string"})
        return [value_for_property(item_schema) for _ in range(count)]
    if kind == "object":
        return {}
    return {}


def example_for_schema(schema: dict) -> dict:
    result = {}
    properties = schema.get("properties", {})
    for name in schema.get("required", []):
        result[name] = value_for_property(properties.get(name, {}))
    return result


def wrong_type_for(prop: dict):
    kind = prop.get("type")
    return {
        "string": 123,
        "integer": "not-an-integer",
        "number": "not-a-number",
        "boolean": "not-a-boolean",
        "array": {},
        "object": [],
    }.get(kind, "wrong-type")


def main() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    positive = FIXTURES / "positive"
    negative = FIXTURES / "negative"
    positive.mkdir(parents=True, exist_ok=True)
    negative.mkdir(parents=True, exist_ok=True)

    for entry in registry["contracts"]:
        contract_id = entry["contract_id"]
        schema = json.loads((ROOT / "contracts" / entry["schema"]).read_text(encoding="utf-8"))
        example = example_for_schema(schema)

        (positive / f"{contract_id}.json").write_text(
            json.dumps(example, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        required = schema.get("required", [])
        if required:
            missing = dict(example)
            missing.pop(required[0], None)
            (negative / f"{contract_id}__missing-required.json").write_text(
                json.dumps(missing, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )

        extra = dict(example)
        extra["__unexpected_fixture_property__"] = True
        (negative / f"{contract_id}__extra-property.json").write_text(
            json.dumps(extra, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        for name in required:
            prop = schema.get("properties", {}).get(name, {})
            wrong = wrong_type_for(prop)
            if wrong == "wrong-type":
                continue
            invalid = dict(example)
            invalid[name] = wrong
            (negative / f"{contract_id}__wrong-type-{name}.json").write_text(
                json.dumps(invalid, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )

    print(f"Generated fixtures for {len(registry['contracts'])} contracts.")


if __name__ == "__main__":
    main()
