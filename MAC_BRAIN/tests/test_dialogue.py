"""Tests for the portable dialogue engine and brain.compose_reply (rules 8/9/10).

These lock in the communication contract from docs/06-soul/07 §5 (no assistant
persona) and docs/06-soul/00 §6.5 (no unnecessary repetition): a forbidden
assistant phrase is never emitted, a repetitive reply is rejected, an addressee's
name is not over-used, and the brain — not the web server — owns the reply.
"""

from __future__ import annotations

import unittest

from MAC_BRAIN.dialogue import (
    DialogueEngine,
    _extract_topic,
    _is_forbidden,
    _is_near_repetitive,
    _is_repetitive,
    _reduce_name_repetition,
    followup_question,
    natural_fallback,
)
from MAC_BRAIN.runtime import MacBrain


class DialogueFilterTests(unittest.TestCase):
    def test_assistant_opener_is_forbidden(self):
        self.assertTrue(_is_forbidden("Hi, I am Novi, how can I help you today?"))
        self.assertTrue(_is_forbidden("As an AI, I have no feelings."))
        self.assertTrue(_is_forbidden("I'm your personal assistant."))

    def test_natural_reply_is_not_forbidden(self):
        self.assertFalse(_is_forbidden("I remember that alice moved the door."))
        self.assertFalse(_is_forbidden("oh, that's interesting — tell me more."))

    def test_repetitive_reply_detected(self):
        self.assertTrue(_is_repetitive("I remember that.", "I remember that."))
        self.assertFalse(_is_repetitive("I remember that.", ""))

    def test_name_repetition_reduced_to_one(self):
        out = _reduce_name_repetition("hi Vano yes Vano ok Vano", "Vano")
        self.assertEqual(out.lower().count("vano"), 1)
        self.assertIn("vano", out.lower())

    def test_engine_rejects_assistant_phrase(self):
        eng = DialogueEngine()
        r = eng.reply(system="s", user="u", llm_chat=lambda **k: "Hi I am Novi, how can I help you")
        self.assertIsNone(r["text"])
        self.assertTrue(r["rejected"])

    def test_engine_returns_clean_reply(self):
        eng = DialogueEngine()
        r = eng.reply(system="s", user="u", llm_chat=lambda **k: "I remember that alice moved the door.")
        self.assertEqual(r["text"], "I remember that alice moved the door.")
        self.assertFalse(r["rejected"])

    def test_engine_rejects_repetitive_reply(self):
        eng = DialogueEngine()
        r = eng.reply(system="s", user="u", llm_chat=lambda **k: "I remember that.", last_novi_text="I remember that.")
        self.assertIsNone(r["text"])
        self.assertTrue(r["rejected"])

    def test_engine_handles_silence(self):
        eng = DialogueEngine()
        r = eng.reply(system="s", user="u", llm_chat=lambda **k: "[silence]")
        self.assertIsNone(r["text"])
        self.assertTrue(r["silent"])

    def test_engine_handles_unreachable_transport(self):
        eng = DialogueEngine()
        r = eng.reply(system="s", user="u", llm_chat=lambda **k: None)
        self.assertIsNone(r["text"])

    def test_natural_fallback_is_never_robotic(self):
        for tone in ("curious", "warm", "calm", "cautious", "recovering"):
            line = natural_fallback({"tone": tone}, {}, cycle=0)
            self.assertTrue(line)
            self.assertFalse(_is_forbidden(line))

    def test_followup_question_is_in_context(self):
        q = followup_question("do you know anything about the garden lights?")
        self.assertIn("garden", q.lower())
        self.assertFalse(_is_forbidden(q))

    def test_followup_question_has_generic_fallback(self):
        q = followup_question("hmm")
        self.assertTrue(q)
        self.assertFalse(_is_forbidden(q))

    def test_extract_topic_picks_substantive_word(self):
        self.assertEqual(_extract_topic("tell me about the solar panels"), "panels")
        self.assertEqual(_extract_topic(""), "")

    def test_near_repetitive_across_recent_replies(self):
        # a short stutter that repeats a prior line's words should be rejected
        self.assertTrue(_is_near_repetitive("hello there", ["hello there", "what's up?"]))
        # a substantive restatement of a fact (user asked again) is allowed
        self.assertFalse(_is_near_repetitive("alice moved the door yesterday", ["alice moved the door"]))

    def test_engine_rejects_near_repeat_across_recent(self):
        eng = DialogueEngine()
        r = eng.reply(system="s", user="u", llm_chat=lambda **k: "hello there", recent_novi=["hello there", "what's up?"])
        self.assertIsNone(r["text"])
        self.assertTrue(r["rejected"])

    def test_engine_allows_restatement_of_fact(self):
        eng = DialogueEngine()
        r = eng.reply(system="s", user="u", llm_chat=lambda **k: "alice moved the door yesterday",
                        recent_novi=["alice moved the door"])
        self.assertEqual(r["text"], "alice moved the door yesterday")
        self.assertFalse(r["rejected"])


class ComposeReplyTests(unittest.TestCase):
    def _brain(self) -> MacBrain:
        return MacBrain()

    def test_no_transport_returns_none_for_deterministic_fallback(self):
        # CI / no-LLM path: the brain does not fabricate a reply.
        b = self._brain()
        r = b.compose_reply("hello", llm_chat=None)
        self.assertIsNone(r["text"])

    def test_uses_transport_for_clean_reply(self):
        b = self._brain()
        r = b.compose_reply("what do you remember?", llm_chat=lambda **k: "I remember that alice moved the door.")
        self.assertEqual(r["text"], "I remember that alice moved the door.")
        self.assertFalse(r["fallback"])

    def test_falls_back_naturally_when_reply_rejected(self):
        b = self._brain()
        r = b.compose_reply("hi", llm_chat=lambda **k: "Hi I am Novi, how can I help you")
        self.assertIsNotNone(r["text"])
        self.assertTrue(r["fallback"])
        self.assertFalse(_is_forbidden(r["text"]))
        # the forbidden phrase must never reach the user
        self.assertNotIn("how can i help", r["text"].lower())


if __name__ == "__main__":
    unittest.main()
