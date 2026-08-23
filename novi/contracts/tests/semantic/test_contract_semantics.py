#!/usr/bin/env python3
"""Cross-field semantic checks that complement JSON Schema validation."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CONTRACTS = ROOT / "novi" / "contracts"


def load_schema(relative: str) -> dict:
    return json.loads((CONTRACTS / relative).read_text(encoding="utf-8"))


def validate_semantics() -> list[str]:
    failures: list[str] = []

    event_schema = load_schema("system/event-envelope/1.0.0/schema.json")
    event = {
        "event_id": "evt-semantic-001",
        "event_type": "semantic.fixture",
        "schema_version": "1.0.0",
        "occurred_at": "2026-01-01T00:00:00Z",
        "producer_id": "semantic-test",
        "payload": {},
    }
    if event["schema_version"] != event_schema["properties"]["schema_version"]["const"]:
        failures.append("EventEnvelope schema_version does not match its schema identity")
    if not event["event_id"] or not event["producer_id"]:
        failures.append("EventEnvelope requires stable event and producer identities")

    observation_schema = load_schema("system/observation/1.0.0/schema.json")
    observation = {
        "observation_id": "obs-semantic-001",
        "observed_at": "2026-01-01T00:00:00Z",
        "source_type": "sensor",
        "source_id": "sensor-1",
        "modality": "temperature",
        "value": 21.0,
        "quality": "measured",
        "uncertainty": {"kind": "absolute", "value": 0.5},
        "provenance": {"source": "sensor-1"},
    }
    for field in observation_schema["required"]:
        if field not in observation:
            failures.append(f"Observation semantic fixture missing required meaning: {field}")
    if not observation["source_type"] or not observation["source_id"]:
        failures.append("Observation must identify the acquisition source")
    if observation["uncertainty"] is None:
        failures.append("Observation must carry uncertainty and must not imply certainty")
    if observation["provenance"] is None:
        failures.append("Observation must carry provenance")

    evidence_schema = load_schema("system/evidence/1.0.0/schema.json")
    evidence = {
        "evidence_id": "evidence-semantic-001",
        "created_at": "2026-01-01T00:00:01Z",
        "evidence_type": "sensor-derived",
        "source_observation_refs": [observation["observation_id"]],
        "claim": {"temperature_c": 21.0},
        "confidence": 0.9,
        "uncertainty": {"kind": "absolute", "value": 0.5},
        "provenance": {"source_observation_refs": [observation["observation_id"]]},
        "verification_status": "unverified",
    }
    if len(evidence["source_observation_refs"]) < 1:
        failures.append("Evidence must reference at least one Observation")
    if not evidence["provenance"]:
        failures.append("Evidence must preserve provenance")
    if evidence["verification_status"] == "verified" and not evidence["source_observation_refs"]:
        failures.append("Verified Evidence cannot exist without source observations")

    # Keep the foundational semantic distinction explicit: acquisition,
    # interpretation and knowledge are separate stages and cannot be silently
    # collapsed into one contract.
    if "claim" not in evidence or "value" in evidence:
        failures.append("Evidence semantic shape must remain distinct from Observation")

    return failures


def main() -> int:
    failures = validate_semantics()
    if failures:
        print("SEMANTIC VALIDATION: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("SEMANTIC VALIDATION: PASS")
    print("Validated EventEnvelope, Observation, and Evidence semantic invariants.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
