"""Face identity provider for the Mac Brain (gap-audit plan Phase B2).

Sits behind the engine's ``face_id`` boundary
(``identify(detection={"label","track","bbox","image"})``).

Two implementations:
  - ``OpenCVFaceID``: deterministic gradient-histogram faceprint over a
    detected crop (OpenCV is already the Mac vision extra; no model download).
  - ``InsightFaceFaceID``: optional stronger embedding, import-guarded — it
    simply reports unavailable when insightface is not installed.

Recognition is evidence for PersonIdentity tiering, never an assertion or an
authorization. Same waveform/crop ⇒ same print ⇒ same match (deterministic).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from .identity import IdentityMatch


def _cosine(a: list[float], b: list[float]) -> float:
    num = sum(x * y for x, y in zip(a, b, strict=False))
    da = math.sqrt(sum(x * x for x in a)) or 1.0
    db = math.sqrt(sum(y * y for y in b)) or 1.0
    return num / (da * db)


def _l2(v: list[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def _load_image(payload) -> Any:
    """Decode a flexible frame payload into a numpy BGR image (or None)."""
    try:
        import cv2
        import numpy as np
    except Exception:  # noqa: BLE001 - vision extra absent
        return None
    if payload is None:
        return None
    if isinstance(payload, np.ndarray):
        return payload
    if isinstance(payload, (bytes, bytearray)):
        arr = np.frombuffer(payload, dtype=np.uint8)
        try:
            return cv2.imdecode(arr, cv2.IMREAD_COLOR)
        except Exception:  # noqa: BLE001
            return None
    if isinstance(payload, (str, Path)):
        try:
            return cv2.imread(str(payload), cv2.IMREAD_COLOR)
        except Exception:  # noqa: BLE001
            return None
    return None


class OpenCVFaceID:
    """Deterministic faceprint provider using OpenCV (vision extra)."""

    def __init__(self, *, threshold: float = 0.86, crop_size: int = 64, cells: int = 4) -> None:
        self.threshold = float(threshold)
        self.crop_size = int(crop_size)
        self.cells = int(cells)
        self._prints: dict[str, list[list[float]]] = {}
        try:
            import cv2  # noqa: F401
            self._cv2 = cv2
        except Exception:  # noqa: BLE001 - vision extra absent
            self._cv2 = None

    @property
    def available(self) -> bool:
        return self._cv2 is not None

    # ---- features ----

    def features(self, image, bbox=None) -> list[float] | None:
        """Faceprint of an image (path/bytes/ndarray) and optional xyxy bbox."""
        if self._cv2 is None:
            return None
        cv2 = self._cv2
        img = _load_image(image)
        if img is None or getattr(img, "size", 0) == 0:
            return None
        h, w = img.shape[:2]
        if bbox and len(bbox) == 4:
            x1, y1, x2, y2 = [int(max(0, v)) for v in bbox]
            x2, y2 = min(x2, w), min(y2, h)
            if x2 - x1 < 8 or y2 - y1 < 8:
                return None
            crop = img[y1:y2, x1:x2]
        else:
            crop = img
        try:
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, (self.crop_size, self.crop_size))
        except Exception:  # noqa: BLE001 - degenerate crop
            return None
        # Gradient-orientation histogram over cells (deterministic faceprint).
        gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0)
        gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1)
        mag, ang = cv2.cartToPolar(gx, gy)
        cell = self.crop_size // self.cells
        bins_n = 8
        vec: list[float] = []
        for cy in range(self.cells):
            for cx in range(self.cells):
                m = mag[cy * cell:(cy + 1) * cell, cx * cell:(cx + 1) * cell]
                a = ang[cy * cell:(cy + 1) * cell, cx * cell:(cx + 1) * cell]
                hist = [0.0] * bins_n
                idx = ((a / (math.pi * 2.0) * bins_n).astype("int") % bins_n).flatten()
                for i, b in enumerate(idx):
                    hist[int(b)] += float(m.flatten()[i])
                s = sum(hist) or 1.0
                vec.extend(h / s for h in hist)
        return _l2(vec)

    # ---- enrollment / recognition ----

    def enroll(self, name: str, image, bbox=None) -> bool:
        f = self.features(image, bbox)
        if f is None:
            return False
        self._prints.setdefault(name, []).append(f)
        return True

    def identify(self, detection: dict) -> IdentityMatch | None:
        """Engine contract: identify(detection={"bbox":..., "image":...})."""
        det = detection or {}
        f = self.features(det.get("image"), det.get("bbox"))
        if f is None:
            return None
        best_name, best_score = "", -1.0
        for name, prints in self._prints.items():
            score = max(_cosine(f, p) for p in prints)
            if score > best_score:
                best_name, best_score = name, score
        if not best_name or best_score < self.threshold:
            return None
        return IdentityMatch(name=best_name, confidence=min(1.0, best_score), modality="face")

    def known_faces(self) -> list[str]:
        return sorted(self._prints)


class InsightFaceFaceID(OpenCVFaceID):
    """Optional stronger embedding via insightface; falls back to the
    deterministic OpenCV faceprint when the package/model is unavailable."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._model = None
        try:
            from insightface.app import FaceAnalysis  # type: ignore[import-not-found]
            self._model = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        except Exception:  # noqa: BLE001 - heavy optional dep stays optional
            self._model = None

    @property
    def available(self) -> bool:
        return self._model is not None
