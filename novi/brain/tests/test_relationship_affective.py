"""Tests for the relationship-model extension of novi/brain/social.py.

Plan 24 Phase 7: RelationshipState gains communication_preferences,
interaction_history_summary, successful_patterns, failed_patterns,
preferred_verbosity, preferred_directness, typical_interruptibility and
confidence. Uses operational proxies — never numeric claims about "love" or
"friendship".
"""

from __future__ import annotations

import unittest

from novi.brain.social import Relationship, Relationships


class RelationshipAffectiveTest(unittest.TestCase):
    def setUp(self) -> None:
        self.relationships = Relationships()

    def test_new_fields_default(self) -> None:
        rel = self.relationships.get("Vano")
        self.assertEqual(rel.preferred_verbosity, "measured")
        self.assertEqual(rel.preferred_directness, "balanced")
        self.assertEqual(rel.typical_interruptibility, 0.5)
        self.assertEqual(rel.communication_preferences, {})
        self.assertEqual(rel.successful_patterns, [])
        self.assertEqual(rel.failed_patterns, [])
        self.assertEqual(rel.confidence, 0.0)

    def test_note_pattern_records_success_and_failure(self) -> None:
        self.relationships.note_pattern("Vano", pattern="concise_explanations", successful=True)
        self.relationships.note_pattern("Vano", pattern="long_explanations", successful=False)
        rel = self.relationships.get("Vano")
        self.assertIn("concise_explanations", rel.successful_patterns)
        self.assertIn("long_explanations", rel.failed_patterns)
        self.assertGreater(rel.confidence, 0.0)

    def test_note_pattern_does_not_duplicate(self) -> None:
        self.relationships.note_pattern("Vano", pattern="concise_explanations", successful=True)
        self.relationships.note_pattern("Vano", pattern="concise_explanations", successful=True)
        rel = self.relationships.get("Vano")
        self.assertEqual(rel.successful_patterns.count("concise_explanations"), 1)

    def test_note_communication_preference(self) -> None:
        self.relationships.note_communication_preference(
            "Vano", verbosity="concise", directness="direct", interruptibility=0.7
        )
        rel = self.relationships.get("Vano")
        self.assertEqual(rel.preferred_verbosity, "concise")
        self.assertEqual(rel.preferred_directness, "direct")
        self.assertEqual(rel.typical_interruptibility, 0.7)
        self.assertEqual(rel.communication_preferences["verbosity"], "concise")
        self.assertEqual(rel.communication_preferences["directness"], "direct")
        self.assertEqual(rel.communication_preferences["interruptibility"], 0.7)

    def test_note_interaction_summary(self) -> None:
        self.relationships.note_interaction_summary("Vano", summary="camera debugging, prefers short answers")
        rel = self.relationships.get("Vano")
        self.assertEqual(rel.interaction_history_summary, "camera debugging, prefers short answers")

    def test_interaction_bumps_confidence(self) -> None:
        before = self.relationships.get("Vano").confidence
        self.relationships.note_interaction("Vano", quality=0.8, positive=True)
        after = self.relationships.get("Vano").confidence
        self.assertGreater(after, before)

    def test_snapshot_roundtrip_preserves_new_fields(self) -> None:
        self.relationships.note_pattern("Vano", pattern="concise_explanations", successful=True)
        self.relationships.note_communication_preference("Vano", verbosity="concise", directness="direct")
        restored = Relationships.from_snapshot(self.relationships.snapshot())
        rel = restored.get("Vano")
        self.assertIn("concise_explanations", rel.successful_patterns)
        self.assertEqual(rel.preferred_verbosity, "concise")
        self.assertEqual(rel.preferred_directness, "direct")
        self.assertGreater(rel.confidence, 0.0)


if __name__ == "__main__":
    unittest.main()
