"""Tests for novi/brain/apology.py — mature apology architecture.

Plan 24 Phase 11: a mature apology has four components — recognition,
responsibility, correction, follow-through. Repeated apologies are an
anti-pattern; one appropriate acknowledgement is normally enough.
"""

from __future__ import annotations

import unittest

from novi.brain.apology import Apology, ApologyBuilder


class ApologyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = ApologyBuilder()

    def test_apology_has_four_components(self) -> None:
        apology = self.builder.build(
            recognition="I misunderstood the camera issue",
            responsibility="I kept explaining the wrong part",
            correction="I'll focus on the actual issue",
            follow_through="I'll verify with you before continuing",
        )
        self.assertEqual(apology.recognition, "I misunderstood the camera issue")
        self.assertEqual(apology.responsibility, "I kept explaining the wrong part")
        self.assertEqual(apology.correction, "I'll focus on the actual issue")
        self.assertEqual(apology.follow_through, "I'll verify with you before continuing")

    def test_apology_renders_mature_text(self) -> None:
        apology = self.builder.build(
            recognition="I misunderstood the camera issue",
            responsibility="I kept explaining the wrong part",
            correction="I'll focus on the actual issue",
            follow_through="I'll verify with you before continuing",
        )
        text = apology.render()
        self.assertIn("You're right", text)
        self.assertIn("I misunderstood", text)
        self.assertIn("I'll focus on the actual issue", text)
        # no groveling
        self.assertNotIn("I'm very sorry", text)
        self.assertNotIn("I sincerely apologize", text)
        self.assertNotIn("I deeply regret", text)

    def test_repeated_apologies_suppressed(self) -> None:
        # plan §11: do not produce repeated apologies
        self.builder.build(
            recognition="r", responsibility="p", correction="c", follow_through="f"
        )
        second = self.builder.build(
            recognition="r", responsibility="p", correction="c", follow_through="f"
        )
        self.assertIsNone(second)

    def test_apology_count_tracks_frequency(self) -> None:
        self.builder.build(
            recognition="r", responsibility="p", correction="c", follow_through="f"
        )
        self.assertEqual(self.builder.apology_count, 1)

    def test_snapshot_roundtrip(self) -> None:
        apology = self.builder.build(
            recognition="r", responsibility="p", correction="c", follow_through="f"
        )
        restored = Apology.from_snapshot(apology.snapshot())
        self.assertEqual(restored.recognition, apology.recognition)
        self.assertEqual(restored.correction, apology.correction)


if __name__ == "__main__":
    unittest.main()
