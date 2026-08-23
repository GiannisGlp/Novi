"""Phase E1 (gap-audit plan 13): Soul slow personality learning.

Pins:
  - learn_from_interaction moves mapped traits by at most ±0.01 per event;
  - audit check #5: playfulness 0.60 → 0.64 over 5 play interactions;
  - unreinforced traits decay back to baseline over ~100 cycles;
  - interaction history is recorded per person and type;
  - motivation_priority weights attention relevance and goal priority
    deterministically.
"""

import unittest

from novi.brain.soul import (
    DEFAULT_TRAITS,
    MAX_INTERACTION_DELTA,
    TRAIT_DECAY_HORIZON_CYCLES,
    Soul,
)


class LearnFromInteractionTests(unittest.TestCase):
    def test_playfulness_rises_060_to_064_over_five_plays(self):
        soul = Soul()
        self.assertAlmostEqual(soul.personality.traits["playfulness"], 0.60)
        for _ in range(5):
            soul.learn_from_interaction("vano", "play")
        self.assertAlmostEqual(soul.personality.traits["playfulness"], 0.64)

    def test_delta_is_clamped_to_max(self):
        soul = Soul()
        before = soul.personality.traits["playfulness"]
        soul.learn_from_interaction("x", "play", delta=99.0)
        self.assertAlmostEqual(soul.personality.traits["playfulness"], before + MAX_INTERACTION_DELTA)

    def test_unknown_interaction_type_defaults_to_playfulness(self):
        soul = Soul()
        before = soul.personality.traits["playfulness"]
        soul.learn_from_interaction("x", "mystery_type")
        # Unknown types use the small default delta, still on playfulness.
        self.assertAlmostEqual(soul.personality.traits["playfulness"], before + 0.005)

    def test_traits_stay_bounded(self):
        soul = Soul()
        for _ in range(10000):
            soul.learn_from_interaction("x", "boundary")  # pushes caution up
            soul.decay_toward_baseline(cycles=TRAIT_DECAY_HORIZON_CYCLES)
        for name, v in soul.personality.traits.items():
            self.assertTrue(0.0 <= v <= 1.0, name)

    def test_history_recorded_per_person(self):
        soul = Soul()
        soul.learn_from_interaction("Vano", "play")
        soul.learn_from_interaction("vano", "play")
        self.assertEqual(soul.interaction_history["vano"]["play"], 2)


class DecayToBaselineTests(unittest.TestCase):
    def test_decay_returns_trait_to_baseline_over_horizon(self):
        soul = Soul()
        for _ in range(5):
            soul.learn_from_interaction("x", "play")
        raised = soul.personality.traits["playfulness"]
        self.assertGreater(raised, DEFAULT_TRAITS["playfulness"])
        # No reinforcement: decay in one horizon-sized step returns to baseline.
        soul.decay_toward_baseline(cycles=TRAIT_DECAY_HORIZON_CYCLES)
        self.assertAlmostEqual(soul.personality.traits["playfulness"], DEFAULT_TRAITS["playfulness"], places=6)

    def test_partial_decay_is_proportional(self):
        soul = Soul()
        for _ in range(5):
            soul.learn_from_interaction("x", "play")
        raised = soul.personality.traits["playfulness"]
        base = DEFAULT_TRAITS["playfulness"]
        soul.decay_toward_baseline(cycles=50)  # half the gap closed
        expected = raised + (base - raised) * 0.5
        self.assertAlmostEqual(soul.personality.traits["playfulness"], expected, places=6)


class MotivationPriorityTests(unittest.TestCase):
    def test_attention_relevance_boosts_understand(self):
        soul = Soul()
        plain = dict(soul.motivation_priority())
        boosted = dict(soul.motivation_priority(attention_relevance={"cup": 0.9}))
        self.assertGreater(boosted["understand"], plain["understand"])

    def test_goal_priority_boosts_help(self):
        soul = Soul()
        plain = dict(soul.motivation_priority())
        boosted = dict(soul.motivation_priority(goal_priority=1.0))
        self.assertGreater(boosted["help"], plain["help"])

    def test_deterministic_sorted_output(self):
        soul = Soul()
        out = soul.motivation_priority(goal_priority=0.5, attention_relevance={"a": 0.5})
        names = [n for n, _ in out]
        weights = [w for _, w in out]
        self.assertEqual(names, sorted(names, key=lambda n: -dict(out)[n]))
        self.assertEqual(weights, sorted(weights, reverse=True))
        self.assertEqual(out, soul.motivation_priority(goal_priority=0.5, attention_relevance={"a": 0.5}))


if __name__ == "__main__":
    unittest.main()
