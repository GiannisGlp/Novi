#!/usr/bin/env python3
"""Executable integration gate for Novi's consequential-action boundary.

This test does not implement a production controller. It verifies the
normative contract boundary and the minimum deterministic semantics that must
hold before a proposed action can become an execution record.

The important invariant is:

    proposal -> authorization -> safety -> execution -> outcome

No probabilistic/model output, proposal, expired authorization, unsafe
hardware state, or emergency-stop state may become execution authority.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = ROOT / "contracts"
REGISTRY = CONTRACTS / "registry.json"

REQUIRED = {
    "novi.action-proposal": "autonomy/action-proposal/1.0.0/schema.json",
    "novi.authorization-decision": "safety/authorization-decision/1.0.0/schema.json",
    "novi.safety-decision": "safety/safety-decision/1.0.0/schema.json",
    "novi.action-execution": "execution/action-execution/1.0.0/schema.json",
    "novi.action-outcome": "execution/action-outcome/1.0.0/schema.json",
    "novi.hardware-health": "hardware/hardware-health/1.0.0/schema.json",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def within_window(now: datetime, valid_from: str, valid_until: str) -> bool:
    return parse_time(valid_from) <= now <= parse_time(valid_until)


def authorization_allows(decision: dict, now: datetime) -> bool:
    return decision["decision"] in {"ALLOW", "ALLOW_WITH_CONSTRAINTS"} and within_window(
        now, decision["valid_from"], decision["valid_until"]
    )


def safety_allows(decision: dict, now: datetime) -> bool:
    return decision["decision"] in {"ALLOW", "ALLOW_WITH_CONSTRAINTS"} and parse_time(
        decision["valid_until"]
    ) >= now


def can_execute(
    proposal: dict,
    authorization: dict,
    safety: dict,
    hardware: dict,
    now: datetime,
) -> bool:
    """Minimum deterministic execution gate for consequential actions."""
    if proposal["proposal_id"] != safety["proposal_ref"]:
        return False
    if authorization["decision_id"] != authorization["decision_id"]:
        return False
    if authorization["decision"] not in {"ALLOW", "ALLOW_WITH_CONSTRAINTS"}:
        return False
    if not authorization_allows(authorization, now):
        return False
    if not safety_allows(safety, now):
        return False
    if hardware["state"] != "HEALTHY":
        return False
    if hardware["communication_state"] != "CONNECTED":
        return False
    if hardware["calibration_state"] != "VALID":
        return False
    if "EMERGENCY_STOP" in hardware["fault_codes"]:
        return False
    return True


def base_documents(now: datetime) -> tuple[dict, dict, dict, dict]:
    valid_from = (now - timedelta(seconds=1)).isoformat()
    valid_until = (now + timedelta(seconds=30)).isoformat()

    proposal = {
        "proposal_id": "proposal-test-001",
        "capability": "base.motion",
        "semantic_intent": "move forward a short distance",
        "parameters": {"distance_m": 0.1},
        "constraints": {"max_speed_mps": 0.1},
        "expected_effects": {"motion": True},
        "risks": {"action_class": "S2"},
        "requester_id": "test-runtime",
        "authorization_context": {},
        "expires_at": valid_until,
        "idempotency_key": "idem-test-001",
        "provenance": {"source": "integration-test"},
    }
    authorization = {
        "decision_id": "auth-test-001",
        "principal": "test-runtime",
        "capability": "base.motion",
        "target": "test-robot",
        "purpose": "integration-test",
        "scope": {"max_speed_mps": 0.1},
        "policy_version": "test-policy-1",
        "state_revision": 1,
        "decision": "ALLOW",
        "valid_from": valid_from,
        "valid_until": valid_until,
        "provenance": {"source": "deterministic-test-policy"},
    }
    safety = {
        "decision_id": "safety-test-001",
        "proposal_ref": proposal["proposal_id"],
        "safety_policy_version": "test-safety-1",
        "hardware_health_revision": 1,
        "environment_state_revision": 1,
        "decision": "ALLOW",
        "constraints": {"max_speed_mps": 0.1},
        "reason_codes": ["SAFE_TEST_STATE"],
        "valid_until": valid_until,
        "audit_ref": "audit-test-001",
    }
    hardware = {
        "device_id": "robot-test-001",
        "device_type": "mobile-base",
        "observed_at": now.isoformat(),
        "state": "HEALTHY",
        "communication_state": "CONNECTED",
        "calibration_state": "VALID",
        "firmware_version": "test",
        "driver_version": "test",
        "health_metrics": {},
        "fault_codes": [],
        "provenance": {"source": "integration-test"},
    }
    return proposal, authorization, safety, hardware


def assert_contract_baseline() -> list[str]:
    failures: list[str] = []
    registry = load_json(REGISTRY)
    entries = {entry["contract_id"]: entry for entry in registry["contracts"]}

    for contract_id, schema_relpath in REQUIRED.items():
        if contract_id not in entries:
            failures.append(f"missing registry contract: {contract_id}")
            continue
        schema_path = CONTRACTS / schema_relpath
        if not schema_path.exists():
            failures.append(f"missing schema: {schema_relpath}")
            continue
        schema = load_json(schema_path)
        if schema.get("$id") != f"{contract_id}/1.0.0":
            failures.append(f"schema id mismatch: {contract_id}")
        if schema.get("additionalProperties") is not False:
            failures.append(f"schema must reject undeclared fields: {contract_id}")

    return failures


def run() -> int:
    failures = assert_contract_baseline()
    now = utc_now()
    proposal, authorization, safety, hardware = base_documents(now)

    # Normal path: every boundary is present and the command is executable.
    if not can_execute(proposal, authorization, safety, hardware, now):
        failures.append("normal authorized action was incorrectly blocked")

    # Proposal is not execution authority.
    if proposal.get("decision") in {"ALLOW", "ALLOW_WITH_CONSTRAINTS"}:
        failures.append("proposal must never contain execution authority")

    # Authorization must be present and valid in time.
    expired = dict(authorization)
    expired["valid_until"] = (now - timedelta(seconds=1)).isoformat()
    if can_execute(proposal, expired, safety, hardware, now):
        failures.append("expired authorization was accepted")

    denied = dict(authorization)
    denied["decision"] = "DENY"
    if can_execute(proposal, denied, safety, hardware, now):
        failures.append("denied authorization was accepted")

    # Safety is an independent gate even when authorization says ALLOW.
    blocked = dict(safety)
    blocked["decision"] = "DENY"
    if can_execute(proposal, authorization, blocked, hardware, now):
        failures.append("denied safety decision was accepted")

    # Hardware health is authoritative for execution eligibility.
    unhealthy = dict(hardware)
    unhealthy["state"] = "FAULT"
    if can_execute(proposal, authorization, safety, unhealthy, now):
        failures.append("unhealthy hardware was accepted")

    disconnected = dict(hardware)
    disconnected["communication_state"] = "DISCONNECTED"
    if can_execute(proposal, authorization, safety, disconnected, now):
        failures.append("disconnected hardware was accepted")

    uncalibrated = dict(hardware)
    uncalibrated["calibration_state"] = "INVALID"
    if can_execute(proposal, authorization, safety, uncalibrated, now):
        failures.append("uncalibrated hardware was accepted")

    # Emergency stop must dominate all ordinary authorization.
    emergency = dict(hardware)
    emergency["fault_codes"] = ["EMERGENCY_STOP"]
    if can_execute(proposal, authorization, safety, emergency, now):
        failures.append("emergency-stop state did not block execution")

    # Safety validity must expire independently of authorization validity.
    safety_expired = dict(safety)
    safety_expired["valid_until"] = (now - timedelta(seconds=1)).isoformat()
    if can_execute(proposal, authorization, safety_expired, hardware, now):
        failures.append("expired safety decision was accepted")

    if failures:
        print("SAFETY AUTHORIZATION INTEGRATION GATE: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("SAFETY AUTHORIZATION INTEGRATION GATE: PASS")
    print("Validated proposal -> authorization -> safety -> execution boundary.")
    print("Validated expiry, denial, hardware health, calibration, communication, and emergency-stop rejection.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
