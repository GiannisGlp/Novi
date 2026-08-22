"""Observation contract (doc 26 §8).

An Observation preserves sensor/runtime provenance and avoids semantic
overclaiming: "camera detected pixels consistent with a person" — not
"Vano is present". The interpretation transformation belongs to evidence.
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
)

Modality = Literal[
    "camera",
    "audio",
    "depth",
    "lidar",
    "imu",
    "touch",
    "proprioception",
    "simulation",
    "text",
    "other",
]

CONTRACT_TYPE = "Observation"
SCHEMA_VERSION = "1.0.0"


class Observation(BaseModel):
    """A raw observation reference (doc 26 §8 minimum fields)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: SchemaVersion = Field(default_factory=lambda: SchemaVersion.parse(SCHEMA_VERSION))
    contract_type: str = CONTRACT_TYPE
    id: str
    modality: Modality
    sensor_id: str
    sensor_time: datetime
    receive_time: datetime
    clock_domain: str = "wall"  # canonical ClockDomain literal
    frame_id: str = "base"
    payload_ref: str  # reference to raw payload, not the payload itself
    quality: dict[str, Any] = Field(default_factory=dict)
    calibration_version: str | None = None
    source: str = "perception"
    provenance: Provenance = Field(default_factory=Provenance)
    privacy: PrivacyClassificationModel = Field(default_factory=PrivacyClassificationModel)
    spatial: SpatialReference | None = None
    correlation_id: str | None = None
    causation_id: str | None = None

    @property
    def created_at(self) -> datetime:
        return self.receive_time


class ObservationEnvelope(BaseModel):
    """Observation with the standard envelope (doc 26 §7)."""

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
    observation: Observation
