"""VisionBudget: cost gate + timing telemetry for the camera loop.

The camera loop used to run every expensive stage (SFace face embed, ResNet18
object embed, preview b64 encode) on every frame — caps effective frame rate
with no way to measure it. VisionBudget gates the expensive stages to a budget
(detection + presence still run every frame) and records per-stage timing so
the loop can report what it actually achieves.

Two independent gates per stage:

1. a counter gate (``n % every_n == 1`` — frame 1 is the baseline that runs
   every stage), and
2. an optional minimum interval in seconds, so a very fast loop can't hammer a
   stage more often than the budget allows.

A ``scene.changed`` event forces every stage for one frame so novel content is
re-embedded immediately. Pure and deterministic (injectable clock) so tests
drive it exactly.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Any, Callable

STAGES = ("detect", "face_embed", "object_embed", "preview")
_GATED = ("face_embed", "object_embed", "preview")


class VisionBudget:
    """Deterministic per-stage gating + processed-fps/stage-ms telemetry."""

    _MAX_SAMPLES = 128
    _MAX_RING = 4096

    def __init__(
        self,
        *,
        detect_every_n: int = 1,
        face_every_n: int = 3,
        object_every_n: int = 4,
        preview_every_n: int = 2,
        face_min_interval_s: float = 0.0,
        object_min_interval_s: float = 0.0,
        preview_min_interval_s: float = 0.0,
        scene_resets: bool = True,
        fps_window_s: float = 5.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._every_n = {
            "detect": self._valid(detect_every_n, "detect_every_n"),
            "face_embed": self._valid(face_every_n, "face_every_n"),
            "object_embed": self._valid(object_every_n, "object_every_n"),
            "preview": self._valid(preview_every_n, "preview_every_n"),
        }
        self._min_interval_s = {
            "face_embed": max(0.0, float(face_min_interval_s)),
            "object_embed": max(0.0, float(object_min_interval_s)),
            "preview": max(0.0, float(preview_min_interval_s)),
        }
        self._scene_resets = bool(scene_resets)
        self._fps_window_s = max(0.1, float(fps_window_s))
        self._clock = clock
        self._frame_count = 0
        self._force_next = False
        self._last_ran_at: dict[str, float] = {}
        self._stage_ms: dict[str, deque[float]] = {s: deque() for s in STAGES}
        self._runs: dict[str, int] = {s: 0 for s in STAGES}
        self._processed_ts: deque[float] = deque()

    @staticmethod
    def _valid(n: int, name: str) -> int:
        n = int(n)
        if n < 1:
            raise ValueError(f"{name} must be >= 1")
        return n

    # -- decisions -------------------------------------------------------

    def decide(self, *, frame_seq: int, scene_changed: bool = False) -> dict[str, bool]:
        """Return which stages run for this processed frame.

        ``scene_changed`` (e.g. from the previous frame's ``scene.changed``
        event) forces every gated stage for one frame — novel content is
        re-embedded immediately instead of waiting for the counter. Detection
        always runs; the gated stages follow counter + min-interval.
        """
        self._frame_count += 1
        n = self._frame_count
        force = self._force_next or (self._scene_resets and scene_changed)
        self._force_next = False
        now = self._clock()
        flags: dict[str, bool] = {"detect": True}
        for stage in _GATED:
            due = self._every_n[stage] == 1 or (n % self._every_n[stage] == 1)
            interval_ok = now - self._last_ran_at.get(
                stage, -float("inf")
            ) >= self._min_interval_s[stage]
            flags[stage] = (force or due) and interval_ok
            if flags[stage]:
                self._last_ran_at[stage] = now
        return flags

    def mark_scene_change(self) -> None:
        """Force every stage on the next ``decide()`` call."""
        self._force_next = True

    # -- telemetry ----------------------------------------------------------

    def add_sample(self, stage: str, elapsed_ms: float) -> None:
        """Record one stage duration in milliseconds (bounded ring)."""
        ring = self._stage_ms.get(stage)
        if ring is None:
            return
        ring.append(max(0.0, float(elapsed_ms)))
        if len(ring) > self._MAX_SAMPLES:
            ring.popleft()

    def record_run(self, stage: str) -> None:
        """Count one run of a stage (for the ``runs`` telemetry)."""
        if stage in self._runs:
            self._runs[stage] += 1
            self._last_ran_at[stage] = self._clock()

    def mark_processed(self) -> None:
        """Feed one processed-frame timestamp into the fps window."""
        self._processed_ts.append(self._clock())
        while (
            self._processed_ts
            and self._processed_ts[0] < self._processed_ts[-1] - self._fps_window_s
        ):
            self._processed_ts.popleft()

    def _processed_fps(self, now: float) -> float | None:
        if len(self._processed_ts) < 2:
            return None
        if now - self._processed_ts[-1] > self._fps_window_s:
            return 0.0  # idle: no frames processed recently
        span = self._processed_ts[-1] - self._processed_ts[0]
        if span <= 0.0:
            return None
        return (len(self._processed_ts) - 1) / span

    def telemetry(self, *, now: float | None = None) -> dict[str, Any]:
        """Per-stage timing + processed frame rate (plain JSON-safe floats)."""
        n = now if now is not None else self._clock()
        stage_ms: dict[str, Any] = {}
        for stage in STAGES:
            ring = self._stage_ms[stage]
            if not ring:
                stage_ms[stage] = {"samples": 0, "avg_ms": 0.0, "max_ms": 0.0}
                continue
            avg = sum(ring) / len(ring)
            stage_ms[stage] = {
                "samples": len(ring),
                "avg_ms": round(avg, 3),
                "max_ms": round(max(ring), 3),
            }
        return {
            "frames_processed": self._frame_count,
            "processed_fps": self._processed_fps(n),
            "stage_ms": stage_ms,
            "runs": dict(self._runs),
        }

    def reset(self) -> None:
        """Clear counters, timings and the fps window (e.g. on camera restart)."""
        self._frame_count = 0
        self._force_next = False
        self._last_ran_at.clear()
        self._stage_ms = {s: deque() for s in STAGES}
        self._runs = {s: 0 for s in STAGES}
        self._processed_ts.clear()
