"""Camera acquisition: provider wrapper with bounded drop-oldest queue,
health state machine, and freshness telemetry (doc 01_CAMERA_ACQUISITION.md).

Capture runs on its own thread; the cognitive loop polls at its own rate
and never blocks on camera I/O. Drops are counted telemetry, never silent
loss. Health transitions surface into the hardware-health view.
"""

from __future__ import annotations

import enum
import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Protocol

from novi.brain.io import CameraFrame


class CameraHealth(enum.Enum):
    UNKNOWN = "unknown"
    AVAILABLE = "available"
    DEGRADED = "degraded"
    FAILED = "failed"
    OFFLINE = "offline"


class CameraProvider(Protocol):
    """Doc-01 provider contract; real AVFoundation/OpenCV backend later."""

    def open(self) -> None: ...
    def read(self) -> CameraFrame: ...
    def close(self) -> None: ...


@dataclass
class FrameRecord:
    """A frame plus acquisition provenance."""

    frame: CameraFrame
    received_monotonic: float
    seq: int
    metadata: dict = field(default_factory=dict)

    @property
    def frame_id(self) -> str:
        return self.frame.frame_id

    def age_s(self, now_monotonic: float) -> float:
        return max(0.0, now_monotonic - self.received_monotonic)

    def is_stale(self, now_monotonic: float, *, stale_after_s: float) -> bool:
        return self.age_s(now_monotonic) > stale_after_s


# Health thresholds on consecutive read failures.
_FAIL_AT = 1        # first failure -> degraded
_FAILED_AT = 5      # sustained failure -> failed


class CameraFeed:
    """Owns the capture thread; consumers poll FrameRecords non-blocking."""

    def __init__(self, provider: CameraProvider, *, queue_size: int = 8) -> None:
        if queue_size < 1:
            raise ValueError("queue_size must be >= 1")
        self._provider = provider
        self._q: queue.Queue[FrameRecord] = queue.Queue(maxsize=queue_size)
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._seq = 0
        self._lock = threading.Lock()

        # telemetry
        self.dropped = 0
        self.captured = 0
        self.consecutive_failures = 0
        self.recoveries = 0
        self.last_frame_mono: float | None = None

        self.health = CameraHealth.UNKNOWN

    # -- lifecycle -----------------------------------------------------------

    def start(self) -> None:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop.clear()
            self._provider.open()
            self._thread = threading.Thread(target=self._run, daemon=True, name="novi-camera")
            self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        t = self._thread
        if t is not None:
            t.join(timeout=2.0)
            self._thread = None
        try:
            self._provider.close()
        except Exception:
            pass
        self.health = CameraHealth.OFFLINE

    # -- consumption -----------------------------------------------------------

    def poll(self, *, timeout_s: float = 0.0) -> FrameRecord | None:
        """Non-blocking pull; small optional wait; None when empty."""
        try:
            return self._q.get(timeout=timeout_s)
        except queue.Empty:
            return None

    # -- freshness ---------------------------------------------------------------

    def last_frame_age_s(self) -> float | None:
        if self.last_frame_mono is None:
            return None
        return max(0.0, time.monotonic() - self.last_frame_mono)

    def is_stale(self, *, stale_after_s: float = 1.0) -> bool:
        age = self.last_frame_age_s()
        return age is None or age > stale_after_s

    # -- internals ------------------------------------------------------------------

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                frame = self._provider.read()
            except Exception:
                self.consecutive_failures += 1
                if self.consecutive_failures >= _FAILED_AT:
                    self.health = CameraHealth.FAILED
                elif self.health in (CameraHealth.UNKNOWN, CameraHealth.AVAILABLE):
                    self.health = CameraHealth.DEGRADED
                # brief backoff so a dead bus doesn't spin the CPU
                if self._stop.wait(0.01):
                    break
                continue

            self.consecutive_failures = 0
            if self.health in (CameraHealth.FAILED, CameraHealth.DEGRADED):
                self.recoveries += 1
            self.health = CameraHealth.AVAILABLE

            self._seq += 1
            rec = FrameRecord(
                frame=frame,
                received_monotonic=time.monotonic(),
                seq=self._seq,
            )
            self.last_frame_mono = rec.received_monotonic
            self.captured += 1
            try:
                self._q.put_nowait(rec)
            except queue.Full:
                # drop-oldest under pressure — counted, never silent
                try:
                    self._q.get_nowait()
                    self.dropped += 1
                except queue.Empty:
                    pass
                try:
                    self._q.put_nowait(rec)
                except queue.Full:  # pragma: no cover - race guard
                    pass
