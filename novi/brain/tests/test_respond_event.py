"""Tests for respond_event() — autonomous-utterance variant of respond().

Deterministic, hardware-free: a CandidateInitiative is naturalized through the
same guardrails as a composed reply, emits speech.autonomous, and returns the
brain-owned communicative act.
"""

from __future__ import annotations

import unittest

from novi.brain.chat import history_tail_text
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.io import CameraFrame
from novi.brain.salience import CandidateInitiative


class HistoryTailTextTests(unittest.TestCase):
    """history_tail_text must read the web history shape (``text`` key)."""

    def test_reads_text_key(self) -> None:
        history = [
            {"role": "user", "text": "remember the blue door"},
            {"role": "novi", "text": "noted"},
        ]
        tail = history_tail_text(history)
        self.assertIn("blue door", tail)

    def test_legacy_content_key_still_works(self) -> None:
        tail = history_tail_text([{"role": "user", "content": "legacy shape"}])
        self.assertIn("legacy shape", tail)

    def test_empty_and_missing_shapes(self) -> None:
        self.assertEqual(history_tail_text(None), "")
        self.assertEqual(history_tail_text([]), "")
        self.assertEqual(history_tail_text([{"role": "user"}]), "")

    def test_last_turns_and_char_cap(self) -> None:
        history = [{"role": "user", "text": f"turn-{i}"} for i in range(6)]
        tail = history_tail_text(history)
        self.assertNotIn("turn-0", tail)
        self.assertIn("turn-5", tail)


class FakeCamera:
    def __init__(self) -> None:
        self.n = 0

    def read(self) -> CameraFrame:
        self.n += 1
        return CameraFrame(
            frame_id=f"r-{self.n}",
            captured_at="t",
            width=1,
            height=1,
            payload=b"frame",
            metadata={"backend": "deterministic"},
        )

    def close(self) -> None:
        return None


def _brain() -> MacBrain:
    return MacBrain(camera=FakeCamera(), config=MacBrainConfig(curiosity_enabled=False))


def _candidate(**overrides) -> CandidateInitiative:
    base = {
        "kind": "presence.entered",
        "entity": "Alice",
        "text": "Hey Alice — good to see you.",
        "reason": "presence_entered:known=True",
        "affordance": "greet",
        "source_event": {"kind": "presence.entered", "source": "cam", "seq": 1},
    }
    base.update(overrides)
    return CandidateInitiative(**base)


class RespondEventTest(unittest.TestCase):
    def test_returns_autonomous_reply(self) -> None:
        b = _brain()
        result = b.respond_event(_candidate())
        self.assertEqual(result["reply_source"], "autonomous")
        self.assertEqual(result["text"], "Hey Alice — good to see you.")
        self.assertEqual(result["reason"], "presence_entered:known=True")

    def test_emits_speech_autonomous(self) -> None:
        b = _brain()
        b.respond_event(_candidate())
        emitted = [e for e in b.events if e["event_type"] == "speech.autonomous"]
        self.assertEqual(len(emitted), 1)
        self.assertEqual(emitted[0]["payload"]["kind"], "presence.entered")
        self.assertEqual(emitted[0]["payload"]["entity"], "Alice")

    def test_empty_text_returns_none(self) -> None:
        b = _brain()
        result = b.respond_event(_candidate(text="   "))
        self.assertEqual(result["reply_source"], "none")
        self.assertIsNone(result["text"])

    def test_guardrail_rejects_assistant_speak(self) -> None:
        b = _brain()
        result = b.respond_event(_candidate(text="How can I help you today?"))
        self.assertEqual(result["reply_source"], "rejected")
        self.assertIsNone(result["text"])

    def test_guardrail_rejects_meta_referential(self) -> None:
        b = _brain()
        result = b.respond_event(_candidate(text="As an AI language model, I noticed the mug moved."))
        self.assertEqual(result["reply_source"], "rejected")
        self.assertIsNone(result["text"])

    def test_grounding_appended_to_remark(self) -> None:
        b = _brain()
        result = b.respond_event(
            _candidate(text="I noticed your red mug moved."),
            grounding="I remember your red mug was on the counter.",
        )
        self.assertEqual(result["reply_source"], "autonomous")
        self.assertIn("I remember your red mug was on the counter.", result["text"])
        self.assertIn("I noticed your red mug moved.", result["text"])


if __name__ == "__main__":
    unittest.main()
