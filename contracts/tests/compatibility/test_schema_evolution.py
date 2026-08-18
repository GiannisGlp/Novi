#!/usr/bin/env python3
"""Executable schema-evolution compatibility checks for EventEnvelope."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator, FormatChecker

from event_envelope_adapter import upgrade_1_0_to_1_1

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_ROOT = ROOT / "contracts" / "system" / "event-envelope"

BASE_1_0 = {
    "event_id": "evt-compat-base",
    "event_type": "compatibility.fixture",
    "schema_version": "1.0.0",
    "occurred_at": "2026-01-01T00:00:00Z",
    "producer_id": "compatibility-test",
    "payload": {},
}


def validator(version: str) -> Draft202012Validator:
    schema = json.loads((SCHEMA_ROOT / version / "schema.json").read_text(encoding="utf-8"))
    return Draft202012Validator(schema, format_checker=FormatChecker())


def assert_valid(v: Draft202012Validator, value: dict, label: str, failures: list[str]) -> None:
    if errors := list(v.iter_errors(value)):
        failures.append(f"{label} is invalid: {errors[0].message}")


def assert_invalid(v: Draft202012Validator, value: dict, label: str, failures: list[str]) -> None:
    if not list(v.iter_errors(value)):
        failures.append(f"{label} was unexpectedly accepted")


def main() -> int:
    v10 = validator("1.0.0")
    v11 = validator("1.1.0")
    v20 = validator("2.0.0")
    failures: list[str] = []

    # Current 1.0 contract remains valid.
    assert_valid(v10, BASE_1_0, "1.0 baseline payload", failures)

    # Option B: compatibility is explicit through a versioned adapter.
    upgraded = upgrade_1_0_to_1_1(BASE_1_0)
    upgraded["compatibility_note"] = "optional additive field"
    assert_valid(v11, upgraded, "1.0 -> 1.1 adapted payload", failures)

    # The adapter must preserve all original semantic fields.
    for field in ("event_id", "event_type", "occurred_at", "producer_id", "payload"):
        if upgraded[field] != BASE_1_0[field]:
            failures.append(f"adapter changed existing field: {field}")

    # A 1.0 payload cannot be silently accepted as a 2.0 payload.
    major = copy.deepcopy(BASE_1_0)
    major["schema_version"] = "2.0.0"
    assert_invalid(v20, major, "1.0 payload presented as 2.0", failures)

    # The 2.0 breaking schema requires an explicit migration field.
    breaking = copy.deepcopy(major)
    breaking["breaking_required_field"] = "migration-required"
    assert_valid(v20, breaking, "explicit 2.0 migrated payload", failures)

    if failures:
        print("SCHEMA EVOLUTION VALIDATION: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("SCHEMA EVOLUTION VALIDATION: PASS")
    print("Validated 1.0 baseline, explicit 1.0 -> 1.1 adaptation, and 2.0 breaking boundary.")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.exit(main())
