"""WorldState contract (doc 26 §11).

WorldState is revisioned; a consumer can record which world revision it used.
A new revision does not erase historical evidence — that belongs to Memory.
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
from novi.cognition.contracts.entity import Entity, Relation

CONTRACT_TYPE = "WorldState"
SCHEMA_VERSION = "1.0.0"


class WorldState(BaseModel):
    """A revisioned semantic world state (doc 26 §11)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: SchemaVersion = Field(default_factory=lambda: SchemaVersion.parse(SCHEMA_VERSION))
    contract_type: str = CONTRACT_TYPE
    id: str
    revision: int = Field(ge=0)
    created_at: datetime
    entities: list[Entity] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)
    active_events: list[str] = Field(default_factory=list)
    spatial_state: dict[str, object] = Field(default_factory=dict)
    temporal_context: dict[str, object] = Field(default_factory=dict)
    uncertainty_summary: Uncertainty = Field(default_factory=Uncertainty)
    source_event_ids: list[str] = Field(default_factory=list)
    source: str = "cognition"
    provenance: Provenance = Field(default_factory=Provenance)
    privacy: PrivacyClassificationModel = Field(default_factory=PrivacyClassificationModel)
    correlation_id: str | None = None
    causation_id: str | None = None

    def entity_by_id(self, entity_id: str) -> Entity | None:
        for entity in self.entities:
            if entity.id == entity_id:
                return entity
        return None
