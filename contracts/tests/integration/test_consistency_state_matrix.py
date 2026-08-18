#!/usr/bin/env python3
"""Validate the ARCH-CLOSE-002 state-class matrix as an executable completeness gate."""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT.parent / "docs" / "01-system-architecture" / "26_ARCH_CLOSE_002_CONSISTENCY_STATE_CLASS_MATRIX.md"

REQUIRED_COLUMNS = [
    "State class", "Examples", "Source of truth", "Durability", "Consistency",
    "Transaction requirement", "Concurrency", "Conflict policy", "Stage-1 replication",
    "Recovery", "Deletion/erasure",
]
REQUIRED_CLASSES = [
    "Authoritative event history", "Critical governance state", "Authorization state",
    "Safety/control state", "Current world state", "Durable episodic memory",
    "Verified knowledge", "Goals", "Plans", "Action proposals",
    "Action authorization decisions", "Action execution state", "Action outcomes",
    "Model invocation records", "Hardware health", "Configuration", "Contract/version metadata",
    "Checkpoint metadata", "Derived search indexes", "Embeddings / derived representations",
    "Analytics/metrics", "Runtime queues", "Transient sensor buffers", "Temporary model context",
    "Local caches",
]


def main() -> int:
    text = DOC.read_text(encoding="utf-8")
    failures: list[str] = []

    header = next((line for line in text.splitlines() if line.startswith("| State class |")), "")
    for column in REQUIRED_COLUMNS:
        if column not in header:
            failures.append(f"missing matrix column: {column}")

    for state_class in REQUIRED_CLASSES:
        if f"| {state_class} |" not in text:
            failures.append(f"missing state class: {state_class}")

    # The matrix must retain the architectural guardrails against unsafe generic policies.
    required_invariants = [
        "`last-write-wins` is not a universal Novi conflict policy",
        "Replication is not required for Stage 1",
        "An unknown external side-effect outcome must remain `UNKNOWN`",
        "A storage engine is an implementation mechanism, not a semantic authority.",
    ]
    for invariant in required_invariants:
        if invariant not in text:
            failures.append(f"missing invariant: {invariant}")

    rows = [line for line in text.splitlines() if line.startswith("|") and not line.startswith("|---")]
    if len(rows) < len(REQUIRED_CLASSES) + 1:
        failures.append("state-class matrix contains fewer rows than required classes")

    if failures:
        print("ARCH-CLOSE-002 CONSISTENCY MATRIX GATE: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("ARCH-CLOSE-002 CONSISTENCY MATRIX GATE: PASS")
    print(f"Validated {len(REQUIRED_CLASSES)} normative state classes and all required consistency fields/invariants.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
