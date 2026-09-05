"""Instrumented autonomy/soak runner (Brain Exit Contract, doc 14: B1 + B5).

Continuous-operation evidence writer: drives a brain's ``step()`` on a
real wall-clock loop and writes the machine-checkable archive that
``benchmarks/gate_runner.py`` consumes for gates B1 (>= 24 h autonomy)
and B5 (>= 168 h soak):

- ``uptime.json`` — accumulated active seconds, cycles, error totals,
  multitask tracks completed, preemption/resume events, restart-surviving
  state (SoakState.save/load);
- ``day_N.json`` — one report per day boundary with hours and
  silent-failure counts (bursts of consecutive step errors).

Nothing else in the repo writes this archive (gate_runner only reads
``mac_test_results/gates/B1/``), so this module is the missing producer
behind the B1/B5 evidence format. ``day_boundary_s`` compresses a "day"
for tests/CI (e.g. 0.05 s == one day); real acceptance runs leave it at
the default 86400 s and run for 24 h / 168 h.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

UPTIME_FILE = "uptime.json"
# A track is "complete" after this many focused steps (multitask demo size).
_TRACK_LENGTH_STEPS = 3
# The runner always maintains at least two concurrent goal tracks.
_MIN_TRACKS = 2


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class SoakState:
    """Restart-surviving accumulation persisted to ``uptime.json``.

    ``save()``/``load()`` are the restart contract: accumulated active
    time and cycles must survive a runner restart (test-covered).
    """

    data_dir: Path
    started_at: str = field(default_factory=_utc_now_iso)
    accumulated_active_s: float = 0.0
    cycles: int = 0
    errors_total: int = 0
    silent_failures_total: int = 0
    multitask_tracks_completed: int = 0
    preemption_resume_events: int = 0
    last_active_at: str = field(default_factory=_utc_now_iso)

    def save(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        payload = self.to_dict()
        (self.data_dir / UPTIME_FILE).write_text(json.dumps(payload, indent=2))

    @classmethod
    def load(cls, data_dir: str | Path) -> "SoakState":
        data_dir = Path(data_dir)
        path = data_dir / UPTIME_FILE
        if not path.exists():
            return cls(data_dir=data_dir)
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return cls(data_dir=data_dir)
        return cls(
            data_dir=data_dir,
            started_at=str(data.get("started_at") or _utc_now_iso()),
            accumulated_active_s=float(data.get("accumulated_active_s") or 0.0),
            cycles=int(data.get("cycles") or 0),
            errors_total=int(data.get("errors_total") or 0),
            silent_failures_total=int(data.get("silent_failures_total") or 0),
            multitask_tracks_completed=int(data.get("multitask_tracks_completed") or 0),
            preemption_resume_events=int(data.get("preemption_resume_events") or 0),
            last_active_at=str(data.get("last_active_at") or _utc_now_iso()),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at,
            "last_active_at": self.last_active_at,
            "accumulated_active_s": round(self.accumulated_active_s, 3),
            "cycles": self.cycles,
            "hours": round(self.accumulated_active_s / 3600.0, 6),
            "errors_total": self.errors_total,
            "silent_failures": self.silent_failures_total,
            "multitask_tracks_completed": self.multitask_tracks_completed,
            "preemption_resume_events": self.preemption_resume_events,
        }


@dataclass
class _Track:
    """One concurrent goal track (multitask)."""

    goal: Any
    progress_steps: int = 0
    started: bool = False
    completed: bool = False

    @property
    def done(self) -> bool:
        return self.completed or self.progress_steps >= _TRACK_LENGTH_STEPS


class SoakRunner:
    """Drives one brain through ``run_for(seconds)`` of autonomy.

    ``brain_factory`` (callable returning a brain with ``step()`` and
    ``set_goal()``) and ``goal_factory(label)`` keep the runner agnostic
    to the real autonomy stack. ``tick_s`` paces cycles; ``heartbeat_s``
    controls uptime.json write cadence; ``day_boundary_s`` compresses a
    day for tests. State is loaded at construction, so restarting the
    runner on the same ``data_dir`` continues accumulation.
    """

    def __init__(
        self,
        *,
        brain_factory: Callable[[], Any],
        goal_factory: Callable[[str], Any],
        data_dir: str | Path,
        tick_s: float = 1.0,
        heartbeat_s: float = 60.0,
        day_boundary_s: float = 86400.0,
        b1_target_h: float = 24.0,
        b5_target_h: float = 168.0,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.state = SoakState.load(self.data_dir)
        self.brain = brain_factory()
        self.goal_factory = goal_factory
        self.tick_s = max(0.001, float(tick_s))
        self.heartbeat_s = max(0.001, float(heartbeat_s))
        self.day_boundary_s = max(0.001, float(day_boundary_s))
        self.b1_target_h = float(b1_target_h)
        self.b5_target_h = float(b5_target_h)

        # Multitask: maintain >= 2 concurrent goal tracks from the start.
        self.tracks: list[_Track] = [
            _Track(goal=self.goal_factory(f"goal-{i}")) for i in range(_MIN_TRACKS)
        ]
        self._focus = 0
        self._last_day_index = int(self.state.accumulated_active_s / self.day_boundary_s)
        self._consecutive_errors = 0
        self._day_silent_failures = 0
        self._day_errors = 0
        self._day_cycles = 0
        self._day_active_s = 0.0
        self._last_heartbeat = time.monotonic()
        try:
            self.brain.set_goal(self.tracks[self._focus].goal)
        except Exception:  # noqa: BLE001 - a stub without goals must not break soak
            pass

    # -- report helpers ----------------------------------------------------

    def _day_index(self) -> int:
        return int(self.state.accumulated_active_s / self.day_boundary_s)

    def _write_uptime(self) -> None:
        self.state.last_active_at = _utc_now_iso()
        self.state.save()

    def _write_day_report(self, index: int) -> None:
        """Emit one day report. ``hours`` is THIS day's active time (the
        gate_runner sums day_*.json hours for B5, so cumulative values would
        over-count quadratically); the file names the day it summarizes."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "day": index,
            "hours": round(self._day_active_s / 3600.0, 6),
            "cycles": self._day_cycles,
            "errors_total": self._day_errors,
            "silent_failures": self._day_silent_failures,
            "multitask_tracks_completed": self.state.multitask_tracks_completed,
            "preemption_resume_events": self.state.preemption_resume_events,
            "written_at": _utc_now_iso(),
        }
        (self.data_dir / f"day_{index:03d}.json").write_text(
            json.dumps(payload, indent=2))

    def _flush_trailing_burst(self) -> None:
        """A burst of consecutive errors still open at run end (or restart)
        never meets a following success, so close it explicitly as a silent
        failure before writing any final evidence."""
        if self._consecutive_errors > 0:
            self.state.silent_failures_total += 1
            self._day_silent_failures += 1
            self._consecutive_errors = 0

    # -- autonomy -----------------------------------------------------------

    def _step_once(self) -> bool:
        """One brain cycle. Returns True on success, False on a step error."""
        try:
            self.brain.step()
            return True
        except Exception:  # noqa: BLE001 - step errors are measured, never fatal
            return False

    def _advance_multitask(self) -> None:
        """Rotate focus across >=2 tracks; close completed ones and record
        preemption/resume events when returning to an unfinished track."""
        focus = self.tracks[self._focus]
        if focus.started and not focus.done:
            self.state.preemption_resume_events += 1
        focus.started = True
        focus.progress_steps += 1
        if focus.done and not focus.completed:
            focus.completed = True
            self.state.multitask_tracks_completed += 1
            self.tracks[self._focus] = _Track(
                goal=self.goal_factory(f"goal-{self.state.multitask_tracks_completed + _MIN_TRACKS}"))
        self._focus = (self._focus + 1) % len(self.tracks)
        try:
            self.brain.set_goal(self.tracks[self._focus].goal)
        except Exception:  # noqa: BLE001
            pass

    def run_for(self, seconds: float) -> None:
        """Run autonomy cycles until ``seconds`` of wall clock have elapsed."""
        deadline = time.monotonic() + max(0.0, float(seconds))
        while time.monotonic() < deadline:
            cycle_start = time.monotonic()
            ok = self._step_once()
            self.state.cycles += 1
            if ok:
                # A burst of consecutive errors ends at the first success: it
                # is a silent failure (no audible/handled recovery evidence).
                if self._consecutive_errors > 0:
                    self.state.silent_failures_total += 1
                    self._day_silent_failures += 1
                    self._consecutive_errors = 0
            else:
                self._consecutive_errors += 1
                self.state.errors_total += 1
                self._day_errors += 1
            self._advance_multitask()
            # Pace to tick_s so short runs still accumulate real cycles.
            elapsed = time.monotonic() - cycle_start
            if elapsed < self.tick_s:
                time.sleep(self.tick_s - elapsed)
            # Active time is the full paced cycle, so short runs accumulate
            # measurable wall-clock evidence instead of ~0.0 s of step time.
            period = time.monotonic() - cycle_start
            self.state.accumulated_active_s += period
            self._day_active_s += period
            self._day_cycles += 1
            # Heartbeat: keep uptime.json fresh without a write per cycle.
            if time.monotonic() - self._last_heartbeat >= self.heartbeat_s:
                self._write_uptime()
                self._last_heartbeat = time.monotonic()
            # Day boundary: the compressed day just finished (last_day_index)
            # is flushed with ITS OWN deltas; counters reset for the new day.
            day_index = self._day_index()
            if day_index > self._last_day_index:
                self._write_day_report(self._last_day_index)
                self._day_silent_failures = 0
                self._day_errors = 0
                self._day_cycles = 0
                self._day_active_s = 0.0
                self._last_day_index = day_index
        # Final flush: close any open error burst, then uptime + the partial
        # day since the last boundary.
        self._flush_trailing_burst()
        self._write_uptime()
        day_index = self._day_index()
        if day_index >= self._last_day_index and self._day_active_s > 0.0:
            self._write_day_report(day_index)
            self._last_day_index = day_index
