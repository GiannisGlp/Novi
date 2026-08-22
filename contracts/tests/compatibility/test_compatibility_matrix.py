#!/usr/bin/env python3
"""Executable compatibility checks for the canonical Novi contract registry."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REGISTRY = ROOT / "contracts" / "registry.json"
MATRIX = ROOT / "contracts" / "tests" / "compatibility" / "compatibility_matrix.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    registry = load(REGISTRY)
    matrix = load(MATRIX)
    registry_entries = {x["contract_id"]: x for x in registry["contracts"]}
    failures: list[str] = []

    # The compatibility matrix is a global policy document. It intentionally
    # does not contain per-contract entries; the registry is the authority for
    # each contract's declared semantic version and compatibility policy.
    if matrix.get("policy") != "major-stable":
        failures.append(
            f"compatibility matrix policy must be 'major-stable', got {matrix.get('policy')!r}"
        )

    rules = matrix.get("rules")
    if not isinstance(rules, list):
        failures.append("compatibility matrix must contain a 'rules' array")
        rules = []

    expected_rules = {
        (1, 1): True,
        (1, 2): False,
    }
    actual_rules = {}
    for rule in rules:
        if not isinstance(rule, dict):
            failures.append("compatibility matrix contains a non-object rule")
            continue
        key = (rule.get("from_major"), rule.get("to_major"))
        actual_rules[key] = rule.get("compatible")

    for key, expected in expected_rules.items():
        if actual_rules.get(key) is not expected:
            failures.append(
                f"compatibility matrix rule {key[0]} -> {key[1]} must have compatible={expected}"
            )

    for key in actual_rules:
        if key not in expected_rules:
            failures.append(f"unsupported compatibility matrix rule {key[0]} -> {key[1]}")

    for contract_id, entry in registry_entries.items():
        policy = entry.get("compatibility")
        if policy != matrix.get("policy"):
            failures.append(
                f"{contract_id}: registry compatibility policy does not match matrix policy"
            )
        version = entry.get("semantic_version")
        if not isinstance(version, str) or not version.split(".")[0].isdigit():
            failures.append(f"{contract_id}: invalid semantic_version {version!r}")
            continue
        major = int(version.split(".")[0])
        if major == 1 and actual_rules.get((1, 1)) is not True:
            failures.append(f"{contract_id}: no compatible 1.x -> 1.x matrix rule")
        if major == 1 and actual_rules.get((1, 2)) is not False:
            failures.append(f"{contract_id}: no incompatible 1.x -> 2.x matrix rule")

    if failures:
        print("COMPATIBILITY VALIDATION: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("COMPATIBILITY VALIDATION: PASS")
    print(f"Validated {len(registry_entries)} registry entries against the global compatibility policy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
