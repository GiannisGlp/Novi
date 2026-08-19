from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol


class PerceptionError(RuntimeError):
    pass


@dataclass(frozen=True)
class Detection:
    label: str
    confidence: float
    bbox_xyxy: tuple[float, float, float, float]


@dataclass(frozen=True)
class DepthEstimate:
    width: int
    height: int
    metric: str
    confidence: float
    values: tuple[float, ...]


@dataclass(frozen=True)
class SegmentationResult:
    width: int
    height: int
    labels: tuple[int, ...]
    confidence: float


@dataclass(frozen=True)
class PerceptionEvidence:
    sensor_id: str
    frame_id: str
    timestamp: str
    detections: tuple[Detection, ...] = ()
    depth: DepthEstimate | None = None
    segmentation: SegmentationResult | None = None
    provenance: Mapping[str, Any] = field(default_factory=dict)


class PerceptionBackend(Protocol):
    def detect(self, frame: Any) -> tuple[Detection, ...]: ...
    def depth(self, frame: Any) -> DepthEstimate | None: ...
    def segment(self, frame: Any) -> SegmentationResult | None: ...


class DeterministicPerceptionBackend:
    """Contract-test backend. It does not perform learned inference."""

    def detect(self, frame: Any) -> tuple[Detection, ...]:
        return ()

    def depth(self, frame: Any) -> DepthEstimate | None:
        return None

    def segment(self, frame: Any) -> SegmentationResult | None:
        return None


class SpecialistPerception:
    """Hardware/backend-neutral specialist perception boundary."""

    def __init__(self, backend: PerceptionBackend | None = None) -> None:
        self.backend = backend or DeterministicPerceptionBackend()

    def process(
        self,
        *,
        sensor_id: str,
        frame_id: str,
        timestamp: str,
        frame: Any,
    ) -> PerceptionEvidence:
        detections = self.backend.detect(frame)
        for detection in detections:
            if not 0.0 <= detection.confidence <= 1.0:
                raise PerceptionError("invalid_detection_confidence")
            x1, y1, x2, y2 = detection.bbox_xyxy
            if x2 < x1 or y2 < y1:
                raise PerceptionError("invalid_detection_bbox")

        depth = self.backend.depth(frame)
        if depth is not None and not 0.0 <= depth.confidence <= 1.0:
            raise PerceptionError("invalid_depth_confidence")

        segmentation = self.backend.segment(frame)
        if segmentation is not None and not 0.0 <= segmentation.confidence <= 1.0:
            raise PerceptionError("invalid_segmentation_confidence")

        return PerceptionEvidence(
            sensor_id=sensor_id,
            frame_id=frame_id,
            timestamp=timestamp,
            detections=tuple(detections),
            depth=depth,
            segmentation=segmentation,
            provenance={
                "backend": type(self.backend).__name__,
                "source": "specialist_perception",
            },
        )
