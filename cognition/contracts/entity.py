"""Entity and Relation contracts (doc 26 §10).

Entities use stable internal IDs independent of model-generated names; relations
reference entity IDs rather than embedding duplicate entity descriptions.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from cognition.contracts.common import (
    PrivacyClassificationModel,
    Provenance,
    SchemaVersion,
    SpatialReference,
    Uncertainty,
)

CONTRACT_TYPE_ENTITY = "Entity"
CONTRACT_TYPE_RELATION = "Relation"
SCHEMA_VERSION = "1.0.0"

EpistemicStatus = Literal[
    "OBSERVED",
    "INFERRED",
    "PREDICTED",
    "SIMULATED",
    "VERIFIED",
    "UNKNOWN",
]

EntityKind = Literal[
    "person",
    "robot",
    "object",
    "place",
    "group",
    "concept",
    "unknown",
]


class Entity(BaseModel):
    """A tracked world entity with epistemic status (doc 26 §10)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: SchemaVersion = Field(default_factory=lambda: SchemaVersion.parse(SCHEMA_VERSION))
    contract_type: str = CONTRACT_TYPE_ENTITY
    id: str  # stable internal id, independent of model-generated names
    kind: EntityKind = "unknown"
    name: str | None = None  # best-known label; may change without identity change
    attributes: dict[str, Any] = Field(default_factory=dict)
    epistemic_status: EpistemicStatus = "OBSERVED"
    uncertainty: Uncertainty = Field(default_factory=Uncertainty)
    spatial: SpatialReference | None = None
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    source: str = "cognition"
    provenance: Provenance = Field(default_factory=Provenance)
    privacy: PrivacyClassificationModel = Field(default_factory=PrivacyClassificationModel)
    correlation_id: str | None = None
    causation_id: str | None = None


class Relation(BaseModel):
    """A typed relationship between entities (doc 26 §10)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: SchemaVersion = Field(default_factory=lambda: SchemaVersion.parse(SCHEMA_VERSION))
    contract_type: str = CONTRACT_TYPE_RELATION
    id: str
    subject_ref: str  # entity id
    predicate: str  # e.g. "looking_at", "near", "contains"
    object_ref: str  # entity id
    attributes: dict[str, Any] = Field(default_factory=dict)
    epistemic_status: EpistemicStatus = "OBSERVED"
    uncertainty: Uncertainty = Field(default_factory=Uncertainty)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    source: str = "cognition"
    provenance: Provenance = Field(default_factory=Provenance)
    privacy: PrivacyClassificationModel = Field(default_factory=PrivacyClassificationModel)
    correlation_id: str | None = None
    causation_id: str | None = None
