#!/usr/bin/env python3
"""Validate the Novi canonical contract registry and its JSON Schemas.

This validator intentionally performs structural checks only. Domain semantics
remain owned by the canonical contract documents and domain test suites.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Missing dependency: jsonschema. Install with: python -m pip install jsonschema") from exc

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "contracts" / "registry.json"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    registry = load_json(REGISTRY_PATH)
    contracts = registry.get("contracts", [])
    failures: list[str] = []

    if len(contracts) != 18:
        failures.append(f"registry contains {len(contracts)} contracts; expected 18")

    seen_ids: set[str] = set()
    seen_names: set[str] = set()

    for entry in contracts:
        contract_id = entry.get("contract_id")
        name = entry.get("canonical_name")
        schema_rel = entry.get("schema")

        if not contract_id or contract_id in seen_ids:
            failures.append(f"duplicate/missing contract_id: {contract_id!r}")
        seen_ids.add(contract_id)

        if not name or name in seen_names:
            failures.append(f"duplicate/missing canonical_name: {name!r}")
        seen_names.add(name)

        schema_path = ROOT / "contracts" / schema_rel
        if not schema_path.is_file():
            failures.append(f"missing schema for {contract_id}: {schema_rel}")
            continue

        schema = load_json(schema_path)
        if schema.get("$id") != f"{contract_id}/{entry['semantic_version']}":
            failures.append(f"$id mismatch for {contract_id}: {schema.get('$id')!r}")

        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:  # pragma: no cover - exact library exception varies
            failures.append(f"invalid JSON Schema for {contract_id}: {exc}")

        required = schema.get("required", [])
        properties = schema.get("properties", {})
        for field in required:
            if field not in properties:
                failures.append(f"required field {field!r} absent from properties in {contract_id}")

    if failures:
        print("CONTRACT VALIDATION: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("CONTRACT VALIDATION: PASS")
    print(f"Validated registry entries: {len(contracts)}")
    print("All mapped schemas exist and pass Draft 2020-12 meta-schema validation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
