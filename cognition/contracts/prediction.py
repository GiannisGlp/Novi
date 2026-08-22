"""Prediction contract (doc 26 §14; P1 gap 12).

A future-state hypothesis. Predictions never overwrite observed state; they are
epistemic proposals until verified.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from cognition.contracts.common import (
    PrivacyClassificationModel,
    Provenance,
    SchemaVersion,
    Uncertainty,
)

CONTRACT_TYPE = "Prediction"
SCHEMA_VERSION = "1.0.0"


class Prediction(BaseModel):
    """A future-state hypothesis from Cognition (doc 26 §14)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: SchemaVersion = Field(default_factory=lambda: SchemaVersion.parse(SCHEMA_VERSION))
    contract_type: str = CONTRACT_TYPE
    id: str
    created_at: datetime
    predicts_at: datetime  # the time the prediction applies to
    subject_ref: str  # entity/state the prediction is about
    predicted_attribute: str  # e.g. "position", "intent", "activity"
    predicted_value: Any = None
    confidence: float = Field(ge=0.0, le=1.0)
    uncertainty: Uncertainty = Field(default_factory=Uncertainty)
    basis: str  # e.g. "observed_pattern", "model_output", "simulation"
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    counterfactual: bool = False
    source: str = "cognition"
    provenance: Provenance = Field(default_factory=Provenance)
    privacy: PrivacyClassificationModel = Field(default_factory=PrivacyClassificationModel)
    correlation_id: str | None = None
    causation_id: str | None = None
