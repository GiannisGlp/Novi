"""Compat event retention bounds (plan 02, Phase 1 / Test A).

The flattened ``MacBrain.events`` view must stay bounded at the source no
matter how many events are emitted — with or without a web server draining.
"""

import unittest

from novi.brain.engine import WEB_COMPAT_EVENT_HISTORY, MacBrain, MacBrainConfig


def _make_brain(limit: int | None = None) -> MacBrain:
    if limit is None:
        return MacBrain()
    return MacBrain(config=MacBrainConfig(compat_event_history=limit))


class CompatEventBoundTests(unittest.TestCase):
    def test_overflow_stays_bounded(self) -> None:
        brain = _make_brain(limit=128)
        for i in range(5000):
            brain._emit("probe.event", {"i": i})
        self.assertLessEqual(len(brain.events), 128)

    def test_newest_retained_oldest_evicted(self) -> None:
        brain = _make_brain(limit=100)
        for i in range(250):
            brain._emit("probe.event", {"i": i})
        self.assertEqual(len(brain.events), 100)
        retained = [e["payload"]["i"] for e in brain.events]
        self.assertEqual(retained[0], 150)
        self.assertEqual(retained[-1], 249)

    def test_default_limit_matches_authoritative_store(self) -> None:
        brain = _make_brain()
        self.assertEqual(brain._compat_event_limit(), WEB_COMPAT_EVENT_HISTORY)
        for i in range(WEB_COMPAT_EVENT_HISTORY + 2000):
            brain._emit("probe.event", {"i": i})
        self.assertLessEqual(len(brain.events), WEB_COMPAT_EVENT_HISTORY)
        # Newest event survives; oldest retained is inside the expected window.
        self.assertEqual(brain.events[-1]["payload"]["i"], WEB_COMPAT_EVENT_HISTORY + 1999)
        self.assertGreaterEqual(brain.events[0]["payload"]["i"], 2000)

    def test_bounded_without_any_drain(self) -> None:
        """Auto-step mode never calls the legacy drain path; the brain must
        still stay bounded (the pre-fix OOM: _drain was the only trim)."""
        brain = _make_brain(limit=64)
        for i in range(3000):
            brain._emit("probe.event", {"i": i})
            # Deliberately never draining, like the auto-step loop.
        self.assertLessEqual(len(brain.events), 64)

    def test_large_payloads_not_retained(self) -> None:
        brain = _make_brain(limit=16)
        big = bytes(256 * 1024)
        brain._emit("probe.frame", {"frame": big, "frame_id": "f1"})
        stored = brain.events[-1]["payload"]
        self.assertEqual(stored["frame_id"], "f1")
        self.assertIsInstance(stored["frame"], dict)
        self.assertTrue(stored["frame"].get("truncated"))
        # The raw buffer must not be reachable from the retained event.
        self.assertIsNot(stored["frame"], big)

    def test_small_bytes_and_scalars_pass_through(self) -> None:
        brain = _make_brain(limit=16)
        brain._emit("probe.ok", {"n": 3, "s": "x", "small": b"ab"})
        payload = brain.events[-1]["payload"]
        self.assertEqual((payload["n"], payload["s"], payload["small"]), (3, "x", b"ab"))

    def test_event_stays_list_compatible(self) -> None:
        brain = _make_brain(limit=8)
        for i in range(20):
            brain._emit("probe.event", {"i": i})
        self.assertIsInstance(brain.events, list)
        self.assertEqual(brain.events[-1]["payload"]["i"], 19)
        self.assertEqual(len(brain.events[-4:]), 4)
        self.assertEqual(len(list(iter(brain.events))), 8)


if __name__ == "__main__":
    unittest.main()
