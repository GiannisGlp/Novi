#!/usr/bin/env python3
"""Executable schema-evolution compatibility checks for EventEnvelope."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[3]
SCHEMA = ROOT / "contracts" / "schemas" / "novi.event-envelope.schema.json"

BASE = {
    "event_id": "evt-compat-base",
    "event_type": "compatibility.fixture",
    "schema_version": "1.0.0",
    "occurred_at": "2026-01-01T00:00:00Z",
    "producer_id": "compatibility-test",
    "payload": {},
}


def main() -> int:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    failures: list[str] = []

    # Baseline 1.x payload must remain valid.
    errors = list(validator.iter_errors(BASE))
    if errors:
        failures.append("1.0 baseline payload is invalid")

    # A minor evolution may add optional data without invalidating the old
    # contract payload. This is tested structurally against the 1.0 schema.
    additive = copy.deepcopy(BASE)
    additive["compatibility_note"] = "optional additive field"
    errors = list(validator.iter_errors(additive))
    if errors:
        # Current EventEnvelope is closed to undeclared fields. Record this as
        # an explicit architectural incompatibility rather than hiding it.
        failures.append(
            "declared additive 1.x fixture is rejected by the current closed schema; "
            "schema evolution must explicitly permit optional additions"
        )

    # A major-version fixture must not be accepted as the current 1.x schema.
    major = copy.deepcopy(BASE)
    major["schema_version"] = "2.0.0"
    major["breaking_required_field"] = "migration-required"
    errors = list(validator.iter_errors(major))
    if not errors:
        failures.append("2.0 breaking fixture was unexpectedly accepted by the 1.x schema")

    if failures:
        print("SCHEMA EVOLUTION VALIDATION: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("SCHEMA EVOLUTION VALIDATION: PASS")
    print("Validated baseline, additive evolution, and major-version rejection.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
