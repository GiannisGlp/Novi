"""Evidence contract (doc 26 §9).

Evidence is a bounded interpreted claim: it may say "camera evidence consistent
with a person", never silently "Vano is present" — that requires identity
interpretation and remains distinguishable. Confidence and probability are
separate fields.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from novi.cognition.contracts.common import (
    PrivacyClassificationModel,
    Provenance,
    SchemaVersion,
    Uncertainty,
)

CONTRACT_TYPE = "Evidence"
SCHEMA_VERSION = "1.0.0"

EvidenceType = Literal[
    "presence",
    "identity_hypothesis",
    "attribute",
    "spatial",
    "activity",
    "relationship_hypothesis",
    "intent_hypothesis",
    "anomaly",
    "generic",
]


class Evidence(BaseModel):
    """A bounded interpreted claim derived from observations (doc 26 §9)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: SchemaVersion = Field(default_factory=lambda: SchemaVersion.parse(SCHEMA_VERSION))
    contract_type: str = CONTRACT_TYPE
    id: str
    type: EvidenceType = "generic"
    subject_ref: str  # entity/object the claim is about
    attributes: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)
    uncertainty: Uncertainty = Field(default_factory=Uncertainty)
    source_observation_ids: list[str] = Field(default_factory=list)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    source: str = "cognition"
    provenance: Provenance = Field(default_factory=Provenance)
    privacy: PrivacyClassificationModel = Field(default_factory=PrivacyClassificationModel)
    correlation_id: str | None = None
    causation_id: str | None = None

    @property
    def is_active(self, now: datetime | None = None) -> bool:
        now = now or datetime.now().astimezone()
        if self.valid_from is not None and now < self.valid_from:
            return False
        return not (self.valid_until is not None and now > self.valid_until)


class EvidenceEnvelope(BaseModel):
    """Evidence with the standard envelope (doc 26 §7)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: SchemaVersion
    contract_type: str = CONTRACT_TYPE
    id: str
    created_at: datetime
    updated_at: datetime | None = None
    source: str
    provenance: Provenance
    privacy: PrivacyClassificationModel
    correlation_id: str | None = None
    causation_id: str | None = None
    evidence: Evidence
