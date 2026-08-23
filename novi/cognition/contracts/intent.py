"""IntentHypothesis contract (doc 26 §14).

An uncertain interpretation of another actor's intent. A proposal, not a
command — it never grants authorization or directly triggers an actuator.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from novi.cognition.contracts.common import (
    PrivacyClassificationModel,
    Provenance,
    SchemaVersion,
    Uncertainty,
)

CONTRACT_TYPE = "IntentHypothesis"
SCHEMA_VERSION = "1.0.0"


class IntentHypothesis(BaseModel):
    """An uncertain interpretation of intent (doc 26 §14)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: SchemaVersion = Field(default_factory=lambda: SchemaVersion.parse(SCHEMA_VERSION))
    contract_type: str = CONTRACT_TYPE
    id: str
    created_at: datetime
    actor_ref: str  # entity whose intent is hypothesized
    intent: str  # e.g. "requesting_object", "greeting", "leaving"
    confidence: float = Field(ge=0.0, le=1.0)
    uncertainty: Uncertainty = Field(default_factory=Uncertainty)
    alternatives: list[str] = Field(default_factory=list)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    source: str = "cognition"
    provenance: Provenance = Field(default_factory=Provenance)
    privacy: PrivacyClassificationModel = Field(default_factory=PrivacyClassificationModel)
    correlation_id: str | None = None
    causation_id: str | None = None
