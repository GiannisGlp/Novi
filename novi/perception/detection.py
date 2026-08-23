"""Detection contract + deterministic detector (doc 02 §1).

Real backends (SSDLite320 MobileNetV3 primary, RT-DETR/YOLO-nano
benchmark-gated) implement ObjectDetector; CI uses the scripted detector.
Bboxes are pixel-space (x, y, w, h); confidence floor filters noise at
the boundary so downstream tracking stays clean.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from novi.brain.io import CameraFrame


@dataclass(frozen=True)
class Detection:
    """One detected object in one frame (pixel bbox, provenance attached)."""

    label: str
    confidence: float
    bbox: tuple[int, int, int, int]  # x, y, w, h in pixels
    frame_id: str

    def __post_init__(self) -> None:
        if not self.frame_id:
            raise ValueError("Detection requires frame_id provenance")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within [0, 1]")
        if len(self.bbox) != 4 or not all(isinstance(v, int) and not isinstance(v, bool) for v in self.bbox):
            raise ValueError("bbox must be integer pixel-space (x, y, w, h)")
        x, y, w, h = self.bbox
        if w <= 0 or h <= 0 or x < 0 or y < 0:
            raise ValueError("bbox must be positive pixel-space (x, y, w, h)")


@runtime_checkable
class ObjectDetector(Protocol):
    def detect(self, frame: CameraFrame) -> list[Detection]: ...


class DeterministicObjectDetector:
    """Scripted detections keyed by frame id, with a confidence floor."""

    def __init__(
        self,
        *,
        scripted: dict[str, list[tuple[str, float, tuple[int, int, int, int]]]],
        confidence_floor: float = 0.60,
    ) -> None:
        self._scripted = scripted
        self._floor = confidence_floor

    def detect(self, frame: CameraFrame) -> list[Detection]:
        if not frame.frame_id:
            raise ValueError("frame must carry frame_id provenance")
        out: list[Detection] = []
        for label, conf, bbox in self._scripted.get(frame.frame_id, []):
            if conf < self._floor:
                continue
            out.append(Detection(label=label, confidence=conf, bbox=bbox, frame_id=frame.frame_id))
        return out
