"""Plan 19, Phase 5: neural perception cadence (power-aware).

The neural perception backend is the most expensive part of the cognitive loop.
For Jetson power budgets, perception should run every-Nth-cycle rather than
every cycle, while the rest of the loop keeps ticking. On skipped cycles the
brain reuses the last evidence (or reports a skip) instead of re-running the
expensive detector.

Pins:
  - `perception_every_n_cycles` config (default 1 = every cycle, unchanged);
  - when >1, the perception backend is invoked only on cadence multiples;
  - the loop still steps every cycle (no stall);
  - deterministic fakes unaffected (default cadence 1).
"""

from __future__ import annotations

import unittest

from novi.brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.tests.test_mac_brain import FakeCamera


class _CountingBackend(DeterministicPerceptionBackend):
    def __init__(self):
        self.calls = 0

    def detect(self, frame):
        self.calls += 1
        return (Detection("cup", 0.85, (0.1, 0.1, 0.5, 0.5)),)


def _brain(backend, **kw) -> MacBrain:
    cfg = MacBrainConfig(curiosity_enabled=False, **kw)
    return MacBrain(camera=FakeCamera(), perception=SpecialistPerception(backend), config=cfg)


class PerceptionCadenceTests(unittest.TestCase):
    def test_default_runs_every_cycle(self):
        backend = _CountingBackend()
        brain = _brain(backend)
        brain.start()
        try:
            for _ in range(4):
                brain.step()
            self.assertEqual(backend.calls, 4, "default cadence runs perception every cycle")
        finally:
            brain.stop()

    def test_every_nth_runs_on_cadence(self):
        backend = _CountingBackend()
        brain = _brain(backend, perception_every_n_cycles=2)
        brain.start()
        try:
            for _ in range(4):
                brain.step()
            # Cycle 1 runs (baseline, no prior evidence), cycle 2 runs (multiple),
            # cycle 3 skips, cycle 4 runs (multiple) = 3 calls, not 4.
            self.assertEqual(backend.calls, 3, "perception runs on cadence multiples + first-cycle baseline")
        finally:
            brain.stop()

    def test_loop_keeps_stepping_on_skipped_cycles(self):
        backend = _CountingBackend()
        brain = _brain(backend, perception_every_n_cycles=3)
        brain.start()
        try:
            for _ in range(6):
                brain.step()
            self.assertEqual(brain._cycle, 6, "the loop keeps stepping on skipped perception cycles")
        finally:
            brain.stop()


if __name__ == "__main__":
    unittest.main()
