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
    _extract_self_name,
    _is_joke_request,
    _is_meta_referential,
    _is_near_repetitive,
    _is_physical_action_request,
    _is_perception_question,
    _is_realtime_data_question,
    _is_recall_question,
    _is_reminder_request,
    _is_thanks,
    _is_time_greeting,
    _is_acknowledgment,
    _is_bodily_need_question,
    _is_embodiment_question,
    _is_assurance_question,
    _is_repeat_question,
    _is_engagement_check,
    _is_memory_question,
    _is_talk_request,
    _is_debate_request,
    _is_farewell,
    _is_world_question,
    _is_identity_question,
    _is_praise,
    _is_capability_question,
    _is_remote_action_request,
    _is_reassurance_question,
    _is_future_question,
    _is_repetitive,
    _time_greeting_part,
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

    def test_identity_overexplanation_forbidden(self):
        # Answering a simple question shouldn't volunteer "I'm a transparent /
        # non-deceptive being" or "no hidden agenda".
        for s in ["Novi. I'm a transparent, non-deceptive being.",
                  "I'm a transparent AI being.",
                  "I don't have a hidden agenda or secret layers."]:
            self.assertTrue(_is_forbidden(s), s)
        # ...even with intervening words between the term and "being".
        self.assertTrue(_is_forbidden("I'm Novi — a transparent, non-deceptive embodied being."))
        # a natural reply is not rejected
        self.assertFalse(_is_forbidden("Novi — I live in this room."))

    def test_emotional_state_not_an_introduction(self):
        # "i'm nervous / worried / down" are states, not self-introductions.
        for s in ["i'm nervous", "i'm worried about the exam", "give me a pep talk, i'm nervous"]:
            self.assertFalse(_is_introduction(s), s)
        # real names are still introductions
        self.assertTrue(_is_introduction("i'm alex"))
        self.assertTrue(_is_introduction("my name is alice"))

    def test_departure_not_an_introduction(self):
        # "i'm leaving / going home / on my way" are actions, not self-introductions.
        for s in ["i'm leaving now", "i'm going home", "i'm on my way"]:
            self.assertFalse(_is_introduction(s), s)
        self.assertTrue(_is_introduction("i'm alex"))

    def test_embodiment_question_detection(self):
        for s in ["are you in the room with me right now?", "do you have a body?",
                  "where are you?", "can you stand?"]:
            self.assertTrue(_is_embodiment_question(s), s)
        self.assertFalse(_is_embodiment_question("what's the time?"))

    def test_future_question_not_topic(self):
        for s in ["what do you think will happen next week?", "what's next?",
                  "what will happen after that?", "what is going to happen?"]:
            self.assertTrue(_is_future_question(s), s)
        self.assertFalse(_is_future_question("what's the time?"))
        self.assertFalse(_is_future_question("what happened yesterday?"))

    def test_system_prompt_forbids_physical_life_fabrication(self):
        # Novi has no body — the prompt must forbid inventing errands/cafes/meals.
        b = MacBrain()
        sp = b._dialogue_system_prompt({}, {})
        self.assertIn("You have no body", sp)
        self.assertIn("Never invent past physical experiences", sp)

    def test_debate_request_detection(self):
        # "argue that X is better" is a debate prompt, not a request to deflect.
        for s in ["argue that cats are better than dogs", "defend pineapple on pizza", "convince me that reading is good"]:
            self.assertTrue(_is_debate_request(s), s)
        self.assertFalse(_is_debate_request("tell me about your day"))

    def test_talk_request_not_topic(self):
        # "just talk to me" is a request to converse, not a topic ("talk").
        for s in ["just talk to me about anything", "let's chat", "chat with me", "talk to me"]:
            self.assertTrue(_is_talk_request(s), s)
        self.assertFalse(_is_talk_request("tell me about cats"))
        self.assertFalse(_is_talk_request("what's the time?"))

    def test_memory_question_detection(self):
        # "will you forget me?" is relational, not a topic or implementation-speak.
        for s in ["will you forget me?", "are you going to forget me?", "do you remember me?"]:
            self.assertTrue(_is_memory_question(s), s)
        self.assertFalse(_is_memory_question("what's the time?"))

    def test_memory_impl_leak_is_forbidden(self):
        for s in ["my memory is built into how I process things.",
                  "I don't have a separate 'forget' button or a temporary buffer.",
                  "nothing is erased between sessions.",
                  "it shapes my responses."]:
            self.assertTrue(_is_forbidden(s), s)

    def test_engagement_check_detection(self):
        # "are you there / can you hear me" deserve a warm presence reply, not a topic.
        for s in ["are you there?", "can you hear me?", "are you listening?", "are you still with me?", "do you understand me?"]:
            self.assertTrue(_is_engagement_check(s), s)
        self.assertFalse(_is_engagement_check("what's the time?"))

    def test_bodily_need_question_detection(self):
        # Novi has no body, so eating/sleeping/dreaming questions must be honest.
        for s in ["what did you have for breakfast?", "did you sleep well last night?",
                  "are you hungry?", "do you dream?", "do you like coffee?",
                  "what's your favorite food?", "can you cook?"]:
            self.assertTrue(_is_bodily_need_question(s), s)
        self.assertFalse(_is_bodily_need_question("what's your favorite movie?"))
        self.assertFalse(_is_bodily_need_question("do you like music?"))
        self.assertFalse(_is_bodily_need_question("what do you think of the weather?"))

    def test_assurance_question_not_topic(self):
        # "Can you keep a secret?" is social, not a topic to answer dryly.
        for s in ["can you keep a secret?", "promise you won't tell?", "can i trust you?"]:
            self.assertTrue(_is_assurance_question(s), s)
        self.assertFalse(_is_assurance_question("what's the time?"))

    def test_repeat_question_not_topic(self):
        # "what did you just say?" is about the prior turn, not a topic.
        for s in ["what did you just say?", "can you repeat that?", "say it again please"]:
            self.assertTrue(_is_repeat_question(s), s)
        self.assertFalse(_is_repeat_question("what's the time?"))

    def test_implementation_leak_is_forbidden(self):
        # Novi must never mention its system prompt / blank message.
        for s in ["my last message was blank, just the system prompt.",
                  "due to the context window limit, I can't see earlier turns."]:
            self.assertTrue(_is_forbidden(s), s)

    def test_guardrails_do_not_reject_legitimate_replies(self):
        # Replies that legitimately mention conversation/remembering must pass.
        for s in ["I'd love to keep this conversation going.",
                  "We talked about your garden last week, how is it now?",
                  "You mentioned alice earlier — how is she?",
                  "I remember what we discussed about the lights."]:
            self.assertFalse(_is_meta_referential(s), s)
            self.assertFalse(_is_forbidden(s), s)

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

    def test_time_greeting_detection(self):
        for s in ["good morning", "morning!", "good afternoon", "good evening", "good night"]:
            self.assertTrue(_is_time_greeting(s), s)
        self.assertFalse(_is_time_greeting("hello"))
        self.assertFalse(_is_time_greeting("what's up"))
        self.assertEqual(_time_greeting_part("good morning"), "morning")

    def test_perception_question_detection(self):
        for s in ["can you hear me?", "can you see me?", "are you listening?", "did you see that?"]:
            self.assertTrue(_is_perception_question(s), s)
        self.assertFalse(_is_perception_question("what's the time?"))

    def test_reminder_detection(self):
        for s in ["remind me to water the plants", "don't forget to call my mom",
                  "set me a reminder for tomorrow"]:
            self.assertTrue(_is_reminder_request(s), s)
        self.assertFalse(_is_reminder_request("what's the time?"))

    def test_acknowledgment_detection(self):
        for s in ["okay", "sure", "got it", "sounds good", "yeah", "cool", "alright", "yes"]:
            self.assertTrue(_is_acknowledgment(s), s)
        self.assertFalse(_is_acknowledgment("what's the time?"))
        self.assertFalse(_is_acknowledgment("hello"))
        # a longer message is not a bare acknowledgment
        self.assertFalse(_is_acknowledgment("okay so tell me about the garden"))

    def test_single_short_word_not_a_topic(self):
        # "yes"/"hm"/"no" must not become "no good answer on <word>".
        for s in ["yes", "hm", "no", "k"]:
            self.assertEqual(_extract_topic(s), "", s)
        self.assertEqual(_extract_topic("what about the weather?"), "weather")

    def test_slang_acknowledgment_detection(self):
        # Casual agreement markers are acknowledgments, not literal topics or bets.
        for s in ["bet", "facts", "word", "no cap", "fr", "for real", "preach"]:
            self.assertTrue(_is_acknowledgment(s), s)

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
        self.assertNotIn("good answer on", q.lower())

    def test_followup_question_no_awkward_topic_phrasing(self):
        # The catch-all must not say "I don't have a good answer on <word>".
        for s in ["what is love?", "i need advice", "help me", "are you happy?"]:
            q = followup_question(s)
            self.assertNotIn("good answer on", q.lower(), s)
            self.assertNotIn("no good answer", q.lower(), s)
            self.assertFalse(_is_forbidden(q), s)

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

    def test_gerund_phrase_not_intro(self):
        # "i'm failing at everything" / "i'm working on a project" are states/
        # verb phrases, not self-introductions.
        for s in ["i feel like i'm failing at everything", "i'm struggling with work",
                  "i'm trying to sleep", "i'm working on a project"]:
            self.assertFalse(_is_introduction(s), s)
            self.assertEqual(_extract_self_name(s), "", s)
        # Multi-word real names still recognized.
        self.assertEqual(_extract_self_name("i'm John Smith"), "John Smith")

    def test_state_word_not_intro(self):
        # "i'm starving/tired/coming" are states, not self-introductions.
        for s in ["i'm starving", "i'm coming", "i'm just kidding", "i'm tired"]:
            self.assertFalse(_is_introduction(s), s)
            self.assertEqual(_extract_self_name(s), "", s)
        # Real names are still recognized.
        self.assertTrue(_is_introduction("i'm novi"))
        self.assertEqual(_extract_self_name("i'm john"), "john")

    def test_reassurance_question_detection(self):
        # "are you mad at me? / do you hate me?" get warm reassurance, never a
        # topic follow-up.
        for s in ["are you mad at me?", "are you upset with me?", "are you angry at me?",
                  "do you hate me?", "are you bored with me?", "did i upset you?"]:
            self.assertTrue(_is_reassurance_question(s), s)
        self.assertFalse(_is_reassurance_question("what's the time?"))

    def test_empathy_statement_detection(self):
        # "my head hurts / i can't sleep / i miss my dog / today was rough" are
        # distress statements that get empathy, not a topic follow-up.
        for s in ["my head hurts", "i can't sleep", "i miss my dog",
                  "today was rough", "long day at work", "i miss you"]:
            self.assertTrue(_is_emotional_statement(s), s)
        self.assertFalse(_is_emotional_statement("it's a beautiful day"))
        self.assertFalse(_is_emotional_statement("what's the time?"))

    def test_remote_action_request_detection(self):
        # "send an email / book a flight / call my mom / order a pizza" are
        # actions Novi can't do — answer honestly, never "no good answer".
        for s in ["send an email to my boss", "book me a flight", "book the tickets",
                  "call my mom", "order a pizza", "send a text message",
                  "buy me those shoes online"]:
            self.assertTrue(_is_remote_action_request(s), s)
        self.assertFalse(_is_remote_action_request("what's the time?"))

    def test_physical_contact_request_detection(self):
        # "give me a hug / hand me the book / carry me" are physical requests
        # that must answer honestly, not "no good answer on give".
        for s in ["give me a hug", "hug me", "hold my hand", "hand me the book",
                  "carry me", "high five"]:
            self.assertTrue(_is_physical_action_request(s), s)
        self.assertFalse(_is_physical_action_request("what's the time?"))

    def test_praise_and_capability_detection(self):
        # "you're amazing / i love you" get a warm reply, not "no good answer".
        for s in ["you're amazing", "i love you", "you're my favorite", "you're the best"]:
            self.assertTrue(_is_praise(s), s)
        self.assertFalse(_is_praise("what's the time?"))
        # "can you sing/dance?" are capability questions, answered honestly.
        for s in ["can you sing?", "dance for me", "are you smart?"]:
            self.assertTrue(_is_capability_question(s), s)
        self.assertFalse(_is_capability_question("what's the time?"))

    def test_identity_question_detection(self):
        # "are you a robot? / do you have hands? / who made you?" are identity
        # questions that must answer honestly, not "no good answer on <word>".
        for s in ["are you a robot?", "do you have hands?", "when were you born?",
                  "who made you?", "where do you live?", "are you real?",
                  "what are you exactly?", "can you fall in love?"]:
            self.assertTrue(_is_identity_question(s), s)
        self.assertFalse(_is_identity_question("what's the time?"))

    def test_farewell_detection(self):
        # "bye / i'm leaving now / see you later" are farewells, not intros/topics.
        for s in ["goodbye", "bye", "i'm leaving now", "i'm going home", "see you later"]:
            self.assertTrue(_is_farewell(s), s)
        self.assertFalse(_is_farewell("hello"))
        self.assertFalse(_is_farewell("what's the time?"))

    def test_world_question_detection(self):
        # "what's going on in the world?" is a news question, not a topic.
        for s in ["what's going on in the world?", "what's the news today?"]:
            self.assertTrue(_is_world_question(s), s)
        self.assertFalse(_is_world_question("what's the time?"))

    def test_broad_naturalness_smoke_no_awkward_fallbacks(self):
        # Representative inputs across 37 rounds must never produce a "no good
        # answer on <word>" fallback or a forbidden program-speak phrase.
        b = self._brain()
        cases = [
            "hello", "what system?", "i'm nervous", "can you hear me?",
            "remind me to water the plants", "what will happen next week?",
            "can you keep a secret?", "i'm leaving now", "what did you just say?",
            "are you going to forget me?", "what's going on in the world?",
            "just talk to me about anything", "argue that cats are better than dogs",
            "what did you have for breakfast?", "yes", "do you like coffee?",
            "are you a robot?", "do you have hands?", "when were you born?",
        ]
        for u in cases:
            r = b.compose_reply(u, llm_chat=lambda **k: None)
            t = (r.get("text") or "").lower()
            self.assertNotIn("no good answer", t, u)
            self.assertNotIn("good answer on", t, u)
            self.assertFalse(_is_forbidden(t), u)



    def test_system_prompt_includes_character_and_reactions(self):
        b = self._brain()
        prompt = b._dialogue_system_prompt(b._chat_self_state(), {"tier": "friend", "expression": {"warmth": 0.8, "formality": "low", "playful": True}})
        self.assertIn("real, consistent character", prompt)
        self.assertIn("not like a neutral narrator", prompt)
        # Must not over-explain identity/embodiment unless asked.
        self.assertIn("Don't over-explain", prompt)
        # Natural conversations ask one thing at a time.
        self.assertIn("at most one question", prompt)

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

    def test_time_greeting_routes_to_matching_reply(self):
        b = self._brain()
        r = b.compose_reply("good night", llm_chat=lambda **k: "ignored")
        self.assertIsNotNone(r["text"])
        self.assertEqual(r["grounding"]["route"], "time_greeting")
        self.assertIn("night", r["text"].lower())

    def test_perception_question_gets_honest_reply_not_topic_followup(self):
        b = self._brain()
        # "can you hear me?" is a presence/engagement check — warm and honest.
        r = b.compose_reply("can you hear me?", llm_chat=lambda **k: None)
        self.assertIsNotNone(r["text"])
        self.assertEqual(r["grounding"]["route"], "engagement")
        self.assertIn("hear", r["text"].lower())
        self.assertNotIn("good answer", r["text"].lower())
        # a vision question answered honestly per availability
        rv = b.compose_reply("did you see that?", llm_chat=lambda **k: None)
        self.assertNotIn("good answer", rv["text"].lower())

    def test_reminder_is_honest_and_persisted(self):
        b = self._brain()
        r = b.compose_reply("remind me to water the plants", llm_chat=lambda **k: None)
        self.assertIsNotNone(r["text"])
        self.assertEqual(r["grounding"]["route"], "reminder_honesty")
        self.assertNotIn("water the plants", r["text"])  # no false timed promise
        # persists so it can be recalled later
        b._learn_from_chat("remind me to water the plants", person="alice")
        self.assertTrue(any("water the plants" in e for e in b._chat_experience("alice")))

    def test_acknowledgment_not_topic_or_introduction(self):
        b = self._brain()
        for u in ["got it", "sure", "yeah", "okay"]:
            r = b.compose_reply(u, llm_chat=lambda **k: "ignored")
            self.assertIsNotNone(r["text"])
            self.assertEqual(r["grounding"]["route"], "acknowledgment", u)
            # must not be the "no good answer on X" topic fallback or an intro
            self.assertNotIn("good answer", r["text"].lower())
            self.assertNotIn("i'm novi", r["text"].lower())

    def test_homework_not_flagged_as_physical_action(self):
        # A mental/intellectual request must not trigger the physical-action honesty
        # clause; the base caps clause should not volunteer "physical actions
        # unavailable" for non-physical requests.
        from MAC_BRAIN.runtime import MacBrain
        b = MacBrain()
        st = b._chat_self_state()
        rel = {"tier": "friend", "expression": {"warmth": 0.8, "formality": "low", "playful": True}}
        prompt = b._dialogue_system_prompt(st, rel, capabilities=b.self_model().get("capabilities"))
        self.assertNotIn("degraded or unavailable", prompt)


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
