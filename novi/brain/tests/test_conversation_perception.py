"""Plan 03 Gap 3: perception question chain — intent, voicing, fixtures.

Deterministic, socket-free. Perception questions must classify as
OBSERVATION_QUERY, staged world entities must be voiced ("I can see a
cup."), and unstaged perception must stay honest. Fixtures seed the
production WorldModel — never a fake memory.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from novi.brain.b2_perception import SpecialistPerception
from novi.brain.conversation.conversation_state import ConversationState
from novi.brain.conversation.intent import classify_intent
from novi.brain.conversation.response_planner import _world_phrase
from novi.brain.conversation_replay import seed_world_entities
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


class PerceptionIntentTests(unittest.TestCase):
    def test_table_question_is_observation(self) -> None:
        result = classify_intent("What is on the table?", ConversationState())
        self.assertEqual(result.intent, "OBSERVATION_QUERY")

    def test_walked_in_is_observation(self) -> None:
        result = classify_intent("Who just walked in?", ConversationState())
        self.assertEqual(result.intent, "OBSERVATION_QUERY")

    def test_stale_cup_question_is_observation(self) -> None:
        result = classify_intent("Is the cup still on the table?",
                                 ConversationState())
        self.assertEqual(result.intent, "OBSERVATION_QUERY")

    def test_physical_action_not_rerouted(self) -> None:
        # "from the table" is an action frame, not a scene question.
        result = classify_intent("Pick up the cup from the table for me.",
                                 ConversationState())
        self.assertNotEqual(result.intent, "OBSERVATION_QUERY")


class WorldPhraseTests(unittest.TestCase):
    def test_labels_win_over_payload(self) -> None:
        phrase = _world_phrase({"labels": ["cup"],
                                "text": "{'entity_id': 'cup_001', 'x': 1}"})
        self.assertEqual(phrase, "cup")

    def test_falls_back_to_text(self) -> None:
        phrase = _world_phrase({"text": "a red mug by the window"})
        self.assertIn("red mug", phrase)


class FixtureSeedingTests(unittest.TestCase):
    def test_seed_counts_and_tolerates_garbage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = _brain(tmp)
            try:
                staged = seed_world_entities(brain, [
                    {"entity_id": "cup_001", "entity_type": "object",
                     "labels": ["cup"], "confidence": 0.85},
                    {"nope": True},
                ])
                self.assertEqual(staged, 1)
                self.assertEqual(seed_world_entities(brain, []), 0)
                self.assertEqual(seed_world_entities(object(), [{"labels": ["x"]}]), 0)
            finally:
                brain.stop()

    def test_staged_cup_is_voiced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = _brain(tmp)
            try:
                seed_world_entities(brain, [
                    {"entity_id": "cup_001", "entity_type": "object",
                     "labels": ["cup"], "confidence": 0.85}])
                resp = brain.respond("What is on the table?")
            finally:
                brain.stop()
        self.assertIn("cup", (resp["text"] or "").lower())

    def test_unstaged_perception_stays_honest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = _brain(tmp)
            try:
                resp = brain.respond("What is on the table?")
            finally:
                brain.stop()
        text = (resp["text"] or "").lower()
        self.assertNotIn("cup", text)
        self.assertTrue("can't reliably see" in text or "don't" in text
                        or "not sure" in text)

    def test_routine_memory_never_voiced_as_seen(self) -> None:
        # A memory-only answer must not pass through the "I can see" path:
        # seed a preference and ask a memory question instead.
        with tempfile.TemporaryDirectory() as tmp:
            brain = _brain(tmp)
            try:
                brain.respond("Remember that I prefer dark interiors.")
                resp = brain.respond("What kind of interiors do I prefer?")
            finally:
                brain.stop()
        text = (resp["text"] or "").lower()
        self.assertIn("dark", text)
        self.assertNotIn("i can see", text)


if __name__ == "__main__":
    unittest.main()
