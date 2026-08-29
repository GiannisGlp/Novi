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


def validate_autonomy_semantics() -> list[str]:
    """Autonomy-domain invariants (06_AUTONOMY docs 01/02/05/07).

    These complement JSON Schema: they check cross-field meaning that a
    structural validator cannot express — authorization leases, verified
    success, bounded retries, and state-transition accountability.
    """
    failures: list[str] = []

    # --- AutonomyState (doc 01 Step 1): every transition must carry a
    # reason and an originating component, and the snapshot must be dated.
    state_schema = load_schema("autonomy/autonomy-state/1.0.0/schema.json")
    state = {
        "state_id": "st-semantic-001",
        "state": "EXECUTING",
        "authority_level": "BOUNDED_AUTONOMY",
        "entered_at": "2026-01-01T00:00:00Z",
        "reason": "goal_requires_object_search",
        "originating_component": "supervisor",
        "provenance": {"source": "supervisor"},
    }
    for field in state_schema["required"]:
        if field not in state:
            failures.append(f"AutonomyState semantic fixture missing required meaning: {field}")
    if not state["reason"] or not state["originating_component"] or not state["entered_at"]:
        failures.append("AutonomyState transition must carry reason, originating component and timestamp")

    # --- AutonomyEvent (doc 01 Step 5): an action event must reference what
    # it is about — an action, goal or plan — and declare the authority used.
    event_schema = load_schema("autonomy/autonomy-event/1.0.0/schema.json")
    event = {
        "event_id": "evt-autonomy-001",
        "event_type": "ACTION_STARTED",
        "goal_id": "goal-1",
        "action_ref": "act-1",
        "authority": "BOUNDED_AUTONOMY",
        "reason": "goal_requires_object_search",
        "timestamp": "2026-01-01T00:00:00Z",
        "producer_id": "supervisor",
        "provenance": {"source": "supervisor"},
    }
    for field in event_schema["required"]:
        if field not in event:
            failures.append(f"AutonomyEvent semantic fixture missing required meaning: {field}")
    if not event["authority"] or not event["timestamp"]:
        failures.append("AutonomyEvent must declare authority level and timestamp")
    if not (event.get("goal_id") or event.get("plan_id") or event.get("action_ref") or event.get("skill_id")):
        failures.append("AutonomyEvent must reference the goal, plan, skill or action it records")

    # --- AuthorizedAction (doc 01 Step 6): only the policy layer may create
    # an authorization; a proposal is not its own grant, and a lease cannot
    # expire before it is issued.
    auth_schema = load_schema("autonomy/authorized-action/1.0.0/schema.json")
    auth = {
        "authorization_id": "authz-001",
        "proposal_ref": "prop-1",
        "grant_ref": "grant-1",
        "action": "move_forward",
        "parameters": {"distance_m": 0.5},
        "authority_level": "BOUNDED_AUTONOMY",
        "issued_at": "2026-01-01T00:00:00Z",
        "expires_at": "2026-01-01T00:01:00Z",
        "idempotency_key": "authz-001",
        "provenance": {"source": "governance-guard"},
    }
    for field in auth_schema["required"]:
        if field not in auth:
            failures.append(f"AuthorizedAction semantic fixture missing required meaning: {field}")
    if auth["proposal_ref"] == auth["grant_ref"]:
        failures.append("AuthorizedAction proposal_ref and grant_ref must be distinct (proposal != authorization)")
    if auth["expires_at"] <= auth["issued_at"]:
        failures.append("AuthorizedAction lease must not expire before it is issued")

    # --- ActionResult (doc 00 principle 3): no action counts as successful
    # merely because a model said so — success requires verification evidence.
    result_schema = load_schema("autonomy/action-result/1.0.0/schema.json")
    result = {
        "result_id": "res-001",
        "action_ref": "act-1",
        "outcome": "SUCCESS",
        "verification": {"verification_id": "ver-1", "status": "PASS", "observed_evidence": {"pose_error_m": 0.02}},
        "observed_effects": {"pose": [1.0, 2.0, 90.0]},
        "latency_ms": 120,
        "provenance": {"source": "closed-loop"},
    }
    for field in result_schema["required"]:
        if field not in result:
            failures.append(f"ActionResult semantic fixture missing required meaning: {field}")
    if result["outcome"] == "SUCCESS" and not result.get("verification"):
        failures.append("ActionResult SUCCESS requires verification evidence (world must verify, not the model)")

    # --- VerificationResult: PASS cannot exist without observed evidence.
    verification_schema = load_schema("autonomy/verification-result/1.0.0/schema.json")
    verification = {
        "verification_id": "ver-1",
        "target_ref": "act-1",
        "method": "pose_within_tolerance",
        "status": "PASS",
        "observed_evidence": {"pose_error_m": 0.02},
        "threshold": {"pose_error_m": 0.1},
        "provenance": {"source": "verifier"},
    }
    for field in verification_schema["required"]:
        if field not in verification:
            failures.append(f"VerificationResult semantic fixture missing required meaning: {field}")
    if verification["status"] == "PASS" and not verification.get("observed_evidence"):
        failures.append("VerificationResult PASS requires observed evidence")

    # --- RecoveryRequest (doc 07 Step 5): a retry strategy must have a
    # budget — every retry consumes one, so zero-budget retries are infinite.
    recovery_schema = load_schema("autonomy/recovery-request/1.0.0/schema.json")
    recovery = {
        "recovery_id": "rec-001",
        "failure_ref": "fail-1",
        "failure_class": "execution",
        "strategy": "retry",
        "retry_budget": 2,
        "reason": "timeout",
        "provenance": {"source": "supervisor"},
    }
    for field in recovery_schema["required"]:
        if field not in recovery:
            failures.append(f"RecoveryRequest semantic fixture missing required meaning: {field}")
    if recovery["strategy"] == "retry" and recovery["retry_budget"] <= 0:
        failures.append("RecoveryRequest retry strategy requires a positive retry budget")

    # --- AuthorityContext (doc 01 Step 2 / doc 02 Step 6): authority is a
    # scoped, dated grant; a full-local grant cannot appear before the
    # safety-certification authority exists.
    authority_schema = load_schema("autonomy/authority-context/1.0.0/schema.json")
    authority = {
        "authority_id": "actx-001",
        "authority_level": "BOUNDED_AUTONOMY",
        "autonomy_mode": "bounded",
        "scope": {"skills": ["observe", "speak"]},
        "grantor": "user",
        "issued_at": "2026-01-01T00:00:00Z",
        "constraints": {"max_risk_class": "R2"},
        "provenance": {"source": "policy"},
    }
    for field in authority_schema["required"]:
        if field not in authority:
            failures.append(f"AuthorityContext semantic fixture missing required meaning: {field}")
    if authority["authority_level"] not in {
        "PASSIVE", "ASSISTED", "BOUNDED_AUTONOMY", "SUPERVISED_AUTONOMY", "FULL_LOCAL_AUTONOMY",
    }:
        failures.append("AuthorityContext must use a canonical authority level")
    if authority["authority_level"] == "FULL_LOCAL_AUTONOMY" and authority["grantor"] != "safety-certification":
        failures.append("FULL_LOCAL_AUTONOMY requires an explicit safety-certification grantor")
    if authority.get("expires_at") and authority["expires_at"] <= authority["issued_at"]:
        failures.append("AuthorityContext lease must not expire before it is issued")

    # --- PlanStep (doc 05 Step 1): every step must declare how its expected
    # effect will be verified — postcondition verification is not optional.
    plan_step_schema = load_schema("autonomy/plan-step/1.0.0/schema.json")
    plan_step = {
        "step_id": "step-1",
        "plan_ref": "plan-1",
        "action": "NavigateTo",
        "preconditions": {"localized": True},
        "expected_effects": {"pose": "kitchen"},
        "verification": {"method": "pose_within_tolerance"},
        "timeout": 60,
        "retry_budget": 1,
        "status": "PENDING",
        "provenance": {"source": "planner"},
    }
    for field in plan_step_schema["required"]:
        if field not in plan_step:
            failures.append(f"PlanStep semantic fixture missing required meaning: {field}")
    if not plan_step.get("verification"):
        failures.append("PlanStep must declare a postcondition verification method")

    # --- AutonomyHealth (doc 01 Step 8): a health snapshot must name the
    # components it is grading; DEGRADED must say which component degraded.
    health_schema = load_schema("autonomy/autonomy-health/1.0.0/schema.json")
    health = {
        "health_id": "h-001",
        "timestamp": "2026-01-01T00:00:00Z",
        "overall_status": "DEGRADED",
        "components": {"perception_freshness": "degraded", "safety_monitor": "healthy"},
        "provenance": {"source": "supervisor"},
    }
    for field in health_schema["required"]:
        if field not in health:
            failures.append(f"AutonomyHealth semantic fixture missing required meaning: {field}")
    if not health.get("components"):
        failures.append("AutonomyHealth must grade at least one component")
    if health["overall_status"] == "DEGRADED" and "degraded" not in str(health["components"]):
        failures.append("AutonomyHealth DEGRADED must identify the degraded component(s)")

    # --- GoalStatus (doc 02 Step 2): the lifecycle is a single canonical
    # enum; a status record without a reason is not auditable.
    goal_status_schema = load_schema("autonomy/goal-status/1.0.0/schema.json")
    goal_status = {
        "goal_id": "goal-1",
        "status": "ACTIVE",
        "updated_at": "2026-01-01T00:00:00Z",
        "reason": "accepted",
        "provenance": {"source": "goal-manager"},
    }
    for field in goal_status_schema["required"]:
        if field not in goal_status:
            failures.append(f"GoalStatus semantic fixture missing required meaning: {field}")
    if not goal_status["reason"]:
        failures.append("GoalStatus transition must record why the status changed")

    return failures


def main() -> int:
    failures = validate_semantics()
    failures += validate_autonomy_semantics()
    if failures:
        print("SEMANTIC VALIDATION: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("SEMANTIC VALIDATION: PASS")
    print("Validated EventEnvelope, Observation, Evidence, and autonomy-domain semantic invariants.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
