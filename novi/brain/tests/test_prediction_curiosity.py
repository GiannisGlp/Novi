"""Plan 19, Phase 3: prediction-error → curiosity loop.

A sequence prediction violation (A appeared, B was expected within k cycles but
never did) is a *surprise* signal. It should feed curiosity so Novi acts on the
unexpected — e.g. emit a `curiosity.surprise` event and, when idle, spawn a
bounded investigate goal for the missing target ("I expected the cup near the
book — did someone move it?").

Pins:
  - a sequence violation emits `curiosity.surprise` with the source/target;
  - when curiosity is enabled and no goal is active, the violation spawns an
    investigate goal for the missing target;
  - predictions never write world state (unchanged).
"""

from __future__ import annotations

import unittest

from novi.brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.tests.test_mac_brain import FakeCamera


class _SeqBackend(DeterministicPerceptionBackend):
    """cup for 2 cycles, then book for 2 cycles, then cup again (learns cup->book)."""

    def __init__(self):
        self._n = 0

    def detect(self, frame):
        self._n += 1
        if self._n % 4 in (1, 2):
            return (Detection("cup", 0.85, (0.1, 0.1, 0.5, 0.5)),)
        return (Detection("book", 0.85, (0.1, 0.1, 0.5, 0.5)),)


class _ViolationBackend(DeterministicPerceptionBackend):
    """cup, cup, book (learns cup->book), then cup again but book NEVER returns
    within the window -> the cup->book prediction is violated."""

    _SEQ = ["cup", "cup", "book", "cup", "cup", "lamp", "lamp", "lamp"]

    def __init__(self):
        self._n = 0

    def detect(self, frame):
        label = self._SEQ[self._n % len(self._SEQ)]
        self._n += 1
        return (Detection(label, 0.85, (0.1, 0.1, 0.5, 0.5)),)


def _brain(backend, **kw) -> MacBrain:
    cfg = MacBrainConfig(curiosity_enabled=True, **kw)
    return MacBrain(camera=FakeCamera(), perception=SpecialistPerception(backend), config=cfg)


class PredictionCuriosityTests(unittest.TestCase):
    def test_sequence_violation_emits_curiosity_surprise(self):
        brain = _brain(_ViolationBackend())
        brain.start()
        try:
            for _ in range(8):
                brain.step()
            kinds = {e.get("event_type") for e in brain.events}
            self.assertIn("curiosity.surprise", kinds, "a sequence violation must emit curiosity.surprise")
        finally:
            brain.stop()

    def test_violation_spawns_investigate_goal_for_missing_target(self):
        brain = _brain(_ViolationBackend())
        brain.start()
        try:
            for _ in range(8):
                brain.step()
            states = [s for s in (brain.goals.history + [brain.goals.active]) if s is not None]
            investigate = [s for s in states if s.goal.kind == "investigate"]
            self.assertTrue(investigate, "a sequence violation should spawn an investigate goal when idle")
            # The surprise-driven goal targets the MISSING entity (book), not a
            # novel one — Novi investigates what it expected but didn't find.
            self.assertIn("book", {s.goal.target for s in investigate})
        finally:
            brain.stop()

    def test_no_surprise_without_violation(self):
        brain = _brain(_SeqBackend())  # cup->book always confirmed, no violation
        brain.start()
        try:
            for _ in range(8):
                brain.step()
            kinds = {e.get("event_type") for e in brain.events}
            self.assertNotIn("curiosity.surprise", kinds, "no violation means no surprise")
        finally:
            brain.stop()


if __name__ == "__main__":
    unittest.main()
