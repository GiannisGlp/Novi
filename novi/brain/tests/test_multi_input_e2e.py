"""Multi-source concurrency E2E test — unified input architecture (north star §6).

Scenario (owner requirement R5): a remote owner sends a web-chat message while
Novi is interacting with someone at home via voice, and the camera reports a
presence transition — all at the same time. Every input must be consumed
exactly once through ONE cognition loop, with sensible priority handling.

Deterministic: fake camera, no network, no hardware, no LLM (fallback path).
"""

from __future__ import annotations

import threading
import unittest

from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.io import CameraFrame


class FakeCamera:
    """Deterministic frame source; payload carries scripted detections."""

    def __init__(self) -> None:
        self.n = 0

    def read(self) -> CameraFrame:
        self.n += 1
        return CameraFrame(
            frame_id=f"e2e-{self.n}",
            captured_at="t",
            width=1,
            height=1,
            payload=b"frame",
            metadata={"backend": "deterministic-e2e"},
        )

    def close(self) -> None:
        return None


class MultiSourceSimultaneousInputsTests(unittest.TestCase):
    def _brain(self) -> MacBrain:
        return MacBrain(
            camera=FakeCamera(),
            config=MacBrainConfig(curiosity_enabled=False),
        )

    def test_remote_message_home_voice_and_presence_same_cycle(self) -> None:
        brain = self._brain()
        brain.start()
        try:
            receipts = []

            # Producer 1: remote owner over HTTP (would be web chat).
            t1 = threading.Thread(
                target=lambda: receipts.append(
                    brain.submit("web:remote", "chat", {"text": "remind me about the door"})
                )
            )
            # Producer 2: in-home voice turn.
            t2 = threading.Thread(
                target=lambda: receipts.append(
                    brain.submit("voice:home", "message", {"text": "novi, what time is it"})
                )
            )
            # Producer 3: camera presence transition.
            t3 = threading.Thread(
                target=lambda: receipts.append(
                    brain.submit("camera", "presence.entered", {"person": "Alice"})
                )
            )
            # Producer 4: direct address must outrank everything.
            t4 = threading.Thread(
                target=lambda: receipts.append(
                    brain.submit("cli", "interrupt", {"text": "novi, stop"})
                )
            )
            for t in (t1, t2, t3, t4):
                t.start()
            for t in (t1, t2, t3, t4):
                t.join(timeout=5)

            self.assertEqual(len(receipts), 4)
            self.assertEqual(len(set(receipts)), 4, "receipts must be unique")

            # One cognition cycle consumes everything.
            step = brain.step()
            consumed = step.get("consumed_inputs", [])
            self.assertEqual(len(consumed), 4)
            sources = {c["source"] for c in consumed}
            self.assertEqual(sources, {"web:remote", "voice:home", "camera", "cli"})

            # Priority order: interrupt first, then speech (FIFO), then event.
            kinds = [c["kind"] for c in consumed]
            self.assertEqual(kinds[0], "interrupt")
            self.assertEqual(set(kinds[1:3]), {"chat", "message"})
            self.assertEqual(kinds[3], "presence.entered")

            # Speech inputs were admitted to durable memory like any utterance.
            admitted = [c for c in consumed if c.get("admitted")]
            self.assertEqual(len(admitted), 3)  # all but the presence event

            # Bus is empty afterwards; a second step consumes nothing.
            self.assertEqual(brain.input_bus.stats()["depth"], 0)
            step2 = brain.step()
            self.assertEqual(step2.get("consumed_inputs"), [])
        finally:
            brain.stop()

    def test_producers_never_blocked_while_stepping(self) -> None:
        """submit() latency stays microseconds even while the loop steps."""
        import time

        brain = self._brain()
        brain.start()
        try:
            worst_put_ms = 0.0
            stop_at = time.perf_counter() + 1.0
            i = 0
            while time.perf_counter() < stop_at:
                brain.step()
                t0 = time.perf_counter()
                brain.submit("perf", "chat", {"text": f"m{i}"})
                worst_put_ms = max(worst_put_ms, (time.perf_counter() - t0) * 1000.0)
                i += 1
            # North-star budget: producers never block on the brain lock (<10ms).
            self.assertLess(worst_put_ms, 10.0, f"submit took {worst_put_ms:.2f}ms")
            # Drain whatever queued so the bus is clean.
            brain.drain_inputs(max_items=512)
        finally:
            brain.stop()


if __name__ == "__main__":
    unittest.main()
