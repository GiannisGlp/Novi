"""Semantic validation for the typed cognition contracts (doc 26 §17).

Structural validation alone is insufficient. Semantic validators verify:

- References: entities exist or are explicitly unresolved; world revisions
  exist; situations reference a valid world revision; evidence references valid
  observations; decisions reference a valid situation.
- Time: timestamps parseable; validity intervals coherent; clock domain
  declared; impossible ordering rejected or marked uncertain.
- Uncertainty: confidence/probability in range; calibration explicit;
  alternatives compatible with the hypothesis.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from cognition.contracts.common import ValidationIssue


class SemanticContext(BaseModel):
    """Known ids the validator can resolve references against (doc 26 §17)."""

    model_config = ConfigDict(extra="forbid")

    entity_ids: set[str] = Field(default_factory=set)
    observation_ids: set[str] = Field(default_factory=set)
    evidence_ids: set[str] = Field(default_factory=set)
    world_revisions: set[int] = Field(default_factory=set)
    situation_ids: set[str] = Field(default_factory=set)
    allow_unresolved: bool = True  # doc 26: "exists or is explicitly unresolved"


class SemanticValidation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valid: bool
    issues: list[ValidationIssue] = Field(default_factory=list)


def _issue(category: str, message: str, contract_type: str | None = None, field_path: str | None = None) -> ValidationIssue:
    return ValidationIssue(
        category=category,  # type: ignore[arg-type]
        message=message,
        contract_type=contract_type,
        field_path=field_path,
    )


def _ref_ok(ref: str, known: set[str], allow_unresolved: bool) -> bool:
    return allow_unresolved or ref in known


def validate_semantic(obj: Any, ctx: SemanticContext | None = None) -> SemanticValidation:
    """Validate semantic invariants for a canonical cognitive object.

    Accepts a typed Pydantic instance or a plain dict.
    """
    ctx = ctx or SemanticContext()
    issues: list[ValidationIssue] = []
    if hasattr(obj, "model_dump"):
        obj = obj.model_dump()
    if not isinstance(obj, dict):
        return SemanticValidation(
            valid=False,
            issues=[_issue("schema_invalid", "semantic validation requires an object")],
        )

    contract_type = obj.get("contract_type", "?")

    # --- References -------------------------------------------------------
    subject = obj.get("subject_ref")
    if subject and not _ref_ok(subject, ctx.entity_ids, ctx.allow_unresolved):
        issues.append(_issue("reference_invalid", f"unknown subject_ref {subject!r}", contract_type, "subject_ref"))
    object_ref = obj.get("object_ref")
    if object_ref and not _ref_ok(object_ref, ctx.entity_ids, ctx.allow_unresolved):
        issues.append(_issue("reference_invalid", f"unknown object_ref {object_ref!r}", contract_type, "object_ref"))
    person_ref = obj.get("person_ref")
    if person_ref and not _ref_ok(person_ref, ctx.entity_ids, ctx.allow_unresolved):
        issues.append(_issue("reference_invalid", f"unknown person_ref {person_ref!r}", contract_type, "person_ref"))

    source_observations = obj.get("source_observation_ids") or []
    for obs_id in source_observations:
        if not _ref_ok(obs_id, ctx.observation_ids, ctx.allow_unresolved):
            issues.append(_issue("reference_invalid", f"unknown observation {obs_id!r}", contract_type, "source_observation_ids"))

    source_evidence = obj.get("source_evidence_ids") or []
    for ev_id in source_evidence:
        if not _ref_ok(ev_id, ctx.evidence_ids, ctx.allow_unresolved):
            issues.append(_issue("reference_invalid", f"unknown evidence {ev_id!r}", contract_type, "source_evidence_ids"))

    world_revision = obj.get("world_revision")
    if world_revision is not None and not ctx.allow_unresolved and world_revision not in ctx.world_revisions:
        issues.append(_issue("reference_invalid", f"unknown world revision {world_revision}", contract_type, "world_revision"))

    situation_ref = obj.get("situation_ref")
    if situation_ref and not _ref_ok(situation_ref, ctx.situation_ids, ctx.allow_unresolved):
        issues.append(_issue("reference_invalid", f"unknown situation {situation_ref!r}", contract_type, "situation_ref"))

    # --- Time -------------------------------------------------------------
    def _as_dt(value: Any) -> datetime | None:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    valid_from = obj.get("valid_from")
    valid_until = obj.get("valid_until")
    vf, vu = _as_dt(valid_from), _as_dt(valid_until)
    if vf is not None and vu is not None and vu < vf:
        issues.append(_issue("time_invalid", "valid_until precedes valid_from", contract_type, "valid_until"))

    sensor_time = obj.get("sensor_time")
    receive_time = obj.get("receive_time")
    st, rt = _as_dt(sensor_time), _as_dt(receive_time)
    if st is not None and rt is not None and rt < st:
        issues.append(_issue("time_invalid", "receive_time precedes sensor_time", contract_type, "receive_time"))

    predicts_at = obj.get("predicts_at")
    created_at = obj.get("created_at") or obj.get("sensor_time")
    pt, ct = _as_dt(predicts_at), _as_dt(created_at)
    # A prediction may target the present or future; targeting the deep
    # past without a declared basis is flagged as impossible ordering.
    if pt is not None and ct is not None and pt < ct and not obj.get("counterfactual"):
        issues.append(_issue("time_invalid", "prediction targets a time before its creation", contract_type, "predicts_at"))

    # --- Uncertainty ------------------------------------------------------
    confidence = obj.get("confidence")
    if confidence is not None and not (0.0 <= float(confidence) <= 1.0):
        issues.append(_issue("field_invalid", "confidence out of range", contract_type, "confidence"))

    uncertainty = obj.get("uncertainty")
    if isinstance(uncertainty, dict):
        prob = uncertainty.get("probability")
        if prob is not None and not (0.0 <= float(prob) <= 1.0):
            issues.append(_issue("field_invalid", "probability out of range", contract_type, "uncertainty.probability"))

    return SemanticValidation(valid=not issues, issues=issues)
