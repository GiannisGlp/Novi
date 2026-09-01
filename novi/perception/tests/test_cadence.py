"""Tests: VisionBudget — cost gating + timing telemetry for the camera loop.

The camera loop used to run every expensive stage (face embed, object embed,
preview encode) every frame. VisionBudget gates them to a budget so a very
fast loop can't hammer the embedders, while detection + presence still run
every frame. Deterministic via an injected clock.
"""

from __future__ import annotations

import pytest

from novi.perception.cadence import VisionBudget


class _Clock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    def advance(self, dt: float) -> None:
        self.t += dt


def _budget(**kw) -> VisionBudget:
    kw.setdefault("clock", _Clock())
    return VisionBudget(**kw)


class TestDecideBaseline:
    def test_first_frame_runs_every_stage(self):
        b = _budget()
        d = b.decide(frame_seq=1)
        assert d["detect"] is True
        assert d["face_embed"] is True
        assert d["object_embed"] is True
        assert d["preview"] is True

    def test_detect_always_runs(self):
        b = _budget()
        for s in range(1, 13):
            assert b.decide(frame_seq=s)["detect"] is True

    def test_counter_gate(self):
        b = _budget(face_every_n=3, object_every_n=4, preview_every_n=2)
        runs = {s: b.decide(frame_seq=s) for s in range(1, 13)}
        # face on frames 1,4,7,10
        assert [s for s, d in runs.items() if d["face_embed"]] == [1, 4, 7, 10]
        # object on frames 1,5,9
        assert [s for s, d in runs.items() if d["object_embed"]] == [1, 5, 9]
        # preview on frames 1,3,5,7,9,11
        assert [s for s, d in runs.items() if d["preview"]] == [1, 3, 5, 7, 9, 11]

    def test_every_n_1_runs_always(self):
        b = _budget(face_every_n=1)
        for s in range(1, 5):
            assert b.decide(frame_seq=s)["face_embed"] is True


class TestSceneReset:
    def test_scene_change_forces_every_stage_next_frame(self):
        b = _budget(face_every_n=3, object_every_n=4, preview_every_n=2)
        # skip past the baseline so no stage is due by counter
        for s in range(2, 5):
            b.decide(frame_seq=s)
        d = b.decide(frame_seq=5, scene_changed=True)
        assert all(d.values()) is True  # detect + all gated stages forced

    def test_scene_change_flag_consumed(self):
        b = _budget(face_every_n=3)
        d = b.decide(frame_seq=2, scene_changed=True)
        assert d["face_embed"] is True
        # next frame (without flag) follows the counter again
        d2 = b.decide(frame_seq=3)
        assert d2["face_embed"] is False

    def test_scene_resets_disabled(self):
        b = _budget(face_every_n=3, scene_resets=False)
        b.decide(frame_seq=2)
        d = b.decide(frame_seq=3, scene_changed=True)
        assert d["face_embed"] is False


class TestMinInterval:
    def test_suppresses_run_within_interval(self):
        clk = _Clock()
        b = _budget(face_every_n=1, face_min_interval_s=1.0, clock=clk)
        assert b.decide(frame_seq=1)["face_embed"] is True
        clk.advance(0.5)
        assert b.decide(frame_seq=2)["face_embed"] is False, "within interval -> suppressed"
        clk.advance(0.6)
        assert b.decide(frame_seq=3)["face_embed"] is True, "interval elapsed -> runs"

    def test_first_run_always_allowed(self):
        clk = _Clock()
        b = _budget(face_every_n=1, face_min_interval_s=5.0, clock=clk)
        assert b.decide(frame_seq=1)["face_embed"] is True

    def test_min_interval_zero_is_never_suppressive(self):
        b = _budget(face_every_n=1, face_min_interval_s=0.0)
        for s in range(1, 4):
            assert b.decide(frame_seq=s)["face_embed"] is True


class TestTelemetry:
    def test_stage_ms_averages_and_max(self):
        b = _budget()
        b.add_sample("detect", 12.0)
        b.add_sample("detect", 14.0)
        b.add_sample("detect", 10.0)
        tel = b.telemetry()
        st = tel["stage_ms"]["detect"]
        assert st["samples"] == 3
        assert st["avg_ms"] == pytest.approx(12.0)
        assert st["max_ms"] == 14.0

    def test_runs_counted_per_stage(self):
        b = _budget()
        b.record_run("face_embed")
        b.record_run("face_embed")
        assert b.telemetry()["runs"]["face_embed"] == 2

    def test_processed_fps_none_below_two_samples(self):
        b = _budget()
        assert b.telemetry()["processed_fps"] is None

    def test_processed_fps_zero_after_idle_window(self):
        clk = _Clock()
        b = _budget(clock=clk, fps_window_s=5.0)
        b.mark_processed()
        clk.advance(0.05)
        b.mark_processed()
        clk.advance(10.0)  # idle well past the window
        assert b.telemetry()["processed_fps"] == 0.0

    def test_processed_fps_positive_while_active(self):
        clk = _Clock()
        b = _budget(clock=clk, fps_window_s=5.0)
        for _ in range(10):
            clk.advance(0.1)
            b.mark_processed()
        fps = b.telemetry()["processed_fps"]
        assert fps is not None and fps > 0.0 and fps < 20.0  # 10 frames / ~0.9s ≈ 11

    def test_reset_clears(self):
        b = _budget()
        b.mark_processed()
        b.add_sample("detect", 1.0)
        b.reset()
        assert b.telemetry()["frames_processed"] == 0


class TestValidation:
    def test_every_n_below_one_rejected(self):
        with pytest.raises(ValueError):
            VisionBudget(face_every_n=0)
