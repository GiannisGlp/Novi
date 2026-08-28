"""Real perception backends for Mac (doc 02 §1-2 concrete providers).

Objects : torchvision SSDLite320-MobileNetV3 (MPS when available) adapted to
          the perception ``ObjectDetector`` contract (pixel bbox + frame_id).
Faces   : OpenCV YuNet (detection) + SFace (128-d embedding), models fetched
          once into a local cache dir and loaded lazily. Everything degrades
          honestly: construction returns None / embed returns None when deps,
          models, or hardware are absent — CI stays deterministic.

No cloud: every model runs locally on the Mac (Jetson-plausible later).
"""

from __future__ import annotations

import math
import os
import threading
import urllib.request
from pathlib import Path
from typing import Any

from novi.brain.io import CameraFrame

# ---------------------------------------------------------------------------
# Objects — SSDLite320-MobileNetV3 -> perception.Detection
# ---------------------------------------------------------------------------


class TorchvisionPerceptionDetector:
    """Adapts brain.models.TorchvisionSSDLiteDetector to perception contract.

    SSD emits float (x1, y1, x2, y2); perception.Detection wants integer
    pixel-space (x, y, w, h) plus frame_id provenance — converted here so the
    pipeline/tracker stay unchanged.
    """

    def __init__(self, *, confidence_threshold: float = 0.45, device: str | None = None) -> None:
        from novi.brain.models.torchvision_detector import TorchvisionSSDLiteDetector

        self._impl = TorchvisionSSDLiteDetector(
            confidence_threshold=confidence_threshold, device=device
        )

    @property
    def device(self) -> str:
        return self._impl.device

    @property
    def model_id(self) -> str:
        return self._impl.model_id

    def detect(self, frame: CameraFrame) -> list[Any]:
        import cv2
        import numpy as np

        from novi.perception.detection import Detection

        np_array = self._decode(frame.payload)
        if np_array is None:
            return []
        rgb = cv2.cvtColor(np_array, cv2.COLOR_BGR2RGB)
        results = self._impl.detect(rgb)
        detections: list[Detection] = []
        for item in results:
            x1, y1, x2, y2 = (float(v) for v in item.bbox)
            x, y = max(0, int(x1)), max(0, int(y1))
            w, h = max(0, int(x2 - x1)), max(0, int(y2 - y1))
            if w == 0 or h == 0:
                continue
            detections.append(
                Detection(
                    label=str(item.label),
                    confidence=float(item.confidence),
                    bbox=(x, y, w, h),
                    frame_id=frame.frame_id,
                )
            )
        return detections

    @staticmethod
    def _decode(payload: Any):
        """JPEG bytes / ndarray / ndarray-in-frame -> BGR ndarray, else None."""
        try:
            import cv2
            import numpy as np

            if isinstance(payload, (bytes, bytearray)):
                return cv2.imdecode(np.frombuffer(payload, dtype=np.uint8), cv2.IMREAD_COLOR)
            if isinstance(payload, np.ndarray) and payload.ndim == 3:
                return payload
        except Exception:  # noqa: BLE001 - decode failure means no detections
            return None
        return None


# ---------------------------------------------------------------------------
# Faces — OpenCV YuNet (detect) + SFace (embedding)
# ---------------------------------------------------------------------------

_YUNET_URL = (
    "https://github.com/opencv/opencv_zoo/raw/main/models/"
    "face_detection_yunet/face_detection_yunet_2023mar.onnx"
)
_SFACE_URL = (
    "https://github.com/opencv/opencv_zoo/raw/main/models/"
    "face_recognition_sface/face_recognition_sface_2021dec.onnx"
)


def default_model_dir() -> Path:
    base = os.environ.get("NOVI_MODEL_DIR")
    root = Path(base) if base else Path.home() / ".cache" / "novi" / "models"
    root.mkdir(parents=True, exist_ok=True)
    return root


class OpenCVFaceEmbedder:
    """Detects the largest face and returns its SFace 128-d embedding.

    Lazy: models are downloaded on first successful use (not import), so
    importing this module never touches the network. ``available`` reports
    whether the backend is usable; ``embed`` returns (None, None) otherwise.
    """

    def __init__(
        self,
        *,
        model_dir: Path | None = None,
        det_score_threshold: float = 0.60,
    ) -> None:
        self.model_dir = Path(model_dir) if model_dir else default_model_dir()
        self.det_score_threshold = det_score_threshold
        self._yunet_path = self.model_dir / "face_detection_yunet_2023mar.onnx"
        self._sface_path = self.model_dir / "face_recognition_sface_2021dec.onnx"
        self._detector: Any | None = None
        self._recognizer: Any | None = None
        self._failed = False
        self._lock = threading.Lock()

    # -- availability ---------------------------------------------------------

    @property
    def available(self) -> bool:
        try:
            import cv2  # noqa: F401
        except Exception:  # noqa: BLE001
            return False
        return not self._failed and self._ensure()

    def _ensure(self) -> bool:
        with self._lock:
            if self._detector is not None and self._recognizer is not None:
                return True
            if self._failed:
                return False
            try:
                if not self._yunet_path.exists() or not self._sface_path.exists():
                    self._download(self._yunet_path, _YUNET_URL)
                    self._download(self._sface_path, _SFACE_URL)
                import cv2

                self._recognizer = cv2.FaceRecognizerSF.create(
                    str(self._sface_path), ""
                )
                self._detector = cv2.FaceDetectorYN.create(
                    str(self._yunet_path),
                    "",
                    (320, 240),
                    score_threshold=self.det_score_threshold,
                )
                return True
            except Exception:  # noqa: BLE001 - offline/no-models => honest degrade
                self._failed = True
                self._detector = None
                self._recognizer = None
                return False

    @staticmethod
    def _download(dest: Path, url: str) -> None:
        tmp = dest.with_suffix(".part")
        urllib.request.urlretrieve(url, tmp)  # noqa: S310 - fixed https URLs
        tmp.replace(dest)

    # -- inference --------------------------------------------------------------

    def embed(self, payload: bytes | bytearray) -> tuple[list[float] | None, tuple[int, int, int, int] | None]:
        """JPEG/PNG bytes -> (128-d embedding, (x, y, w, h)) for the largest face."""
        if not self.available:
            return None, None
        try:
            import cv2
            import numpy as np

            img = cv2.imdecode(np.frombuffer(payload, dtype=np.uint8), cv2.IMREAD_COLOR)
            if img is None:
                return None, None
            h, w = img.shape[:2]
            assert self._detector is not None
            self._detector.setInputSize((w, h))
            _, faces = self._detector.detect(img)
            if faces is None or len(faces) == 0:
                return None, None
            # largest box = closest person
            best = max(faces, key=lambda f: float(f[2]) * float(f[3]))
            aligned = self._recognizer.alignCrop(img, best)  # type: ignore[union-attr]
            feature = self._recognizer.feature(aligned)  # type: ignore[union-attr]
            vec = [float(v) for v in feature.flatten()]
            x, y, fw, fh = (int(round(float(best[i]))) for i in range(4))
            return vec, (x, y, fw, fh)
        except Exception:  # noqa: BLE001 - biometrics are best-effort
            return None, None


def build_face_identifier():
    """FaceIdentifier with SFace-calibrated thresholds, or None when unusable."""
    from novi.perception.faces import FaceIdentifier

    embedder = OpenCVFaceEmbedder()
    if not embedder.available:
        return None, None
    # SFace cosine: same-person typically >= ~0.40, different <= ~0.25.
    faces = FaceIdentifier(tau_match=0.42, tau_ambig=0.30)
    return faces, embedder


# ---------------------------------------------------------------------------
# Objects — torchvision ResNet18 features (instance-level object embedding)
# ---------------------------------------------------------------------------


def _l2(v: list[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


class TorchvisionObjectEmbedder:
    """Extracts a 512-d visual embedding per object crop via ResNet18.

    Instance-level object recognition: the same physical object yields a
    similar embedding across frames/sessions, so Novi can remember *"my
    mug"* rather than just the category "cup". Lazy: the model loads on
    first successful use (not import), so importing this module never
    touches the network. ``available`` reports usability; ``embed``
    returns None per bbox otherwise. A ``core`` callable may be injected
    for CI (no model download).
    """

    def __init__(self, *, device: str | None = None, core: Any | None = None) -> None:
        self._device = device
        self._core = core  # callable(PIL RGB image) -> list[float]; None -> lazy ResNet18
        self._failed = False
        self._lock = threading.Lock()

    # -- availability ---------------------------------------------------------

    @property
    def available(self) -> bool:
        if self._core is not None:
            return True  # injected core (CI) needs no torch/torchvision
        try:
            import torch  # noqa: F401
            import torchvision  # noqa: F401
        except Exception:  # noqa: BLE001
            return False
        return not self._failed and self._ensure()

    def _ensure(self) -> bool:
        with self._lock:
            if self._core is not None:
                return True
            if self._failed:
                return False
            try:
                import torch
                from torchvision.models import ResNet18_Weights, resnet18

                weights = ResNet18_Weights.DEFAULT
                model = resnet18(weights=weights)
                model.fc = torch.nn.Identity()  # drop classifier -> 512-d features
                device = self._device
                if device is None:
                    device = (
                        "mps"
                        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
                        else "cpu"
                    )
                model.eval().to(device)
                preprocess = weights.transforms()
                self._device = device

                def _core(pil_img: Any) -> list[float]:
                    tensor = preprocess(pil_img).unsqueeze(0).to(device)
                    with torch.inference_mode():
                        vec = model(tensor)
                    return vec.squeeze(0).detach().cpu().tolist()

                self._core = _core
                return True
            except Exception:  # noqa: BLE001 - offline/no-torch => honest degrade
                self._failed = True
                self._core = None
                return False

    # -- inference --------------------------------------------------------------

    def embed(self, payload: Any, bboxes: list[tuple[int, int, int, int]]) -> list[list[float] | None]:
        """JPEG/PNG bytes or ndarray + list of (x, y, w, h) -> one vector per bbox."""
        img = self._decode(payload)
        if img is None:
            return [None] * len(bboxes)
        if not self.available:
            return [None] * len(bboxes)
        return [self._embed_crop(img, bbox) for bbox in bboxes]

    def _embed_crop(self, img: Any, bbox: tuple[int, int, int, int]) -> list[float] | None:
        try:
            import cv2
            from PIL import Image

            x, y, w, h = (int(v) for v in bbox)
            ih, iw = img.shape[:2]
            x2, y2 = min(x + w, iw), min(y + h, ih)
            if x2 - x < 8 or y2 - y < 8:
                return None
            crop = img[y:y2, x:x2]
            rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
            pil = Image.fromarray(rgb)
            vec = self._core(pil)  # type: ignore[misc]
            return _l2([float(v) for v in vec])
        except Exception:  # noqa: BLE001 - degenerate crop => no embedding
            return None

    @staticmethod
    def _decode(payload: Any):
        """JPEG bytes / ndarray -> BGR ndarray, else None."""
        try:
            import cv2
            import numpy as np

            if isinstance(payload, (bytes, bytearray)):
                return cv2.imdecode(np.frombuffer(payload, dtype=np.uint8), cv2.IMREAD_COLOR)
            if isinstance(payload, np.ndarray) and payload.ndim == 3:
                return payload
        except Exception:  # noqa: BLE001 - decode failure means no embeddings
            return None
        return None


def build_object_embedder() -> TorchvisionObjectEmbedder | None:
    """Lazy object embedder (no model download until first use), or None."""
    try:
        import torch  # noqa: F401
        import torchvision  # noqa: F401
    except Exception:  # noqa: BLE001 - neural deps optional
        return None
    return TorchvisionObjectEmbedder()
