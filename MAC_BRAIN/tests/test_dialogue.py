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
    _is_clarification,
    _is_continuation,
    _is_emotional_statement,
    _is_forbidden,
    _is_greeting,
    _is_introduction,
    _is_joke_request,
    _is_meta_referential,
    _is_near_repetitive,
    _is_physical_action_request,
    _is_realtime_data_question,
    _is_recall_question,
    _is_thanks,
    _is_repetitive,
    _reduce_name_repetition,
    clarification_reply,
    continuation_reply,
    followup_question,
    greeting_reply,
    introduction_reply,
    joke_reply,
    natural_fallback,
    recall_reply,
)
from MAC_BRAIN.runtime import MacBrain


class DialogueFilterTests(unittest.TestCase):
    def test_assistant_opener_is_forbidden(self):
        self.assertTrue(_is_forbidden("Hi, I am Novi, how can I help you today?"))
        self.assertTrue(_is_forbidden("As an AI, I have no feelings."))
        self.assertTrue(_is_forbidden("I'm your personal assistant."))
        self.assertTrue(_is_forbidden("That's a great question."))
        self.assertTrue(_is_forbidden("I appreciate you sharing that."))
        self.assertTrue(_is_forbidden("Sounds like you're feeling a bit off."))
        self.assertTrue(_is_forbidden("As an AI model, I can help."))
        self.assertTrue(_is_forbidden("I've been processing some interesting data lately."))
        self.assertTrue(_is_forbidden("I'm just a program."))

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

    def test_greeting_detection(self):
        self.assertTrue(_is_greeting("Hello."))
        self.assertTrue(_is_greeting("hey there"))
        self.assertTrue(_is_greeting("good morning"))
        self.assertFalse(_is_greeting("what is your name"))
        self.assertFalse(_is_greeting(""))

    def test_greeting_reply_is_short_and_natural(self):
        for i in range(8):
            g = greeting_reply(cycle=i)
            self.assertTrue(g)
            self.assertLess(len(g), 60)
            self.assertFalse(_is_forbidden(g))

    def test_meta_referential_reply_rejected(self):
        self.assertTrue(_is_meta_referential("In our conversation, you greeted me and I responded warmly."))
        self.assertTrue(_is_meta_referential("I'm not sure what you mean. That's the main interaction we've had."))
        self.assertFalse(_is_meta_referential("I remember that alice moved the door."))

    def test_clarification_detection(self):
        self.assertTrue(_is_clarification("what system?"))
        self.assertTrue(_is_clarification("what do you mean?"))
        self.assertTrue(_is_clarification("come again?"))
        self.assertFalse(_is_clarification("what's up"))
        self.assertFalse(_is_clarification("what time is it"))

    def test_clarification_reply_is_natural(self):
        for i in range(6):
            c = clarification_reply(cycle=i)
            self.assertTrue(c)
            self.assertFalse(_is_forbidden(c))
            self.assertNotIn("what's on your mind", c.lower())

    def test_introduction_detection(self):
        self.assertTrue(_is_introduction("my name is alice"))
        self.assertTrue(_is_introduction("I'm Vano"))
        self.assertFalse(_is_introduction("hello"))
        self.assertFalse(_is_introduction(""))

    def test_introduction_not_mistaken_for_state(self):
        # "i'm <state>" is a status, not an introduction.
        for s in ["i'm tired today", "i'm not sure", "i'm sorry", "i'm here",
                  "i'm feeling tired", "i'm a bit cold"]:
            self.assertFalse(_is_introduction(s), s)

    def test_joke_detection(self):
        self.assertTrue(_is_joke_request("tell me a joke"))
        self.assertTrue(_is_joke_request("can you make me laugh?"))
        self.assertFalse(_is_joke_request("what time is it"))

    def test_joke_reply_is_clean(self):
        for i in range(6):
            j = joke_reply(cycle=i)
            self.assertTrue(j)
            self.assertFalse(_is_forbidden(j))

    def test_recall_detection(self):
        self.assertTrue(_is_recall_question("what do you remember about me?"))
        self.assertTrue(_is_recall_question("what do you know about alice?"))
        self.assertFalse(_is_recall_question("hello"))

    def test_recall_reply_with_and_without_known(self):
        self.assertIn("jazz", recall_reply(["I learned you like jazz"], "alice"))
        self.assertIn("don't have much", recall_reply([], "alice"))

    def test_continuation_detection(self):
        self.assertTrue(_is_continuation("why?"))
        self.assertTrue(_is_continuation("go on"))
        self.assertTrue(_is_continuation("tell me more"))
        self.assertTrue(_is_continuation("and then?"))
        self.assertFalse(_is_continuation("what time is it"))
        self.assertFalse(_is_continuation(""))

    def test_continuation_reply_is_engaged(self):
        for i in range(6):
            c = continuation_reply(cycle=i)
            self.assertTrue(c)
            self.assertFalse(_is_forbidden(c))

    def test_physical_action_detection(self):
        self.assertTrue(_is_physical_action_request("can you turn on the lights?"))
        self.assertTrue(_is_physical_action_request("open the door"))
        self.assertTrue(_is_physical_action_request("pick up the cup"))
        self.assertFalse(_is_physical_action_request("what's the time?"))
        self.assertFalse(_is_physical_action_request(""))

    def test_realtime_data_detection(self):
        for q in ["what's the latest price of bitcoin?", "how much is bitcoin right now?",
                  "what's the weather today?", "what's the temperature outside?"]:
            self.assertTrue(_is_realtime_data_question(q), q)
        for q in ["who won the world cup in 2022?", "what's the capital of france?", "do you like jazz?"]:
            self.assertFalse(_is_realtime_data_question(q), q)

    def test_emotional_statement_detection(self):
        for s in ["i've been feeling really down lately", "i feel sad", "i'm so tired",
                  "i had a rough day", "i'm stressed out", "i'm happy today"]:
            self.assertTrue(_is_emotional_statement(s), s)
        for s in ["what's the time?", "tell me a joke", "my name is alice"]:
            self.assertFalse(_is_emotional_statement(s), s)

    def test_thanks_detection(self):
        for s in ["thanks", "thank you", "thx!", "appreciate it"]:
            self.assertTrue(_is_thanks(s), s)
        self.assertFalse(_is_thanks("thank you for nothing"))
        self.assertFalse(_is_thanks(""))

    def test_engine_rejects_meta_referential_reply(self):
        eng = DialogueEngine()
        r = eng.reply(system="s", user="u", llm_chat=lambda **k: "In our conversation, you greeted me and I responded warmly.")
        self.assertIsNone(r["text"])
        self.assertTrue(r["rejected"])

    def test_engine_rejects_whats_on_your_mind(self):
        eng = DialogueEngine()
        r = eng.reply(system="s", user="u", llm_chat=lambda **k: "What's on your mind today?")
        self.assertIsNone(r["text"])
        self.assertTrue(r["rejected"])

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

    def test_character_clause_weaves_traits_and_values(self):
        b = self._brain()
        clause = b._character_clause({"traits": {"curious": 0.8, "warm": 0.7}, "values": {"kindness": "kindness", "honesty": "honesty"}})
        self.assertIn("curious", clause)
        self.assertIn("kindness", clause)

    def test_system_prompt_includes_character_and_reactions(self):
        b = self._brain()
        prompt = b._dialogue_system_prompt(b._chat_self_state(), {"tier": "friend", "expression": {"warmth": 0.8, "formality": "low", "playful": True}})
        self.assertIn("real, consistent character", prompt)
        self.assertIn("not like a neutral narrator", prompt)
        # Must not over-explain identity/embodiment unless asked.
        self.assertIn("Don't over-explain", prompt)

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
        r = b.compose_reply("tell me about yourself", llm_chat=lambda **k: "Hi I am Novi, how can I help you")
        self.assertIsNotNone(r["text"])
        self.assertTrue(r["fallback"])
        self.assertFalse(_is_forbidden(r["text"]))
        # the forbidden phrase must never reach the user
        self.assertNotIn("how can i help", r["text"].lower())

    def test_greeting_gets_short_warm_reply(self):
        b = self._brain()
        r = b.compose_reply("Hello.", llm_chat=lambda **kw: "ignored")
        self.assertIsNotNone(r["text"])
        self.assertFalse(r["fallback"])
        self.assertLess(len(r["text"]), 60, "greeting reply should be short")
        self.assertNotIn("what's on your mind", r["text"].lower())
        self.assertNotIn("system", r["text"].lower())

    def test_reply_carries_specific_reason(self):
        b = self._brain()
        r = b.compose_reply("do you remember what i like?", llm_chat=lambda **k: "you like jazz.")
        self.assertEqual(r["text"], "you like jazz.")
        self.assertIn("grounded", r["reason"].lower())

    def test_followup_carries_reason(self):
        b = self._brain()
        r = b.compose_reply("what about the garden lights?", llm_chat=lambda **k: "[silence]")
        self.assertIsNotNone(r["text"])
        self.assertTrue(r["fallback"])
        self.assertIn("follow-up", r["reason"].lower())

    def test_clarification_fallback_in_compose_reply(self):
        b = self._brain()
        r = b.compose_reply("what system?", llm_chat=lambda **k: "I'm not sure what you're referring to. In our conversation, you greeted me.")
        self.assertIsNotNone(r["text"])
        self.assertTrue(r["fallback"])
        self.assertNotIn("system yet", r["text"].lower())
        self.assertIn("clarif", r["reason"].lower())

    def test_introduction_in_compose_reply(self):
        b = self._brain()
        r = b.compose_reply("my name is alice", llm_chat=lambda **k: "ignored")
        self.assertIsNotNone(r["text"])
        self.assertIn("Alice", r["text"])
        self.assertNotIn("good answer", r["text"].lower())

    def test_joke_in_compose_reply(self):
        b = self._brain()
        r = b.compose_reply("tell me a joke", llm_chat=lambda **k: "ignored")
        self.assertIsNotNone(r["text"])
        self.assertNotIn("good answer", r["text"].lower())

    def test_recall_in_compose_reply(self):
        b = self._brain()
        b._learn_from_chat("i like jazz", person="alice")
        r = b.compose_reply("what do you remember about alice?", person="alice", llm_chat=lambda **k: None)
        self.assertIsNotNone(r["text"])
        self.assertIn("jazz", r["text"])

    def test_continuation_in_compose_reply(self):
        b = self._brain()
        r = b.compose_reply("go on", llm_chat=lambda **k: None)
        self.assertIsNotNone(r["text"])
        self.assertTrue(r["fallback"])
        self.assertNotEqual(r["text"].lower(), "hey, i'm here.")
        self.assertIn("continu", r["reason"].lower())

    def test_physical_action_is_honest_not_overclaimed(self):
        b = self._brain()
        r = b.compose_reply("can you turn on the lights?", llm_chat=lambda **k: None)
        self.assertIsNotNone(r["text"])
        self.assertFalse(b._has_physical_action_capability())
        self.assertIn("can't", r["text"].lower())
        self.assertNotIn("i'll flip", r["text"].lower())
        self.assertEqual(r["grounding"]["route"], "physical_honesty")

    def test_realtime_question_is_honest_not_invented(self):
        b = self._brain()
        r = b.compose_reply("what's the latest price of bitcoin?", llm_chat=lambda **k: None)
        self.assertIsNotNone(r["text"])
        self.assertNotIn("$", r["text"])
        self.assertIn("offline", r["text"].lower())
        self.assertEqual(r["grounding"]["route"], "realtime_honesty")

    def test_emotional_statement_gets_warm_reply_not_topic_followup(self):
        b = self._brain()
        r = b.compose_reply("i've been feeling really down lately", llm_chat=lambda **k: None)
        self.assertIsNotNone(r["text"])
        self.assertEqual(r["grounding"]["route"], "emotion")
        self.assertNotIn("good answer", r["text"].lower())
        # "i'm so stressed" must not be misread as an introduction.
        self.assertFalse(_is_introduction("i'm so stressed"))

    def test_thanks_gets_brief_natural_reply(self):
        b = self._brain()
        r = b.compose_reply("thanks", llm_chat=lambda **k: "I'm glad I could help.")
        self.assertIsNotNone(r["text"])
        self.assertEqual(r["grounding"]["route"], "thanks")
        self.assertNotIn("glad i could help", r["text"].lower())
        self.assertLess(len(r["text"]), 40)


class ExperienceLearningTests(unittest.TestCase):
    def _brain(self) -> MacBrain:
        return MacBrain()

    def test_learns_like_from_chat(self):
        b = self._brain()
        learned = b._learn_from_chat("I like jazz", person="alice")
        self.assertIn(("likes", "jazz"), learned)
        self.assertIn("I learned you like jazz", b._chat_experience("alice"))

    def test_learns_prefer_from_chat(self):
        b = self._brain()
        b._learn_from_chat("i'd prefer you call me alice", person="alice")
        self.assertTrue(any("prefer" in f for f in b._chat_experience("alice")))

    def test_learns_dislike_from_chat(self):
        b = self._brain()
        b._learn_from_chat("i don't like loud alarms", person="alice")
        self.assertTrue(any("don't like" in f for f in b._chat_experience("alice")))

    def test_experience_is_person_scoped(self):
        b = self._brain()
        b._learn_from_chat("i like jazz", person="alice")
        self.assertEqual(b._chat_experience("bob"), [])

    def test_experience_injected_into_reply_grounding(self):
        b = self._brain()
        b._learn_from_chat("i like jazz", person="alice")
        captured = {}
        def transport(**kw):
            captured["user"] = kw["user"]
            return "noted, jazz is nice."
        r = b.compose_reply("do you remember anything i like?", person="alice", llm_chat=transport, addressee_name="alice")
        self.assertIsNotNone(r["text"])
        self.assertIn("jazz", captured["user"])

    def test_reflection_lesson_surfaces_when_actions_ineffective(self):
        b = self._brain()
        for i in range(4):
            b.reflection.record(cycle=i, action="inspect", intent="learn", effective=False, note="no change")
        facts = b._chat_experience("")
        self.assertTrue(any("repeating the same move" in f for f in facts))

    def test_no_lesson_when_actions_effective(self):
        b = self._brain()
        for i in range(4):
            b.reflection.record(cycle=i, action="inspect", intent="learn", effective=True, note="worked")
        self.assertFalse(any("repeating the same move" in f for f in b._chat_experience("")))


if __name__ == "__main__":
    unittest.main()
