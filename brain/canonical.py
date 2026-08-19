from __future__ import annotations

"""Canonical contract payload factories used by the Stage-0 Brain runtime."""

from typing import Any
from uuid import uuid4

from .contracts import utc_now, validate_contract


def observation_payload(*, source_type: str, source_id: str, modality: str, value: Any, quality: Any, uncertainty: Any, provenance: dict[str, Any], subject_refs: list[str] | None = None) -> dict[str, Any]:
    payload = {
        "observation_id": str(uuid4()),
        "observed_at": utc_now(),
        "source_type": source_type,
        "source_id": source_id,
        "modality": modality,
        "value": value,
        "quality": quality,
        "uncertainty": uncertainty,
        "provenance": provenance,
    }
    if subject_refs is not None:
        payload["subject_refs"] = subject_refs
    return validate_contract("novi.observation", payload)


def action_proposal_payload(*, capability: str, semantic_intent: Any, parameters: Any, constraints: Any, expected_effects: Any, risks: Any, requester_id: str, authorization_context: Any, expires_at: str, idempotency_key: str, provenance: dict[str, Any], target_refs: list[str] | None = None) -> dict[str, Any]:
    payload = {
        "proposal_id": str(uuid4()),
        "capability": capability,
        "semantic_intent": semantic_intent,
        "parameters": parameters,
        "constraints": constraints,
        "expected_effects": expected_effects,
        "risks": risks,
        "requester_id": requester_id,
        "authorization_context": authorization_context,
        "expires_at": expires_at,
        "idempotency_key": idempotency_key,
        "provenance": provenance,
    }
    if target_refs is not None:
        payload["target_refs"] = target_refs
    return validate_contract("novi.action-proposal", payload)


def safety_decision_payload(*, proposal_ref: str, policy_version: str, hardware_health_revision: int, environment_state_revision: int, decision: str, constraints: Any, reason_codes: list[str], valid_until: str, audit_ref: str) -> dict[str, Any]:
    payload = {
        "decision_id": str(uuid4()),
        "proposal_ref": proposal_ref,
        "safety_policy_version": policy_version,
        "hardware_health_revision": hardware_health_revision,
        "environment_state_revision": environment_state_revision,
        "decision": decision,
        "constraints": constraints,
        "reason_codes": reason_codes,
        "valid_until": valid_until,
        "audit_ref": audit_ref,
    }
    return validate_contract("novi.safety-decision", payload)


def action_outcome_payload(*, execution_ref: str, status: str, observed_effects: Any, expected_effect_comparison: Any, sensor_evidence_refs: list[str], recovery_state: Any, provenance: dict[str, Any], error_code: str | None = None) -> dict[str, Any]:
    payload = {
        "outcome_id": str(uuid4()),
        "execution_ref": execution_ref,
        "completed_at": utc_now(),
        "status": status,
        "observed_effects": observed_effects,
        "expected_effect_comparison": expected_effect_comparison,
        "sensor_evidence_refs": sensor_evidence_refs,
        "recovery_state": recovery_state,
        "provenance": provenance,
    }
    if error_code is not None:
        payload["error_code"] = error_code
    return validate_contract("novi.action-outcome", payload)
