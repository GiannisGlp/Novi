"""Residual live-LLM failure classes (plan-03 acceptance C-032/C-072/C-150).

Deterministic, socket-free, stdlib-only. Each class pins the exact mechanism
layer that leaked live while staying green on the frozen deterministic replay:

- C-072 repetition: the model must SEE its own previous reply in the prompt
  (render_conversation_block), not just be told "don't repeat";
- C-032 irrelevant memory: a vehicle class noun ("the car") must never bind a
  place entity ("Porto"), and the grounded context must not force the place in;
- C-150 one-word slot answer: a CLARIFICATION_ANSWER closes the open slot and
  plans a direct (non-question) reply.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from novi.brain.b2_perception import SpecialistPerception
from novi.brain.conversation.conversation_state import (
    ConversationState,
    IntentResult,
    ReferentResult,
    ResponsePlan,
)
from novi.brain.conversation.intent import classify_intent
from novi.brain.conversation.llm_binding import render_conversation_block
from novi.brain.conversation.referent_resolution import resolve_referents
from novi.brain.conversation.response_critic import critique_draft
from novi.brain.conversation.response_planner import (
    plan_response,
    render_deterministic,
)
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.io import CameraFrame


class _Cam:
    def close(self) -> None:
        return None

    def read(self) -> CameraFrame:
        return CameraFrame(frame_id="f", captured_at="t", width=2,
                           height=2, payload=b"f", metadata={})


def _brain(tmp: str) -> MacBrain:
    brain = MacBrain(
        camera=_Cam(), perception=SpecialistPerception(),
        store_path=str(Path(tmp) / "m.db"),
        config=MacBrainConfig(curiosity_enabled=False,
                              initiative_enabled=False))
    brain.start()
    return brain


def _conv(*, intent: IntentResult | None = None,
          referents: ReferentResult | None = None,
          packet=None, plan: ResponsePlan | None = None,
          state: ConversationState | None = None) -> dict:
    return {
        "intent": intent if intent is not None else
        IntentResult(intent="INFORMATION_REQUEST", dialogue_act="QUESTION",
                     confidence=0.8),
        "referents": referents if referents is not None else ReferentResult(),
        "packet": packet,
        "plan": plan if plan is not None else ResponsePlan(goal="ANSWER_DIRECTLY"),
        "state": state,
    }


def _state(*, entities: list[str], anchor_entity: str = "",
           recent: list[str] | None = None) -> ConversationState:
    state = ConversationState()
    state.active_entities = list(entities)
    state.anchor.active_entity = anchor_entity
    for turn in recent or []:
        state.recent_turns.append({"user": turn, "novi": ""})
    return state


class RepetitionGroundingTests(unittest.TestCase):
    """C-072: the no-repeat directive must be grounded in the prior reply."""

    def test_render_block_includes_previous_reply(self) -> None:
        prior = "The Model Y launched in 2020 as Tesla's most affordable vehicle."
        conv = _conv(state=ConversationState(last_novi_claim=prior))
        block = render_conversation_block(conv)
        self.assertIn("launched in 2020", block)
        self.assertIn("repeat", block.lower())

    def test_render_block_without_previous_reply_still_has_directive(self) -> None:
        block = render_conversation_block(_conv())
        self.assertIn("repeat", block.lower())

    def test_stub_llm_repeating_verbatim_sees_previous_reply_and_triggers_repair(self) -> None:
        fixed = "The Model Y launched in 2020 as Tesla's most affordable vehicle."
        systems: list[str] = []

        def stub(*, system: str, user: str) -> str:
            systems.append(system)
            return fixed

        with tempfile.TemporaryDirectory() as tmp:
            brain = _brain(tmp)
            try:
                brain.respond("Tell me about the Model Y.", llm_chat=stub)
                systems.clear()
                resp2 = brain.respond("And more on the Model Y?", llm_chat=stub)
            finally:
                brain.stop()
        # The second turn's model prompt (initial + repair) shows the prior reply.
        self.assertTrue(systems)
        self.assertTrue(any(fixed in s for s in systems),
                        "model never saw its own previous reply")
        repair = (resp2.get("grounding") or {}).get("llm_repair") or {}
        self.assertTrue(repair.get("attempted"))


class MemoryRestraintTests(unittest.TestCase):
    """C-032: a car-interior question must not ground on a place entity."""

    def test_vehicle_class_noun_does_not_bind_place(self) -> None:
        state = _state(entities=["Porto"], anchor_entity="Porto",
                       recent=["My sister lives in Porto."])
        result = resolve_referents("What interior should I pick for the car?",
                                   state)
        self.assertNotIn("the car", result.resolutions)
        self.assertNotIn("the car", result.ambiguous)

    def test_vehicle_class_noun_still_binds_vehicle(self) -> None:
        state = _state(entities=["Model Y"], anchor_entity="Model Y")
        result = resolve_referents("How much does the car cost?", state)
        self.assertEqual(result.resolutions.get("the car"), "Model Y")

    def test_interior_question_does_not_ground_on_irrelevant_memories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = _brain(tmp)
            try:
                brain.respond("I prefer dark interiors.")
                brain.respond("My favorite pizza topping is mushrooms.")
                brain.respond("My sister lives in Porto.")
                conv = brain._conversation_turn(
                    "What interior should I pick for the car?",
                    addressee="", cycle=0, discourse_topic="", speaker="user")
            finally:
                brain.stop()
        packet = conv["packet"]
        plan = conv["plan"]
        block = render_conversation_block(conv)
        # "the car" must not resolve to the place entity, and the plan must
        # not force it into must_include.
        self.assertNotIn("Porto", [str(v) for v in packet.resolved_entities.values()])
        self.assertNotIn("Porto", plan.must_include)
        for forbidden in ("porto", "pizza", "mushroom", "sister"):
            self.assertNotIn(forbidden, block.lower())
        # The relevant preference still reaches the model.
        self.assertIn("dark", block.lower())


class SlotAnswerTests(unittest.TestCase):
    """C-150: a one-word slot answer closes the question, no re-ask."""

    def _packet(self, **kw):
        from novi.brain.conversation.conversation_state import (
            ContextPacket,
            ConversationAnchor,
        )
        base = {
            "current_turn": "The Tesla.",
            "intent": IntentResult(intent="CLARIFICATION",
                                   dialogue_act="CLARIFICATION_ANSWER",
                                   confidence=0.75),
            "resolved_entities": {"the tesla": "Tesla"},
            "anchor": ConversationAnchor(active_entity="Tesla"),
            "relevant_memories": [],
        }
        base.update(kw)
        return ContextPacket(**base)

    def test_slot_answer_plans_direct_non_question(self) -> None:
        packet = self._packet()
        plan = plan_response(packet)
        self.assertEqual(plan.goal, "SLOT_ANSWER")
        self.assertFalse(plan.question_allowed)
        text = render_deterministic(plan, packet)
        self.assertNotIn("?", text)

    def test_slot_answer_block_directs_answer_not_reask(self) -> None:
        packet = self._packet()
        plan = plan_response(packet)
        block = render_conversation_block(_conv(
            intent=packet.intent, referents=ReferentResult(
                resolutions={"the tesla": "Tesla"}), packet=packet, plan=plan))
        self.assertIn("SLOT_ANSWER", block)
        self.assertIn("do not ask", block.lower())

    def test_trailing_question_on_slot_answer_fails_critic(self) -> None:
        packet = self._packet()
        plan = plan_response(packet)
        verdict = critique_draft(
            draft="What drew you toward the Tesla over the BMW?",
            packet=packet, plan=plan)
        self.assertTrue(verdict.needs_repair)
        self.assertIn("clarification_safety", verdict.failed)

    def test_non_question_slot_answer_passes_critic(self) -> None:
        packet = self._packet()
        plan = plan_response(packet)
        verdict = critique_draft(draft="I'd pick the Tesla, honestly.",
                                 packet=packet, plan=plan)
        self.assertNotIn("clarification_safety", verdict.failed)


if __name__ == "__main__":
    unittest.main()
