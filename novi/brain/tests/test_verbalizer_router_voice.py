"""Tests for plan 22 Phase 15–17: verbalizer, tier router, voice turn session."""

from __future__ import annotations

import unittest

from novi.brain.models.tier_router import (
    COMPLEX,
    FAST,
    NEVER_MODEL_TRUTH,
    NORMAL,
    SPECIALIZED,
    TIER_MODELS,
    RoutingSignals,
    TierRouter,
)
from novi.brain.verbalizer import Verbalizer
from novi.voice.turn_session import TurnSession


class VerbalizerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.v = Verbalizer()

    def test_length_control_respects_verbosity(self) -> None:
        long_text = " ".join(["word"] * 120)
        out = self.v.verbalize(long_text, verbosity="short")
        self.assertLessEqual(len(out.text.split()), 40)
        self.assertIn("truncated_to_short", out.controls)

    def test_hedging_only_on_low_confidence(self) -> None:
        out = self.v.verbalize("the mug moved.", confidence=0.4)
        self.assertTrue(out.text.startswith("I think"))
        out2 = self.v.verbalize("the mug moved.", confidence=0.9)
        self.assertFalse(out2.text.startswith("I think"))

    def test_question_form(self) -> None:
        out = self.v.verbalize("that was the blue bottle", question=True)
        self.assertTrue(out.text.endswith("?"))

    def test_no_mangling_of_existing_questions(self) -> None:
        out = self.v.verbalize("is it still there?", question=True)
        self.assertEqual(out.text, "is it still there?")

    def test_natural_preference_rule(self) -> None:
        robotic = "I acknowledge the information you have provided."
        natural = "Yeah, that makes sense."
        self.assertEqual(self.v.prefer_natural(robotic, natural), natural)

    def test_empty_text_returns_empty(self) -> None:
        out = self.v.verbalize("")
        self.assertEqual(out.text, "")


class TierRouterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.router = TierRouter()

    def test_reflex_uses_fast_model(self) -> None:
        sig = RoutingSignals(task_complexity=0.1, reasoning_depth=0.1)
        self.assertEqual(self.router.tier_for(sig), FAST)
        self.assertEqual(self.router.model_for(sig), TIER_MODELS[FAST])

    def test_complex_reasoning_uses_large_model(self) -> None:
        sig = RoutingSignals(task_complexity=0.9, reasoning_depth=0.9, uncertainty=0.6)
        self.assertEqual(self.router.tier_for(sig), COMPLEX)
        self.assertEqual(self.router.model_for(sig), "qwen3.8:27b")

    def test_uncertainty_escalates_medium_complexity(self) -> None:
        sig = RoutingSignals(task_complexity=0.5, uncertainty=0.8)
        self.assertEqual(self.router.tier_for(sig), COMPLEX)

    def test_medium_complexity_uses_normal(self) -> None:
        sig = RoutingSignals(task_complexity=0.5)
        self.assertEqual(self.router.tier_for(sig), NORMAL)

    def test_tight_latency_uses_specialized(self) -> None:
        sig = RoutingSignals(task_complexity=0.1, latency_budget_s=3.0)
        self.assertEqual(self.router.tier_for(sig), SPECIALIZED)

    def test_model_is_never_truth_source(self) -> None:
        self.assertIn("identity", NEVER_MODEL_TRUTH)
        self.assertIn("safety_authorization", NEVER_MODEL_TRUTH)
        self.assertIn("physical_command_validity", NEVER_MODEL_TRUTH)


class TurnSessionTest(unittest.TestCase):
    def test_full_turn_lifecycle(self) -> None:
        s = TurnSession()
        self.assertEqual(s.start("hello vano"), "speaking")
        s.note_progress(5)
        self.assertEqual(s.pause(), "paused")
        self.assertEqual(s.resume(), "speaking")
        summary = s.finish()
        self.assertEqual(summary["state"], "idle")
        self.assertEqual(s.state, "idle")

    def test_barge_in_preserves_unfinished_state(self) -> None:
        s = TurnSession()
        s.start("there's one part of the camera integration we haven't closed", act="CONTINUE")
        s.note_progress(30)
        self.assertEqual(s.interrupt(), "interrupted")
        self.assertEqual(s.barge_in_count, 1)
        self.assertTrue(s.unfinished["attenuate_tts"])
        self.assertEqual(s.unfinished["act"], "CONTINUE")
        # replan: resume continues the preserved act
        self.assertEqual(s.resume(), "speaking")
        self.assertEqual(s.unfinished, {})
        self.assertEqual(s.snapshot()["state"], "speaking")

    def test_interrupt_only_while_speaking(self) -> None:
        s = TurnSession()
        self.assertEqual(s.interrupt(), "idle")  # no-op outside a turn
        self.assertEqual(s.barge_in_count, 0)

    def test_backchannel_is_listener_ack(self) -> None:
        s = TurnSession()
        self.assertEqual(s.backchannel(), "mhm")

    def test_duplicate_start_is_noop(self) -> None:
        s = TurnSession()
        s.start("one")
        self.assertEqual(s.start("two"), "speaking")
        self.assertEqual(s.text, "one")


if __name__ == "__main__":
    unittest.main()
