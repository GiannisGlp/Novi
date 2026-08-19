from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class Detection:
    label: str
    confidence: float
    bbox: tuple[float, float, float, float]
    provenance: dict[str, Any]


class ObjectDetector(Protocol):
    """Capability boundary for local and future NVIDIA object detectors."""

    def detect(self, frame: Any) -> tuple[Detection, ...]: ...


class DeterministicObjectDetector:
    """Test provider used by CI and deterministic Mac tests."""

    def __init__(self, detections: tuple[Detection, ...] = ()) -> None:
        self._detections = detections

    def detect(self, frame: Any) -> tuple[Detection, ...]:
        return self._detections
