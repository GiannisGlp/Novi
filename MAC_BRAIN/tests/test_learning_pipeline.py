"""Tests for the learning pipeline (roadmap item 13).

Covers the knowledge-promotion pipeline (evidence thresholds, simulation never
promotes), user corrections with provenance (supersede without deleting
history), routine detection (hypotheses only), and the counterfactual engine
(hypothetical, never merged into facts).
"""

import unittest

from MAC_BRAIN.kgraph import EntityKnowledgeGraph
from MAC_BRAIN.learning_pipeline import (
    CorrectionRecord,
    CounterfactualEngine,
    KnowledgePromotionPipeline,
    RoutineDetector,
    UserCorrectionLog,
)


class KnowledgePromotionTests(unittest.TestCase):
    def test_requires_evidence_threshold(self):
        pp = KnowledgePromotionPipeline(promote_min_evidence=3)
        kg = EntityKnowledgeGraph()
        for _ in range(2):  # below threshold
            pp.observe("alice", "prefers", "warm_greeting", confidence=0.9, source="chat")
        self.assertFalse(pp.promote_all_ready(kg))
        self.assertIsNone(kg.leading("alice", "prefers"))

    def test_promotes_past_threshold(self):
        pp = KnowledgePromotionPipeline(promote_min_evidence=3)
        kg = EntityKnowledgeGraph()
        for _ in range(3):
            pp.observe("alice", "prefers", "warm_greeting", confidence=0.9, source="chat")
        self.assertTrue(pp.promote_all_ready(kg))
        self.assertEqual(kg.leading("alice", "prefers").object, "warm_greeting")

    def test_simulation_never_promotes(self):
        pp = KnowledgePromotionPipeline(promote_min_evidence=3)
        kg = EntityKnowledgeGraph()
        for _ in range(5):
            pp.observe("bot", "moves", "door", confidence=0.95, source="sim",
                       epistemic="SIMULATED")
        self.assertEqual(pp.promote_all_ready(kg), 0)
        self.assertIsNone(kg.leading("bot", "moves"))

    def test_prediction_never_promotes(self):
        pp = KnowledgePromotionPipeline(promote_min_evidence=3)
        kg = EntityKnowledgeGraph()
        for _ in range(5):
            pp.observe("alice", "intends", "leave_soon", confidence=0.8,
                       source="prediction", epistemic="PREDICTED")
        self.assertEqual(pp.promote_all_ready(kg), 0)

    def test_observed_with_sufficient_evidence_promotes(self):
        pp = KnowledgePromotionPipeline(promote_min_evidence=2)
        kg = EntityKnowledgeGraph()
        for _ in range(2):
            pp.observe("kitchen", "has", "coffee_maker", confidence=0.9,
                       source="vision", epistemic="OBSERVED")
        self.assertTrue(pp.promote_all_ready(kg))
        self.assertEqual(kg.leading("kitchen", "has").object, "coffee_maker")

    def test_candidate_promoted_only_once(self):
        # Regression: promote_all_ready used to re-promote every ready candidate
        # on each call, inflating graph evidence/confidence without new evidence.
        pp = KnowledgePromotionPipeline(promote_min_evidence=1, promote_min_confidence=0.0)
        kg = EntityKnowledgeGraph()
        pp.observe("a", "r", "b", confidence=0.9)
        self.assertEqual(pp.promote_all_ready(kg), 1)
        self.assertEqual(pp.promote_all_ready(kg), 0)
        self.assertEqual(len(pp.promotions()), 1)


class UserCorrectionTests(unittest.TestCase):
    def setUp(self):
        self.kg = EntityKnowledgeGraph()
        self.kg.add("alice", "prefers", "concise_replies", confidence=0.9,
                    source="observation", cycle=1)

    def test_correction_supersedes_prior_claim(self):
        log = UserCorrectionLog()
        record = CorrectionRecord(
            subject="alice", predicate="prefers", old_object="concise_replies",
            new_object="detailed_replies", person="alice",
            source="spoken", cycle=5,
        )
        changed = log.apply(record, self.kg)
        self.assertTrue(changed)
        self.assertEqual(self.kg.leading("alice", "prefers").object, "detailed_replies")

    def test_prior_evidence_preserved_not_deleted(self):
        log = UserCorrectionLog()
        log.apply(CorrectionRecord("alice", "prefers", "concise_replies",
                                   "detailed_replies", person="alice",
                                   source="spoken", cycle=5), self.kg)
        triples = self.kg.triples(subject="alice", predicate="prefers")
        self.assertEqual(len(triples), 2)
        statuses = {t.object: t.status for t in triples}
        self.assertEqual(statuses["detailed_replies"], "active")
        self.assertEqual(statuses["concise_replies"], "contradicted")

    def test_unchanged_correction_reports_false(self):
        log = UserCorrectionLog()
        changed = log.apply(CorrectionRecord("alice", "prefers", "concise_replies",
                                             "concise_replies", person="alice",
                                             source="spoken", cycle=5), self.kg)
        self.assertFalse(changed)
        self.assertEqual(len(log.records()), 1)  # still recorded as an explicit event

    def test_correction_has_provenance(self):
        log = UserCorrectionLog()
        record = CorrectionRecord("alice", "prefers", "concise_replies",
                                  "detailed_replies", person="alice",
                                  source="spoken", cycle=5)
        log.apply(record, self.kg)
        snap = log.records()[0].snapshot()
        self.assertEqual(snap["corrected_by"], "alice")
        self.assertEqual(snap["source"], "spoken")
        self.assertEqual(snap["old_object"], "concise_replies")


class RoutineDetectorTests(unittest.TestCase):
    def test_repeated_pattern_becomes_routine_hypothesis(self):
        rd = RoutineDetector(window=3, min_occurrences=2)
        rd.observe(1, {"morning_coffee", "alice_present"})
        rd.observe(2, {"morning_coffee", "alice_present"})
        self.assertEqual(len(rd.routines()), 0)
        rd.observe(3, {"morning_coffee", "alice_present"})
        self.assertEqual(len(rd.routines()), 0)  # one full window: still accumulating
        rd.observe(4, {"morning_coffee", "alice_present"})
        routines = rd.routines()
        self.assertEqual(len(routines), 1)
        r = routines[0]
        self.assertEqual(set(r.pattern), {"morning_coffee", "alice_present"})
        self.assertGreaterEqual(r.occurrences, 2)
        self.assertEqual(r.snapshot()["epistemic"], "INFERRED")

    def test_one_off_pattern_is_not_a_routine(self):
        rd = RoutineDetector(window=3, min_occurrences=2)
        rd.observe(1, {"event_a"})
        rd.observe(2, {"event_b"})
        rd.observe(3, {"event_c"})
        self.assertEqual(len(rd.routines()), 0)


class CounterfactualEngineTests(unittest.TestCase):
    def test_query_is_hypothetical_and_never_factual(self):
        ce = CounterfactualEngine()
        result = ce.evaluate(
            premise="if the door were closed",
            if_evidence={"door": "closed"},
            then_prediction="alice would knock",
            confidence=0.5,
        )
        self.assertEqual(result["epistemic"], "SIMULATED")
        self.assertEqual(result["status"], "hypothetical")
        self.assertEqual(len(ce.queries()), 1)

    def test_queries_are_snapshotted_in_order(self):
        ce = CounterfactualEngine()
        ce.evaluate(premise="p1", if_evidence={"a": 1}, then_prediction="t1")
        ce.evaluate(premise="p2", if_evidence={"b": 2}, then_prediction="t2")
        self.assertEqual([q["premise"] for q in ce.queries()], ["p1", "p2"])


class RuntimeLearningTests(unittest.TestCase):
    @staticmethod
    def _brain():
        from brain.b2_perception import DeterministicPerceptionBackend, SpecialistPerception
        from MAC_BRAIN.runtime import MacBrain, MacBrainConfig
        from MAC_BRAIN.tests.test_mac_brain import FakeCamera
        return MacBrain(
            camera=FakeCamera(),
            perception=SpecialistPerception(DeterministicPerceptionBackend()),
            config=MacBrainConfig(curiosity_enabled=False),
            store_path=None,
        )

    def test_runtime_wires_pipeline(self):
        brain = self._brain()
        brain.start()
        try:
            self.assertIsNotNone(brain.learning)
            self.assertIsNotNone(brain.corrections)
            self.assertIsNotNone(brain.routines)
            self.assertIsNotNone(brain.counterfactuals)
        finally:
            brain.stop()

    def test_runtime_promotes_and_emits(self):
        brain = self._brain()
        brain.start()
        try:
            promoted = False
            for i in range(3):
                promoted = brain.observe_knowledge(
                    "alice", "prefers", "warm_greeting",
                    confidence=0.9, source=f"chat-{i}")
            self.assertTrue(promoted)
            self.assertEqual(brain.knowledge.leading("alice", "prefers").object, "warm_greeting")
            emitted = [e for e in brain.events if e.get("event_type") == "learning.candidate"]
            self.assertGreaterEqual(len(emitted), 3)
            self.assertEqual(emitted[-1]["payload"]["status"], "promoted")
        finally:
            brain.stop()

    def test_runtime_correction_emits_changed(self):
        brain = self._brain()
        brain.start()
        try:
            for i in range(3):
                brain.observe_knowledge("alice", "prefers", "warm_greeting",
                                        confidence=0.9, source=f"chat-{i}")
            changed = brain.correct_knowledge("alice", "prefers", "short_greeting",
                                              person="alice")
            self.assertTrue(changed)
            self.assertEqual(brain.knowledge.leading("alice", "prefers").object, "short_greeting")
            emitted = [e for e in brain.events if e.get("event_type") == "learning.corrected"]
            self.assertEqual(len(emitted), 1)
            self.assertEqual(emitted[0]["payload"]["corrected_by"], "alice")
        finally:
            brain.stop()

    def test_runtime_counterfactual_never_merges(self):
        brain = self._brain()
        brain.start()
        try:
            q = brain.counterfactual(premise="if door closed",
                                     if_evidence={"door": "closed"},
                                     then_prediction="alice knocks")
            self.assertEqual(q["epistemic"], "SIMULATED")
            self.assertIsNone(brain.knowledge.leading("door", "sounds"))
        finally:
            brain.stop()


if __name__ == "__main__":
    unittest.main()
