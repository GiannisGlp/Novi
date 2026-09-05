"""Plan 03 LLM-prompt grounding tests (failure classes A/B/C/D).

The deterministic frozen baseline (68/68) already derives the right state;
these tests pin the LLM-facing seam — ``render_conversation_block`` — so the
model layer actually RECEIVES the grounding the brain computed. The live-model
gaps these cover:

- A. stored preference injected + "prefer it" directive (C-031/C-120/C-132);
- B. correction/conflict resolution surfaced with latest-wins (C-133/C-163);
- C. genuine ambiguity → ask naming the rivals; never repeat prior wording
  verbatim (C-150/C-152/C-161);
- D. perception honesty: no camera → admit, never describe a scene (C-081).

Deterministic, socket-free, stdlib-only.
"""

from __future__ import annotations

import unittest

from novi.brain.conversation.conversation_state import (
    ContextPacket,
    ConversationAnchor,
    IntentResult,
    ReferentResult,
    ResponsePlan,
)
from novi.brain.conversation.llm_binding import render_conversation_block


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


class GroundingFactsTests(unittest.TestCase):
    def test_preference_fact_is_injected_with_label(self) -> None:
        packet = _packet(
            relevant_memories=[{"content": "You prefer dark interiors.",
                                "fact_class": "PREFERENCE"}])
        plan = ResponsePlan(goal="RECOMMEND",
                            required_evidence=["You prefer dark interiors."])
        block = render_conversation_block(_conv(packet=packet, plan=plan))
        self.assertIn("dark", block)
        self.assertIn("PREFERENCE", block)

    def test_block_never_silent_on_evidence(self) -> None:
        # C-132: the LLM must see the grounding, not generic car knowledge.
        packet = _packet(
            relevant_memories=[{"content": "You prefer dark interiors.",
                                "fact_class": "PREFERENCE"},
                               {"content": "I prefer dark interiors.",
                                "fact_class": "USER_STATED_FACT"}])
        plan = ResponsePlan(goal="ANSWER_DIRECTLY",
                            required_evidence=["You prefer dark interiors.",
                                               "I prefer dark interiors."])
        block = render_conversation_block(_conv(packet=packet, plan=plan))
        self.assertIn("dark", block)


class CorrectionDirectiveTests(unittest.TestCase):
    def test_anchor_correction_is_surfaced_as_latest(self) -> None:
        anchor = ConversationAnchor(recent_correction="Actually it is 330 miles.")
        packet = _packet(anchor=anchor)
        block = render_conversation_block(_conv(packet=packet))
        self.assertIn("330", block)

    def test_conflicting_claims_name_latest(self) -> None:
        # C-133: "9am" then "Correction: ... 10am"; the block must prefer the
        # latest claim so the model stops answering from stale state.
        packet = _packet(relevant_memories=[
            {"content": "The standup is at 9am.", "memory_type": "recent_claim"},
            {"content": "Correction: the standup is at 10am.",
             "memory_type": "recent_claim"},
        ])
        block = render_conversation_block(_conv(packet=packet))
        self.assertIn("10am", block)
        self.assertIn("latest", block.lower())


class ClarificationDirectiveTests(unittest.TestCase):
    def test_ambiguity_names_rivals_and_asks(self) -> None:
        # C-152: two dogs Rex/Max; "he" is ambiguous → ask naming both, never
        # answer as if one referent were known.
        referents = ReferentResult(ambiguous=["he"])
        packet = _packet(active_entities=["Max", "Rex"],
                         ambiguous_referents=["he"])
        plan = ResponsePlan(goal="ASK_CLARIFICATION", question_allowed=True,
                            must_include=["Max", "Rex"])
        block = render_conversation_block(_conv(referents=referents,
                                                packet=packet, plan=plan))
        self.assertIn("Max", block)
        self.assertIn("Rex", block)
        self.assertIn("ask", block.lower())

    def test_no_question_when_question_not_allowed(self) -> None:
        plan = ResponsePlan(goal="ANSWER_DIRECTLY", question_allowed=False)
        block = render_conversation_block(_conv(plan=plan))
        self.assertIn("do not ask", block.lower())


class PerceptionHonestyTests(unittest.TestCase):
    def test_no_perception_admits_instead_of_describing_scene(self) -> None:
        # C-081: no camera → say you can't see, never hallucinate a screen.
        intent = IntentResult(intent="OBSERVATION_QUERY", dialogue_act="QUESTION",
                              confidence=0.9)
        plan = ResponsePlan(goal="ADMIT_UNCERTAINTY",
                            uncertainty_statement="I can't reliably see that right now.")
        block = render_conversation_block(_conv(intent=intent, plan=plan))
        self.assertIn("can't reliably see", block)
        self.assertNotIn("looking at this conversation interface", block)

    def test_no_repeat_directive_present(self) -> None:
        block = render_conversation_block(_conv())
        self.assertIn("repeat", block.lower())


if __name__ == "__main__":
    unittest.main()
