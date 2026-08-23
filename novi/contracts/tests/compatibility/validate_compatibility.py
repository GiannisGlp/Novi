#!/usr/bin/env python3
"""Validate compatibility policy declared by the canonical contract registry.

This is a structural compatibility baseline. It verifies that every registered
contract has an explicit compatibility policy, semantic version, schema, and
validation-suite identifier, and that its declared policy is consistent with
the global compatibility matrix.

The compatibility matrix is intentionally a *global policy document* — it does
not contain per-contract entries. The registry is the authority for each
contract's declared semantic version and compatibility policy (see
`test_compatibility_matrix.py`). Cross-version semantics must be added as
explicit compatibility cases when a contract version changes.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
REGISTRY = ROOT / "novi" / "contracts" / "registry.json"
MATRIX = ROOT / "novi" / "contracts" / "tests" / "compatibility" / "compatibility_matrix.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    registry = load(REGISTRY)
    matrix = load(MATRIX)
    entries = registry.get("contracts", [])
    failures: list[str] = []

    expected_policy = matrix.get("policy")
    if expected_policy is None:
        failures.append("compatibility matrix must declare a global 'policy'")
        expected_policy = "major-stable"

    if len(entries) != 25:
        failures.append(f"expected 25 registered contracts, found {len(entries)}")

    # Declared 1.x -> 1.x compatible and 1.x -> 2.x breaking rules from the matrix.
    rules = {tuple([int(r.get("from_major")), int(r.get("to_major"))]): r.get("compatible")
             for r in matrix.get("rules", []) if isinstance(r, dict)}

    for entry in entries:
        cid = entry.get("contract_id")
        version = entry.get("semantic_version")
        policy = entry.get("compatibility")
        suite = entry.get("validation_suite")
        schema = entry.get("schema")
        if not cid or not version or not policy or not suite or not schema:
            failures.append(f"incomplete compatibility metadata: {cid!r}")
            continue
        if policy != expected_policy:
            failures.append(
                f"{cid}: registry compatibility policy {policy!r} does not match matrix policy {expected_policy!r}"
            )
        if not isinstance(version, str) or not version.split(".")[0].isdigit():
            failures.append(f"{cid}: invalid semantic_version {version!r}")
            continue
        major = int(version.split(".")[0])
        if major == 1 and rules.get((1, 1)) is not True:
            failures.append(f"{cid}: no compatible 1.x -> 1.x matrix rule")
        if major == 1 and rules.get((1, 2)) is not False:
            failures.append(f"{cid}: no incompatible 1.x -> 2.x matrix rule")

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
