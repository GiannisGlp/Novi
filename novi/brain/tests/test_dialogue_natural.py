"""Phase 1 dialogue-naturalness tests.

1. Meta-framing ("Okay, let me unpack this…") is stripped from LLM replies.
2. Deterministic social-move banks only fire WITHOUT an LLM transport —
   with ollama up, replies are LLM-composed (cognition/memory/context).
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from novi.brain.chat import ChatMixin
from novi.brain.dialogue import DialogueEngine, _is_meta_referential, _strip_meta_framing


class MetaFramingTests(unittest.TestCase):
    def test_leading_meta_framing_is_stripped(self) -> None:
        text = "Okay, let me unpack this carefully. The cup moved earlier — it's on the counter now."
        self.assertEqual(_strip_meta_framing(text), "The cup moved earlier — it's on the counter now.")

    def test_multiple_meta_sentences_stripped(self) -> None:
        text = "Alright, let me think. The user just asked about the cup. It's on the counter now."
        self.assertEqual(_strip_meta_framing(text), "It's on the counter now.")

    def test_plain_reply_untouched(self) -> None:
        text = "I saw the cup move — it's on the counter now."
        self.assertEqual(_strip_meta_framing(text), text)

    def test_fully_meta_reply_becomes_empty(self) -> None:
        text = "Okay, let me go through this step by step. The user asked what I remember."
        self.assertEqual(_strip_meta_framing(text), "")

    def test_qwen3_narration_style_stripped(self) -> None:
        text = "First, looking at the conversation history. The user has been saying 'do you know me?' earlier. I remember you — you're Vano."
        self.assertEqual(_strip_meta_framing(text), "I remember you — you're Vano.")

    def test_meta_referential_rejects_leaked_phrasing(self) -> None:
        for bad in ("Let me unpack this for you.", "The user just asked about the cup.",
                    "We are given the conversation history.", "I'll figure out how to respond.",
                    "The user has been saying that all day.", "Novi has been responding with canned lines.",
                    "Looking at the conversation history, the topic was the cup.", "I was mid-sentence in the previous reply."):
            self.assertTrue(_is_meta_referential(bad), bad)

    def test_engine_strips_meta_framing_from_reply(self) -> None:
        engine = DialogueEngine()

        def stub_llm(system: str, user: str) -> str:  # noqa: ARG001
            return "Okay, let me break this down. I remember you like jazz — so what's playing?"

        out = engine.reply(system="s", user="u", llm_chat=stub_llm)
        self.assertEqual(out["text"], "I remember you like jazz — so what's playing?")
        self.assertFalse(out["rejected"])


class _StubBrain(ChatMixin):
    """Minimal ChatMixin with enough state for the LLM-primary compose path."""

    def __init__(self, llm_text: str) -> None:
        self._cycle = 7
        self.skills = None
        self.narrator = None
        self._last_context_package = None
        self.memory = SimpleNamespace(active_rows=lambda: [])
        self.governance = SimpleNamespace(store=None)
        self._emit = lambda *a, **k: None
        self.soul = SimpleNamespace(
            identity=SimpleNamespace(name="Novi", persona="a warm presence", origin=""),
            personality=SimpleNamespace(traits={"warmth": 0.7}, values={"honesty": True}),
            affect=SimpleNamespace(dimensions={"valence": 0.5}),
            tone=lambda ctx: {"tone": "warm"},
            learn_from_interaction=lambda *a, **k: None,
        )
        self.communication_decision = SimpleNamespace(
            should_speak=lambda **k: (True, ""), fatigue_level=0.2, interaction_count=3,
            record_interaction=lambda: None,
        )
        self.relationships = SimpleNamespace(category_for=lambda p: SimpleNamespace(value="known"))
        self.identity = SimpleNamespace(identity_for=lambda p: None)
        self.unified_world = SimpleNamespace(entities=[])
        self.dialogue = SimpleNamespace(reply=lambda **k: {"text": llm_text, "rejected": False})
        # stub out the state-assembly helpers (unit scope: gating, not content)
        self._chat_surroundings = lambda: {"space": "the room"}
        self._chat_knowledge = lambda t: ""
        self._chat_known_persons = lambda: []
        self._chat_experience = lambda p: []
        self._chat_self_state = self._real_self_state
        self.self_model = lambda: {"capabilities": {}}
        self._character_clause = lambda self_state: "you're warm and honest"
        self._matched_instruction_guidance = lambda *a, **k: ("", [])
        self._humanizer_system_block = lambda: ""
        self._vocabulary_scope_for = lambda p: {"warning": None}
        self.note_user_message = lambda t: {"resolved_topic": ""}

    def _real_self_state(self) -> dict:
        from novi.brain.chat import ChatMixin

        return ChatMixin._chat_self_state(self)


class LLMPrimaryComposeTests(unittest.TestCase):
    def test_check_in_reaches_llm_when_transport_available(self) -> None:
        brain = _StubBrain(llm_text="I'm doing alright — the room's been quiet. You?")
        out = brain.compose_reply("whats up?", llm_chat=lambda **k: "unused")
        self.assertEqual(out["text"], "I'm doing alright — the room's been quiet. You?")

    def test_engagement_check_reaches_llm_when_transport_available(self) -> None:
        brain = _StubBrain(llm_text="Right here. What's on your mind?")
        out = brain.compose_reply("are you there?", llm_chat=lambda **k: "unused")
        self.assertEqual(out["text"], "Right here. What's on your mind?")

    def test_det_banks_still_fire_without_transport(self) -> None:
        brain = _StubBrain(llm_text="unused")
        brain._cycle = 3
        det = brain._det_social_reply("whats up?")
        assert det is not None
        self.assertTrue(det["fallback"])

    def test_greeting_stays_deterministic_even_with_transport(self) -> None:
        brain = _StubBrain(llm_text="unused")
        out = brain.compose_reply("hello", llm_chat=lambda **k: "unused")
        self.assertEqual(out["grounding"]["route"], "greeting")


if __name__ == "__main__":
    unittest.main()
