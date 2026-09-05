"""Live-LLM mechanism-gap fixes (plan-03 acceptance C-133/C-152/C-154).

Deterministic, socket-free, stdlib-only. Each class pins the exact mechanism
layer that leaked live, while staying green on the frozen deterministic replay:

- C-133 contradictory evidence: second-hand/pronoun fact-assertions must
  register as ``recent_claim`` candidates, and two competing claims must reach
  the model with a both-claims + latest directive;
- C-152 same-type pronoun rivals: "he" over two same-kind entities must stay
  ambiguous (never bind via mild recency), and the packet must not contradict
  the ASK_CLARIFICATION plan with "stay grounded on <anchor>";
- C-154 terse continuation: a bare wh-follow-up ("Why?") is a continuation of
  the active subject, and the model must be grounded on that subject.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from novi.brain.b2_perception import SpecialistPerception
from novi.brain.conversation.claim_registration import (
    has_anaphoric_subject,
    is_fact_assertion,
)
from novi.brain.conversation.conversation_state import (
    ContextPacket,
    ConversationAnchor,
    ConversationState,
    IntentResult,
    ReferentResult,
    ResponsePlan,
)
from novi.brain.conversation.intent import classify_intent
from novi.brain.conversation.llm_binding import render_conversation_block
from novi.brain.conversation.referent_resolution import resolve_referents
from novi.brain.conversation.response_planner import plan_response
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
          packet: ContextPacket | None = None,
          plan: ResponsePlan | None = None) -> dict:
    return {
        "intent": intent if intent is not None else
        IntentResult(intent="INFORMATION_REQUEST", dialogue_act="QUESTION",
                     confidence=0.8),
        "referents": referents if referents is not None else ReferentResult(),
        "packet": packet,
        "plan": plan if plan is not None else ResponsePlan(goal="ANSWER_DIRECTLY"),
    }


def _packet(**kw) -> ContextPacket:
    base = {
        "intent": IntentResult(intent="INFORMATION_REQUEST",
                               dialogue_act="QUESTION", confidence=0.8),
        "anchor": ConversationAnchor(),
    }
    base.update(kw)
    return ContextPacket(**base)


def _state(*, entities: list[str], anchor_entity: str = "",
           recent: list[str] | None = None) -> ConversationState:
    state = ConversationState()
    state.active_entities = list(entities)
    state.anchor = ConversationAnchor(active_entity=anchor_entity)
    for turn in recent or []:
        state.recent_turns.append({"user": turn, "novi": ""})
    return state


class ClaimRegistrationTests(unittest.TestCase):
    """C-133: fact assertions register as recent_claim candidates."""

    def test_fact_assertion_recognizes_second_hand_correction_and_plain(self) -> None:
        for text in (
            "The standup is at 9am.",
            "Hmm, I heard the standup is at 10am.",
            "Actually it is 330 miles.",
            "it's at 10am",
            "The Model Y has 500 miles of range.",
        ):
            with self.subTest(text=text):
                self.assertTrue(is_fact_assertion(text), text)

    def test_fact_assertion_rejects_non_fact_statements(self) -> None:
        for text in (
            "I have two dogs, Rex and Max.",
            "My sister lives in Porto.",
            "I like jazz music.",
            "Why?",
            "Rex is older.",
        ):
            with self.subTest(text=text):
                self.assertFalse(is_fact_assertion(text), text)

    def test_anaphoric_subject_detected(self) -> None:
        self.assertTrue(has_anaphoric_subject("Actually it is 330 miles."))
        self.assertTrue(has_anaphoric_subject("it's at 10am"))
        self.assertFalse(has_anaphoric_subject("The standup is at 9am."))

    def test_i_heard_registers_as_recent_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = _brain(tmp)
            try:
                brain.respond("The standup is at 9am.")
                brain.respond("Hmm, I heard the standup is at 10am.")
                reply = brain.respond("When is the standup?")
            finally:
                brain.stop()
        packet = (reply.get("grounding") or {}).get("packet") or {}
        claims = [str(m.get("content", ""))
                  for m in packet.get("relevant_memories") or []
                  if m.get("memory_type") == "recent_claim"]
        self.assertIn("The standup is at 9am.", claims)
        self.assertIn("Hmm, I heard the standup is at 10am.", claims)


class ConflictRenderTests(unittest.TestCase):
    """C-133: two competing claims reach the model with a latest directive."""

    def test_conflicting_claims_render_both_and_latest(self) -> None:
        packet = _packet(relevant_memories=[
            {"content": "The standup is at 9am.", "memory_type": "recent_claim"},
            {"content": "Hmm, I heard the standup is at 10am.",
             "memory_type": "recent_claim"},
        ])
        block = render_conversation_block(
            _conv(packet=packet, plan=ResponsePlan(goal="ANSWER_DIRECTLY")))
        self.assertIn("9am", block)
        self.assertIn("10am", block)
        self.assertIn("latest", block.lower())
        self.assertIn("conflict", block.lower())

    def test_single_claim_renders_no_conflict_directive(self) -> None:
        packet = _packet(relevant_memories=[
            {"content": "The standup is at 9am.", "memory_type": "recent_claim"},
        ])
        block = render_conversation_block(_conv(packet=packet))
        self.assertNotIn("conflict", block.lower())


class SameTypePronounRivalTests(unittest.TestCase):
    """C-152: "he" over Rex/Max stays ambiguous; plan asks naming both."""

    def test_he_over_two_dogs_is_ambiguous(self) -> None:
        state = _state(entities=["Max", "Rex"], anchor_entity="Rex",
                       recent=["I have two dogs, Rex and Max. Rex is older."])
        result = resolve_referents("Is he good with kids?", state)
        self.assertEqual(result.resolutions, {})
        self.assertEqual(result.ambiguous, ["he"])

    def test_planner_asks_clarification_naming_both(self) -> None:
        packet = _packet(
            active_entities=["Max", "Rex"],
            ambiguous_referents=["he"],
            anchor=ConversationAnchor(active_entity="Rex"),
        )
        plan = plan_response(packet)
        self.assertEqual(plan.goal, "ASK_CLARIFICATION")
        self.assertIn("Max", plan.must_include)
        self.assertIn("Rex", plan.must_include)

    def test_ambiguous_turn_does_not_force_stay_grounded_on_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = _brain(tmp)
            try:
                brain.respond("I have two dogs, Rex and Max. Rex is older.")
                reply = brain.respond("Is he good with kids?")
            finally:
                brain.stop()
        packet = (reply.get("grounding") or {}).get("packet") or {}
        requirements = [str(r) for r in packet.get("response_requirements") or []]
        joined = " ".join(requirements).lower()
        self.assertNotIn("stay grounded on rex", joined)
        self.assertIn("rex", joined)
        self.assertIn("max", joined)
        goal = ((reply.get("trace") or {}).get("conversation") or {})
        goal = (goal.get("response_goal") or {}).get("goal")
        self.assertEqual(goal, "ASK_CLARIFICATION")

    def test_single_referent_stays_unambiguous(self) -> None:
        # C-010/C-141: one plausible entity must not become a clarification.
        state = _state(entities=["Model Y"], anchor_entity="Model Y",
                       recent=["I was looking at the Model Y yesterday."])
        result = resolve_referents("Is it practical for a family?", state)
        self.assertEqual(result.resolutions.get("it"), "Model Y")
        self.assertEqual(result.ambiguous, [])


class TerseContinuationTests(unittest.TestCase):
    """C-154: bare wh-follow-up continues the active subject."""

    def test_bare_why_in_context_is_continuation_request(self) -> None:
        state = ConversationState()
        state.anchor.active_entity = "Model Y"
        result = classify_intent("Why?", state)
        self.assertEqual(result.intent, "EXPLANATION_REQUEST")
        self.assertEqual(result.dialogue_act, "QUESTION")

    def test_bare_why_without_context_stays_generic(self) -> None:
        result = classify_intent("Why?", ConversationState())
        self.assertEqual(result.intent, "INFORMATION_REQUEST")

    def test_render_grounds_followup_on_active_entity(self) -> None:
        referents = ReferentResult(resolutions={"(implicit subject)": "Model Y"})
        packet = _packet(anchor=ConversationAnchor(active_entity="Model Y"),
                         response_requirements=[
                             "continuing about Model Y — answer on this subject, "
                             "do not deflect"])
        plan = ResponsePlan(goal="ANSWER_DIRECTLY", must_include=["Model Y"])
        block = render_conversation_block(
            _conv(referents=referents, packet=packet, plan=plan))
        self.assertIn("Model Y", block)
        self.assertIn("continuing", block.lower())
        self.assertIn("deflect", block.lower())

    def test_why_turn_plans_answer_on_model_y(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = _brain(tmp)
            try:
                brain.respond("Tell me about the Model Y.")
                reply = brain.respond("Why?")
            finally:
                brain.stop()
        conv = (reply.get("trace") or {}).get("conversation") or {}
        intent = (conv.get("intent") or {}).get("intent")
        self.assertEqual(intent, "EXPLANATION_REQUEST")
        goal = (conv.get("response_goal") or {}).get("goal")
        self.assertEqual(goal, "ANSWER_DIRECTLY")
        self.assertIn("Model Y", (conv.get("response_goal") or {}).get("must_include", []))
        packet = (reply.get("grounding") or {}).get("packet") or {}
        requirements = " ".join(str(r) for r in
                                packet.get("response_requirements") or [])
        self.assertIn("Model Y", requirements)
        self.assertIn("continuing", requirements.lower())


if __name__ == "__main__":
    unittest.main()
