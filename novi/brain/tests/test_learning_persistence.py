"""Phase 4c (north-star gap analysis): learning survives restart AND changes
behavior afterwards.

docs/audits/NOVI_NORTH_STAR_GAP_ANALYSIS_2026-08-29.md §4 Phase 4c:
"Persist learning subsystems and connect them to behavior (routines/
corrections/reflections/lessons survive restart; promoted routine changes
action selection; protected invariants untouched)."

Acceptance:
- a learned routine, reflections, and lessons all survive a full engine
  restart over the same store;
- a restored routine SHIFTS the deliberator's option scores (learning
  changes behavior after restart, not just in memory);
- a corrupted learning blob fails closed at startup (fresh learning, no
  crash).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from novi.brain.b2_perception import SpecialistPerception
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.io import CameraFrame
from novi.brain.models.reasoning import DeliberativeReasoningProvider
from novi.brain.storage import DurableMemoryStore


class _Cam:
    def __init__(self) -> None:
        self.sequence = 0

    def close(self) -> None:
        self.sequence = self.sequence

    def read(self) -> CameraFrame:
        self.sequence += 1
        return CameraFrame(
            frame_id=f"f-{self.sequence}",
            captured_at="2026-08-29T12:00:00Z",
            width=2,
            height=2,
            payload=b"frame",
            metadata={"backend": "test"},
        )


def _brain(store_path: str) -> MacBrain:
    return MacBrain(
        camera=_Cam(),
        perception=SpecialistPerception(),
        store_path=store_path,
        config=MacBrainConfig(curiosity_enabled=False),
    )


class LearningPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.store_path = str(Path(self._tmp.name) / "mem.db")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_routines_reflections_and_lessons_survive_restart(self):
        first = _brain(self.store_path)
        first.start()
        try:
            for cycle in (1, 2, 3, 4, 5, 6):
                first.routines.observe(cycle, {"cup", "key"})
            first.reflection.record(cycle=5, action="inspect", intent="look", effective=False)
            lesson = first.lessons.propose(title="approach the cup gently", evidence_refs=("obs-1",))
            lesson.verified = True
            first.lessons.promote(lesson, regression_scenario="cup_scenario")
            first.persist_learning()
        finally:
            first.stop()

        second = _brain(self.store_path)
        second.start()
        try:
            self.assertIn(
                ("cup", "key"),
                [tuple(r.pattern) for r in second.routines.routines()],
                "learned routines must survive a restart",
            )
            self.assertIsNotNone(second.reflection.last())
            self.assertEqual(second.reflection.last().action, "inspect")
            self.assertEqual(second.lessons.scenarios_for(lesson.lesson_id), ("cup_scenario",))
        finally:
            second.stop()

    def test_restored_routine_shifts_action_selection(self):
        first = _brain(self.store_path)
        first.start()
        try:
            for cycle in (1, 2, 3, 4, 5, 6):
                first.routines.observe(cycle, {"cup", "alice"})
            first.persist_learning()
        finally:
            first.stop()

        second = _brain(self.store_path)
        second.start()
        try:
            provider = DeliberativeReasoningProvider()
            evidence = {"inspect": 0.0, "observe": 0.2, "wait": 0.0,
                        "move_forward": 0.0, "turn_left": 0.0, "turn_right": 0.0}
            with_routine = provider._option_scores(evidence, 0.7, {
                "salient_entities": ("cup",),
                "routines": [list(r.pattern) for r in second.routines.routines()],
            })
            without_routine = provider._option_scores(evidence, 0.7, {"salient_entities": ("cup",)})
            self.assertGreater(
                with_routine["observe"].expected_success,
                without_routine["observe"].expected_success,
                "the restored routine must raise the attention option's success evidence",
            )
        finally:
            second.stop()

    def test_corrupted_learning_blob_fails_closed(self):
        first = _brain(self.store_path)
        first.start()
        try:
            first.persist_learning()
        finally:
            first.stop()

        # Corrupt the blob directly.
        store = DurableMemoryStore(self.store_path)
        store._conn.execute("INSERT OR REPLACE INTO learning (key, value) VALUES ('state', 'not-json{')")
        store._conn.commit()
        store.close()

        second = _brain(self.store_path)
        second.start()
        try:
            self.assertEqual(second.routines.routines(), (), "corrupt blob -> fresh learning")
        finally:
            second.stop()


class DedicatedLearningTableTests(unittest.TestCase):
    """Dedicated store tables + immediate persist + behavior loop.

    - save_*/load_* round-trip over the SAME db path across a store reopen;
    - a user correction changes a subsequent decision (behavior loop);
    - a routine observed via the engine (no manual persist) survives restart.
    Socket-free, deterministic, tmp DB paths.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.store_path = str(Path(self._tmp.name) / "mem.db")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_dedicated_tables_survive_store_reopen(self):
        from novi.brain.kgraph import EntityKnowledgeGraph
        from novi.brain.learning_pipeline import (
            CorrectionRecord,
            KnowledgePromotionPipeline,
            RoutineDetector,
            UserCorrectionLog,
        )
        from novi.brain.recovery import RegressionMemory
        from novi.brain.reflection import ReflectionEngine

        store = DurableMemoryStore(self.store_path)
        pipeline = KnowledgePromotionPipeline()
        graph = EntityKnowledgeGraph()
        for _ in range(3):
            pipeline.observe("alice", "prefers", "warm_greeting", confidence=0.9, source="chat")
        self.assertEqual(pipeline.promote_all_ready(graph), 1)
        detector = RoutineDetector()
        for cycle in (1, 2, 3, 4):
            detector.observe(cycle, {"cup", "key"})
        corrections = UserCorrectionLog()
        corrections.apply(
            CorrectionRecord(
                subject="novi", predicate="should_do", old_object="inspect",
                new_object="wait", person="tester", source="user_correction", cycle=1,
            ),
            graph,
        )
        reflection = ReflectionEngine()
        reflection.record(cycle=2, action="inspect", intent="look", effective=False)
        lessons = RegressionMemory()
        lesson = lessons.propose(title="approach gently", evidence_refs=("obs-1",))
        lesson.verified = True
        lessons.promote(lesson, regression_scenario="cup_scenario")
        store.save_routines(detector.snapshot())
        store.save_corrections(corrections.snapshot())
        store.save_reflections(reflection.snapshot())
        store.save_lessons(lessons.snapshot())
        store.save_promotions(pipeline.snapshot())
        store.close()

        reopened = DurableMemoryStore(self.store_path)
        try:
            restored_detector = RoutineDetector().from_snapshot(reopened.load_routines())
            self.assertIn(
                ("cup", "key"),
                [tuple(r.pattern) for r in restored_detector.routines()],
                "routines must survive a store reopen",
            )
            restored_corrections = UserCorrectionLog().restore(reopened.load_corrections())
            self.assertEqual(len(restored_corrections.records()), 1)
            self.assertEqual(restored_corrections.records()[0].new_object, "wait")
            restored_reflection = ReflectionEngine.from_snapshot(reopened.load_reflections())
            self.assertIsNotNone(restored_reflection.last())
            self.assertEqual(restored_reflection.last().action, "inspect")
            restored_lessons = RegressionMemory().from_snapshot(reopened.load_lessons())
            self.assertEqual(restored_lessons.scenarios_for(lesson.lesson_id), ("cup_scenario",))
            restored_pipeline = KnowledgePromotionPipeline().from_snapshot(reopened.load_promotions())
            self.assertEqual(len(restored_pipeline.promotions()), 1)
            # Promotion history dedup survives the round trip: nothing re-promotes.
            self.assertEqual(restored_pipeline.promote_all_ready(EntityKnowledgeGraph()), 0)
        finally:
            reopened.close()

    def test_correction_changes_subsequent_decision(self):
        from novi.brain.models.reasoning import DeliberativeReasoningProvider

        brain = _brain(self.store_path)
        brain.start()
        try:
            brain.knowledge.add(
                "novi", "should_do", "inspect", confidence=0.9, source="test", cycle=0
            )
            provider = DeliberativeReasoningProvider()
            baseline = provider.decide(
                conclusion="environmental_change_is_relevant",
                confidence=0.9,
                situation={"salient_entities": ()},
            )
            self.assertEqual(baseline.action, "inspect")
            changed = brain.correct_knowledge(
                "novi", "should_do", "wait", person="tester"
            )
            self.assertTrue(changed)
            self.assertTrue(
                any(e.get("event_type") == "learning.corrected" for e in brain.events),
                "corrections must emit via self._emit",
            )
            corrected = provider.decide(
                conclusion="environmental_change_is_relevant",
                confidence=0.9,
                situation={
                    "salient_entities": (),
                    "corrections": brain.corrections.snapshot(),
                },
            )
            self.assertNotEqual(
                corrected.action, baseline.action,
                "a correction must change the subsequent decision",
            )
            self.assertEqual(corrected.action, "wait")
        finally:
            brain.stop()

        # The correction was persisted immediately: it survives the restart.
        restarted = _brain(self.store_path)
        restarted.start()
        try:
            records = restarted.corrections.records()
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].new_object, "wait")
        finally:
            restarted.stop()

    def test_routine_survives_restart_without_manual_persist(self):
        first = _brain(self.store_path)
        first.start()
        try:
            # No explicit persist_learning(): observe_routine checkpoints itself.
            for cycle in (1, 2, 3, 4, 5):
                first._cycle = cycle
                first.observe_routine({"cup", "key"})
            self.assertIn(
                ("cup", "key"),
                [tuple(r.pattern) for r in first.routines.routines()],
            )
        finally:
            first.stop()

        second = _brain(self.store_path)
        second.start()
        try:
            self.assertIn(
                ("cup", "key"),
                [tuple(r.pattern) for r in second.routines.routines()],
                "routines persisted on update must survive a restart",
            )
        finally:
            second.stop()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
