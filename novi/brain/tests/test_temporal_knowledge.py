"""Phase P3 (temporal knowledge) tests — validity windows, supersession,
source-confidence weighting, and taxonomy-constrained extraction.

Plan: docs/plans/BRAIN_COGNITION_IMPROVEMENT_PLAN_2026-08-25.md §P3.
"""

from __future__ import annotations

import unittest

from novi.brain.kgraph import EntityKnowledgeGraph, _source_weight


class TemporalValidityTests(unittest.TestCase):
    def test_new_triple_is_current_with_open_window(self) -> None:
        g = EntityKnowledgeGraph()
        g.add("cup", "located_near", "book", confidence=0.9, source="perception", cycle=3)
        (t,) = g.current_triples(subject="cup")
        self.assertEqual(t.valid_from_cycle, 3)
        self.assertIsNone(t.valid_until_cycle)

    def test_supersession_closes_window_and_links_successor(self) -> None:
        g = EntityKnowledgeGraph()
        g.add("alice", "located_near", "kitchen", confidence=0.9, source="perception", cycle=2)
        g.add("alice", "located_near", "garden", confidence=0.95, source="perception", cycle=5)
        lead = g.leading("alice", "located_near")
        self.assertEqual(lead.object, "garden")  # newer + stronger wins
        (old,) = g.history(subject="alice", predicate="located_near")
        self.assertEqual(old.object, "kitchen")
        self.assertEqual(old.valid_from_cycle, 2)
        self.assertEqual(old.valid_until_cycle, 5)
        self.assertEqual(old.superseded_by, ("alice", "located_near", "garden"))

    def test_context_defaults_to_current_facts_only(self) -> None:
        g = EntityKnowledgeGraph()
        g.add("alice", "located_near", "kitchen", confidence=0.9, source="perception", cycle=1)
        g.add("alice", "located_near", "garden", confidence=0.95, source="perception", cycle=4)
        current = {t.object for t in g.context("alice")}
        self.assertEqual(current, {"garden"})  # kitchen is history now
        with_history = {t.object for t in g.context("alice", include_history=True)}
        self.assertEqual(with_history, {"garden", "kitchen"})

    def test_time_travel_query_at_cycle(self) -> None:
        g = EntityKnowledgeGraph()
        g.add("alice", "located_near", "kitchen", confidence=0.9, source="perception", cycle=1)
        g.add("alice", "located_near", "garden", confidence=0.95, source="perception", cycle=4)
        past = {t.object for t in g.current_triples(subject="alice", at_cycle=2)}
        self.assertEqual(past, {"kitchen"})  # valid at cycle 2
        now = {t.object for t in g.current_triples(subject="alice")}
        self.assertEqual(now, {"garden"})

    def test_snapshot_roundtrip_preserves_temporal_fields(self) -> None:
        g = EntityKnowledgeGraph()
        g.add("alice", "located_near", "kitchen", confidence=0.9, source="perception", cycle=1)
        g.add("alice", "located_near", "garden", confidence=0.95, source="perception", cycle=4)
        revived = EntityKnowledgeGraph.from_snapshot(g.snapshot())
        (old,) = revived.history(subject="alice")
        self.assertEqual(old.valid_until_cycle, 4)
        self.assertEqual(old.superseded_by, ("alice", "located_near", "garden"))
        lead = revived.leading("alice", "located_near")
        self.assertEqual(lead.valid_from_cycle, 4)
        self.assertIsNone(lead.valid_until_cycle)


class SourceConfidenceTests(unittest.TestCase):
    def test_perception_outranks_hearsay_in_lead_selection(self) -> None:
        # hearsay accumulates more evidence but perception still leads.
        g = EntityKnowledgeGraph()
        g.add("door", "is", "open", confidence=0.7, source="speech", cycle=1)
        g.add("door", "is", "open", confidence=0.7, source="speech", cycle=2)
        g.add("door", "is", "closed", confidence=0.85, source="camera", cycle=3)
        lead = g.leading("door", "is")
        self.assertEqual(lead.object, "closed")

    def test_source_weights_ordered(self) -> None:
        self.assertGreater(_source_weight("camera"), _source_weight("web"))
        self.assertGreater(_source_weight("perception"), _source_weight("hearsay"))
        self.assertEqual(_source_weight("mystery.backend"), 0.8)


class TaxonomyExtractionTests(unittest.TestCase):
    def test_unknown_relation_not_learned_as_related_to(self) -> None:
        g = EntityKnowledgeGraph()
        out = g.extract_from_text("bob chatted with alice about the door", ("bob", "alice"))
        self.assertEqual(out, [])  # no known predicate -> nothing learned

    def test_known_relation_still_extracted(self) -> None:
        g = EntityKnowledgeGraph()
        out = g.extract_from_text("alice moved the door", ("alice", "door"))
        self.assertEqual(out, [("alice", "moved", "door")])


if __name__ == "__main__":
    unittest.main()
