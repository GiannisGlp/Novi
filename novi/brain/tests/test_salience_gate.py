"""Tests for the plan 22 Phase 8 anti-narration guard (SalienceGate).

Plan §8.3 examples that should normally remain silent:
  chair detected / wall detected / same mug seen again / same person seated
and examples potentially worth speaking:
  person enters / known object disappears / user points at object /
  safety event / task completes / commitment due.

Task 8.2 separation: the gate only decides "worth saying" — attention and
salience live upstream.
"""

from __future__ import annotations

import unittest

from novi.brain.salience import SalienceGate


class SalienceGateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.gate = SalienceGate()

    def test_anti_narration_examples_stay_silent(self) -> None:
        for kind, entity in [
            ("object.detected", "chair"),
            ("object.detected", "wall"),
            ("object.seen", "mug"),
            ("presence.seen", "vano"),
            ("scene.stable", ""),
        ]:
            speak, reason = self.gate.should_speak({}, kind=kind, entity=entity, novelty=0.9)
            self.assertFalse(speak, f"{kind} should stay silent")
            self.assertIn("anti_narration", reason)

    def test_worth_speaking_examples_speak(self) -> None:
        for kind in [
            "presence.entered",
            "identity.recognized",
            "object.novel",
            "object.disappeared",
            "object.pointed",
            "task.completed",
            "commitment.due",
            "hearing.anomaly",
        ]:
            speak, reason = self.gate.should_speak({}, kind=kind, novelty=0.5)
            self.assertTrue(speak, f"{kind} may be worth saying")
            self.assertIn("worth_speaking", reason)

    def test_safety_event_overrides_suppression(self) -> None:
        # a repeated, low-novelty, silent-kind event still speaks when safety
        speak, reason = self.gate.should_speak(
            {}, kind="object.detected", safety=True,
            seen_recently=True, seen_cycles_ago=1,
        )
        self.assertTrue(speak)
        self.assertEqual(reason, "safety_event_overrides_suppression")

    def test_recently_said_same_event_is_deduped(self) -> None:
        speak, reason = self.gate.should_speak(
            {}, kind="presence.entered", entity="vano",
            seen_recently=True, seen_cycles_ago=5,
        )
        self.assertFalse(speak)
        self.assertEqual(reason, "recently_said_dedup")

    def test_high_novelty_unknown_kind_speaks(self) -> None:
        speak, reason = self.gate.should_speak({}, kind="weird.event", novelty=0.95)
        self.assertTrue(speak)
        self.assertIn("high_novelty", reason)

    def test_below_threshold_unknown_kind_silent(self) -> None:
        speak, reason = self.gate.should_speak({}, kind="weird.event", novelty=0.2)
        self.assertFalse(speak)
        self.assertEqual(reason, "below_speech_threshold")

    def test_upstream_vetted_skips_novelty_recheck(self) -> None:
        # an upstream evaluator already thresholded novelty; the gate only
        # enforces the hard guards
        speak, reason = self.gate.should_speak(
            {}, kind="scene.changed", novelty=0.0, upstream_vetted=True
        )
        self.assertTrue(speak)
        self.assertEqual(reason, "upstream_vetted")
        # ...but the anti-narration list still applies
        speak, _ = self.gate.should_speak(
            {}, kind="object.seen", entity="mug", upstream_vetted=True
        )
        self.assertFalse(speak)

    def test_attention_salience_policy_separation(self) -> None:
        """Task 8.2: an event can be noticed (attention) and salient
        (importance) yet still not worth saying — the gate is the last layer."""
        speak, reason = self.gate.should_speak({}, kind="object.seen", entity="mug", novelty=0.99)
        self.assertFalse(speak)  # salient but not worth saying
        self.assertIn("anti_narration", reason)


if __name__ == "__main__":
    unittest.main()
