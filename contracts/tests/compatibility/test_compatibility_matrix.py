#!/usr/bin/env python3
"""Executable compatibility checks for the canonical Novi contract registry."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
REGISTRY = ROOT / "contracts" / "registry.json"
MATRIX = ROOT / "contracts" / "tests" / "compatibility" / "compatibility_matrix.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    registry = load(REGISTRY)
    matrix = load(MATRIX)
    registry_entries = {x["contract_id"]: x for x in registry["contracts"]}
    matrix_entries = {x["contract_id"]: x for x in matrix["contracts"]}
    failures: list[str] = []

    if set(registry_entries) != set(matrix_entries):
        failures.append("registry and compatibility matrix contain different contract IDs")

    for contract_id, entry in registry_entries.items():
        matrix_entry = matrix_entries.get(contract_id)
        if not matrix_entry:
            continue
        if matrix_entry.get("current_version") != entry.get("semantic_version"):
            failures.append(
                f"{contract_id}: matrix current_version does not match registry semantic_version"
            )
        if matrix_entry.get("compatibility") != entry.get("compatibility"):
            failures.append(
                f"{contract_id}: matrix compatibility policy does not match registry"
            )
        policy = matrix_entry.get("compatibility")
        if policy not in {"major-stable", "minor-stable"}:
            failures.append(f"{contract_id}: unsupported compatibility policy {policy!r}")

    if failures:
        print("COMPATIBILITY VALIDATION: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("COMPATIBILITY VALIDATION: PASS")
    print(f"Validated {len(registry_entries)} registry/matrix entries.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
