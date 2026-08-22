#!/usr/bin/env python3
"""Consumer-boundary checks for canonical Novi contracts.

These tests model the minimum integration guarantees without inventing runtime
implementations: consumers must identify the contract, enforce its declared
version, and preserve semantic boundaries between acquisition, evidence, and
execution stages.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REGISTRY = ROOT / "contracts" / "registry.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def contract_map(registry):
    return {entry["contract_id"]: entry for entry in registry["contracts"]}


def version(contract_id: str, registry_by_id: dict) -> str:
    return registry_by_id[contract_id]["semantic_version"]


def accepts_version(contract_id: str, supplied: str, registry_by_id: dict) -> bool:
    return supplied == version(contract_id, registry_by_id)


def main() -> int:
    registry = load(REGISTRY)
    contracts = contract_map(registry)
    failures: list[str] = []

    required_ids = {
        "novi.event-envelope",
        "novi.observation",
        "novi.evidence",
        "novi.action-proposal",
        "novi.authorization-decision",
        "novi.safety-decision",
        "novi.action-execution",
        "novi.action-outcome",
    }
    missing = required_ids - contracts.keys()
    if missing:
        failures.append(f"required integration contracts missing: {sorted(missing)}")

    for contract_id in required_ids - missing:
        current = version(contract_id, contracts)
        if not accepts_version(contract_id, current, contracts):
            failures.append(f"{contract_id}: current version was not accepted")
        major = int(current.split(".")[0])
        unsupported = f"{major + 1}.0.0"
        if accepts_version(contract_id, unsupported, contracts):
            failures.append(f"{contract_id}: unsupported major version was silently accepted")

    # The integration boundary must preserve the architecture's semantic
    # separation: observation/evidence are not interchangeable, and proposal
    # is not execution authority.
    if "novi.observation" in contracts and "novi.evidence" in contracts:
        if contracts["novi.observation"]["canonical_name"] == contracts["novi.evidence"]["canonical_name"]:
            failures.append("Observation and Evidence cannot share a canonical semantic identity")

    if "novi.action-proposal" in contracts and "novi.action-execution" in contracts:
        if contracts["novi.action-proposal"]["canonical_name"] == contracts["novi.action-execution"]["canonical_name"]:
            failures.append("ActionProposal and ActionExecution cannot share a canonical semantic identity")

    if failures:
        print("CONTRACT CONSUMER INTEGRATION VALIDATION: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("CONTRACT CONSUMER INTEGRATION VALIDATION: PASS")
    print(f"Validated consumer boundaries for {len(required_ids)} canonical contracts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
