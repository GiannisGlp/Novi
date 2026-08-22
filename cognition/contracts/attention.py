"""AttentionCandidate contract (doc 26 §14).

Attention candidates are proposals for downstream autonomy — NOT commands.
They may never grant authorization or directly trigger an actuator.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from cognition.contracts.common import (
    PrivacyClassificationModel,
    Provenance,
    SchemaVersion,
    Uncertainty,
)

CONTRACT_TYPE = "AttentionCandidate"
SCHEMA_VERSION = "1.0.0"


class AttentionCandidate(BaseModel):
    """A candidate salience proposal from Cognition to Autonomy (doc 26 §14)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: SchemaVersion = Field(default_factory=lambda: SchemaVersion.parse(SCHEMA_VERSION))
    contract_type: str = CONTRACT_TYPE
    id: str
    created_at: datetime
    target_ref: str  # entity/evidence/situation the candidate refers to
    salience_score: float = Field(ge=0.0, le=1.0)
    reason: str
    suggested_focus: str | None = None  # e.g. "inspect", "track", "listen"
    source_event_ids: list[str] = Field(default_factory=list)
    uncertainty: Uncertainty = Field(default_factory=Uncertainty)
    source: str = "cognition"
    provenance: Provenance = Field(default_factory=Provenance)
    privacy: PrivacyClassificationModel = Field(default_factory=PrivacyClassificationModel)
    correlation_id: str | None = None
    causation_id: str | None = None

    # Ownership invariant: must never become an authorization grant or an
    # actuator command carrying authority. Autonomy decides; Policy permits.
    @property
    def is_proposal_only(self) -> bool:
        return True
