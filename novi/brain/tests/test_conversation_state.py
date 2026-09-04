"""Foundation contract tests: ConversationState + topic classifier."""

from __future__ import annotations

import unittest

from novi.brain.conversation import (
    ConversationState,
    TopicTransition,
    classify_topic_transition,
)


class StateUpdateTests(unittest.TestCase):
    def test_record_turn_bounds_history_and_entities(self) -> None:
        state = ConversationState()
        for i in range(20):
            state.record_turn(user_text=f"question {i} about Trains",
                              novi_text="answer here.",
                              entities=[f"Entity{i % 10}"])
        self.assertEqual(len(state.recent_turns), 12)
        self.assertEqual(len(state.active_entities), 8)
        self.assertEqual(state.conversation_phase, "ongoing")
        self.assertEqual(state.turn_count, 20)

    def test_entity_dedup_case_insensitive(self) -> None:
        state = ConversationState()
        state.record_turn(user_text="a", entities=["Model Y"])
        state.record_turn(user_text="b", entities=["model y"])
        self.assertEqual(state.active_entities, ["Model Y"])

    def test_question_tracking_and_closure(self) -> None:
        state = ConversationState()
        state.record_turn(user_text="hi", question_asked="What model?")
        self.assertEqual(state.open_questions, ["What model?"])
        closed = state.answer_open_question("The Model Y.")
        self.assertEqual(closed, "What model?")
        self.assertEqual(state.open_questions, [])
        self.assertEqual(state.answer_open_question("x"), "")

    def test_long_phase(self) -> None:
        state = ConversationState()
        for _ in range(21):
            state.record_turn(user_text="x")
        self.assertEqual(state.conversation_phase, "long")


class TopicTests(unittest.TestCase):
    def test_first_topic_adopted(self) -> None:
        state = ConversationState()
        state.set_topic("Tesla", transition=TopicTransition.CONTINUE_CURRENT_TOPIC)
        self.assertEqual(state.topic, "Tesla")

    def test_new_topic_preserves_old_as_subtopic(self) -> None:
        state = ConversationState()
        state.set_topic("Tesla", transition=TopicTransition.NEW_TOPIC)
        state.set_topic("Football", transition=TopicTransition.NEW_TOPIC)
        self.assertEqual(state.topic, "Football")
        self.assertIn("Tesla", state.subtopics)

    def test_return_restores_previous(self) -> None:
        state = ConversationState()
        state.set_topic("Tesla", transition=TopicTransition.NEW_TOPIC)
        state.set_topic("Football", transition=TopicTransition.NEW_TOPIC)
        state.set_topic("Tesla", transition=TopicTransition.RETURN_TO_PREVIOUS_TOPIC)
        self.assertEqual(state.topic, "Tesla")

    def test_classifier_cues(self) -> None:
        state = ConversationState(topic="Tesla")
        self.assertEqual(classify_topic_transition("What about the range?", state),
                         TopicTransition.CONTINUE_CURRENT_TOPIC)
        self.assertEqual(classify_topic_transition("Back to the Tesla.", state),
                         TopicTransition.RETURN_TO_PREVIOUS_TOPIC)
        self.assertEqual(classify_topic_transition(
            "Give me a full quantum chromodynamics lecture with math", state),
            TopicTransition.NEW_TOPIC)

    def test_snapshot_roundtrip(self) -> None:
        state = ConversationState()
        state.set_topic("Tesla", transition=TopicTransition.NEW_TOPIC)
        state.record_turn(user_text="hi", novi_text="hello",
                          intent="GREETING", entities=["Tesla"])
        clone = ConversationState.from_dict(state.to_dict())
        self.assertEqual(clone.topic, "Tesla")
        self.assertEqual(clone.current_intent, "GREETING")
        self.assertEqual(clone.anchor.active_entity, "Tesla")
        self.assertEqual(clone.turn_count, 1)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
