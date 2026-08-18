#!/usr/bin/env python3
"""Generate deterministic positive/negative contract fixtures from registry schemas."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "contracts" / "registry.json"
FIXTURES = ROOT / "contracts" / "tests" / "fixtures"

# Minimal values chosen to satisfy the current structural schemas. These are
# deliberately synthetic and carry no real user/device data.
VALUE_BY_TYPE = {
    "string": "fixture-value",
    "integer": 1,
    "number": 1.0,
    "boolean": True,
    "object": {},
    "array": [],
}


def example_for_schema(schema: dict) -> dict:
    result = {}
    for name in schema.get("required", []):
        prop = schema.get("properties", {}).get(name, {})
        if "const" in prop:
            result[name] = prop["const"]
            continue
        if "default" in prop:
            result[name] = prop["default"]
            continue
        if prop.get("format") == "date-time":
            result[name] = "2026-01-01T00:00:00Z"
            continue
        kind = prop.get("type", "object")
        if kind == "array":
            result[name] = []
        elif kind == "object":
            result[name] = {}
        else:
            result[name] = VALUE_BY_TYPE.get(kind, "fixture-value")
    return result


def main() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    positive = FIXTURES / "positive"
    negative = FIXTURES / "negative"
    positive.mkdir(parents=True, exist_ok=True)
    negative.mkdir(parents=True, exist_ok=True)

    for entry in registry["contracts"]:
        contract_id = entry["contract_id"]
        schema_path = ROOT / "contracts" / entry["schema"]
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
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

    print(f"Generated fixtures for {len(registry['contracts'])} contracts.")


if __name__ == "__main__":
    main()
