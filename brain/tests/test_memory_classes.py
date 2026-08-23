"""Tests for the memory-class decision + schema-evolution hooks (item 16).

The decision itself is recorded in brain/memory_classes.py; these tests
pin the now-vs-defer classification and the L0–L6 autonomy gate so the
decision cannot silently drift.
"""

import unittest

from brain.memory_classes import (
    DEFERRED_CLASSES,
    IMPLEMENTED_NOW,
    MemoryClass,
    MemoryClassDecisionRegistry,
    SchemaEvolutionGate,
    SchemaEvolutionLevel,
)


class MemoryClassDecisionTests(unittest.TestCase):
    def setUp(self):
        self.registry = MemoryClassDecisionRegistry()

    def test_implemented_classes_recorded(self):
        implemented = set(self.registry.implemented())
        for cls in IMPLEMENTED_NOW:
            self.assertIn(cls, implemented)
        self.assertIn(MemoryClass.SEMANTIC, implemented)
        self.assertIn(MemoryClass.SPATIAL, implemented)
        self.assertIn(MemoryClass.EPISODIC, implemented)

    def test_deferred_classes_recorded(self):
        deferred = set(self.registry.deferred())
        for cls in DEFERRED_CLASSES:
            self.assertIn(cls, deferred)
        # The four heavy classes are deferred by design (body phase).
        self.assertIn(MemoryClass.PROCEDURAL_COMPETENCE, deferred)
        self.assertIn(MemoryClass.PROSPECTIVE, deferred)
        self.assertIn(MemoryClass.METAMEMORY, deferred)
        self.assertIn(MemoryClass.AUTOBIOGRAPHICAL, deferred)

    def test_no_class_is_both_implemented_and_deferred(self):
        self.assertTrue(IMPLEMENTED_NOW.isdisjoint(DEFERRED_CLASSES))

    def test_every_class_has_a_decision(self):
        for cls in MemoryClass:
            decision = self.registry.decision(cls)
            self.assertIn(decision.state, {"implemented", "deferred", "candidate"})
            self.assertTrue(decision.rationale)

    def test_snapshot_round_trip(self):
        snap = self.registry.snapshot()
        self.assertEqual(len(snap["implemented"]), len(IMPLEMENTED_NOW))
        self.assertEqual(len(snap["deferred"]), len(DEFERRED_CLASSES))
        self.assertEqual(len(snap["decisions"]), len(MemoryClass))


class SchemaEvolutionGateTests(unittest.TestCase):
    def setUp(self):
        self.gate = SchemaEvolutionGate()

    def test_l0_to_l3_are_autonomous(self):
        for level in (SchemaEvolutionLevel.L0_RUNTIME_STATE,
                      SchemaEvolutionLevel.L1_MEMORY_CONTENT,
                      SchemaEvolutionLevel.L2_KNOWLEDGE_CONTENT,
                      SchemaEvolutionLevel.L3_NONSTRUCTURAL_METADATA):
            self.assertTrue(self.gate.is_autonomously_allowed(level))

    def test_l4_to_l6_are_not_autonomous(self):
        for level in (SchemaEvolutionLevel.L4_SCHEMA_EXTENSION,
                      SchemaEvolutionLevel.L5_RUNTIME_SOFTWARE,
                      SchemaEvolutionLevel.L6_PROTECTED_CORE):
            self.assertFalse(self.gate.is_autonomously_allowed(level))

    def test_proposal_records_level_and_allowed(self):
        p1 = self.gate.propose(change_id="chg-1", description="add tag column",
                               level=SchemaEvolutionLevel.L3_NONSTRUCTURAL_METADATA,
                               compatibility="COMPATIBLE")
        self.assertTrue(p1.allowed)
        p2 = self.gate.propose(change_id="chg-2", description="add entity type",
                               level=SchemaEvolutionLevel.L4_SCHEMA_EXTENSION,
                               compatibility="MIGRATION_REQUIRED")
        self.assertFalse(p2.allowed)
        self.assertEqual(len(self.gate.proposals()), 2)

    def test_protected_core_never_allowed(self):
        p = self.gate.propose(change_id="chg-3", description="rewrite governance",
                              level=SchemaEvolutionLevel.L6_PROTECTED_CORE,
                              compatibility="FORBIDDEN")
        self.assertFalse(p.allowed)
        self.assertEqual(p.compatibility, "FORBIDDEN")


class RuntimeMemoryClassTests(unittest.TestCase):
    @staticmethod
    def _brain():
        from brain.b2_perception import DeterministicPerceptionBackend, SpecialistPerception
        from brain.engine import MacBrain, MacBrainConfig
        from brain.tests.test_mac_brain import FakeCamera
        return MacBrain(
            camera=FakeCamera(),
            perception=SpecialistPerception(DeterministicPerceptionBackend()),
            config=MacBrainConfig(curiosity_enabled=False),
            store_path=None,
        )

    def test_runtime_wires_registry_and_gate(self):
        brain = self._brain()
        brain.start()
        try:
            self.assertIsNotNone(brain.memory_classes)
            self.assertIsNotNone(brain.schema_evolution)
            self.assertIn("semantic", brain.memory_classes.snapshot()["implemented"])
            self.assertIn("prospective", brain.memory_classes.snapshot()["deferred"])
        finally:
            brain.stop()


if __name__ == "__main__":
    unittest.main()
