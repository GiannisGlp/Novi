"""Phase 2 contract tests: deterministic intent + dialogue-act classification."""

from __future__ import annotations

import unittest

from novi.brain.conversation.conversation_state import ConversationState
from novi.brain.conversation.intent import classify_intent


def classify(text: str, **kwargs) -> object:
    state = ConversationState(**kwargs) if kwargs else ConversationState()
    return classify_intent(text, state)


class TaxonomyCoverageTests(unittest.TestCase):
    CASES = {
        "What is the range of the Model Y?": "INFORMATION_REQUEST",
        "Why is the sky blue?": "EXPLANATION_REQUEST",
        "What do you think of Tesla?": "OPINION_REQUEST",
        "Compare the Model 3 and the Model Y.": "COMPARISON",
        "Recommend a good EV for commuting.": "RECOMMENDATION",
        "Do you remember my trip?": "MEMORY_QUERY",
        "Remember that my birthday is June 1st.": "MEMORY_UPDATE",
        "No, I meant the Model Y, not the Model 3.": "CORRECTION",
        "Yes, exactly.": "CONFIRMATION",
        "Nope, not really.": "DISCONFIRMATION",
        "What do you mean by range?": "CLARIFICATION",
        "I feel awful today, cheer me up.": "EMOTIONAL_SUPPORT",
        "Is everything going to be ok?": "REASSURANCE",
        "Hello!": "GREETING",
        "Goodbye, talk later!": "FAREWELL",
        "How are you today?": "SOCIAL_CHAT",
        "Tell me a joke.": "JOKE/HUMOR",
        "I've been thinking about my career a lot.": "REFLECTION",
        "Help me plan my road trip itinerary.": "PLANNING",
        "Remind me to charge the car at 9pm.": "TASK_REQUEST",
        "What do you see in front of you?": "OBSERVATION_QUERY",
        "Did you hear that sound?": "PERCEPTION_QUERY",
        "Who are you?": "IDENTITY_QUERY",
        "What can you do?": "CAPABILITY_QUERY",
        "Thanks, that helped a lot!": "FEEDBACK",
        "I disagree, that's not how it works.": "DISAGREEMENT",
        "I agree, you're right.": "AGREEMENT",
        "Let's talk about something else entirely.": "TOPIC_CHANGE",
    }

    def test_every_taxonomy_intent_hit(self) -> None:
        for text, expected in self.CASES.items():
            with self.subTest(text=text):
                result = classify(text)
                self.assertEqual(result.intent, expected)

    def test_intent_set_matches_plan_taxonomy(self) -> None:
        from novi.brain.conversation.intent import _candidate_rules  # noqa: PLC2701
        del _candidate_rules  # contract is behavioural, not structural
        plan_intents = {
            "INFORMATION_REQUEST", "EXPLANATION_REQUEST", "OPINION_REQUEST",
            "COMPARISON", "RECOMMENDATION", "MEMORY_QUERY", "MEMORY_UPDATE",
            "CORRECTION", "CONFIRMATION", "DISCONFIRMATION", "FOLLOW_UP",
            "CLARIFICATION", "EMOTIONAL_SUPPORT", "REASSURANCE", "GREETING",
            "FAREWELL", "SOCIAL_CHAT", "JOKE/HUMOR", "REFLECTION",
            "PLANNING", "TASK_REQUEST", "OBSERVATION_QUERY",
            "PERCEPTION_QUERY", "IDENTITY_QUERY", "CAPABILITY_QUERY",
            "FEEDBACK", "DISAGREEMENT", "AGREEMENT", "TOPIC_CHANGE",
        }
        covered = set(self.CASES.values()) | {
            classify("What about the range?", topic="Model Y").intent}
        self.assertEqual(classify("What about the range?",
                                  topic="Model Y").intent, "FOLLOW_UP")
        self.assertTrue(plan_intents <= covered)


class DialogueActSeparationTests(unittest.TestCase):
    """Plan Step 2.2: the same surface form can carry different acts."""

    def test_memory_query_is_question(self) -> None:
        result = classify("You remember my trip?")
        self.assertEqual(result.intent, "MEMORY_QUERY")
        self.assertEqual(result.dialogue_act, "QUESTION")

    def test_memory_update_is_assertion(self) -> None:
        result = classify("I told you yesterday that I hate flying.")
        self.assertEqual(result.dialogue_act, "ASSERTION")
        self.assertIn(result.intent, {"MEMORY_UPDATE", "CORRECTION"})

    def test_empathic_trigger(self) -> None:
        result = classify("That sounds awful.")
        self.assertEqual(result.intent, "EMOTIONAL_SUPPORT")
        self.assertEqual(result.dialogue_act, "EMPATHIC_TRIGGER")

    def test_correction_act(self) -> None:
        result = classify("Actually, I wanted the AWD one.")
        self.assertEqual(result.intent, "CORRECTION")
        self.assertEqual(result.dialogue_act, "CORRECTION")

    def test_greeting_act(self) -> None:
        result = classify("Hi!")
        self.assertEqual((result.intent, result.dialogue_act),
                         ("GREETING", "GREETING"))

    def test_clarification_answer_uses_state(self) -> None:
        state = ConversationState(topic="cars")
        state.record_turn(user_text="hi", question_asked="What model?")
        result = classify_intent("The Model Y.", state)
        self.assertEqual(result.intent, "CLARIFICATION")
        self.assertEqual(result.dialogue_act, "CLARIFICATION_ANSWER")

    def test_request_act(self) -> None:
        result = classify("Recommend a good EV for commuting.")
        self.assertEqual(result.dialogue_act, "REQUEST")


class ConfidenceBandTests(unittest.TestCase):
    def test_strong_cue_high_band(self) -> None:
        result = classify("Hello!")
        self.assertGreaterEqual(result.confidence, 0.85)
        self.assertFalse(result.needs_clarification)

    def test_cautious_band_no_clarification(self) -> None:
        result = classify("What is the range?")
        self.assertGreaterEqual(result.confidence, 0.60)
        self.assertLess(result.confidence, 0.85)
        self.assertFalse(result.needs_clarification)

    def test_empty_input_needs_clarification(self) -> None:
        result = classify("   ")
        self.assertLess(result.confidence, 0.60)
        self.assertTrue(result.needs_clarification)

    def test_nocue_statement_needs_no_clarification(self) -> None:
        # Plan Step 2.3: clarification is owed only when ambiguity affects
        # the answer. A bare assertion asks nothing — asking "which do you
        # mean?" about it is UNNECESSARY_CLARIFICATION.
        result = classify("The sky is blue in summer.")
        self.assertLess(result.confidence, 0.60)
        self.assertFalse(result.needs_clarification)

    def test_competing_cues_downgrade_to_clarify(self) -> None:
        result = classify("Actually, do you remember my trip?")
        self.assertLess(result.confidence, 0.60)
        self.assertTrue(result.needs_clarification)
        self.assertIn(result.intent, {"CORRECTION", "MEMORY_QUERY"})

    def test_confidence_in_unit_interval(self) -> None:
        for text in ["Hi", "Why?", "", "xylophone zzz qqq",
                     "Remind me to call mom"]:
            result = classify(text)
            self.assertGreaterEqual(result.confidence, 0.0)
            self.assertLessEqual(result.confidence, 1.0)


class CorrectionDetectionTests(unittest.TestCase):
    CORRECTIONS = [
        "No, I meant the blue one.",
        "Actually I wanted something cheaper.",
        "That's wrong, the meeting is Tuesday.",
        "My mistake, it's 5pm not 6pm.",
        "Let me rephrase: I need the AWD model.",
        "That's incorrect, I live in Boston.",
        "You misunderstood, I said Friday.",
    ]

    def test_explicit_corrections(self) -> None:
        for text in self.CORRECTIONS:
            with self.subTest(text=text):
                result = classify(text)
                self.assertEqual(result.intent, "CORRECTION")
                self.assertEqual(result.dialogue_act, "CORRECTION")

    def test_bare_no_is_not_correction(self) -> None:
        result = classify("No.")
        self.assertEqual(result.intent, "DISCONFIRMATION")

    def test_correction_beats_question_shape(self) -> None:
        result = classify("Actually, what did I tell you about my trip?")
        self.assertEqual(result.intent, "CORRECTION")


if __name__ == "__main__":
    unittest.main()
