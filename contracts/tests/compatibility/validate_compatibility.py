#!/usr/bin/env python3
"""Validate compatibility policy declared by the canonical contract registry.

This is a structural compatibility baseline. It verifies that every registered
contract has an explicit compatibility policy, semantic version, schema, and
validation-suite identifier. It does not invent cross-version semantics; those
must be added as explicit compatibility cases when a contract version changes.
"""
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
    entries = registry.get("contracts", [])
    cases = matrix.get("cases", [])
    by_id = {case.get("contract_id"): case for case in cases}
    failures: list[str] = []

    if len(entries) != 18:
        failures.append(f"expected 18 registered contracts, found {len(entries)}")

    for entry in entries:
        cid = entry.get("contract_id")
        version = entry.get("semantic_version")
        policy = entry.get("compatibility")
        suite = entry.get("validation_suite")
        if not cid or not version or not policy or not suite:
            failures.append(f"incomplete compatibility metadata: {cid!r}")
        case = by_id.get(cid)
        if case is None:
            failures.append(f"missing compatibility matrix case: {cid}")
            continue
        if case.get("current_version") != version:
            failures.append(f"version mismatch for {cid}")
        if case.get("policy") != policy:
            failures.append(f"policy mismatch for {cid}")

    unknown = set(by_id) - {entry.get("contract_id") for entry in entries}
    for cid in sorted(unknown):
        failures.append(f"compatibility matrix references unknown contract: {cid}")

    if failures:
        print("CONTRACT COMPATIBILITY: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("CONTRACT COMPATIBILITY: PASS")
    print(f"Validated compatibility metadata for {len(entries)} contracts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
