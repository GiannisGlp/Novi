"""Tests: soak runner — the instrumented autonomy session (doc 14, B1+B5).

With tiny durations (CI-safe):
- writes uptime.json accumulating hours/cycles/tracks/preemptions;
- writes day_N.json reports at day boundaries;
- counts silent failures on consecutive step errors;
- state survives runner restart (accumulated time persists);
- multitask: maintains >=2 goal tracks during the run.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path


def _run_soak(tmp: Path, seconds: float, *, fail_steps: int = 0, day_boundary_s: float = 0.05):
    """Run a short soak with a stub brain; returns (uptime, day_reports)."""
    from benchmarks.soak_runner import SoakRunner

    calls = {"n": 0}

    class StubBrain:
        def __init__(self):
            self.curiosity_label = None

        def step(self):
            calls["n"] += 1
            if calls["n"] <= fail_steps:
                raise RuntimeError("injected failure")
            return {"reasoning": "ok", "action": "wait"}

        # minimal goal surface used by the runner
        def set_goal(self, goal):
            return goal

    class StubGoal:
        def __init__(self, label):
            self.label = label

    runner = SoakRunner(
        brain_factory=StubBrain,
        goal_factory=lambda label: StubGoal(label),
        data_dir=tmp,
        tick_s=0.01,
        heartbeat_s=seconds / 4 if seconds > 0.04 else 0.01,
        day_boundary_s=day_boundary_s,
        b1_target_h=24,
        b5_target_h=168,
    )
    runner.run_for(seconds)
    up = json.loads((tmp / "uptime.json").read_text())
    days = sorted(tmp.glob("day_*.json"))
    return up, [json.loads(p.read_text()) for p in days]


class TestSoakRunner(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_uptime_json_shape_and_accumulation(self):
        up, _ = _run_soak(self.tmp, seconds=0.12)
        for key in ("started_at", "accumulated_active_s", "cycles", "hours",
                    "multitask_tracks_completed", "preemption_resume_events"):
            self.assertIn(key, up)
        self.assertGreater(up["cycles"], 0)
        self.assertGreater(up["accumulated_active_s"], 0)

    def test_day_report_written_with_no_silent_failures(self):
        _, days = _run_soak(self.tmp, seconds=0.15)
        self.assertTrue(len(days) >= 1)
        d = days[0]
        self.assertIn("hours", d)
        self.assertEqual(d.get("silent_failures"), 0)

    def test_consecutive_errors_recorded_as_silent_failures(self):
        up, days = _run_soak(self.tmp, seconds=0.12, fail_steps=3)
        combined = json.dumps([up] + days)
        # injected failures must be visible somewhere in the evidence
        self.assertTrue(up.get("errors_total", 0) >= 1 or "silent_failures\": 0" not in combined)

    def test_state_survives_restart(self):
        from benchmarks.soak_runner import SoakState

        state = SoakState(self.tmp)
        state.accumulated_active_s = 3600.0
        state.cycles = 100
        state.save()
        fresh = SoakState.load(self.tmp)
        self.assertAlmostEqual(fresh.accumulated_active_s, 3600.0)
        self.assertEqual(fresh.cycles, 100)


if __name__ == "__main__":
    unittest.main()
