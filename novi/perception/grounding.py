"""Typed Novi spatial-grounding contracts (plan Phase 1, Step 1.1).

Canonical language-conditioned perception surface. These types hide all
NVIDIA LocateAnything implementation details (special tokens, generation
parameters) from the rest of Novi: cognition speaks `SpatialQuery`, perception
answers `GroundingResult`, and no other component ever sees raw model text.

Coordinate policy (spec 02 §4): source coordinates are integer-normalized
[0, 1000] as emitted by the model; pixel coordinates are derived once, at
observation construction, via locate_anything_geometry — the source
representation is always preserved for provenance.

Observation kinds:
- `GroundingObservation` — a spatial region (box) matched to the query;
  may carry an optional point (model emits points only for point queries,
  which produce `PointObservation` instead).
- `PointObservation` — a single localized point.

All records are frozen dataclasses (immutability principle); validation is
fail-fast at construction.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, runtime_checkable

from novi.brain.io import CameraFrame
from novi.perception.locate_anything_geometry import (
    source_box_to_pixel_box,
    source_point_to_pixel,
    validate_source_box,
    validate_source_point,
)

SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


def sha256_hex(text: str) -> str:
    """Deterministic sha256 of a raw response, for audit without raw retention."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class SpatialInferenceMode(Enum):
    """Inference modes (plan Step 3.5 / spec 02 §5). Default: HYBRID."""

    FAST = "fast"
    SLOW = "slow"
    HYBRID = "hybrid"


class BackendState(Enum):
    """Explicit capability state (plan Step 0.3).

    Missing LocateAnything must never crash normal Novi startup: any state
    other than AVAILABLE makes the backend unusable and callers fall back
    to the fast detector / deterministic path.
    """

    AVAILABLE = "available"
    LOADING = "loading"
    UNAVAILABLE = "unavailable"
    UNSUPPORTED = "unsupported"
    DEPENDENCY_MISSING = "dependency_missing"
    MODEL_MISSING = "model_missing"
    FAILED = "failed"


@dataclass(frozen=True)
class SpatialQuery:
    """One language-conditioned spatial query against one frame (plan Step 1.1)."""

    text: str
    frame_id: str
    timestamp: str
    requested_output: str = "both"  # "box" | "point" | "both"
    max_results: int = 5
    latency_budget_ms: int | None = None
    risk_class: str = "routine"
    privacy_class: str = "low"
    preferred_mode: SpatialInferenceMode = SpatialInferenceMode.HYBRID
    candidate_labels: tuple[str, ...] = ()
    requester: str = "unknown"
    correlation_id: str | None = None

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("query text must be non-empty")
        if not self.frame_id:
            raise ValueError("query requires frame_id provenance")
        if self.requested_output not in ("box", "point", "both"):
            raise ValueError(f"requested_output must be box|point|both, got {self.requested_output!r}")
        if self.max_results < 1:
            raise ValueError(f"max_results must be >= 1, got {self.max_results}")
        if self.latency_budget_ms is not None and self.latency_budget_ms <= 0:
            raise ValueError(f"latency_budget_ms must be positive, got {self.latency_budget_ms}")
        if not isinstance(self.preferred_mode, SpatialInferenceMode):
            raise ValueError(f"preferred_mode must be a SpatialInferenceMode, got {self.preferred_mode!r}")
        if not self.risk_class:
            raise ValueError("risk_class must be non-empty")


@dataclass(frozen=True)
class SpatialInferencePolicy:
    """Bounded, typed policy for one grounding call (plan Step 3.5 / spec 02 §6).

    Generation parameters beyond these are owned by the backend, never exposed
    wholesale to cognition.
    """

    mode: SpatialInferenceMode = SpatialInferenceMode.HYBRID
    max_results: int = 5
    latency_budget_ms: int | None = None
    risk_class: str = "routine"

    def __post_init__(self) -> None:
        if not isinstance(self.mode, SpatialInferenceMode):
            raise ValueError(f"mode must be a SpatialInferenceMode, got {self.mode!r}")
        if self.max_results < 1:
            raise ValueError(f"max_results must be >= 1, got {self.max_results}")
        if self.latency_budget_ms is not None and self.latency_budget_ms <= 0:
            raise ValueError(f"latency_budget_ms must be positive, got {self.latency_budget_ms}")
        if not self.risk_class:
            raise ValueError("risk_class must be non-empty")


def _require_str(value: object, name: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string, got {value!r}")


def _require_confidence(value: object) -> None:
    if value is not None and not 0.0 <= value <= 1.0:  # type: ignore[operator]
        raise ValueError(f"confidence must be within [0, 1], got {value}")


def _require_latency(value: object) -> None:
    if value is not None and value < 0:  # type: ignore[operator]
        raise ValueError(f"latency_ms must be >= 0, got {value}")


@dataclass(frozen=True)
class GroundingObservation:
    """One validated spatial region matched to a query (plan Step 1.1).

    `source_box` (integer-normalized [0, 1000] corners) is the provenance
    truth; `pixel_box` is derived once via the canonical conversion.
    """

    observation_id: str
    query: str
    label: str
    source_box: tuple[int, int, int, int]
    image_width: int
    image_height: int
    model_id: str
    model_revision: str
    backend_version: str
    inference_mode: SpatialInferenceMode
    frame_id: str
    timestamp: str
    source_point: tuple[int, int] | None = None
    confidence: float | None = None
    fallback: bool = False
    fallback_reason: str | None = None
    latency_ms: float | None = None
    provenance: str = "locate_anything"
    pixel_box: tuple[int, int, int, int] = field(init=False)
    pixel_point: tuple[int, int] | None = field(init=False)

    def __post_init__(self) -> None:
        for name in ("observation_id", "label", "model_id", "model_revision", "frame_id"):
            _require_str(getattr(self, name), name)
        _require_str(self.query, "query")
        if not isinstance(self.inference_mode, SpatialInferenceMode):
            raise ValueError(f"inference_mode must be a SpatialInferenceMode, got {self.inference_mode!r}")
        validate_source_box(*self.source_box)
        if self.source_point is not None:
            validate_source_point(*self.source_point)
        _require_confidence(self.confidence)
        _require_latency(self.latency_ms)
        object.__setattr__(
            self,
            "pixel_box",
            source_box_to_pixel_box(*self.source_box, self.image_width, self.image_height),
        )
        object.__setattr__(
            self,
            "pixel_point",
            source_point_to_pixel(*self.source_point, self.image_width, self.image_height)
            if self.source_point is not None
            else None,
        )


@dataclass(frozen=True)
class PointObservation:
    """One validated localized point matched to a query (plan Step 1.1)."""

    observation_id: str
    query: str
    label: str
    source_point: tuple[int, int]
    image_width: int
    image_height: int
    model_id: str
    model_revision: str
    backend_version: str
    inference_mode: SpatialInferenceMode
    frame_id: str
    timestamp: str
    confidence: float | None = None
    fallback: bool = False
    fallback_reason: str | None = None
    latency_ms: float | None = None
    provenance: str = "locate_anything"
    pixel_point: tuple[int, int] = field(init=False)

    def __post_init__(self) -> None:
        for name in ("observation_id", "label", "model_id", "model_revision", "frame_id"):
            _require_str(getattr(self, name), name)
        _require_str(self.query, "query")
        if not isinstance(self.inference_mode, SpatialInferenceMode):
            raise ValueError(f"inference_mode must be a SpatialInferenceMode, got {self.inference_mode!r}")
        validate_source_point(*self.source_point)
        _require_confidence(self.confidence)
        _require_latency(self.latency_ms)
        object.__setattr__(
            self,
            "pixel_point",
            source_point_to_pixel(*self.source_point, self.image_width, self.image_height),
        )


@dataclass(frozen=True)
class GroundingResult:
    """Typed answer to one SpatialQuery (plan Step 1.1 / spec 02 §3).

    Fail-closed: when the backend cannot produce validated observations the
    result is `success=False` with a backend_status/validation_errors
    explanation — never an implicit "object absent" conclusion.
    """

    query: str
    observations: tuple[GroundingObservation | PointObservation, ...]
    backend_status: str
    model_id: str
    model_revision: str
    backend_version: str
    inference_mode: SpatialInferenceMode
    frame_id: str
    timestamp: str
    latency_ms: float | None
    success: bool
    validation_errors: tuple[str, ...] = ()
    fallback_count: int = 0
    raw_hash: str | None = None
    no_object: bool = False

    def __post_init__(self) -> None:
        _require_str(self.query, "query")
        if not isinstance(self.inference_mode, SpatialInferenceMode):
            raise ValueError(f"inference_mode must be a SpatialInferenceMode, got {self.inference_mode!r}")
        if self.validation_errors and self.success:
            raise ValueError("success cannot be True while validation_errors are present")
        if self.no_object and self.observations:
            raise ValueError("no_object cannot be True while observations are present")
        if self.raw_hash is not None and not SHA256_HEX.match(self.raw_hash):
            raise ValueError(f"raw_hash must be 64-hex sha256, got {self.raw_hash!r}")
        _require_latency(self.latency_ms)
        if self.fallback_count < 0:
            raise ValueError(f"fallback_count must be >= 0, got {self.fallback_count}")


@dataclass(frozen=True)
class SpatialBackendCapabilities:
    """Capability probe report (plan Step 3.3 / Step 0.3)."""

    state: BackendState
    model_id: str | None = None
    model_revision: str | None = None
    device: str | None = None
    modes: tuple[SpatialInferenceMode, ...] = (SpatialInferenceMode.HYBRID,)
    max_results_cap: int | None = None
    details: tuple[tuple[str, str], ...] = ()

    @property
    def usable(self) -> bool:
        return self.state is BackendState.AVAILABLE

    def mode_supported(self, mode: SpatialInferenceMode) -> bool:
        return mode in self.modes


@runtime_checkable
class SpatialPerceptionBackend(Protocol):
    """Novi-owned spatial perception surface (analysis doc 04 §3).

    Implementations may be LocateAnything (real or deterministic), a future
    alternative backend, or a remote NVIDIA worker — Novi only sees this.
    """

    def capabilities(self) -> SpatialBackendCapabilities: ...

    def ground(
        self,
        image: CameraFrame,
        query: SpatialQuery,
        policy: SpatialInferencePolicy,
    ) -> GroundingResult: ...

    def point(
        self,
        image: CameraFrame,
        query: SpatialQuery,
        policy: SpatialInferencePolicy,
    ) -> GroundingResult: ...

    def detect(
        self,
        image: CameraFrame,
        labels: tuple[str, ...],
        policy: SpatialInferencePolicy,
    ) -> GroundingResult: ...
