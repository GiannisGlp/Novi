"""Tests for the unified WorldModel (PERFECTING_PLAN Step 1).

Covers the acceptance criteria from docs/03-cognition/02_WORLD_MODEL.md:
  1. represent known and unknown entities;
  2. track people and objects over time;
  3. maintain spatial relationships;
  4. distinguish observation from inference;
  5. preserve epistemic categories;
  6. resolve conflicting observations;
  7. expose current state quickly;
  8. preserve world-state lineage;
  9. keep predictions separate from facts;
  10. request additional evidence when uncertainty is operationally important;
  14. evolve entity types without changing the core architecture.
"""

import unittest

from MAC_BRAIN.world_model import (
    ACTIVE,
    ARCHIVED,
    CANDIDATE,
    INFERRED,
    OBJECT,
    OBSERVED,
    PERSON,
    PREDICTED,
    ROOM,
    SIMULATED,
    STALE,
    UNKNOWN,
    Provenance,
    WorldModel,
)


class WorldModelEntityTests(unittest.TestCase):
    def test_add_typed_entity(self):
        wm = WorldModel()
        alice = wm.add_entity("alice_001", PERSON, labels=["Alice"], epistemic_status=OBSERVED, confidence=0.9)
        self.assertEqual(alice.entity_type, PERSON)
        self.assertEqual(alice.epistemic_status, OBSERVED)
        self.assertEqual(alice.label(), "Alice")
        self.assertEqual(alice.lifecycle, CANDIDATE)

    def test_get_entity_by_id(self):
        wm = WorldModel()
        wm.add_entity("cup_001", OBJECT, labels=["cup"], epistemic_status=OBSERVED, confidence=0.8)
        entity = wm.get_entity("cup_001")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.entity_type, OBJECT)

    def test_resolve_by_label(self):
        wm = WorldModel()
        wm.add_entity("cup_001", OBJECT, labels=["cup"], aliases=["mug"], epistemic_status=OBSERVED, confidence=0.8)
        self.assertIsNotNone(wm.resolve("cup"))
        self.assertIsNotNone(wm.resolve("mug"))
        self.assertIsNotNone(wm.resolve("cup_001"))
        self.assertIsNone(wm.resolve("nonexistent"))

    def test_unknown_entity_exists_without_classification(self):
        wm = WorldModel()
        wm.add_entity("unknown_001", OBJECT, epistemic_status=UNKNOWN, confidence=0.1)
        entity = wm.get_entity("unknown_001")
        self.assertEqual(entity.epistemic_status, UNKNOWN)
        self.assertEqual(entity.lifecycle, CANDIDATE)

    def test_unknown_entity_type_rejected(self):
        wm = WorldModel()
        with self.assertRaises(ValueError):
            wm.add_entity("x", "dragon")

    def test_unknown_epistemic_status_rejected(self):
        wm = WorldModel()
        wm.add_entity("x", OBJECT)
        with self.assertRaises(ValueError):
            wm.update_entity_state("x", "state", "open", epistemic_status="GUESSED", confidence=0.5, source="cam")

    def test_add_entity_idempotent_reinforces_labels(self):
        wm = WorldModel()
        wm.add_entity("alice_001", PERSON, labels=["Alice"])
        wm.add_entity("alice_001", PERSON, labels=["Alice", "Ali"], aliases=["Al"])
        entity = wm.get_entity("alice_001")
        self.assertIn("Alice", entity.labels)
        self.assertIn("Ali", entity.labels)
        self.assertIn("Al", entity.aliases)
        self.assertEqual(wm.world_version, 1)  # second add is idempotent, no version bump


class WorldModelStateTests(unittest.TestCase):
    def test_state_distinguishes_observed_from_inferred(self):
        wm = WorldModel()
        wm.add_entity("door_001", OBJECT, labels=["door"], epistemic_status=OBSERVED, confidence=0.9)
        wm.update_entity_state("door_001", "open_state", "open", epistemic_status=OBSERVED, confidence=0.95, source="contact_sensor", timestamp="2026-01-01T10:00:00Z")
        entity = wm.get_entity("door_001")
        self.assertEqual(entity.state_value("open_state"), "open")
        self.assertEqual(entity.state_status("open_state"), OBSERVED)

    def test_inferred_state_marked(self):
        wm = WorldModel()
        wm.add_entity("alice_001", PERSON, epistemic_status=UNKNOWN, confidence=0.0)
        wm.update_entity_state("alice_001", "location", "kitchen", epistemic_status=INFERRED, confidence=0.6, source="inference_model", timestamp="2026-01-01T10:00:00Z")
        entity = wm.get_entity("alice_001")
        self.assertEqual(entity.state_value("location"), "kitchen")
        self.assertEqual(entity.state_status("location"), INFERRED)
        self.assertEqual(entity.epistemic_status, INFERRED)

    def test_prediction_never_overwrites_observed(self):
        wm = WorldModel()
        wm.add_entity("door_001", OBJECT, epistemic_status=OBSERVED, confidence=0.9)
        wm.update_entity_state("door_001", "open_state", "open", epistemic_status=OBSERVED, confidence=0.95, source="sensor", timestamp="2026-01-01T10:00:00Z")
        # A prediction should NOT overwrite the observed value.
        wm.update_entity_state("door_001", "open_state", "closed", epistemic_status=PREDICTED, confidence=0.7, source="prediction_model", timestamp="2026-01-01T11:00:00Z")
        entity = wm.get_entity("door_001")
        self.assertEqual(entity.state_value("open_state"), "open")  # still the observed value
        self.assertEqual(entity.state_status("open_state"), OBSERVED)

    def test_simulated_never_becomes_fact(self):
        wm = WorldModel()
        wm.add_entity("cup_001", OBJECT, epistemic_status=UNKNOWN, confidence=0.0)
        # Simulated state should be stored but not overwrite a real one.
        wm.update_entity_state("cup_001", "location", "table", epistemic_status=SIMULATED, confidence=0.8, source="sim", timestamp="2026-01-01T10:00:00Z")
        entity = wm.get_entity("cup_001")
        # When no real value exists, the simulated one is stored.
        self.assertEqual(entity.state_value("location"), "table")
        self.assertEqual(entity.state_status("location"), SIMULATED)
        # Now a real observation comes in — it should NOT be blocked by the simulation.
        wm.update_entity_state("cup_001", "location", "shelf", epistemic_status=OBSERVED, confidence=0.95, source="camera", timestamp="2026-01-01T10:01:00Z")
        entity = wm.get_entity("cup_001")
        self.assertEqual(entity.state_value("location"), "shelf")
        self.assertEqual(entity.state_status("location"), OBSERVED)


class WorldModelContradictionTests(unittest.TestCase):
    def test_contradiction_preserved_not_overwritten(self):
        wm = WorldModel()
        wm.add_entity("alice_001", PERSON, epistemic_status=OBSERVED, confidence=0.9)
        wm.update_entity_state("alice_001", "location", "kitchen", epistemic_status=OBSERVED, confidence=0.7, source="camera", timestamp="2026-01-01T10:00:00Z")
        # Conflicting observation: camera says kitchen, but another sensor says bedroom.
        wm.update_entity_state("alice_001", "location", "bedroom", epistemic_status=OBSERVED, confidence=0.6, source="rfid", timestamp="2026-01-01T10:01:00Z")
        # The contradiction should be preserved.
        self.assertEqual(len(wm.contradictions), 1)
        c = wm.contradictions[0]
        self.assertEqual(c.entity_id, "alice_001")
        self.assertEqual(c.field_name, "location")
        self.assertEqual(c.resolution, "unresolved")

    def test_higher_confidence_wins_contradiction(self):
        wm = WorldModel()
        wm.add_entity("alice_001", PERSON, epistemic_status=OBSERVED, confidence=0.9)
        wm.update_entity_state("alice_001", "location", "kitchen", epistemic_status=OBSERVED, confidence=0.6, source="camera", timestamp="2026-01-01T10:00:00Z")
        # Higher confidence observation should become current state.
        wm.update_entity_state("alice_001", "location", "living_room", epistemic_status=OBSERVED, confidence=0.9, source="camera_hd", timestamp="2026-01-01T10:01:00Z")
        entity = wm.get_entity("alice_001")
        self.assertEqual(entity.state_value("location"), "living_room")
        self.assertEqual(len(wm.contradictions), 1)

    def test_resolve_contradiction(self):
        wm = WorldModel()
        wm.add_entity("door_001", OBJECT, epistemic_status=OBSERVED, confidence=0.9)
        wm.update_entity_state("door_001", "open_state", "open", epistemic_status=OBSERVED, confidence=0.7, source="sensor_a", timestamp="2026-01-01T10:00:00Z")
        wm.update_entity_state("door_001", "open_state", "closed", epistemic_status=OBSERVED, confidence=0.7, source="sensor_b", timestamp="2026-01-01T10:01:00Z")
        self.assertEqual(len(wm.contradictions), 1)
        cid = wm.contradictions[0].contradiction_id
        self.assertTrue(wm.resolve_contradiction(cid, "resolved_a"))
        self.assertEqual(wm.contradictions[0].resolution, "resolved_a")


class WorldModelRelationTests(unittest.TestCase):
    def test_add_and_get_relation(self):
        wm = WorldModel()
        wm.add_entity("alice_001", PERSON, labels=["Alice"])
        wm.add_entity("kitchen_001", ROOM, labels=["kitchen"])
        rel = wm.add_relation("alice_001", "located_in", "kitchen_001", epistemic_status=OBSERVED, confidence=0.8, source="camera", timestamp="2026-01-01T10:00:00Z")
        self.assertEqual(rel.relation_type, "located_in")
        self.assertTrue(rel.is_active())

    def test_relations_for_entity(self):
        wm = WorldModel()
        wm.add_entity("alice_001", PERSON, labels=["Alice"])
        wm.add_entity("kitchen_001", ROOM, labels=["kitchen"])
        wm.add_entity("cup_001", OBJECT, labels=["cup"])
        wm.add_relation("alice_001", "located_in", "kitchen_001", epistemic_status=OBSERVED, confidence=0.8, source="camera")
        wm.add_relation("alice_001", "holds", "cup_001", epistemic_status=INFERRED, confidence=0.6, source="inference")
        rels = wm.relations_for("alice_001")
        self.assertEqual(len(rels), 2)

    def test_relation_idempotent_reinforces(self):
        wm = WorldModel()
        wm.add_entity("alice_001", PERSON, labels=["Alice"])
        wm.add_entity("kitchen_001", ROOM, labels=["kitchen"])
        wm.add_relation("alice_001", "located_in", "kitchen_001", epistemic_status=OBSERVED, confidence=0.7, source="camera")
        wm.add_relation("alice_001", "located_in", "kitchen_001", epistemic_status=OBSERVED, confidence=0.8, source="camera")
        rel = wm.get_relation("alice_001", "located_in", "kitchen_001")
        self.assertGreater(rel.confidence, 0.7)  # reinforced


class WorldModelSnapshotTests(unittest.TestCase):
    def test_snapshot_captures_full_state(self):
        wm = WorldModel()
        wm.add_entity("alice_001", PERSON, labels=["Alice"], epistemic_status=OBSERVED, confidence=0.9, provenance=Provenance(source="camera"))
        wm.add_entity("cup_001", OBJECT, labels=["cup"], epistemic_status=OBSERVED, confidence=0.8)
        wm.add_relation("alice_001", "holds", "cup_001", epistemic_status=INFERRED, confidence=0.6, source="inference")
        snap = wm.snapshot(created_at="2026-01-01T10:00:00Z")
        self.assertEqual(snap.world_version, wm.world_version)
        self.assertEqual(len(snap.entities), 2)
        self.assertEqual(len(snap.relations), 1)
        self.assertIn("total_entities", snap.uncertainty_summary)
        self.assertIn("sources", snap.provenance_summary)

    def test_snapshot_is_immutable(self):
        wm = WorldModel()
        wm.add_entity("x", OBJECT)
        snap = wm.snapshot()
        # Modifying the world after snapshot should not affect it.
        wm.add_entity("y", OBJECT)
        self.assertEqual(len(snap.entities), 1)


class WorldModelQueryTests(unittest.TestCase):
    def test_visible_entities_by_location(self):
        wm = WorldModel()
        wm.add_entity("alice_001", PERSON, labels=["Alice"])
        wm.update_entity_state("alice_001", "location", "kitchen", epistemic_status=OBSERVED, confidence=0.9, source="cam")
        wm.add_entity("cup_001", OBJECT, labels=["cup"])
        wm.update_entity_state("cup_001", "location", "kitchen", epistemic_status=OBSERVED, confidence=0.8, source="cam")
        wm.add_entity("door_001", OBJECT, labels=["door"])
        wm.update_entity_state("door_001", "location", "hallway", epistemic_status=OBSERVED, confidence=0.9, source="cam")
        kitchen = wm.visible_entities(location="kitchen")
        kitchen_ids = {e.entity_id for e in kitchen}
        self.assertIn("alice_001", kitchen_ids)
        self.assertIn("cup_001", kitchen_ids)
        self.assertNotIn("door_001", kitchen_ids)

    def test_uncertainty_summary(self):
        wm = WorldModel()
        wm.add_entity("alice_001", PERSON, epistemic_status=OBSERVED, confidence=0.9)
        wm.add_entity("bob_001", PERSON, epistemic_status=UNKNOWN, confidence=0.0)
        wm.add_entity("cup_001", OBJECT, epistemic_status=INFERRED, confidence=0.6)
        summary = wm.uncertainty_summary()
        self.assertEqual(summary["total_entities"], 3)
        self.assertIn(OBSERVED, summary["by_epistemic_status"])
        self.assertIn("bob_001", summary["uncertain_entities"])

    def test_lifecycle_transitions(self):
        wm = WorldModel()
        wm.add_entity("cup_001", OBJECT, labels=["cup"], epistemic_status=OBSERVED, confidence=0.8)
        self.assertEqual(wm.get_entity("cup_001").lifecycle, CANDIDATE)
        wm.update_entity_state("cup_001", "location", "table", epistemic_status=OBSERVED, confidence=0.9, source="cam")
        self.assertEqual(wm.get_entity("cup_001").lifecycle, ACTIVE)
        wm.set_entity_lifecycle("cup_001", STALE)
        self.assertEqual(wm.get_entity("cup_001").lifecycle, STALE)

    def test_archived_entities_not_visible(self):
        wm = WorldModel()
        wm.add_entity("old_cup", OBJECT, labels=["old cup"], epistemic_status=OBSERVED, confidence=0.8)
        wm.set_entity_lifecycle("old_cup", ARCHIVED)
        self.assertEqual(len(wm.visible_entities()), 0)


class WorldModelLineageTests(unittest.TestCase):
    def test_world_version_increments(self):
        wm = WorldModel()
        v0 = wm.world_version
        wm.add_entity("alice_001", PERSON, labels=["Alice"])
        v1 = wm.world_version
        self.assertGreater(v1, v0)
        wm.update_entity_state("alice_001", "location", "kitchen", epistemic_status=OBSERVED, confidence=0.9, source="cam")
        v2 = wm.world_version
        self.assertGreater(v2, v1)

    def test_to_dict_serialization(self):
        wm = WorldModel()
        wm.add_entity("alice_001", PERSON, labels=["Alice"], epistemic_status=OBSERVED, confidence=0.9)
        d = wm.to_dict()
        self.assertIn("world_version", d)
        self.assertIn("entities", d)
        self.assertIn("alice_001", d["entities"])
        self.assertEqual(d["entities"]["alice_001"]["entity_type"], PERSON)


if __name__ == "__main__":
    unittest.main()
