"""SituationState and PersonContext contracts (doc 26 §12–13).

SituationState references a specific world revision and remains reconstructible
from the underlying WorldState and evidence. PersonContext is intentionally not
a full person profile — only the current information Cognition needs.
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

CONTRACT_TYPE_SITUATION = "SituationState"
CONTRACT_TYPE_PERSON = "PersonContext"
SCHEMA_VERSION = "1.0.0"


class SituationState(BaseModel):
    """A derived contextual interpretation over a world revision (doc 26 §12)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: SchemaVersion = Field(default_factory=lambda: SchemaVersion.parse(SCHEMA_VERSION))
    contract_type: str = CONTRACT_TYPE_SITUATION
    id: str
    world_revision: int  # must reference a valid world revision
    created_at: datetime
    participants: list[str] = Field(default_factory=list)  # entity ids
    likely_addressees: list[str] = Field(default_factory=list)
    current_activity: str | None = None
    salient_events: list[str] = Field(default_factory=list)
    social_context: dict[str, Any] = Field(default_factory=dict)
    goal_hypotheses: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    uncertainty: dict[str, Any] = Field(default_factory=dict)
    expires_at: datetime | None = None
    source: str = "cognition"
    provenance: Provenance = Field(default_factory=Provenance)
    privacy: PrivacyClassificationModel = Field(default_factory=PrivacyClassificationModel)
    correlation_id: str | None = None
    causation_id: str | None = None


class PersonContext(BaseModel):
    """Current person-specific context, not a complete profile (doc 26 §13)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: SchemaVersion = Field(default_factory=lambda: SchemaVersion.parse(SCHEMA_VERSION))
    contract_type: str = CONTRACT_TYPE_PERSON
    id: str
    person_ref: str  # stable entity id
    created_at: datetime
    presence_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    identity_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    attention_cues: list[str] = Field(default_factory=list)
    speech_cues: list[str] = Field(default_factory=list)
    addressee_cues: list[str] = Field(default_factory=list)
    relationship_category: str | None = None
    relationship_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    authorized_interaction: bool = False
    current_context: str | None = None
    source_evidence_ids: list[str] = Field(default_factory=list)
    source: str = "cognition"
    provenance: Provenance = Field(default_factory=Provenance)
    privacy: PrivacyClassificationModel = Field(default_factory=PrivacyClassificationModel)
    correlation_id: str | None = None
    causation_id: str | None = None
