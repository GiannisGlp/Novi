from __future__ import annotations

import shutil
import subprocess
import wave
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class CameraFrame:
    frame_id: str
    captured_at: str
    width: int
    height: int
    payload: Any
    metadata: dict[str, Any] = field(default_factory=dict)


class Camera(Protocol):
    def read(self) -> CameraFrame: ...
    def close(self) -> None: ...


class MacCamera:
    """macOS camera adapter using OpenCV when installed."""

    def __init__(self, device: int = 0, width: int = 640, height: int = 480) -> None:
        self.device = device
        self.width = width
        self.height = height
        self._capture: Any = None
        self._sequence = 0

    def open(self) -> None:
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError("opencv-python is required for MacCamera") from exc
        capture = cv2.VideoCapture(self.device)
        if not capture.isOpened():
            capture.release()
            raise RuntimeError(f"camera device {self.device} could not be opened")
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self._capture = capture

    def read(self) -> CameraFrame:
        if self._capture is None:
            self.open()
        ok, frame = self._capture.read()
        if not ok:
            raise RuntimeError("camera frame capture failed")
        self._sequence += 1
        actual_height, actual_width = frame.shape[:2]
        return CameraFrame(
            frame_id=f"mac-camera-{self._sequence}",
            captured_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            width=int(actual_width),
            height=int(actual_height),
            payload=frame,
            metadata={"device": self.device, "backend": "opencv"},
        )

    def close(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None


@dataclass(frozen=True)
class AudioRecording:
    recording_id: str
    captured_at: str
    path: Path
    sample_rate: int
    channels: int
    duration_s: float


class MacMicrophone:
    """Optional microphone recorder using sounddevice + the stdlib WAV writer."""

    def __init__(self, sample_rate: int = 16_000, channels: int = 1) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self._sequence = 0

    def record(self, seconds: float, output_dir: Path) -> AudioRecording:
        if seconds <= 0:
            raise ValueError("seconds must be > 0")
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise RuntimeError("sounddevice is required for MacMicrophone") from exc
        output_dir.mkdir(parents=True, exist_ok=True)
        self._sequence += 1
        path = output_dir / f"mac-mic-{self._sequence:05d}.wav"
        frames = int(seconds * self.sample_rate)
        data = sd.rec(frames, samplerate=self.sample_rate, channels=self.channels, dtype="int16")
        sd.wait()
        with wave.open(str(path), "wb") as wav:
            wav.setnchannels(self.channels)
            wav.setsampwidth(2)
            wav.setframerate(self.sample_rate)
            wav.writeframes(data.tobytes())
        return AudioRecording(
            recording_id=path.stem,
            captured_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            path=path,
            sample_rate=self.sample_rate,
            channels=self.channels,
            duration_s=seconds,
        )


class MacSpeaker:
    """Local macOS text-to-speech adapter using the built-in `say` command."""

    def __init__(self, voice: str | None = None) -> None:
        self.voice = voice

    def available(self) -> bool:
        return shutil.which("say") is not None

    def speak(self, text: str) -> None:
        if not text:
            raise ValueError("speech text must not be empty")
        if not self.available():
            raise RuntimeError("macOS `say` command is unavailable")
        command = ["say"]
        if self.voice:
            command.extend(["-v", self.voice])
        command.append(text)
        subprocess.run(command, check=True)


@dataclass
class VirtualBody:
    """Robot-like actuator surface with no physical hardware access."""

    x_m: float = 0.0
    y_m: float = 0.0
    heading_deg: float = 0.0
    velocity_mps: float = 0.0
    last_action: str = "idle"

    ALLOWED_ACTIONS = frozenset({"inspect", "move_forward", "turn_left", "turn_right", "stop", "wait", "observe", "speak"})

    def execute(self, action: str, **parameters: Any) -> dict[str, Any]:
        if action not in self.ALLOWED_ACTIONS:
            raise ValueError(f"virtual action is not allowed: {action}")
        distance = float(parameters.get("distance_m", 0.1))
        degrees = float(parameters.get("degrees", 15.0))
        if action == "move_forward":
            import math
            self.x_m += distance * math.cos(math.radians(self.heading_deg))
            self.y_m += distance * math.sin(math.radians(self.heading_deg))
            self.velocity_mps = distance
        elif action == "turn_left":
            self.heading_deg = (self.heading_deg + degrees) % 360.0
            self.velocity_mps = 0.0
        elif action == "turn_right":
            self.heading_deg = (self.heading_deg - degrees) % 360.0
            self.velocity_mps = 0.0
        elif action in {"stop", "wait", "observe", "inspect", "speak"}:
            self.velocity_mps = 0.0
        self.last_action = action
        return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        return {
            "x_m": self.x_m,
            "y_m": self.y_m,
            "heading_deg": self.heading_deg,
            "velocity_mps": self.velocity_mps,
            "last_action": self.last_action,
        }
