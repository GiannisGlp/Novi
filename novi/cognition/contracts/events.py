"""CognitiveEvent contract (doc 26 §16).

Meaningful state transitions are observable as typed events carrying correlation
and causation identifiers — the foundation for deterministic replay and
cross-domain observability.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from novi.cognition.contracts.common import (
    PrivacyClassificationModel,
    Provenance,
    SchemaVersion,
)

CONTRACT_TYPE = "CognitiveEvent"
SCHEMA_VERSION = "1.0.0"

EventType = Literal[
    "observation_received",
    "evidence_created",
    "world_updated",
    "situation_updated",
    "prediction_created",
    "interpretation_created",
    "decision_recorded",
    "cognitive_error",
]


class CognitiveEvent(BaseModel):
    """An observable cognitive transition (doc 26 §16)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: SchemaVersion = Field(default_factory=lambda: SchemaVersion.parse(SCHEMA_VERSION))
    contract_type: str = CONTRACT_TYPE
    id: str
    event_type: EventType
    occurred_at: datetime
    source: str = "cognition"
    object_refs: list[str] = Field(default_factory=list)  # ids of created/updated objects
    detail: dict[str, object] = Field(default_factory=dict)
    correlation_id: str | None = None
    causation_id: str | None = None
    provenance: Provenance = Field(default_factory=Provenance)
    privacy: PrivacyClassificationModel = Field(default_factory=PrivacyClassificationModel)
