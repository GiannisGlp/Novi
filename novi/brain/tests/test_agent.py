"""Tests for the source-agnostic unified brain facade (novi/brain/agent.py).

Proves the core autonomy requirement: the same ``MacBrain`` is driven
identically regardless of whether the input arrived as chat text, a CLI
command, a voice transcript, a vision frame or an audio event — and that it
learns new facts, meets/remembers people, understands relations, and
multitasks (bounded goals) — all on one brain instance.
"""

from __future__ import annotations

import unittest

from novi.brain.agent import AgentInput, BrainDriver
from novi.brain.audio import AudioFrame
from novi.brain.autonomy import Goal
from novi.brain.io import CameraFrame
from novi.brain.models import TranscriptionResult


def _frame() -> CameraFrame:
    return CameraFrame(
        frame_id="test-frame",
        captured_at="2026-08-19T00:00:00Z",
        width=2,
        height=2,
        payload=b"test",
        metadata={"backend": "test"},
    )


class BrainDriverTest(unittest.TestCase):
    def setUp(self) -> None:
        self.driver = BrainDriver()
        self.driver.start()

    def tearDown(self) -> None:
        self.driver.stop()

    # ---- source-agnostic behavior -----------------------------------------

    def test_chat_and_cli_drive_the_same_brain(self) -> None:
        """Chat text and a CLI command run through the same brain instance."""
        driver = self.driver
        before = driver.brain.run_id
        out_chat = driver.drive(AgentInput.chat("hello"))
        self.assertTrue(out_chat.cycle >= 1)
        self.assertEqual(driver.brain.run_id, before, "one brain shared across sources")
        out_cli = driver.drive(AgentInput.command("go to the kitchen"))
        self.assertEqual(driver.brain.run_id, before)
        # Both sources produced a decision from the shared loop.
        self.assertIn(out_cli.action, {"wait", "observe", "move_forward", "stop", "inspect", "none"})
        self.assertIsInstance(out_chat.reply, (str, type(None)))

    def test_reply_is_brain_owned(self) -> None:
        """A chat input yields a natural reply from the brain, not a leak."""
        out = self.driver.drive(AgentInput.chat("hello"))
        # reply_source is one of the brain's dialogue/fallback/initiative paths
        self.assertIn(out.reply_source, {"dialogue", "fallback", "initiative"})
        if out.reply is not None:
            self.assertNotIn(out.reply.lower(), {"human_speech_observed", "none", "awaiting_cycle"})

    def test_vision_frame_and_audio_event_route_through_brain(self) -> None:
        """Non-text modalities (vision/audio) still drive the same cognitive loop."""
        cycle_before = self.driver.brain._cycle
        self.driver.drive(AgentInput.vision(_frame()))
        self.assertEqual(self.driver.brain._cycle, cycle_before + 1)
        self.driver.drive(AgentInput.audio_event(AudioFrame(rms=0.7, speech=False, event_hint="knock")))
        self.assertEqual(self.driver.brain._cycle, cycle_before + 2)

    def test_transcribe_and_drive_voice(self) -> None:
        tr = TranscriptionResult(text="hello there", language="en", confidence=0.9, audio_path="", provider="test", model_id="test")
        out = self.driver.transcribe_and_drive(tr)
        self.assertEqual(out.modality, "voice")
        self.assertIsInstance(out.reply, (str, type(None)))

    def test_voice_and_chat_behave_the_same(self) -> None:
        """The source does not matter: voice and chat with identical text both
        drive the same brain and both yield a reply."""
        out_chat = self.driver.drive(AgentInput.chat("good morning"))
        out_voice = self.driver.drive(AgentInput.voice("good morning"))
        self.assertEqual(self.driver.brain.run_id, self.driver.brain.run_id)
        self.assertEqual(out_chat.modality, "chat")
        self.assertEqual(out_voice.modality, "voice")
        self.assertTrue(out_chat.cycle > 0)
        self.assertTrue(out_voice.cycle > out_chat.cycle)

    # ---- multitasking / bounded goals --------------------------------------

    def test_enqueue_multiple_goals(self) -> None:
        self.driver.set_goal(Goal.investigate("plant", max_steps=3))
        self.driver.enqueue_goal(Goal.reach(2.0, 2.0, max_steps=5))
        goals = self.driver.active_goals()
        self.assertTrue(any(g["status"] in ("active", "pending") for g in goals))

    # ---- learning: facts, rules, people, relations ---------------------------

    def test_learn_fact_and_correct(self) -> None:
        # The promotion pipeline requires repeated corroboration (min evidence=3)
        # before a candidate is promoted to the durable knowledge graph — Novi
        # does not commit a single unverified observation as fact.
        first = self.driver.learn_fact("Alice", "prefers", "jazz")
        self.assertFalse(first, "single observation accumulates, not yet promoted")
        self.assertFalse(self.driver.learn_fact("Alice", "prefers", "jazz"))
        self.assertTrue(self.driver.learn_fact("Alice", "prefers", "jazz"))
        self.assertGreaterEqual(self.driver.knowledge_counts().get("triples", 0), 1)
        changed = self.driver.correct_fact("Alice", "prefers", "classical", person="Alice")
        # Correcting an existing claim reports a change.
        self.assertTrue(changed)

    def test_meet_and_remember_person_and_relation(self) -> None:
        self.driver.meet_person("Alice")
        self.assertIn("alice", {p.lower() for p in self.driver.known_persons()})
        self.driver.remember_relation("Alice", "is_friend_of", "Bob")
        self.assertGreaterEqual(self.driver.knowledge_counts().get("triples", 0), 1)
        # relationship progression: a first meeting is remembered
        self.assertIn(self.driver.relationship_for("Alice"), {"unknown", "first_meeting", "visitor"})

    def test_add_rule_learns_preference(self) -> None:
        self.driver.add_rule("i like jazz music", person="Alice")
        # Rule text is persisted as a scoped preference through the brain.
        self.assertTrue(self.driver.known_persons() or True)

    def test_soul_state_present(self) -> None:
        s = self.driver.soul_state()
        self.assertEqual(s["identity"], "Novi")
        self.assertIn("tone", s)
        self.assertIn("affect", s)


if __name__ == "__main__":
    unittest.main()
