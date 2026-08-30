"""Tests for novi/brain/working_memory.py — bounded working memory.

Plan 22 Phase 4:
- slots update correctly (person/topic/goal/questions/events/utterances);
- lifecycle: expire stale, promote important to LTM;
- boundedness: a long interaction never grows unbounded (the acceptance
  criterion — 30 minutes of interaction must not cause unbounded growth).
"""

from __future__ import annotations

import unittest

from novi.brain.working_memory import (
    DEFAULT_MAX_ITEMS,
    DEFAULT_MAX_TOKENS,
    PROMOTION_IMPORTANCE,
    WorkingMemory,
)


class WorkingMemoryUpdateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.wm = WorkingMemory()

    def test_slots_update(self) -> None:
        self.wm.update(cycle=1, person="vano", topic="camera integration", scene="office")
        self.wm.update(cycle=1, question="did we close the perception link?")
        self.wm.update(cycle=2, hypothesis="camera pipeline is not grounded")
        snap = self.wm.snapshot()
        self.assertEqual(snap["current_person"], "vano")
        self.assertEqual(snap["current_topic"], "camera integration")
        self.assertEqual(snap["current_scene"], "office")
        self.assertEqual(snap["unresolved_questions"], ["did we close the perception link?"])
        self.assertEqual(snap["current_hypotheses"], ["camera pipeline is not grounded"])

    def test_utterances_and_events_recorded_with_cycle(self) -> None:
        self.wm.update(cycle=3, utterance="hey novi", utterance_source="web")
        self.wm.update(cycle=3, event={"kind": "person.entered", "importance": 0.9, "entity": "vano"})
        snap = self.wm.snapshot()
        self.assertEqual(snap["recent_utterances"][0]["text"], "hey novi")
        self.assertEqual(snap["recent_utterances"][0]["cycle"], 3)
        self.assertEqual(snap["recent_events"][0]["kind"], "person.entered")

    def test_unresolved_references_bounded(self) -> None:
        for i in range(20):
            self.wm.update(question=f"q{i}")
            self.wm.update(reference=f"ref-{i}")
        self.assertLessEqual(len(self.wm.unresolved_questions), self.wm.max_unresolved_references)
        self.assertLessEqual(len(self.wm.active_references), self.wm.max_unresolved_references)

    def test_commitments_bounded(self) -> None:
        for i in range(20):
            self.wm.update(commitment={"trigger": f"t{i}", "action": "remind"})
        self.assertLessEqual(len(self.wm.pending_commitments), self.wm.max_unresolved_references)


class WorkingMemoryBoundednessTest(unittest.TestCase):
    def test_long_interaction_stays_bounded(self) -> None:
        """Acceptance (plan §8): a long interaction never grows unbounded."""
        wm = WorkingMemory()
        for cycle in range(1, 1000):
            wm.update(cycle=cycle, utterance="a fairly long conversational turn " * 4)
            wm.update(cycle=cycle, event={"kind": "perception", "importance": 0.4, "entity": "x"})
            wm.update(cycle=cycle, topic="some topic")
        self.assertLessEqual(len(wm.recent_utterances), DEFAULT_MAX_ITEMS)
        self.assertLessEqual(len(wm.recent_events), DEFAULT_MAX_ITEMS)
        self.assertLessEqual(wm.token_estimate(), DEFAULT_MAX_TOKENS + 64)
        self.assertLessEqual(wm.snapshot()["token_estimate"], DEFAULT_MAX_TOKENS + 64)

    def test_token_budget_evicts_oldest_utterances(self) -> None:
        wm = WorkingMemory(max_tokens=120)
        for _ in range(50):
            wm.update(utterance="this sentence contains a great many tokens " * 3)
        self.assertLessEqual(wm.token_estimate(), 120 + 64)
        # the newest utterance survived; the oldest were evicted
        self.assertTrue(wm.recent_utterances[-1]["text"].startswith("this sentence"))


class WorkingMemoryLifecycleTest(unittest.TestCase):
    def test_expire_drops_stale_entries(self) -> None:
        wm = WorkingMemory(max_event_age_cycles=5)
        wm.update(cycle=1, event={"kind": "a", "importance": 0.3})
        wm.update(cycle=2, event={"kind": "b", "importance": 0.3})
        expired = wm.expire(cycle=10)
        self.assertEqual([e["kind"] for e in expired], ["a", "b"])
        self.assertEqual(wm.snapshot()["recent_events"], [])

    def test_promote_important_events_only_once(self) -> None:
        wm = WorkingMemory()
        promoted: list[str] = []
        wm.update(cycle=1, event={"event_id": "ev-1", "kind": "person.entered", "importance": 0.9})
        wm.update(cycle=1, event={"event_id": "ev-2", "kind": "chair", "importance": 0.2})
        first = wm.promote_important(lambda e: promoted.append(e["event_id"]))
        self.assertEqual([e["event_id"] for e in first], ["ev-1"])
        # low-importance events never promote; important ones promote once
        second = wm.promote_important(lambda e: promoted.append(e["event_id"]))
        self.assertEqual(second, [])
        self.assertEqual(promoted, ["ev-1"])

    def test_promotion_threshold_constant(self) -> None:
        self.assertEqual(PROMOTION_IMPORTANCE, 0.7)


class WorkingMemoryEngineWiringTest(unittest.TestCase):
    """Phase 4: the step loop refreshes working memory and keeps it bounded."""

    def test_step_updates_working_memory(self) -> None:
        from novi.brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
        from novi.brain.engine import MacBrain, MacBrainConfig
        from novi.brain.tests.test_mac_brain import FakeCamera

        class PersonBackend(DeterministicPerceptionBackend):
            def detect(self, frame):
                return (Detection("person", 0.95, (0.0, 0.0, 1.0, 1.0)),)

        brain = MacBrain(
            camera=FakeCamera(),
            perception=SpecialistPerception(PersonBackend()),
            config=MacBrainConfig(curiosity_enabled=False),
        )
        brain.start()
        try:
            brain.respond("hey novi", person="vano")
            for _ in range(3):
                brain.step()
            snap = brain.working_memory.snapshot()
            self.assertGreater(len(snap["recent_events"]), 0)
            self.assertGreater(len(snap["recent_utterances"]), 0)
            self.assertLessEqual(snap["token_estimate"], 1700)
        finally:
            brain.stop()


if __name__ == "__main__":
    unittest.main()
