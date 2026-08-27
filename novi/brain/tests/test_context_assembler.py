"""Tests for the ContextAssembler (PERFECTING_PLAN Step 1).

Covers the acceptance criteria from docs/03-cognition/09_CONTEXT_ENGINE.md:
  - construct task-relevant, provenance-preserving, privacy-filtered context packages
  - reliably exclude irrelevant or stale information
  - contradictions represented explicitly
  - context budget respected
  - the "Bring me that cup" reference resolution case (NVIDIA Exp 1)
"""

import unittest

from novi.brain.context_assembler import (
    LAYER_IMMEDIATE,
    LAYER_KNOWLEDGE,
    LAYER_LONG_HORIZON,
    LAYER_MEMORY,
    LAYER_SITUATIONAL,
    ContextAssembler,
    ContextPackage,
    ContextRequest,
)
from novi.brain.world_model import (
    INFERRED,
    OBJECT,
    OBSERVED,
    PERSON,
    ROOM,
    Provenance,
    WorldModel,
)


def _kitchen_world() -> WorldModel:
    """A world with Alice in the kitchen holding a cup, plus a mug on the table."""
    wm = WorldModel()
    wm.add_entity("alice_001", PERSON, labels=["Alice"], epistemic_status=OBSERVED, confidence=0.95,
                  provenance=Provenance(source="camera"))
    wm.update_entity_state("alice_001", "location", "kitchen", epistemic_status=OBSERVED, confidence=0.9,
                           source="camera", timestamp="2026-01-01T10:00:00Z")

    wm.add_entity("cup_001", OBJECT, labels=["cup"], epistemic_status=OBSERVED, confidence=0.85,
                  provenance=Provenance(source="camera"))
    wm.update_entity_state("cup_001", "location", "kitchen", epistemic_status=OBSERVED, confidence=0.85,
                           source="camera", timestamp="2026-01-01T10:00:00Z")

    wm.add_entity("mug_001", OBJECT, labels=["mug"], aliases=["cup"], epistemic_status=OBSERVED, confidence=0.8,
                  provenance=Provenance(source="camera"))
    wm.update_entity_state("mug_001", "location", "kitchen", epistemic_status=OBSERVED, confidence=0.8,
                           source="camera", timestamp="2026-01-01T10:00:00Z")

    wm.add_entity("kitchen_001", ROOM, labels=["kitchen"], epistemic_status=OBSERVED, confidence=1.0)
    wm.add_entity("table_001", OBJECT, labels=["table"], epistemic_status=OBSERVED, confidence=0.9)
    wm.update_entity_state("table_001", "location", "kitchen", epistemic_status=OBSERVED, confidence=0.9,
                           source="camera", timestamp="2026-01-01T10:00:00Z")

    wm.add_relation("alice_001", "holds", "cup_001", epistemic_status=INFERRED, confidence=0.6,
                    source="inference", timestamp="2026-01-01T10:00:00Z")
    wm.add_relation("cup_001", "located_in", "kitchen_001", epistemic_status=OBSERVED, confidence=0.85,
                    source="camera", timestamp="2026-01-01T10:00:00Z")
    return wm


class ContextAssemblerTests(unittest.TestCase):
    def test_assemble_produces_context_package(self):
        wm = _kitchen_world()
        assembler = ContextAssembler()
        request = ContextRequest(
            speaker_label="Alice",
            location="kitchen",
            utterance="bring me that cup",
            token_budget=5000,
        )
        ctx = assembler.assemble(wm, request)
        self.assertIsInstance(ctx, ContextPackage)
        self.assertGreater(len(ctx.items), 0)

    def test_immediate_layer_includes_speaker_and_location(self):
        wm = _kitchen_world()
        assembler = ContextAssembler()
        request = ContextRequest(speaker_label="Alice", location="kitchen", utterance="hello")
        ctx = assembler.assemble(wm, request)
        immediate = ctx.by_layer(LAYER_IMMEDIATE)
        kinds = [item.kind for item in immediate]
        self.assertIn("speaker", kinds)
        self.assertIn("event", kinds)  # utterance

    def test_immediate_layer_includes_visible_objects(self):
        wm = _kitchen_world()
        assembler = ContextAssembler()
        request = ContextRequest(location="kitchen", token_budget=5000)
        ctx = assembler.assemble(wm, request)
        immediate = ctx.by_layer(LAYER_IMMEDIATE)
        entity_items = [item for item in immediate if item.kind == "entity"]
        # cup_001 is an object in the kitchen
        labels = [item.data.get("labels", []) for item in entity_items]
        flat = [item for sublist in labels for item in sublist]
        self.assertIn("cup", flat)

    def test_situational_layer_includes_active_people(self):
        wm = _kitchen_world()
        assembler = ContextAssembler()
        request = ContextRequest(location="kitchen", token_budget=5000)
        ctx = assembler.assemble(wm, request)
        situational = ctx.by_layer(LAYER_SITUATIONAL)
        entity_items = [item for item in situational if item.kind == "entity"]
        types = [item.data.get("entity_type") for item in entity_items]
        self.assertIn(PERSON, types)

    def test_memory_layer_includes_recalled_memories(self):
        wm = _kitchen_world()
        assembler = ContextAssembler()
        memories = ({"memory_type": "utterance", "content": "Alice asked for a cup", "confidence": 0.7},)
        request = ContextRequest(recalled_memories=memories)
        ctx = assembler.assemble(wm, request)
        mem_items = ctx.by_layer(LAYER_MEMORY)
        self.assertEqual(len(mem_items), 1)
        self.assertEqual(mem_items[0].kind, "memory")

    def test_knowledge_layer_includes_triples(self):
        wm = _kitchen_world()
        assembler = ContextAssembler()
        triples = ({"subject": "alice_001", "predicate": "holds", "object": "cup_001", "confidence": 0.6},)
        request = ContextRequest(knowledge_triples=triples)
        ctx = assembler.assembler = assembler.assemble(wm, request)
        ctx = assembler.assemble(wm, request)
        knowledge = ctx.by_layer(LAYER_KNOWLEDGE)
        self.assertEqual(len(knowledge), 1)

    def test_long_horizon_layer_includes_goal(self):
        wm = _kitchen_world()
        assembler = ContextAssembler()
        goal = {"kind": "fetch", "target": "cup_001"}
        request = ContextRequest(goal=goal)
        ctx = assembler.assemble(wm, request)
        long = ctx.by_layer(LAYER_LONG_HORIZON)
        self.assertEqual(len(long), 1)
        self.assertEqual(long[0].kind, "goal")

    def test_token_budget_trims_items(self):
        wm = _kitchen_world()
        assembler = ContextAssembler()
        request = ContextRequest(location="kitchen", token_budget=10)  # very small budget
        ctx = assembler.assemble(wm, request)
        self.assertGreater(ctx.items_dropped, 0)

    def test_referenced_items_ranked_before_unreferenced(self):
        """Regression: _rank sorted relevance/confidence ascending, so the
        least-relevant items were ranked first (and kept first when trimming).
        Referenced (relevant) items must rank before unreferenced ones."""
        from novi.brain.context_assembler import ContextItem
        assembler = ContextAssembler()
        request = ContextRequest(referenced_labels=("cup",))
        items = [
            ContextItem(layer=LAYER_IMMEDIATE, kind="entity",
                        data={"label": "mug", "aliases": ["cup"]}, confidence=0.8),
            ContextItem(layer=LAYER_IMMEDIATE, kind="entity",
                        data={"label": "cup"}, confidence=0.85),
            ContextItem(layer=LAYER_IMMEDIATE, kind="entity",
                        data={"label": "spoon"}, confidence=0.9),
        ]
        ranked = assembler._rank(items, request)
        # The referenced "cup" item must rank before the unreferenced "spoon".
        self.assertLess(ranked.index(items[1]), ranked.index(items[2]))

    def test_provenance_preserved_on_items(self):
        wm = _kitchen_world()
        assembler = ContextAssembler()
        request = ContextRequest(location="kitchen", token_budget=5000)
        ctx = assembler.assemble(wm, request)
        for item in ctx.items:
            if item.kind == "entity":
                self.assertNotEqual(item.source, "")  # provenance is present
                self.assertGreater(item.confidence, 0.0)

    def test_contradictions_surfaced_explicitly(self):
        wm = _kitchen_world()
        # Create a contradiction.
        wm.update_entity_state("alice_001", "location", "bedroom", epistemic_status=OBSERVED,
                                confidence=0.6, source="rfid", timestamp="2026-01-01T10:01:00Z")
        assembler = ContextAssembler()
        request = ContextRequest(location="kitchen")
        ctx = assembler.assemble(wm, request)
        self.assertGreaterEqual(len(ctx.contradictions), 1)

    def test_privacy_filtering_restricted_scope(self):
        wm = WorldModel()
        wm.add_entity("alice_001", PERSON, labels=["Alice"], epistemic_status=OBSERVED, confidence=0.9)
        wm.get_entity("alice_001").privacy_class = "restricted"
        wm.add_entity("cup_001", OBJECT, labels=["cup"], epistemic_status=OBSERVED, confidence=0.8)
        assembler = ContextAssembler()
        request = ContextRequest(location=None, privacy_scope="restricted", token_budget=5000)
        ctx = assembler.assemble(wm, request)
        entity_ids = [item.data.get("entity_id") for item in ctx.items if item.kind == "entity"]
        self.assertNotIn("alice_001", entity_ids)  # restricted privacy filtered out
        self.assertIn("cup_001", entity_ids)

    def test_privacy_filtering_internal_keeps_everything(self):
        wm = WorldModel()
        wm.add_entity("alice_001", PERSON, labels=["Alice"], epistemic_status=OBSERVED, confidence=0.9)
        wm.get_entity("alice_001").privacy_class = "restricted"
        assembler = ContextAssembler()
        request = ContextRequest(privacy_scope="internal", token_budget=5000)
        ctx = assembler.assemble(wm, request)
        entity_ids = [item.data.get("entity_id") for item in ctx.items if item.kind == "entity"]
        self.assertIn("alice_001", entity_ids)
        self.assertFalse(ctx.privacy_filtered)


class ReferenceResolutionTests(unittest.TestCase):
    """NVIDIA Experiment 1: 'Bring me that cup' reference resolution."""

    def test_resolve_single_cup(self):
        # Remove the mug so there's only one cup.
        # Actually keep both: cup has label "cup", mug has alias "cup" — that's ambiguous.
        # Let's test with just one cup.
        wm2 = WorldModel()
        wm2.add_entity("alice_001", PERSON, labels=["Alice"], epistemic_status=OBSERVED, confidence=0.95)
        wm2.update_entity_state("alice_001", "location", "kitchen", epistemic_status=OBSERVED, confidence=0.9, source="cam")
        wm2.add_entity("cup_001", OBJECT, labels=["cup"], epistemic_status=OBSERVED, confidence=0.85)
        wm2.update_entity_state("cup_001", "location", "kitchen", epistemic_status=OBSERVED, confidence=0.85, source="cam")

        assembler = ContextAssembler()
        request = ContextRequest(
            speaker_label="Alice",
            location="kitchen",
            utterance="bring me that cup",
            referenced_labels=("cup",),
            token_budget=5000,
        )
        result = assembler.resolve_reference(wm2, request, "that cup")
        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(result["entity_id"], "cup_001")
        self.assertEqual(result["label"], "cup")
        self.assertGreater(result["confidence"], 0.0)

    def test_resolve_ambiguous_multiple_cups(self):
        wm = _kitchen_world()
        # Both cup_001 (label "cup") and mug_001 (alias "cup") match "cup".
        assembler = ContextAssembler()
        request = ContextRequest(
            speaker_label="Alice",
            location="kitchen",
            utterance="bring me that cup",
            referenced_labels=("cup",),
            token_budget=5000,
        )
        result = assembler.resolve_reference(wm, request, "that cup")
        self.assertEqual(result["status"], "AMBIGUOUS")
        self.assertGreaterEqual(len(result["candidates"]), 2)

    def test_resolve_unknown_referent(self):
        wm = _kitchen_world()
        assembler = ContextAssembler()
        request = ContextRequest(
            speaker_label="Alice",
            location="kitchen",
            utterance="bring me that book",
            referenced_labels=("book",),
            token_budget=5000,
        )
        result = assembler.resolve_reference(wm, request, "that book")
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertIsNone(result["entity_id"])

    def test_reference_resolution_returns_context(self):
        wm2 = WorldModel()
        wm2.add_entity("alice_001", PERSON, labels=["Alice"], epistemic_status=OBSERVED, confidence=0.95)
        wm2.add_entity("cup_001", OBJECT, labels=["cup"], epistemic_status=OBSERVED, confidence=0.85)
        wm2.update_entity_state("cup_001", "location", "kitchen", epistemic_status=OBSERVED, confidence=0.85, source="cam")
        assembler = ContextAssembler()
        request = ContextRequest(
            speaker_label="Alice", location="kitchen", utterance="bring me that cup",
            referenced_labels=("cup",), token_budget=5000,
        )
        result = assembler.resolve_reference(wm2, request, "that cup")
        self.assertIsInstance(result["context"], ContextPackage)
        self.assertGreater(len(result["context"].items), 0)


if __name__ == "__main__":
    unittest.main()
