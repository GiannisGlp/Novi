"""Tests for novi/brain/initiative_scoring.py — plan 22 Phase 11.

Covers the target formula, policy bands, per-person cooldown (11.1),
per-event dedup (11.2) and conversation suppression (11.3).
"""

from __future__ import annotations

import unittest

from novi.brain.initiative_scoring import (
    CONSIDER,
    HOLD,
    INITIATE,
    MONITOR,
    SILENCE,
    InitiativeGate,
    InitiativeScorer,
    stable_event_key,
)


class InitiativeScorerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.scorer = InitiativeScorer()

    def test_strong_signals_reach_initiate(self) -> None:
        s = self.scorer.score(
            relevance=0.9, confidence=0.9, social_opportunity=0.9,
            novelty=0.9, expected_value=0.9, urgency=0.9,
            interruption_cost=0.02,
        )
        self.assertEqual(s.band, INITIATE)
        self.assertGreater(s.score, 0.85)

    def test_weak_signals_stay_silent(self) -> None:
        s = self.scorer.score(relevance=0.2, confidence=0.2, social_opportunity=0.1)
        self.assertEqual(s.band, SILENCE)

    def test_bands_are_monotonic(self) -> None:
        bands = [
            self.scorer.score(relevance=0.3, confidence=0.3, social_opportunity=0.3, novelty=0.3, expected_value=0.3, urgency=0.3).band,
            self.scorer.score(relevance=0.55, confidence=0.55, social_opportunity=0.55, novelty=0.55, expected_value=0.55, urgency=0.55).band,
            self.scorer.score(relevance=0.75, confidence=0.75, social_opportunity=0.75, novelty=0.75, expected_value=0.75, urgency=0.75).band,
        ]
        self.assertEqual(bands, [HOLD, MONITOR, CONSIDER])

    def test_interruption_cost_lowers_score(self) -> None:
        base = self.scorer.score(relevance=0.9, confidence=0.9, social_opportunity=0.9, novelty=0.9, expected_value=0.9, urgency=0.9)
        costly = self.scorer.score(relevance=0.9, confidence=0.9, social_opportunity=0.9, novelty=0.9, expected_value=0.9, urgency=0.9, interruption_cost=0.5)
        self.assertGreater(base.score, costly.score)
        self.assertIn("interruption_cost", costly.penalties)

    def test_fatigue_penalty_applied(self) -> None:
        s = self.scorer.score(relevance=0.9, confidence=0.9, social_opportunity=0.9, novelty=0.9, expected_value=0.9, urgency=0.9, fatigue_penalty=0.3)
        self.assertGreater(s.penalties["fatigue_penalty"], 0.0)

    def test_snapshot_explainable(self) -> None:
        s = self.scorer.score(relevance=0.8, confidence=0.8, social_opportunity=0.8, novelty=0.8, expected_value=0.8, urgency=0.5)
        snap = s.snapshot()
        self.assertIn("band", snap)
        self.assertIn("components", snap)
        self.assertIn("relevance", snap["components"])


class InitiativeGateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.gate = InitiativeGate(per_person_cooldown_cycles=10)

    def test_per_person_cooldown_blocks_same_person_only(self) -> None:
        self.assertTrue(self.gate.allow(person="vano", cycle=1)[0])
        self.gate.note_spoken(person="vano", cycle=1)
        allowed, reason = self.gate.allow(person="vano", cycle=5)
        self.assertFalse(allowed)
        self.assertEqual(reason, "per_person_cooldown")
        # a different person is free (plan §2.2: no repeated greetings)
        self.assertTrue(self.gate.allow(person="davit", cycle=5)[0])

    def test_event_dedup_blocks_repeated_same_event(self) -> None:
        key = stable_event_key({"kind": "presence.entered", "entity": "vano", "payload": {"seq": 1}})
        self.assertTrue(self.gate.allow(person="vano", cycle=1, event_key=key)[0])
        self.gate.note_spoken(person="vano", cycle=1, event_key=key)
        allowed, reason = self.gate.allow(person="vano", cycle=5, event_key=key)
        self.assertFalse(allowed)
        self.assertEqual(reason, "event_dedup")

    def test_stable_event_key_is_deterministic_and_sensor_agnostic(self) -> None:
        a = stable_event_key({"kind": "object.moved", "entity": "mug", "payload": {"seq": 7}})
        b = stable_event_key({"payload": {"seq": 7}, "entity": "mug", "kind": "object.moved"})
        self.assertEqual(a, b)

    def test_conversation_suppression_holds_proactive(self) -> None:
        allowed, reason = self.gate.allow(person="vano", cycle=1, user_speaking=True)
        self.assertFalse(allowed)
        self.assertEqual(reason, "conversation_suppression")
        allowed, reason = self.gate.allow(person="vano", cycle=1, novi_composing=True)
        self.assertFalse(allowed)
        self.assertEqual(reason, "conversation_suppression")

    def test_safety_overrides_everything(self) -> None:
        allowed, reason = self.gate.allow(
            person="vano", cycle=1, user_speaking=True, safety=True
        )
        self.assertTrue(allowed)
        self.assertEqual(reason, "safety_override")


if __name__ == "__main__":
    unittest.main()
