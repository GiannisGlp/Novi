#!/usr/bin/env python3
"""Validate the Novi canonical contract registry and JSON Schemas."""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Missing dependency: jsonschema. Install with: python -m pip install -r contracts/tests/requirements.txt") from exc

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "contracts"
REGISTRY_PATH = CONTRACTS / "registry.json"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    registry = load_json(REGISTRY_PATH)
    contracts = registry.get("contracts", [])
    failures: list[str] = []

    # 18 system/memory/autonomy/safety/execution/brain/hardware/deployment
    # + 7 cognition contracts (gap-analysis Step 1) = 25.
    if len(contracts) != 25:
        failures.append(f"registry contains {len(contracts)} contracts; expected 25")

    seen_ids: set[str] = set()
    seen_names: set[str] = set()

    for entry in contracts:
        contract_id = entry.get("contract_id")
        name = entry.get("canonical_name")
        schema_rel = entry.get("schema")
        version = entry.get("semantic_version")

        if not contract_id or contract_id in seen_ids:
            failures.append(f"duplicate/missing contract_id: {contract_id!r}")
        seen_ids.add(contract_id)

        if not name or name in seen_names:
            failures.append(f"duplicate/missing canonical_name: {name!r}")
        seen_names.add(name)

        if not version:
            failures.append(f"missing semantic_version for {contract_id}")
            continue

        schema_path = CONTRACTS / schema_rel
        if not schema_path.is_file():
            failures.append(f"missing schema for {contract_id}: {schema_rel}")
            continue

        schema = load_json(schema_path)
        expected_id = f"{contract_id}/{version}"
        if schema.get("$id") != expected_id:
            failures.append(f"$id mismatch for {contract_id}: {schema.get('$id')!r}; expected {expected_id!r}")

        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:  # pragma: no cover
            failures.append(f"invalid JSON Schema for {contract_id}: {exc}")

        properties = schema.get("properties", {})
        for field in schema.get("required", []):
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
