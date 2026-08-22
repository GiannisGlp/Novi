"""Common contract primitives for the typed cognition contract layer.

Implements doc 26 §4: reusable types shared by every canonical cognitive object —
SchemaVersion, ContractEnvelope, Identifier, Timestamp, ClockDomain, Provenance,
Uncertainty, PrivacyClassification, SpatialReference, LifecycleState,
CorrelationId, CausationId.

Pydantic v2 models form the typed boundary; JSON Schema is generated from them
for interoperability (doc 26 §2, §19). The canonical semantic authority remains
the Novi contract docs (`contracts/registry.json`, `docs/03-cognition/22`).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ---------------------------------------------------------------------------
# Versioning
# ---------------------------------------------------------------------------


class SchemaVersion(BaseModel):
    """SemVer version of a contract schema (doc 26 §22)."""

    model_config = ConfigDict(extra="forbid")

    major: int = Field(ge=0)
    minor: int = Field(ge=0)
    patch: int = Field(ge=0)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def parse(cls, value: str) -> "SchemaVersion":
        parts = value.split(".")
        if len(parts) != 3:
            raise ValueError(f"invalid schema version: {value!r}")
        return cls(major=int(parts[0]), minor=int(parts[1]), patch=int(parts[2]))

    @property
    def as_string(self) -> str:
        return str(self)


# ---------------------------------------------------------------------------
# Time
# ---------------------------------------------------------------------------

ClockDomain = Literal[
    "wall",
    "monotonic",
    "sensor",
    "simulation",
    "hardware",
    "unknown",
]

# Canonical time authority: docs/01-system-architecture/19_TIME_SYNCHRONIZATION_AND_CLOCK_SEMANTICS.md


class Timestamp(BaseModel):
    """A timestamp with explicit clock domain (doc 26 §4, §17 Time)."""

    model_config = ConfigDict(extra="forbid")

    value: datetime
    clock_domain: ClockDomain = "wall"
    source_ref: str | None = None  # sensor/system identifier that produced it

    @field_validator("value")
    @classmethod
    def _require_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware (ISO-8601 with offset)")
        return v


# ---------------------------------------------------------------------------
# Identity / correlation
# ---------------------------------------------------------------------------


class Identifier(BaseModel):
    """A stable internal identifier (doc 26 §10 — entities use stable IDs)."""

    model_config = ConfigDict(extra="forbid")

    value: str
    kind: str = "generic"  # e.g. entity, observation, evidence, world_revision


# Correlation and causation ids are plain strings with a clear contract.
CorrelationId = str
CausationId = str


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------


class Provenance(BaseModel):
    """Provenance chain for a derived object (doc 26 §18).

    Every derived object must be traceable: source → observation → evidence →
    derived object. For model-derived results, model ID/version/runtime must be
    recorded.
    """

    model_config = ConfigDict(extra="forbid")

    source: str = "system"  # subsystem/runtime that created the object
    source_observation_ids: list[str] = Field(default_factory=list)
    source_evidence_ids: list[str] = Field(default_factory=list)
    source_object_ids: list[str] = Field(default_factory=list)
    model_ref: str | None = None  # model identifier (e.g. "ollama:qwen3.8")
    model_version: str | None = None
    model_runtime: str | None = None  # e.g. "ollama", "torchvision:mps"
    transformation: str | None = None  # e.g. "identity-recognition", "fusion"
    created_at: datetime | None = None

    @property
    def is_complete_for_durable(self) -> bool:
        """Doc 26 §18: missing provenance must reject durable/decision objects."""
        return self.source != "system" or bool(self.source_observation_ids or self.source_evidence_ids)


# ---------------------------------------------------------------------------
# Uncertainty
# ---------------------------------------------------------------------------


class Uncertainty(BaseModel):
    """Explicit uncertainty (doc 26 §17 Uncertainty).

    Confidence and probability are separate fields; a confidence value must not
    be presented as a calibrated probability unless calibration status says so.
    """

    model_config = ConfigDict(extra="forbid")

    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    probability: float | None = Field(default=None, ge=0.0, le=1.0)
    calibrated: bool = False
    source: str = "model"
    note: str | None = None


# ---------------------------------------------------------------------------
# Privacy
# ---------------------------------------------------------------------------

PrivacyClassification = Literal[
    "none",
    "inherited",
    "field-classified",
    "required",
    "sensitive-biometric",
]


class PrivacyClassificationModel(BaseModel):
    """Privacy classification for a contract/field (canonical registry semantics)."""

    model_config = ConfigDict(extra="forbid")

    classification: PrivacyClassification = "inherited"
    sensitive_fields: list[str] = Field(default_factory=list)
    retention: str | None = None  # e.g. "session", "30d", "indefinite"


# ---------------------------------------------------------------------------
# Spatial reference
# ---------------------------------------------------------------------------


class SpatialReference(BaseModel):
    """Spatial reference for an entity or evidence (doc 26 §4; P4 spatial gap).

    Coordinate frames are explicit; the metric-vs-semantic link is preserved by
    carrying both a frame id and semantic location tags.
    """

    model_config = ConfigDict(extra="forbid")

    frame_id: str = Field(default="base")  # coordinate frame name
    pose: dict[str, Any] = Field(default_factory=dict)  # x/y/z/quaternion by frame convention
    semantic_location: list[str] = Field(default_factory=list)  # e.g. ["kitchen", "table"]
    occupancy: str | None = None  # e.g. "free", "occupied", "unknown"


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

LifecycleState = Literal[
    "created",
    "active",
    "superseded",
    "expired",
    "archived",
    "deleted",
]


# ---------------------------------------------------------------------------
# Envelope
# ---------------------------------------------------------------------------


class ContractEnvelope(BaseModel):
    """Metadata envelope for persisted or exchanged canonical objects (doc 26 §7).

    The envelope is metadata; it must not hide semantic fields.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: SchemaVersion
    contract_type: str
    id: str
    created_at: datetime
    updated_at: datetime | None = None
    source: str = "system"
    provenance: Provenance = Field(default_factory=Provenance)
    privacy: PrivacyClassificationModel = Field(default_factory=PrivacyClassificationModel)
    correlation_id: CorrelationId | None = None
    causation_id: CausationId | None = None


# ---------------------------------------------------------------------------
# Validation error contract (doc 26 §23)
# ---------------------------------------------------------------------------

ValidationErrorCategory = Literal[
    "schema_invalid",
    "field_invalid",
    "reference_invalid",
    "time_invalid",
    "coordinate_invalid",
    "provenance_missing",
    "privacy_invalid",
    "ownership_violation",
    "semantic_conflict",
    "unsupported_version",
]


class ValidationIssue(BaseModel):
    """One machine-readable validation failure (doc 26 §23)."""

    model_config = ConfigDict(extra="forbid")

    category: ValidationErrorCategory
    message: str
    contract_type: str | None = None
    schema_version: str | None = None
    field_path: str | None = None
    correlation_id: str | None = None


def utc_now() -> datetime:
    """Timezone-aware UTC now (single place for contract timestamps)."""
    return datetime.now().astimezone()
