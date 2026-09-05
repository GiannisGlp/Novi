"""Planner + critic tests (plan 03 Phases 7/9). Deterministic, socket-free."""

from __future__ import annotations

import unittest

from novi.brain.conversation import (
    ContextPacket,
    ConversationAnchor,
    IntentResult,
)
from novi.brain.conversation.response_critic import (
    critique_draft,
    repair,
    safety_fallback,
)
from novi.brain.conversation.response_planner import (
    plan_response,
    render_deterministic,
)


def _packet(**kw) -> ContextPacket:
    base: dict = {
        "current_turn": "hello",
        "intent": IntentResult(intent="GREETING", dialogue_act="GREETING",
                               confidence=0.95),
        "resolved_entities": {},
        "anchor": ConversationAnchor(),
        "relevant_memories": [],
    }
    base.update(kw)
    return ContextPacket(**base)


class PlanSelectionTests(unittest.TestCase):
    def test_greeting_never_asks(self) -> None:
        plan = plan_response(_packet())
        self.assertEqual(plan.goal, "ACKNOWLEDGE")
        self.assertFalse(plan.question_allowed)

    def test_low_confidence_ambiguity_asks_specifically(self) -> None:
        packet = _packet(
            intent=IntentResult(intent="RECOMMENDATION", dialogue_act="QUESTION",
                                confidence=0.4, needs_clarification=True),
            resolved_entities={"it-a": "Tesla", "it-b": "BMW"},
        )
        plan = plan_response(packet)
        self.assertEqual(plan.goal, "ASK_CLARIFICATION")
        self.assertTrue(plan.question_allowed)
        text = render_deterministic(plan, packet)
        self.assertIn("?", text)
        self.assertIn("Tesla", text)

    def test_answerable_memory_query_answers(self) -> None:
        packet = _packet(
            intent=IntentResult(intent="MEMORY_QUERY", dialogue_act="QUESTION",
                                confidence=0.9),
            relevant_memories=[{"content": "You prefer dark interiors.",
                                "fact_class": "PREFERENCE"}],
        )
        plan = plan_response(packet)
        self.assertEqual(plan.goal, "ANSWER_DIRECTLY")
        self.assertFalse(plan.question_allowed)
        self.assertIn("dark", render_deterministic(plan, packet))

    def test_unanswerable_admits_gap(self) -> None:
        packet = _packet(
            intent=IntentResult(intent="MEMORY_QUERY", dialogue_act="QUESTION",
                                confidence=0.9))
        plan = plan_response(packet)
        self.assertEqual(plan.goal, "ADMIT_UNCERTAINTY")
        text = render_deterministic(plan, packet)
        self.assertIn("don't", text.lower())

    def test_correction_never_defends(self) -> None:
        packet = _packet(
            intent=IntentResult(intent="CORRECTION", dialogue_act="CORRECTION",
                                confidence=0.9),
            resolved_entities={"model": "Model 3"})
        plan = plan_response(packet)
        self.assertEqual(plan.goal, "CORRECT")
        self.assertIn("defense of the prior interpretation",
                      plan.must_not_include)

    def test_entity_followup_without_facts_names_entity(self) -> None:
        packet = _packet(
            intent=IntentResult(intent="INFORMATION_REQUEST",
                                dialogue_act="QUESTION", confidence=0.8),
            resolved_entities={"range": "Tesla Model Y"})
        plan = plan_response(packet)
        text = render_deterministic(plan, packet)
        self.assertIn("Tesla Model Y", text)
        # Honest: no invented range figures.
        self.assertNotIn("330", text)


class CriticTests(unittest.TestCase):
    def test_repetition_fails(self) -> None:
        packet = _packet()
        plan = plan_response(packet)
        verdict = critique_draft(draft="Hey, I'm here.", packet=packet,
                                 plan=plan, last_novi="Hey, I'm here.")
        self.assertIn("non_repetition", verdict.failed)
        self.assertTrue(verdict.needs_repair)

    def test_near_verbatim_repeat_fails(self) -> None:
        # C-150/C-161: the model re-issues its own previous reply with light
        # rephrasing ("tech side" -> "tech and sustainability angle"). Word-set
        # overlap alone misses it; near-verbatim similarity must flag it.
        packet = _packet()
        plan = plan_response(packet)
        prior = ("I've been thinking about that comparison myself lately. "
                 "A friend just got a BMW and keeps talking about the driving "
                 "feel, while I've been eyeing a Tesla for the tech side. "
                 "What's drawing you toward one over the other?")
        draft = ("I've been thinking about that comparison myself lately. "
                 "A friend just got a BMW and keeps talking about the driving "
                 "feel, while I've been eyeing a Tesla for the tech and "
                 "sustainability angle. What's your take on which one fits "
                 "your style better?")
        verdict = critique_draft(draft=draft, packet=packet, plan=plan,
                                 last_novi=prior)
        self.assertIn("non_repetition", verdict.failed)
        self.assertTrue(verdict.needs_repair)

    def test_filler_only_fails_naturalness(self) -> None:
        packet = _packet()
        plan = plan_response(packet)
        verdict = critique_draft(draft="That sounds interesting", packet=packet,
                                 plan=plan)
        self.assertIn("naturalness", verdict.failed)

    def test_meta_talk_fails(self) -> None:
        packet = _packet()
        plan = plan_response(packet)
        verdict = critique_draft(
            draft="According to the conversation history, hello",
            packet=packet, plan=plan)
        self.assertIn("naturalness", verdict.failed)

    def test_capability_claim_without_world_fails(self) -> None:
        packet = _packet()
        plan = plan_response(packet)
        verdict = critique_draft(draft="I just saw a red car", packet=packet,
                                 plan=plan)
        self.assertIn("capability_honesty", verdict.failed)

    def test_good_draft_passes(self) -> None:
        packet = _packet(
            intent=IntentResult(intent="MEMORY_QUERY", dialogue_act="QUESTION",
                                confidence=0.9),
            relevant_memories=[{"content": "You prefer dark interiors."}])
        plan = plan_response(packet)
        verdict = critique_draft(draft="You prefer dark interiors.",
                                 packet=packet, plan=plan,
                                 last_novi="Hello!")
        self.assertFalse(verdict.needs_repair)

    def test_repair_and_fallback(self) -> None:
        packet = _packet()
        plan = plan_response(packet)
        verdict = critique_draft(draft="Hey, I'm here.", packet=packet,
                                 plan=plan, last_novi="Hey, I'm here.")
        fixed = repair(draft="Hey, I'm here.", packet=packet, plan=plan,
                       verdict=verdict, last_novi="Hey, I'm here.")
        self.assertTrue(fixed.strip())
        fallback = safety_fallback(packet=packet, reason="empty")
        self.assertTrue(fallback.strip())
        self.assertNotIn("330", fallback)

    def test_conflict_voicing_is_not_contradiction(self) -> None:
        # Naming the corrected error alongside its superseding value is
        # the designed conflict path — the critic must not punish it.
        packet = _packet(
            relevant_memories=[
                {"content": "The standup is at 9am.", "memory_type": "recent_claim"},
                {"content": "Correction: the standup is at 10am.",
                 "memory_type": "recent_claim"},
            ])
        packet.anchor.recent_correction = "Correction: the standup is at 10am."
        plan = plan_response(packet)
        draft = ("You mentioned both 'The standup is at 9am' and 'Correction: "
                 "the standup is at 10am' — going by the latest, "
                 "'Correction: the standup is at 10am'.")
        verdict = critique_draft(draft=draft, packet=packet, plan=plan)
        self.assertNotIn("contradiction_safety", verdict.failed)

    def test_lone_error_restatement_still_fails(self) -> None:
        # Parroting the correction utterance without comparative voicing
        # is still a contradiction failure.
        packet = _packet(
            relevant_memories=[
                {"content": "The standup is at 9am.", "memory_type": "recent_claim"},
                {"content": "Correction: the standup is at 10am.",
                 "memory_type": "recent_claim"},
            ])
        packet.anchor.recent_correction = "Correction: the standup is at 10am."
        plan = plan_response(packet)
        verdict = critique_draft(
            draft="Correction: the standup is at 10am. Noted.",
            packet=packet, plan=plan)
        self.assertIn("contradiction_safety", verdict.failed)

    def test_fallback_prefers_latest_over_stale(self) -> None:
        # safety_fallback must never resurrect the superseded value.
        packet = _packet(
            relevant_memories=[
                {"content": "The Model Y has 500 miles of range.",
                 "memory_type": "recent_claim"},
                {"content": "Actually it is 330 miles.",
                 "memory_type": "recent_claim"},
            ])
        fallback = safety_fallback(packet=packet, reason="grounding")
        self.assertIn("330", fallback)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
