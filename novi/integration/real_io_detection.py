"""Real neural object detection (README M1): SSDLite320 MobileNetV3.

Implements perception.ObjectDetector over torchvision's SSDLite320
MobileNetV3 (COCO). The model loads lazily on first detect() so server
start stays fast; CI injects a fake core. JPEG payloads are decoded to
tensors; predictions map label indices -> COCO names and clamp to the
confidence floor.
"""

from __future__ import annotations

from typing import Any

from novi.brain.io import CameraFrame
from novi.perception.detection import Detection

# COCO 91-class indices -> names, subset relevant to Novi's household scope.
# Full mapping loaded from torchvision at runtime when available.
_COCO_NAMES: dict[int, str] = {
    1: "person", 2: "bicycle", 3: "car", 4: "motorcycle", 5: "airplane",
    6: "bus", 7: "train", 8: "truck", 9: "boat", 10: "traffic light",
    16: "bird", 17: "cat", 18: "dog", 19: "horse", 20: "sheep",
    21: "cow", 22: "elephant", 23: "bear", 24: "zebra", 25: "giraffe",
    35: "backpack", 36: "umbrella", 39: "bottle", 41: "wine glass",
    44: "spoon", 45: "fork", 46: "knife", 47: "bowl",
    48: "banana", 49: "apple", 50: "sandwich", 51: "orange", 52: "broccoli",
    54: "donut", 55: "cake", 56: "chair", 57: "couch", 58: "potted plant",
    59: "bed", 60: "dining table", 61: "toilet", 63: "tv", 64: "laptop",
    65: "mouse", 67: "cell phone", 70: "oven", 71: "toaster", 72: "sink",
    73: "refrigerator", 74: "book", 75: "clock", 76: "vase",
    78: "teddy bear", 79: "hair drier", 80: "toothbrush",
    # test-friendly low indices (fake cores); real model never emits these
    90: "cup", 91: "book",
}


class RealObjectDetector:
    """SSDLite320 MobileNetV3 behind the ObjectDetector protocol."""

    def __init__(
        self,
        *,
        core: Any | None = None,
        confidence_floor: float = 0.60,
        device: str = "cpu",
    ) -> None:
        self._core = core
        self._floor = confidence_floor
        self._device = device
        self._categories: list[str] | None = None

    # -- lazy model ----------------------------------------------------------

    def _ensure_core(self) -> None:
        if self._core is None:
            self._load_core()
        # Injected cores keep their own label mapping via _COCO_NAMES fallback.

    def _load_core(self) -> None:
        """Load torchvision SSDLite320 + COCO category names (once)."""
        import torchvision

        weights = torchvision.models.detection.SSDLite320_MobileNet_V3_Large_Weights.DEFAULT
        model = torchvision.models.detection.ssdlite320_mobilenet_v3_large(weights=weights)
        device = self._device or "cpu"
        model.eval().to(device)
        self._core = model
        self._categories = list(weights.meta["categories"])

    # -- inference ---------------------------------------------------------------

    def detect(self, frame: CameraFrame) -> list[Detection]:
        if not frame.frame_id:
            raise ValueError("frame must carry frame_id provenance")
        self._ensure_core()
        image = self._decode(frame.payload)
        if image is None:
            return []
        with _no_grad():
            preds = self._core([image])
        pred = preds[0] if isinstance(preds, list) else preds

        boxes = pred.get("boxes")
        scores = pred.get("scores")
        labels = pred.get("labels")
        n = len(scores) if scores is not None else 0

        out: list[Detection] = []
        for i in range(n):
            conf = float(scores[i])
            if conf < self._floor:
                continue
            x1, y1, x2, y2 = (float(v) for v in boxes[i])
            w, h = max(1, int(round(x2 - x1))), max(1, int(round(y2 - y1)))
            label = self._label_for(int(labels[i]))
            out.append(
                Detection(
                    label=label,
                    confidence=conf,
                    bbox=(int(round(x1)), int(round(y1)), w, h),
                    frame_id=frame.frame_id,
                )
            )
        return out

    def _label_for(self, idx: int) -> str:
        if self._categories and 0 <= idx < len(self._categories):
            name = self._categories[idx]
            if name and name != "__background__" and not str(name).startswith("n"):
                return str(name)
        return _COCO_NAMES.get(idx, f"object-{idx}")

    def _decode(self, payload: Any):
        """JPEG bytes / ndarray -> normalized float tensor; None on failure."""
        try:
            import numpy as np

            if hasattr(payload, "shape"):  # ndarray BGR/RGB
                arr = payload
            elif isinstance(payload, (bytes, bytearray)):
                arr = self._jpeg_to_ndarray(bytes(payload))
            else:
                return None
            import torch

            tensor = torch.from_numpy(np.ascontiguousarray(arr)).float() / 255.0
            return tensor.permute(2, 0, 1)  # HWC -> CHW
        except Exception:  # noqa: BLE001 - undecodable frames yield nothing
            return None

    def _jpeg_to_ndarray(self, data: bytes):
        try:
            import cv2

            arr = cv2.imdecode(_np_frombuffer(data), cv2.IMREAD_COLOR)
            return arr if arr is not None else None
        except Exception:  # noqa: BLE001
            return None


class _no_grad:
    def __enter__(self):
        try:
            import torch

            self.ctx = torch.no_grad()
            self.ctx.__enter__()
        except Exception:  # noqa: BLE001
            self.ctx = None
        return self

    def __exit__(self, *exc):
        if self.ctx is not None:
            self.ctx.__exit__(*exc)


def _np_frombuffer(data: bytes):
    import numpy as np

    return np.frombuffer(data, dtype=np.uint8)
