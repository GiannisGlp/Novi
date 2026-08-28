"""Tests: camera acquisition — bounded queue, drop-oldest under load,
health state machine, freshness decay (doc 01_CAMERA_ACQUISITION.md).

CameraFeed wraps a CameraProvider with:
- own bounded queue; cognitive loop samples at its own rate;
- drop-oldest under pressure, with dropped-frame counters as telemetry
  (never silent loss);
- AVAILABLE → DEGRADED → FAILED → AVAILABLE health transitions surfaced;
- freshness: frames go stale if the stream stops (stale-vision handling).
"""

from __future__ import annotations

import pytest

from novi.brain.io import CameraFrame
from novi.perception.camera import CameraFeed, CameraHealth, FrameRecord


def _frame(fid: str = "f1", captured_at: str = "t0") -> CameraFrame:
    return CameraFrame(
        frame_id=fid,
        captured_at=captured_at,
        width=640,
        height=480,
        payload=b"rgb-bytes",
    )


class _ScriptedProvider:
    """Deterministic provider yielding queued frames then raising."""

    def __init__(self, frames: list[CameraFrame]) -> None:
        self.frames = list(frames)
        self.opened = False
        self.closed = False
        self.fail_reads = False

    def open(self) -> None:
        self.opened = True

    def read(self) -> CameraFrame:
        if self.fail_reads or not self.frames:
            self.fail_reads = True
            raise IOError("camera unplugged")
        return self.frames.pop(0)

    def close(self) -> None:
        self.closed = True


class TestQueueAndDrops:
    def test_frames_flow_through_bounded_queue_in_order(self):
        prov = _ScriptedProvider([_frame("a"), _frame("b"), _frame("c")])
        feed = CameraFeed(prov, queue_size=8)
        feed.start()
        got = [feed.poll().frame_id for _ in range(3)]
        assert got == ["a", "b", "c"]
        feed.stop()

    def test_drop_oldest_under_pressure_with_counter(self):
        frames = [_frame(str(i)) for i in range(10)]
        prov = _ScriptedProvider(frames)
        feed = CameraFeed(prov, queue_size=3)
        feed.start()
        # don't poll: capture thread overflows the queue of 3 with 10 frames
        import time

        deadline = time.time() + 2.0
        while time.time() < deadline and feed.dropped < 5:
            time.sleep(0.01)
        feed.stop()
        assert feed.dropped >= 5, "drops must be counted, not silent"
        rec = feed.poll()
        assert isinstance(rec, FrameRecord)
        assert rec.frame.frame_id != "0", "oldest frame was dropped first"

    def test_poll_on_empty_returns_none_not_block(self):
        prov = _ScriptedProvider([])
        feed = CameraFeed(prov, queue_size=2)
        feed.start()
        assert feed.poll(timeout_s=0.05) is None
        feed.stop()


class TestHealth:
    def test_starts_unknown_until_started(self):
        prov = _ScriptedProvider([])
        feed = CameraFeed(prov, queue_size=2)
        assert feed.health is CameraHealth.UNKNOWN
        feed.start()
        assert feed.health in (CameraHealth.AVAILABLE, CameraHealth.DEGRADED)
        feed.stop()

    def test_provider_failure_degrades_then_fails(self):
        prov = _ScriptedProvider([_frame("only")])
        feed = CameraFeed(prov, queue_size=4)
        feed.start()
        import time

        deadline = time.time() + 2.0
        while time.time() < deadline and feed.health is not CameraHealth.FAILED:
            time.sleep(0.01)
        assert feed.health is CameraHealth.FAILED
        assert feed.consecutive_failures >= 2
        feed.stop()

    def test_recovery_after_failure_returns_to_available(self):
        class Recovering(_ScriptedProvider):
            def __init__(self):
                super().__init__([])
                self.calls = 0
                self._good = _frame("back")

            def read(self):  # fail 3 times, then produce forever
                self.calls += 1
                if self.calls <= 3:
                    raise IOError("glitch")
                return self._good

        feed = CameraFeed(Recovering(), queue_size=2)
        feed.start()
        import time

        deadline = time.time() + 3.0
        while time.time() < deadline and feed.health is not CameraHealth.AVAILABLE:
            time.sleep(0.02)
        assert feed.health is CameraHealth.AVAILABLE
        assert feed.recoveries == 1
        feed.stop()


class TestFreshness:
    def test_frame_record_carries_received_age_and_staleness(self):
        now = 1000.0
        rec = FrameRecord(frame=_frame(), received_monotonic=now - 0.2, seq=7)
        assert rec.age_s(now) == pytest.approx(0.2, abs=1e-6)
        assert rec.is_stale(now, stale_after_s=0.1) is True
        assert rec.is_stale(now, stale_after_s=0.5) is False

    def test_feed_reports_stale_when_no_recent_frames(self):
        prov = _ScriptedProvider([])
        feed = CameraFeed(prov, queue_size=2)
        assert feed.last_frame_age_s() is None  # never saw a frame


class TestLifecycle:
    def test_stop_closes_provider_and_marks_offline(self):
        prov = _ScriptedProvider([])
        feed = CameraFeed(prov, queue_size=2)
        feed.start()
        feed.stop()
        assert prov.closed is True
        assert feed.health is CameraHealth.OFFLINE

    def test_double_start_is_noop(self):
        prov = _ScriptedProvider([])
        feed = CameraFeed(prov, queue_size=2)
        feed.start()
        feed.start()  # must not raise / spawn second thread
        feed.stop()
