"""Tests for novi/brain/dialogue_policy.py — the social decision layer.

Plan 22 Phase 10 and the required dialogue test classes:
- answer when addressed;
- silence when nothing relevant is happening;
- proactive comment only above threshold;
- no proactive speech during active turn unless safety-critical;
- unresolved thread can produce follow-up;
- every proactive decision carries the why_* fields (Task 10.2).
"""

from __future__ import annotations

import unittest

from novi.brain.dialogue_policy import DialogueAct, DialogueContext, DialoguePolicy


class DialoguePolicyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = DialoguePolicy()

    def test_answer_when_addressed(self) -> None:
        ctx = DialogueContext(has_user_message=True, user_message="what time is it?", is_question=True, addressee="vano")
        dec = self.policy.decide(ctx)
        self.assertEqual(dec.act, DialogueAct.RESPOND)
        self.assertEqual(dec.target, "vano")
        self.assertEqual(dec.verbosity, "medium")

    def test_silence_when_nothing_relevant(self) -> None:
        dec = self.policy.decide(DialogueContext())
        self.assertEqual(dec.act, DialogueAct.SILENCE)
        self.assertIn("silence", dec.why_speak)

    def test_greeting_reactive_and_proactive(self) -> None:
        reactive = self.policy.decide(DialogueContext(has_user_message=True, is_greeting=True, addressee="vano"))
        self.assertEqual(reactive.act, DialogueAct.GREETING)
        proactive = self.policy.decide(
            DialogueContext(person_entered=True, addressee="vano", social_opportunity=0.7, interruptibility=1.0)
        )
        self.assertEqual(proactive.act, DialogueAct.GREETING)
        # low opportunity → stay silent despite the entrance
        low = self.policy.decide(
            DialogueContext(person_entered=True, addressee="vano", social_opportunity=0.1, interruptibility=0.0)
        )
        self.assertEqual(low.act, DialogueAct.SILENCE)

    def test_farewell_and_acknowledgement(self) -> None:
        self.assertEqual(
            self.policy.decide(DialogueContext(has_user_message=True, is_farewell=True)).act,
            DialogueAct.FAREWELL,
        )
        self.assertEqual(
            self.policy.decide(DialogueContext(has_user_message=True, is_thanks=True)).act,
            DialogueAct.ACKNOWLEDGE,
        )

    def test_clarification_when_ambiguous(self) -> None:
        dec = self.policy.decide(
            DialogueContext(has_user_message=True, clarification_needed=True, unresolved_questions=["which bottle?"])
        )
        self.assertEqual(dec.act, DialogueAct.CLARIFY)
        self.assertIn("never silently guess", dec.why_speak)

    def test_correction_triggers_repair(self) -> None:
        dec = self.policy.decide(DialogueContext(has_user_message=True, is_correction=True))
        self.assertEqual(dec.act, DialogueAct.REPAIR)

    def test_no_proactive_speech_during_active_turn(self) -> None:
        ctx = DialogueContext(
            speaking_lease_held=True, person_entered=True,
            commitments_due=["remind about camera test"], safety_event=False,
        )
        dec = self.policy.decide(ctx)
        self.assertEqual(dec.act, DialogueAct.SILENCE)
        self.assertEqual(dec.reason, "composing_hold")

    def test_safety_overrides_turn_suppression(self) -> None:
        dec = self.policy.decide(
            DialogueContext(speaking_lease_held=True, safety_event=True)
        )
        self.assertEqual(dec.act, DialogueAct.WARN)
        self.assertGreater(dec.urgency, 0.9)

    def test_commitment_due_initiates(self) -> None:
        dec = self.policy.decide(
            DialogueContext(commitments_due=["test the camera"], addressee="vano", social_opportunity=0.6)
        )
        self.assertEqual(dec.act, DialogueAct.INITIATE)
        self.assertEqual(dec.topic, "test the camera")
        self.assertGreater(dec.expected_value, 0.8)

    def test_unresolved_thread_can_produce_follow_up(self) -> None:
        dec = self.policy.decide(
            DialogueContext(open_threads=["perception integration"], addressee="vano", social_opportunity=0.7, initiative_budget_available=True)
        )
        self.assertEqual(dec.act, DialogueAct.CONTINUE)
        self.assertEqual(dec.topic, "perception integration")
        self.assertEqual(dec.reason, "unfinished_thread")

    def test_comment_only_for_worth_speaking_events(self) -> None:
        ctx = DialogueContext(
            salient_events=[{"kind": "object.detected", "entity": "chair"}],  # anti-narration kind
            interruptibility=1.0, initiative_budget_available=True,
        )
        self.assertEqual(self.policy.decide(ctx).act, DialogueAct.SILENCE)
        ctx = DialogueContext(
            salient_events=[{"kind": "object.disappeared", "entity": "mug"}],
            interruptibility=1.0, initiative_budget_available=True,
        )
        dec = self.policy.decide(ctx)
        self.assertEqual(dec.act, DialogueAct.COMMENT)
        self.assertEqual(dec.topic, "mug")

    def test_proactive_decisions_carry_why_fields(self) -> None:
        dec = self.policy.decide(
            DialogueContext(commitments_due=["x"], addressee="vano")
        )
        for field in ("why_now", "why_this_person", "why_this_topic", "why_this_verbosity", "why_speak"):
            self.assertTrue(getattr(dec, field), f"{field} must be set")

    def test_snapshot_is_explainable(self) -> None:
        dec = self.policy.decide(DialogueContext(has_user_message=True, is_question=True))
        snap = dec.snapshot()
        self.assertEqual(snap["act"], "RESPOND")
        self.assertIn("why_speak", snap)
        self.assertIn("evidence", snap)


if __name__ == "__main__":
    unittest.main()
