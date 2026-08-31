"""Tests for novi/brain/emotional_timing.py — emotional timing.

Plan 24 Phase 16: reaction delay, conversation phase, user speaking state,
pause sensitivity, interruption cost, cooldown. Do not immediately respond to
every emotional cue. Thresholds are configurable, not universal human rules.
"""

from __future__ import annotations

import unittest

from novi.brain.emotional_timing import EmotionalTiming, TimingDecider


class EmotionalTimingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.timing = EmotionalTiming()
        self.decider = TimingDecider()

    def test_defaults_are_configurable(self) -> None:
        self.assertGreater(self.timing.reaction_delay_seconds, 0.0)
        self.assertGreater(self.timing.pause_sensitivity, 0.0)
        self.assertGreater(self.timing.cooldown_cycles, 0)

    def test_short_pause_waits(self) -> None:
        # plan §20: user pauses for 1 second → wait
        decision = self.decider.decide(user_pause_seconds=1.0)
        self.assertEqual(decision["action"], "wait")

    def test_long_silence_after_distress_evaluates_support(self) -> None:
        # plan §20: silent 8s after distressing topic → evaluate whether support is useful
        decision = self.decider.decide(
            user_pause_seconds=8.0, distressing_topic=True
        )
        self.assertEqual(decision["action"], "evaluate_support")

    def test_user_speaking_blocks_response(self) -> None:
        decision = self.decider.decide(user_speaking=True)
        self.assertEqual(decision["action"], "wait")

    def test_clear_turn_allows_response(self) -> None:
        decision = self.decider.decide(user_pause_seconds=2.0, user_speaking=False)
        self.assertEqual(decision["action"], "respond")

    def test_cooldown_blocks_immediate_repeat(self) -> None:
        self.decider.note_responded(cycle=10)
        decision = self.decider.decide(user_pause_seconds=2.0, cycle=11)
        self.assertEqual(decision["action"], "wait")

    def test_thresholds_are_configurable(self) -> None:
        # a higher threshold raises the bar: 3s pause waits under a 5s threshold
        custom = TimingDecider(pause_threshold_seconds=5.0, distress_silence_seconds=15.0)
        decision = custom.decide(user_pause_seconds=3.0)
        self.assertEqual(decision["action"], "wait")  # 3s < 5s threshold
        # but a 6s pause clears the raised bar
        decision = custom.decide(user_pause_seconds=6.0)
        self.assertEqual(decision["action"], "respond")

    def test_snapshot_roundtrip(self) -> None:
        self.decider.note_responded(cycle=5)
        restored = TimingDecider.from_snapshot(self.decider.snapshot())
        self.assertEqual(restored.last_responded_cycle, self.decider.last_responded_cycle)


if __name__ == "__main__":
    unittest.main()
