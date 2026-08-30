"""Tests for novi/brain/reference_resolution.py — unified grounding.

Plan 22 Phase 12 and the required grounding test classes:
- "that" resolves to visually/linguistically supported object;
- ambiguous reference triggers clarification;
- a physical action cannot proceed on unresolved ambiguity.
"""

from __future__ import annotations

import unittest

from novi.brain.reference_resolution import (
    AMBIGUOUS,
    RESOLVED,
    UNRESOLVED,
    CandidateEntity,
    ReferenceResolver,
)


def _entity(eid, label, etype="object"):
    return CandidateEntity(entity_id=eid, label=label, entity_type=etype)


class ReferenceResolutionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.resolver = ReferenceResolver()

    def test_that_resolves_to_visually_supported_object(self) -> None:
        # plan §1 Example C: "Can you get that?" + pointing toward blue bottle
        entities = [
            _entity("track-1", "blue bottle"),
            _entity("track-2", "red book"),
        ]
        res = self.resolver.resolve(
            "can you get that?",
            entities=entities,
            pointing={"track-1": 1.0},
            recent_mentions={"track-1": 1.0},
        )
        self.assertEqual(res.status, RESOLVED)
        self.assertEqual(res.entity_id, "track-1")
        self.assertEqual(res.label, "blue bottle")
        self.assertGreaterEqual(res.confidence, self.resolver.threshold)

    def test_definite_np_resolves_by_compatibility(self) -> None:
        entities = [_entity("track-1", "mug"), _entity("track-2", "lamp")]
        res = self.resolver.resolve("move the mug over there", entities=entities)
        self.assertEqual(res.status, RESOLVED)
        self.assertEqual(res.label, "mug")

    def test_personal_pronoun_prefers_person(self) -> None:
        entities = [_entity("track-1", "vano", "person"), _entity("track-2", "mug", "object")]
        res = self.resolver.resolve("ask him about it", entities=entities)
        self.assertEqual(res.status, RESOLVED)
        self.assertEqual(res.entity_id, "track-1")

    def test_ambiguous_reference_triggers_clarification(self) -> None:
        # two visually similar candidates, no pointing/gaze/recent mention
        entities = [
            _entity("track-1", "blue bottle"),
            _entity("track-2", "blue bottle"),
        ]
        res = self.resolver.resolve("hand me that", entities=entities)
        self.assertEqual(res.status, AMBIGUOUS)
        self.assertGreaterEqual(len(res.candidates), 2)
        # the natural follow-up is a clarification question (plan §16)
        self.assertIn("needs_clarification", res.reason)

    def test_physical_action_cannot_proceed_on_unresolved_ambiguity(self) -> None:
        entities = [_entity("track-1", "blue bottle"), _entity("track-2", "blue bottle")]
        res = self.resolver.resolve("move that over there", entities=entities)
        self.assertFalse(self.resolver.grounding_verification(res))
        res2 = self.resolver.resolve("let us talk about it later", entities=entities)
        self.assertEqual(res2.status, AMBIGUOUS)  # "it" + low evidence → clarify
        self.assertFalse(self.resolver.grounding_verification(res2))
        # truly no reference at all → unresolved
        res3 = self.resolver.resolve("good morning", entities=entities)
        self.assertEqual(res3.status, UNRESOLVED)
        self.assertFalse(self.resolver.grounding_verification(res3))

    def test_fully_resolved_reference_allows_action(self) -> None:
        entities = [_entity("track-1", "blue bottle"), _entity("track-2", "red book")]
        res = self.resolver.resolve(
            "move that over there",
            entities=entities,
            gaze={"track-1": 1.0},
            recent_mentions={"track-1": 1.0},
        )
        self.assertTrue(self.resolver.grounding_verification(res))

    def test_topic_mention_boosts_candidate(self) -> None:
        entities = [_entity("track-1", "mug"), _entity("track-2", "cup")]
        res = self.resolver.resolve(
            "is it still there?", entities=entities,
            topic="mug", recent_mentions={"track-1": 1.0},
        )
        self.assertEqual(res.status, RESOLVED)
        self.assertEqual(res.label, "mug")

    def test_close_candidates_are_ambiguous_not_forced(self) -> None:
        entities = [_entity("track-1", "mug"), _entity("track-2", "mug")]
        res = self.resolver.resolve("the mug", entities=entities, recent_mentions={"track-1": 1.0, "track-2": 1.0})
        self.assertEqual(res.status, AMBIGUOUS)


if __name__ == "__main__":
    unittest.main()
