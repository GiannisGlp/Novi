"""Scheduler tests (plan 12, §20 Phase 15, §26 item 16)."""

from __future__ import annotations

import threading
import time
import unittest

from novi.brain.inference.request import InferenceRequest, RequestPriority
from novi.brain.inference.scheduler import InferenceScheduler


def _request(priority: RequestPriority = RequestPriority.NORMAL, **kwargs) -> InferenceRequest:
    return InferenceRequest(priority=priority, **kwargs)


class InferenceSchedulerTests(unittest.TestCase):
    def test_priority_order_fifo_within_class(self) -> None:
        scheduler = InferenceScheduler(max_concurrent=1)
        scheduler.submit(_request(RequestPriority.LOW, purpose="low"))
        scheduler.submit(_request(RequestPriority.HIGH, purpose="high"))
        scheduler.submit(_request(RequestPriority.NORMAL, purpose="normal"))
        first = scheduler.acquire()
        self.assertEqual(first.request.purpose, "high")
        scheduler.release(first.request_id)
        second = scheduler.acquire()
        self.assertEqual(second.request.purpose, "normal")
        scheduler.release(second.request_id)
        third = scheduler.acquire()
        self.assertEqual(third.request.purpose, "low")
        scheduler.release(third.request_id)
        self.assertIsNone(scheduler.acquire())

    def test_max_concurrent_blocks_acquire(self) -> None:
        scheduler = InferenceScheduler(max_concurrent=1)
        first = scheduler.submit(_request(RequestPriority.HIGH))
        second = scheduler.submit(_request(RequestPriority.NORMAL))
        running = scheduler.acquire()
        self.assertIsNotNone(running)
        self.assertIsNone(scheduler.acquire())
        scheduler.release(first.request_id)
        next_running = scheduler.acquire()
        self.assertEqual(next_running.request_id, second.request_id)

    def test_cancel_queued_request(self) -> None:
        scheduler = InferenceScheduler(max_concurrent=1)
        first = scheduler.submit(_request(RequestPriority.HIGH))
        second = scheduler.submit(_request(RequestPriority.NORMAL))
        scheduler.acquire()
        self.assertTrue(scheduler.cancel(second.request_id))
        self.assertFalse(scheduler.cancel("missing"))
        scheduler.release(first.request_id)
        # The cancelled request must be skipped, not returned.
        self.assertIsNone(scheduler.acquire())

    def test_cancel_running_marks_cancelling(self) -> None:
        scheduler = InferenceScheduler(max_concurrent=1)
        running = scheduler.submit(_request(RequestPriority.HIGH))
        scheduler.acquire()
        self.assertTrue(scheduler.cancel(running.request_id))
        self.assertTrue(running.token.is_cancelled)

    def test_arrival_policy_cancel_background(self) -> None:
        cancelled: list[str] = []

        def on_cancel(request_id: str) -> None:
            cancelled.append(request_id)

        scheduler = InferenceScheduler(
            max_concurrent=2,
            arrival_policy="cancel_background",
            cancel_running=on_cancel,
        )
        background = scheduler.submit(_request(RequestPriority.BACKGROUND, purpose="bg"))
        scheduler.acquire()
        self.assertIn(background.request_id, scheduler._running)
        # A CRITICAL arrival triggers the cancel_background policy.
        scheduler.submit(_request(RequestPriority.CRITICAL, purpose="crit"))
        self.assertIn(background.request_id, cancelled)
        self.assertTrue(background.token.is_cancelled)

    def test_wait_for_slot_acquires_running_work(self) -> None:
        scheduler = InferenceScheduler(max_concurrent=1)
        running = scheduler.submit(_request(RequestPriority.HIGH))
        queued = scheduler.submit(_request(RequestPriority.NORMAL))
        first = scheduler.wait_for_slot(timeout=1.0)
        self.assertEqual(first.request_id, running.request_id)

        def release_later() -> None:
            time.sleep(0.05)
            scheduler.release(first.request_id)

        thread = threading.Thread(target=release_later)
        thread.start()
        second = scheduler.wait_for_slot(timeout=2.0)
        self.assertEqual(second.request_id, queued.request_id)
        thread.join()

    def test_snapshot_and_queue_depth(self) -> None:
        scheduler = InferenceScheduler()
        scheduler.submit(_request(RequestPriority.LOW, purpose="low"))
        scheduler.submit(_request(RequestPriority.BACKGROUND, purpose="bg"))
        depth = scheduler.queue_depth()
        self.assertEqual(depth["LOW"], 1)
        self.assertEqual(depth["BACKGROUND"], 1)
        snapshot = scheduler.snapshot()
        self.assertEqual(snapshot["arrival_policy"], "queue")


if __name__ == "__main__":
    unittest.main()
