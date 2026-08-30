"""Tests for novi/brain/social_context.py — derived social context.

Plan 22 Phase 7: observable, probabilistic descriptions only — no claims
about private mental states. Deterministic and hardware-free.
"""

from __future__ import annotations

import unittest

from novi.brain.social_context import SocialContextBuilder, SocialEvidence


class SocialContextTest(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = SocialContextBuilder()

    def test_available_person_present_no_talk(self) -> None:
        ctx = self.builder.build(SocialEvidence(person_present=True, person_name="vano", familiarity=0.9, relationship="owner"))
        self.assertEqual(ctx.addressee, "vano")
        self.assertEqual(ctx.relationship, "owner")
        self.assertGreater(ctx.familiarity, 0.8)
        self.assertEqual(ctx.user_availability, "available")
        self.assertEqual(ctx.interaction_phase, "none")
        # opportunity exists but modest: engaged=0.15, available, interruptible
        self.assertGreater(ctx.social_opportunity, 0.0)
        self.assertLess(ctx.social_opportunity, 0.6)

    def test_active_conversation_raises_engagement(self) -> None:
        ctx = self.builder.build(
            SocialEvidence(
                person_present=True, recent_utterances=3, interaction_count=5,
                last_user_utterance_cycle=9, current_cycle=10,
            )
        )
        self.assertEqual(ctx.interaction_phase, "active")
        self.assertEqual(ctx.user_availability, "busy")
        self.assertGreater(ctx.user_engagement, 0.6)
        self.assertGreater(ctx.attention_to_novi, 0.5)

    def test_user_speaking_is_not_interruptible(self) -> None:
        ctx = self.builder.build(SocialEvidence(user_speaking=True, person_present=True))
        self.assertEqual(ctx.interruptibility, 0.0)
        self.assertEqual(ctx.user_availability, "busy")

    def test_novi_speaking_lowers_interruptibility(self) -> None:
        ctx = self.builder.build(SocialEvidence(novi_speaking=True, person_present=True))
        self.assertLessEqual(ctx.interruptibility, 0.1)

    def test_temperature_only_from_observable_cues(self) -> None:
        # no cues → no mind-reading
        ctx = self.builder.build(SocialEvidence(person_present=True))
        self.assertEqual(ctx.conversation_temperature, "unknown")
        self.assertEqual(ctx.temperature_confidence, 0.0)
        # fast + loud speech → tense, with confidence and cited cues
        ctx = self.builder.build(
            SocialEvidence(speech_tempo_ratio=1.6, speech_volume_ratio=1.4, person_present=True)
        )
        self.assertEqual(ctx.conversation_temperature, "tense")
        self.assertGreater(ctx.temperature_confidence, 0.5)
        self.assertLess(ctx.temperature_confidence, 1.0)
        cues = {c["cue"] for c in ctx.cues}
        self.assertIn("speech_tempo_increased", cues)
        self.assertIn("speech_volume_increased", cues)

    def test_absent_person_is_departed(self) -> None:
        ctx = self.builder.build(SocialEvidence(person_present=False))
        self.assertEqual(ctx.interaction_phase, "departed")
        self.assertEqual(ctx.user_availability, "unknown")
        self.assertEqual(ctx.social_opportunity, 0.0)

    def test_familiarity_never_exceeds_certainty(self) -> None:
        ctx = self.builder.build(SocialEvidence(person_present=True, familiarity=1.7))
        self.assertLessEqual(ctx.familiarity, 1.0)

    def test_snapshot_shape(self) -> None:
        ctx = self.builder.build(SocialEvidence(person_present=True, person_name="vano"))
        snap = ctx.snapshot()
        self.assertEqual(snap["addressee"], "vano")
        self.assertIn("social_opportunity", snap)
        self.assertIn("cues", snap)
        self.assertIn("interruptibility", snap)


if __name__ == "__main__":
    unittest.main()
