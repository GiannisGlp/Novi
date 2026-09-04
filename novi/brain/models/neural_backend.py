from __future__ import annotations

from typing import Any

from novi.brain.b2_perception import DepthEstimate, SegmentationResult
from novi.brain.b2_perception import Detection as BrainDetection

from .object_detection import Detection as MacDetection
from .torchvision_detector import TorchvisionSSDLiteDetector


class NeuralPerceptionBackend:
    """Bridges a real Mac neural object detector into the canonical Brain
    ``PerceptionBackend`` capability boundary.

    ``TorchvisionSSDLiteDetector`` emits ``brain.models.Detection`` objects
    (``bbox``), while ``SpecialistPerception`` consumes ``brain.b2_perception.Detection``
    (``bbox_xyxy``). This adapter converts between the two so real neural output
    flows through the exact same perception → world-state path as the deterministic
    fixture backend.

    Depth and segmentation are intentionally unsupported here (M1 is detection-only);
    they return ``None`` so the perception contract is preserved.
    """

    def __init__(self, detector: TorchvisionSSDLiteDetector | None = None, *, confidence_threshold: float = 0.40, device: str | None = None) -> None:
        self._detector = detector or TorchvisionSSDLiteDetector(confidence_threshold=confidence_threshold, device=device)

    @property
    def detector(self) -> TorchvisionSSDLiteDetector:
        return self._detector

    def detect(self, frame: Any) -> tuple[BrainDetection, ...]:
        try:
            mac_detections: tuple[MacDetection, ...] = self._detector.detect(frame)
        except Exception:  # noqa: BLE001 - a bad frame degrades to no detections, never crashes step()
            return ()
        return tuple(
            BrainDetection(label=d.label, confidence=d.confidence, bbox_xyxy=d.bbox)
            for d in mac_detections
        )

    def depth(self, frame: Any) -> DepthEstimate | None:
        return None

    def segment(self, frame: Any) -> SegmentationResult | None:
        return None
