from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol


class SpecialistModelError(RuntimeError):
    pass


@dataclass(frozen=True)
class Detection:
    label: str
    confidence: float
    x_min: float
    y_min: float
    x_max: float
    y_max: float


@dataclass(frozen=True)
class ObjectEvidence:
    model_id: str
    frame_id: str
    detections: tuple[Detection, ...]
    source_timestamp: str
    provenance: Mapping[str, Any]


@dataclass(frozen=True)
class DepthEvidence:
    model_id: str
    frame_id: str
    width: int
    height: int
    disparity: tuple[float, ...]
    source_timestamp: str
    provenance: Mapping[str, Any]


class DetectorBackend(Protocol):
    def load(self) -> None: ...
    def unload(self) -> None: ...
    def health(self) -> str: ...
    def detect(self, image: Any) -> tuple[Detection, ...]: ...


class DepthBackend(Protocol):
    def load(self) -> None: ...
    def unload(self) -> None: ...
    def health(self) -> str: ...
    def disparity(self, left_image: Any, right_image: Any) -> tuple[int, int, tuple[float, ...]]: ...


class DeterministicRTDETRBackend:
    """CI backend; it does not execute RT-DETR or any neural network."""

    def __init__(self) -> None:
        self._loaded = False

    def load(self) -> None:
        self._loaded = True

    def unload(self) -> None:
        self._loaded = False

    def health(self) -> str:
        return "READY" if self._loaded else "UNLOADED"

    def detect(self, image: Any) -> tuple[Detection, ...]:
        if not self._loaded:
            raise SpecialistModelError("detector_not_loaded")
        if image is None:
            return ()
        return (Detection("synthetic_object", 0.99, 0.10, 0.10, 0.50, 0.50),)


class DeterministicStereoBackend:
    """CI backend; it does not execute ESS or FoundationStereo."""

    def __init__(self) -> None:
        self._loaded = False

    def load(self) -> None:
        self._loaded = True

    def unload(self) -> None:
        self._loaded = False

    def health(self) -> str:
        return "READY" if self._loaded else "UNLOADED"

    def disparity(self, left_image: Any, right_image: Any) -> tuple[int, int, tuple[float, ...]]:
        if not self._loaded:
            raise SpecialistModelError("depth_model_not_loaded")
        if left_image is None or right_image is None:
            raise SpecialistModelError("stereo_input_missing")
        return 2, 2, (1.0, 1.0, 1.0, 1.0)


class RTDETRAdapter:
    """Novi adapter for a future real RT-DETR/TensorRT backend."""

    model_id = "rtdetr"

    def __init__(self, backend: DetectorBackend | None = None) -> None:
        self.backend = backend or DeterministicRTDETRBackend()

    def load(self) -> None:
        self.backend.load()

    def unload(self) -> None:
        self.backend.unload()

    def health(self) -> str:
        return self.backend.health()

    def infer(self, image: Any, *, frame_id: str, source_timestamp: str) -> ObjectEvidence:
        detections = self.backend.detect(image)
        for detection in detections:
            self._validate_detection(detection)
        return ObjectEvidence(
            model_id=self.model_id,
            frame_id=frame_id,
            detections=detections,
            source_timestamp=source_timestamp,
            provenance={"backend": type(self.backend).__name__, "model_family": "RT-DETR"},
        )

    @staticmethod
    def _validate_detection(detection: Detection) -> None:
        if not 0.0 <= detection.confidence <= 1.0:
            raise SpecialistModelError("invalid_detection_confidence")
        coordinates = (detection.x_min, detection.y_min, detection.x_max, detection.y_max)
        if any(not 0.0 <= value <= 1.0 for value in coordinates):
            raise SpecialistModelError("invalid_detection_coordinates")
        if detection.x_min >= detection.x_max or detection.y_min >= detection.y_max:
            raise SpecialistModelError("invalid_detection_box")


class StereoDepthAdapter:
    """Shared Novi boundary for ESS and FoundationStereo candidates."""

    def __init__(self, model_id: str = "ess", backend: DepthBackend | None = None) -> None:
        if model_id not in {"ess", "foundationstereo"}:
            raise ValueError("unsupported_depth_model")
        self.model_id = model_id
        self.backend = backend or DeterministicStereoBackend()

    def load(self) -> None:
        self.backend.load()

    def unload(self) -> None:
        self.backend.unload()

    def health(self) -> str:
        return self.backend.health()

    def infer(self, left_image: Any, right_image: Any, *, frame_id: str, source_timestamp: str) -> DepthEvidence:
        width, height, disparity = self.backend.disparity(left_image, right_image)
        if width <= 0 or height <= 0 or len(disparity) != width * height:
            raise SpecialistModelError("invalid_disparity_shape")
        if any(value < 0 for value in disparity):
            raise SpecialistModelError("invalid_disparity_value")
        return DepthEvidence(
            model_id=self.model_id,
            frame_id=frame_id,
            width=width,
            height=height,
            disparity=disparity,
            source_timestamp=source_timestamp,
            provenance={"backend": type(self.backend).__name__, "model_family": self.model_id},
        )
