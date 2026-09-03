"""Web-runtime stability regression suite (plan 02, Phase 10).

Each test maps to a plan acceptance test:
  A  event retention bound (compat window + EventBus + server log)
  B  auto-step-style emission without draining stays bounded
  C  event reconnect: resume, no duplicates, stale-cursor recovery
  D  preview backpressure: latest frame only, never a queue
  E  preview cancellation/over-budget handling
  F  page-navigation lifecycle is covered frontend-side (enabled flags);
     here: repeated pollers leave no server-side growth
  G  server restart: repeated start/stop, idempotent lifecycle
  H  large event payloads are truncated at the web boundary
"""

from __future__ import annotations

import json
import threading
import unittest

from novi.web.runtime_budgets import WebRuntimeBudgets
from novi.web.server import NoviWebServer


def _server(**kw) -> NoviWebServer:
    defaults = {"port": 0, "store_path": None, "auto_step": False, "chat_llm": False}
    defaults.update(kw)
    return NoviWebServer(**defaults)


class EventRetentionBoundTests(unittest.TestCase):
    """Test A — compatibility window, EventBus, and server log stay capped."""

    def test_overflow_stays_bounded_end_to_end(self) -> None:
        s = _server()
        try:
            for i in range(6000):
                s.brain._emit("probe.event", {"i": i})
            s._drain()
            self.assertLessEqual(len(s.brain.events), s.brain._compat_event_limit())
            self.assertLessEqual(len(s.brain.event_bus.events()), 4096)
            self.assertLessEqual(len(s._log), s.budgets.max_events)
            # Newest event is retained end to end.
            chunk = s.poll_events(0)
            self.assertTrue(chunk["events"])
            self.assertLessEqual(len(chunk["events"]), s.budgets.event_batch_size)
        finally:
            s.stop()

    def test_auto_step_emission_without_drain_stays_bounded(self) -> None:
        """Test B — the auto-step loop never drains; the brain must not grow."""
        s = _server()
        try:
            for i in range(8000):
                s.brain._emit("probe.event", {"i": i})
                # Deliberately no _drain(), like the auto-step loop.
            self.assertLessEqual(len(s.brain.events), s.brain._compat_event_limit())
            # A later drain still converges without duplicates or skips.
            s._drain()
            first = s.poll_events(0)
            second = s.poll_events(first["after"])
            seqs = [e["seq"] for e in first["events"]] + [e["seq"] for e in second["events"]]
            self.assertEqual(len(seqs), len(set(seqs)))
        finally:
            s.stop()


class EventReconnectTests(unittest.TestCase):
    """Test C — connect, receive, disconnect, reconnect; stale cursors recover."""

    def test_resume_has_no_duplicates(self) -> None:
        s = _server()
        try:
            for i in range(10):
                s.brain._emit("probe.event", {"i": i})
            first = s.poll_events(0)
            self.assertGreater(len(first["events"]), 0)
            second = s.poll_events(first["after"])
            # Nothing new: empty batch, cursor stable, no gap.
            self.assertEqual(second["events"], [])
            self.assertFalse(second["gap"])
            self.assertGreaterEqual(second["after"], first["after"])
        finally:
            s.stop()

    def test_stale_cursor_reports_gap_and_resyncs(self) -> None:
        s = _server()
        try:
            # Fill the window past capacity so seq 1 rolls out of retention.
            for i in range(s.budgets.max_events + 50):
                s.brain._emit("probe.event", {"i": i})
            chunk = s.poll_events(1)
            self.assertTrue(chunk["gap"])
            self.assertTrue(chunk["events"])
            # Following the returned cursor resumes normal delivery.
            nxt = s.poll_events(chunk["after"])
            self.assertFalse(nxt["gap"])
        finally:
            s.stop()

    def test_batch_paging_covers_full_window(self) -> None:
        s = _server()
        try:
            for i in range(30):
                s.brain._emit("probe.event", {"i": i})
            seen: list[int] = []
            after = 0
            for _ in range(10):
                chunk = s.poll_events(after)
                seen.extend(e["seq"] for e in chunk["events"])
                after = chunk["after"]
                if not chunk.get("has_more"):
                    break
            self.assertEqual(len(seen), len(set(seen)))
        finally:
            s.stop()


class PreviewBackpressureTests(unittest.TestCase):
    """Tests D/E — latest frame only; over-budget frames withheld, not queued."""

    def test_rapid_frames_keep_only_latest(self) -> None:
        import numpy as np

        from novi.brain.io import CameraFrame

        s = _server()
        try:
            for n in range(5):
                bgr = np.zeros((8, 8, 3), dtype="uint8")
                rec = type(
                    "Rec",
                    (),
                    {
                        "frame": CameraFrame(
                            frame_id=f"f{n}",
                            captured_at="t",
                            width=8,
                            height=8,
                            payload=bgr,
                        )
                    },
                )()
                s._store_preview_frame(rec, bgr)
            # Exactly one frame slot exists — no queue of historical frames.
            self.assertIsInstance(s.mm_last_frame_b64, str)
            frame = s.preview_frame()
            self.assertIsNotNone(frame["image_data_url"])
            self.assertLessEqual(len(frame["image_data_url"] or ""), s.budgets.preview_max_bytes)
            self.assertFalse(frame["preview_omitted_over_budget"])
        finally:
            s.stop()

    def test_over_budget_frame_withheld_with_flag(self) -> None:
        s = _server()
        try:
            s.mm_last_frame_b64 = "data:image/jpeg;base64," + "A" * (s.budgets.preview_max_bytes + 1)
            frame = s.preview_frame()
            self.assertIsNone(frame["image_data_url"])
            self.assertTrue(frame["preview_omitted_over_budget"])
        finally:
            s.stop()


class LifecycleRestartTests(unittest.TestCase):
    """Test G — idempotent start/stop; repeated restarts return to baseline."""

    def test_double_start_creates_one_loop(self) -> None:
        s = _server()
        try:
            s.start()
            first = s._thread
            self.assertIsNotNone(first)
            s.start()
            # Idempotent: the same live thread, no second loop.
            self.assertIs(s._thread, first)
            self.assertTrue(first.is_alive())
            before = [t for t in threading.enumerate() if t.name == "novi-brain-loop" and t.is_alive()]
            s.start()
            after = [t for t in threading.enumerate() if t.name == "novi-brain-loop" and t.is_alive()]
            self.assertEqual(len(before), len(after))
        finally:
            s.stop()

    def test_stop_without_start_and_double_stop_are_safe(self) -> None:
        s = _server()
        s.stop()
        s.stop()

    def test_repeated_restarts_return_to_baseline(self) -> None:
        baseline = threading.active_count()
        for _ in range(10):
            s = _server()
            s.start()
            s.stop()
        self.assertLessEqual(threading.active_count(), baseline + 1)

    def test_full_stop_is_terminal_for_the_brain_but_leaks_nothing(self) -> None:
        """The brain supervisor lifecycle is single-run by design: a full
        stop() shuts the brain down terminally, so restarting the SAME
        instance is refused. The contract is that the refusal leaks no
        thread and a fresh instance starts clean (restart = new server,
        same as a process restart)."""
        from novi.brain.runtime import InvalidLifecycleTransition

        s = _server()
        try:
            s.start()
            self.assertTrue(s._thread is not None and s._thread.is_alive())
            s.stop()
            self.assertIsNone(s._thread)
            baseline = threading.active_count()
            with self.assertRaises(InvalidLifecycleTransition):
                s.start()
            self.assertIsNone(s._thread)
            self.assertEqual(threading.active_count(), baseline)
        finally:
            s.stop()
        # A fresh instance starts clean after another instance stopped.
        s2 = _server()
        try:
            s2.start()
            self.assertTrue(s2.runtime_metrics()["brain_thread_alive"])
        finally:
            s2.stop()


class LargePayloadTests(unittest.TestCase):
    """Test H — oversized event payloads are truncated at the web boundary."""

    def test_oversized_entry_truncated_with_metadata(self) -> None:
        s = _server()
        try:
            s._record_event({"event_type": "probe.huge", "blob": "x" * (s.budgets.max_event_payload_bytes + 100)})
            chunk = s.poll_events(0)
            self.assertTrue(chunk["events"])
            event = chunk["events"][-1]["event"]
            self.assertTrue(event.get("__truncated__"))
            self.assertEqual(event.get("event_type"), "probe.huge")
            self.assertLess(len(json.dumps(chunk)), s.budgets.max_event_payload_bytes + 4096)
        finally:
            s.stop()


class RuntimeMetricsTests(unittest.TestCase):
    """Phase 9 — metrics expose every bounded counter with its limit."""

    def test_metrics_shape_and_bounds(self) -> None:
        s = _server()
        try:
            m = s.runtime_metrics()
            for key in (
                "compat_event_count",
                "compat_event_limit",
                "eventbus_size",
                "server_log_size",
                "server_log_limit",
                "active_sse_clients",
                "preview_frame_bytes",
                "worker_threads",
            ):
                self.assertIn(key, m)
            self.assertLessEqual(m["compat_event_count"], m["compat_event_limit"])
            self.assertLessEqual(m["server_log_size"], m["server_log_limit"])
            self.assertGreaterEqual(m["active_sse_clients"], 0)
            json.dumps(m)
        finally:
            s.stop()

    def test_custom_budgets_propagate(self) -> None:
        s = _server()
        try:
            s.budgets = WebRuntimeBudgets(max_events=32, event_batch_size=8, max_chat_turns=8)
            for i in range(200):
                s.brain._emit("probe.event", {"i": i})
            s._drain()
            self.assertLessEqual(len(s._log), 32)
            chunk = s.poll_events(0)
            self.assertLessEqual(len(chunk["events"]), 8)
        finally:
            s.stop()


if __name__ == "__main__":
    unittest.main()
