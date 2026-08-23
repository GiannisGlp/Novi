"""CognitiveDecisionRecord contract (doc 26 §15).

The record captures Cognition's structured interpretation/recommendation — it is
deliberately different from an ActionProposal (owned by Autonomy, subsequently
governed by Policy/Safety). Cognition never creates an authorization grant.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from novi.cognition.contracts.common import (
    PrivacyClassificationModel,
    Provenance,
    SchemaVersion,
)

CONTRACT_TYPE = "CognitiveDecisionRecord"
SCHEMA_VERSION = "1.0.0"


class CognitiveDecisionRecord(BaseModel):
    """A structured cognitive interpretation/recommendation (doc 26 §15)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: SchemaVersion = Field(default_factory=lambda: SchemaVersion.parse(SCHEMA_VERSION))
    contract_type: str = CONTRACT_TYPE
    id: str
    created_at: datetime
    situation_ref: str  # valid situation id
    interpretation: str
    alternatives: list[str] = Field(default_factory=list)
    uncertainty: dict[str, Any] = Field(default_factory=dict)
    rationale_refs: list[str] = Field(default_factory=list)
    recommended_next_states: list[str] = Field(default_factory=list)
    model_refs: list[str] = Field(default_factory=list)
    policy_constraints_observed: list[str] = Field(default_factory=list)
    source: str = "cognition"
    provenance: Provenance = Field(default_factory=Provenance)
    privacy: PrivacyClassificationModel = Field(default_factory=PrivacyClassificationModel)
    correlation_id: str | None = None
    causation_id: str | None = None

    # Ownership invariant (doc 26 §17, §21): this record is an interpretation,
    # never an authorization grant and never a physical action command.
    @property
    def is_interpretation_only(self) -> bool:
        return True
