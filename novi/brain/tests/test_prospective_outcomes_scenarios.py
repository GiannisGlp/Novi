"""Tests for plan 22 Phase 6/18/20 — prospective memory, interaction
outcomes, behavioral learning — plus the Phase 20 proactive scenarios P1–P9
driven through the deterministic policy/salience/social layers.
"""

from __future__ import annotations

import unittest

from novi.brain.dialogue_policy import DialogueAct, DialogueContext, DialoguePolicy
from novi.brain.interaction_outcome import InteractionOutcome, OutcomeRecorder
from novi.brain.prospective_memory import (
    PENDING,
    ProspectiveMemoryStore,
    TriggerKind,
)
from novi.brain.salience import SalienceGate
from novi.brain.social_context import SocialContextBuilder


class ProspectiveMemoryTest(unittest.TestCase):
    def test_register_and_check_due_on_conversation_end(self) -> None:
        store = ProspectiveMemoryStore()
        store.register(
            trigger="conversation_end", intended_action="remind_vano(camera_test)",
            owner="vano", priority=0.8,
        )
        self.assertEqual(len(store.pending_entries()), 1)
        due = store.check_due(conversation_ended=True)
        self.assertEqual(len(due), 1)
        self.assertEqual(due[0].status, "due")
        # not due again after fulfillment
        self.assertTrue(store.fulfill(due[0].memory_id))
        self.assertEqual(store.check_due(conversation_ended=True), [])

    def test_time_trigger_fires_when_due(self) -> None:
        store = ProspectiveMemoryStore()
        store.register(
            trigger="time", intended_action="remind(camera_test)",
            trigger_kind=TriggerKind.TIME, due_at="2026-08-30T12:00:00+00:00",
        )
        due = store.check_due(now="2026-08-30T12:01:00+00:00")
        self.assertEqual(len(due), 1)
        self.assertEqual(store.check_due(now="2026-08-30T11:00:00+00:00"), [])

    def test_cancel(self) -> None:
        store = ProspectiveMemoryStore()
        mem = store.register(trigger="x", intended_action="y")
        self.assertTrue(store.cancel(mem.memory_id))
        self.assertEqual(mem.status, "cancelled")
        self.assertNotIn(mem, store.pending_entries())

    def test_bounded_and_snapshot_round_trip(self) -> None:
        store = ProspectiveMemoryStore(max_entries=4)
        for i in range(10):
            store.register(trigger=f"t{i}", intended_action=f"a{i}")
        self.assertLessEqual(len(store._entries), 4)
        restored = ProspectiveMemoryStore.from_snapshot(store.snapshot())
        self.assertEqual(len(restored._entries), len(store._entries))
        self.assertEqual(restored.pending_entries()[0].status, PENDING)


class OutcomeRecorderTest(unittest.TestCase):
    def test_records_and_captures_corrections(self) -> None:
        rec = OutcomeRecorder()
        rec.record(InteractionOutcome(
            interaction_id="i1", input_text="move that", person="vano",
            dialogue_act="CLARIFY", response_text="the blue bottle?",
            user_reaction="correction", correction="no, the red one",
        ))
        rec.record(InteractionOutcome(
            interaction_id="i2", input_text="thanks", person="vano",
            dialogue_act="ACKNOWLEDGE", response_text="sure",
        ))
        self.assertEqual(len(rec.recent()), 2)
        corrections = rec.corrections()
        self.assertEqual(len(corrections), 1)
        self.assertEqual(corrections[0].correction, "no, the red one")
        self.assertEqual(rec.latest().interaction_id, "i2")  # type: ignore[union-attr]

    def test_bounded_history(self) -> None:
        rec = OutcomeRecorder()
        for i in range(100):
            rec.record(InteractionOutcome(interaction_id=f"i{i}", input_text="x", person="p"))
        self.assertLessEqual(len(rec._outcomes), 64)


class BehavioralLearningTest(unittest.TestCase):
    """Phase 18.3: persisted preferences must affect future behavior."""

    def test_verbosity_preference_changes_behavior(self) -> None:
        from novi.brain.b2_perception import DeterministicPerceptionBackend, SpecialistPerception
        from novi.brain.engine import MacBrain, MacBrainConfig
        from novi.brain.tests.test_mac_brain import FakeCamera

        brain = MacBrain(
            camera=FakeCamera(),
            perception=SpecialistPerception(DeterministicPerceptionBackend()),
            config=MacBrainConfig(curiosity_enabled=False),
        )
        brain.start()
        try:
            brain.ingest_transcript(
                __import__("novi.brain.models", fromlist=["TranscriptionResult"]).TranscriptionResult(
                    text="i am vano", confidence=0.9, language="en",
                    audio_path="t.wav", provider="test", model_id="test",
                )
            )
            brain.learn_preference("person", "verbosity", "short", explicit=True)
            model = brain.person_registry.person("person")
            self.assertEqual(model.preferences.get("verbosity"), "short")  # type: ignore[union-attr]
            # Phase 18.3: the persisted preference is available to behavior
            self.assertEqual(brain._preferred_verbosity("person"), "short")
        finally:
            brain.stop()


class ProactiveScenarioSuiteTest(unittest.TestCase):
    """Plan §24 scenarios P1–P9 through the deterministic layers."""

    def setUp(self) -> None:
        self.policy = DialoguePolicy()
        self.gate = SalienceGate()
        self.social = SocialContextBuilder()

    # P1 — unknown person enters: greet cautiously (policy offers GREETING only
    # when opportunity is right; the addressee is unknown)
    def test_p1_unknown_person_enters(self) -> None:
        ctx = DialogueContext(
            person_entered=True, addressee="unknown person",
            addressee_known=False, social_opportunity=0.6, interruptibility=1.0,
        )
        dec = self.policy.decide(ctx)
        self.assertIn(dec.act, (DialogueAct.GREETING, DialogueAct.SILENCE))
        self.assertEqual(dec.target, "unknown person")

    # P2 — known person enters: greeting
    def test_p2_known_person_enters(self) -> None:
        dec = self.policy.decide(DialogueContext(
            person_entered=True, addressee="vano", addressee_known=True,
            social_opportunity=0.7, interruptibility=1.0,
        ))
        self.assertEqual(dec.act, DialogueAct.GREETING)

    # P3 — familiar object disappears: comment only via worth-saying kinds
    def test_p3_object_disappears(self) -> None:
        speak, _ = self.gate.should_speak({}, kind="object.disappeared", entity="mug", novelty=0.9)
        self.assertTrue(speak)
        dec = self.policy.decide(DialogueContext(
            salient_events=[{"kind": "object.disappeared", "entity": "mug"}],
            interruptibility=1.0, initiative_budget_available=True,
        ))
        self.assertEqual(dec.act, DialogueAct.COMMENT)

    # P4 — unusual sound: hearing anomaly is worth asking about
    def test_p4_unusual_sound(self) -> None:
        speak, _ = self.gate.should_speak({}, kind="hearing.anomaly", novelty=0.85)
        self.assertTrue(speak)

    # P5 — task completion
    def test_p5_task_completion(self) -> None:
        speak, _ = self.gate.should_speak({}, kind="task.completed", novelty=0.0)
        self.assertTrue(speak)

    # P6 — unresolved conversation thread drives continuation
    def test_p6_unresolved_thread(self) -> None:
        dec = self.policy.decide(DialogueContext(
            open_threads=["camera integration"], addressee="vano",
            social_opportunity=0.7, initiative_budget_available=True,
        ))
        self.assertEqual(dec.act, DialogueAct.CONTINUE)

    # P7 — user unavailable: silent despite salient non-urgent event
    def test_p7_user_unavailable_stays_silent(self) -> None:
        dec = self.policy.decide(DialogueContext(
            salient_events=[{"kind": "object.moved", "entity": "mug"}],
            interruptibility=0.0, user_engagement=0.0,
            social_opportunity=0.0, initiative_budget_available=True,
        ))
        self.assertEqual(dec.act, DialogueAct.SILENCE)

    # P8 — user already speaking: no interruption
    def test_p8_user_speaking_no_interrupt(self) -> None:
        dec = self.policy.decide(DialogueContext(
            person_entered=True, social_opportunity=0.8, speaking_lease_held=True,
        ))
        self.assertEqual(dec.act, DialogueAct.SILENCE)

    # P9 — safety event overrides ordinary social suppression
    def test_p9_safety_overrides(self) -> None:
        dec = self.policy.decide(DialogueContext(
            speaking_lease_held=True, safety_event=True, interruptibility=0.0,
        ))
        self.assertEqual(dec.act, DialogueAct.WARN)


if __name__ == "__main__":
    unittest.main()
