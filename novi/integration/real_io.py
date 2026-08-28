"""Real I/O bridges (doc 17): camera, microphone, speakers, STT.

Adapts the brain's existing hardware adapters (MacCamera, MacMicrophone,
MacSpeaker, WhisperSTTProvider) into the voice/perception/integration
packages' contracts, so real devices flow through the exact same
deterministic-tested pipelines. Every adapter degrades gracefully when
hardware is absent so CI never depends on devices.
"""

from __future__ import annotations

import base64
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from novi.brain.io import CameraFrame


# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------


class MacCameraAdapter:
    """Adapts brain.io.MacCamera (OpenCV) to perception.CameraProvider."""

    def __init__(self, mac_camera: Any) -> None:
        self._cam = mac_camera

    def open(self) -> None:
        # MacCamera.open() raises RuntimeError when the device is absent.
        self._cam.open()

    def read(self) -> CameraFrame:
        frame = self._cam.read()
        payload = frame.payload
        # perception/preview want portable bytes; convert ndarray -> JPEG once
        if hasattr(payload, "shape"):  # numpy.ndarray from OpenCV
            jpeg = _encode_ndarray_jpeg(payload)
            if jpeg is not None:
                frame = CameraFrame(
                    frame_id=frame.frame_id,
                    captured_at=frame.captured_at,
                    width=frame.width,
                    height=frame.height,
                    payload=jpeg,
                    metadata={**frame.metadata, "format": "jpeg"},
                )
        return frame

    def close(self) -> None:
        self._cam.close()


def _encode_ndarray_jpeg(image: Any) -> bytes | None:
    """ndarray BGR -> JPEG bytes via cv2; None on failure."""
    try:
        import cv2
    except ImportError:
        return None
    try:
        ok, buf = cv2.imencode(".jpg", image)
        return bytes(buf.tobytes()) if ok else None
    except Exception:  # noqa: BLE001
        return None


def encode_frame_jpeg_b64(frame: CameraFrame) -> str | None:
    """CameraFrame -> data URL for the preview page; None when unencodable."""
    payload = frame.payload
    if isinstance(payload, (bytes, bytearray)) and payload[:2] == b"\xff\xd8":
        b64 = base64.b64encode(bytes(payload)).decode()
        return f"data:image/jpeg;base64,{b64}"
    if hasattr(payload, "shape"):
        jpeg = _encode_ndarray_jpeg(payload)
        if jpeg:
            b64 = base64.b64encode(jpeg).decode()
            return f"data:image/jpeg;base64,{b64}"
    return None


def encode_preview_jpeg_b64(
    frame: CameraFrame, *, max_width: int = 640, quality: int = 72
) -> str | None:
    """Downscaled preview data URL; detection stays full-res and untouched.

    The camera-loop embeddings run on ``frame.payload`` unchanged — only the
    browser preview is shrunk, so the base64 payload and encode cost drop
    sharply without degrading face/object recognition.
    """
    try:
        import cv2
        import numpy as np
    except ImportError:  # noqa: SIM105 - optional heavy deps; degrade to no preview
        return None
    payload = frame.payload
    try:
        if isinstance(payload, (bytes, bytearray)) and payload[:2] == b"\xff\xd8":
            image = cv2.imdecode(np.frombuffer(bytes(payload), dtype=np.uint8), cv2.IMREAD_COLOR)
        elif hasattr(payload, "shape"):
            image = payload
        else:
            return None
        if image is None:
            return None
        height, width = image.shape[:2]
        if width > max_width:
            scale = max_width / float(width)
            image = cv2.resize(
                image, (max_width, int(round(height * scale))), interpolation=cv2.INTER_AREA
            )
        ok, buf = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
        if not ok:
            return None
        b64 = base64.b64encode(bytes(buf.tobytes())).decode()
        return f"data:image/jpeg;base64,{b64}"
    except Exception:  # noqa: BLE001 - preview encode is best-effort
        return None


# ---------------------------------------------------------------------------
# Microphone + STT
# ---------------------------------------------------------------------------


class RealMicrophone:
    """Wraps brain.io.MacMicrophone (sounddevice); record() -> dict."""

    def __init__(self, mac_microphone: Any) -> None:
        self._mic = mac_microphone

    def record(self, seconds: float, *, output_dir: Path | str | None = None) -> dict[str, Any]:
        from novi.brain.io import MacMicrophone

        mic = self._mic if self._mic is not None else MacMicrophone()
        rec = mic.record(seconds, Path(output_dir or Path("mac_test_results/voice")))
        return {
            "path": str(rec.path),
            "duration_s": float(getattr(rec, "duration_s", 0.0) or 0.0),
            "sample_rate": int(getattr(rec, "sample_rate", 16000)),
        }


class RealSTT:
    """listen_and_transcribe: RealMicrophone record -> STT provider -> text.

    Works with brain.models.stt.WhisperSTTProvider (real) or the
    DeterministicSTTProvider (CI).
    """

    def __init__(self, stt_provider: Any, mac_microphone: Any | None = None) -> None:
        self._stt = stt_provider
        self._mic: Any = mac_microphone  # lazily replaced with MacMicrophone

    def listen_and_transcribe(
        self,
        seconds: float = 3.0,
        *,
        output_dir: Path | str | None = None,
    ) -> dict[str, Any]:
        mic = self._mic if self._mic is not None else RealMicrophone(None)

        # RealMicrophone.record returns {path, duration_s, sample_rate}
        rec = mic.record(seconds, output_dir=output_dir or Path("mac_test_results/voice"))
        path = rec["path"]

        try:
            tr = self._stt.transcribe(path)
        except Exception as exc:  # noqa: BLE001 - degrade to explicit failure
            return {"ok": False, "text": "", "reason": f"stt-failed: {exc}"}
        return {
            "ok": True,
            "text": (tr.text or "").strip(),
            "confidence": float(tr.confidence),
            "language": getattr(tr, "language", ""),
            "provider": tr.provider,
            "model_id": getattr(tr, "model_id", ""),
            "audio_path": path,
        }


# ---------------------------------------------------------------------------
# Speakers / TTS
# ---------------------------------------------------------------------------


class RealSpeaker:
    """Wraps voice.tts providers (Say today, Piper/Kokoro later).

    speak() never raises for unavailability — it degrades with
    spoken=False so reply paths can keep flowing without audio.
    """

    def __init__(self, tts_provider: Any) -> None:
        self._tts = tts_provider

    def available(self) -> bool:
        avail = getattr(self._tts, "available", None)
        return bool(avail()) if callable(avail) else True

    def speak(self, text: str) -> dict[str, Any]:
        if not (text or "").strip():
            return {"spoken": False, "reason": "empty"}
        if not self.available():
            return {"spoken": False, "reason": "tts-unavailable"}
        try:
            out = self._tts.synthesize(text.strip())
            return {"spoken": bool(getattr(out, "spoken", True)), "text": out.text, "provider": out.provider}
        except Exception as exc:  # noqa: BLE001 - audio is never critical-path
            return {"spoken": False, "reason": f"tts-error: {exc}"}
