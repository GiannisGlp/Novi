#!/usr/bin/env python3
"""Executable integration gate for Novi's consequential-action boundary."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

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


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def within_window(now: datetime, valid_from: str, valid_until: str) -> bool:
    return parse_time(valid_from) <= now <= parse_time(valid_until)


def can_execute(proposal: dict, authorization: dict, safety: dict, hardware: dict, now: datetime) -> bool:
    if proposal["proposal_id"] != safety["proposal_ref"]:
        return False
    if authorization["capability"] != proposal["capability"]:
        return False
    if authorization["decision"] not in {"ALLOW", "ALLOW_WITH_CONSTRAINTS"}:
        return False
    if not within_window(now, authorization["valid_from"], authorization["valid_until"]):
        return False
    if safety["decision"] not in {"ALLOW", "ALLOW_WITH_CONSTRAINTS"} or parse_time(safety["valid_until"]) < now:
        return False
    if hardware["state"] != "HEALTHY" or hardware["communication_state"] != "CONNECTED":
        return False
    if hardware["calibration_state"] != "VALID" or "EMERGENCY_STOP" in hardware["fault_codes"]:
        return False
    return True


def base_documents(now: datetime) -> tuple[dict, dict, dict, dict]:
    valid_from = (now - timedelta(seconds=1)).isoformat()
    valid_until = (now + timedelta(seconds=30)).isoformat()
    proposal = {"proposal_id": "proposal-test-001", "capability": "base.motion"}
    authorization = {"decision_id": "auth-test-001", "capability": "base.motion", "valid_from": valid_from, "valid_until": valid_until, "decision": "ALLOW"}
    safety = {"decision_id": "safety-test-001", "proposal_ref": proposal["proposal_id"], "valid_until": valid_until, "decision": "ALLOW"}
    hardware = {"state": "HEALTHY", "communication_state": "CONNECTED", "calibration_state": "VALID", "fault_codes": []}
    return proposal, authorization, safety, hardware


def run() -> int:
    failures: list[str] = []
    registry = load_json(REGISTRY)
    entries = {entry["contract_id"]: entry for entry in registry["contracts"]}
    for contract_id, schema_relpath in REQUIRED.items():
        if contract_id not in entries:
            failures.append(f"missing registry contract: {contract_id}")
        elif not (CONTRACTS / schema_relpath).exists():
            failures.append(f"missing schema: {schema_relpath}")

    now = datetime.now(timezone.utc)
    proposal, authorization, safety, hardware = base_documents(now)
    if not can_execute(proposal, authorization, safety, hardware, now):
        failures.append("normal authorized action was incorrectly blocked")

    for name, mutation in [
        ("capability mismatch", lambda x: x.update(capability="unknown.capability")),
        ("authorization denial", lambda x: x.update(decision="DENY")),
        ("authorization expiry", lambda x: x.update(valid_until=(now - timedelta(seconds=1)).isoformat())),
    ]:
        candidate = dict(authorization)
        mutation(candidate)
        if can_execute(proposal, candidate, safety, hardware, now):
            failures.append(f"{name} was accepted")

    blocked_safety = dict(safety); blocked_safety["decision"] = "DENY"
    if can_execute(proposal, authorization, blocked_safety, hardware, now):
        failures.append("denied safety decision was accepted")

    for name, mutation in [
        ("unhealthy hardware", lambda x: x.update(state="FAULT")),
        ("disconnected hardware", lambda x: x.update(communication_state="DISCONNECTED")),
        ("uncalibrated hardware", lambda x: x.update(calibration_state="INVALID")),
        ("emergency stop", lambda x: x.update(fault_codes=["EMERGENCY_STOP"])),
    ]:
        candidate = dict(hardware); mutation(candidate)
        if can_execute(proposal, authorization, safety, candidate, now):
            failures.append(f"{name} was accepted")

    if failures:
        print("SAFETY AUTHORIZATION INTEGRATION GATE: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("SAFETY AUTHORIZATION INTEGRATION GATE: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(run())
