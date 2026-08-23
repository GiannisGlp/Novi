"""Tests for spontaneous social initiative when neglected (rules 4/5).

Locks in docs/06-soul/00 §11/§21 (social initiative + idle behavior) and
docs/02-autonomy/03 (attention budget): Novi may initiate a low-cost remark when
neglected, bounded by a neglect threshold and cooldown, never during goal
pursuit, and reset when someone addresses it.
"""

from __future__ import annotations

import unittest

from novi.brain.b2_perception import Detection, SpecialistPerception
from novi.brain.autonomy import Goal
from novi.brain.dialogue import _is_forbidden
from novi.brain.io import CameraFrame
from novi.brain.engine import MacBrain, MacBrainConfig


class FakeCamera:
    def __init__(self) -> None:
        self.sequence = 0
        self.closed = False

    def close(self) -> None:
        self.closed = True

    def read(self) -> CameraFrame:
        self.sequence += 1
        return CameraFrame(frame_id=f"f-{self.sequence}", captured_at="2026-08-19T14:00:00Z", width=2, height=2, payload=b"frame", metadata={"backend": "test"})


class PersonBackend:
    def detect(self, frame):
        return (Detection("person", 0.95, (0.0, 0.0, 1.0, 1.0)),)

    def depth(self, frame):
        return None

    def segment(self, frame):
        return None


def _brain(**kw) -> MacBrain:
    cfg = MacBrainConfig(curiosity_enabled=False, initiative_enabled=True, **kw)
    return MacBrain(camera=FakeCamera(), perception=SpecialistPerception(PersonBackend()), config=cfg)


def _initiated(brain: MacBrain) -> list:
    return [e for e in brain.events if e.get("event_type") == "speech.initiated"]


class InitiativeTests(unittest.TestCase):
    def test_disabled_by_default(self):
        cfg = MacBrainConfig(curiosity_enabled=False)  # initiative_enabled defaults False
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(PersonBackend()), config=cfg)
        brain.start()
        try:
            for _ in range(40):
                brain.step()
            self.assertEqual(_initiated(brain), [])
        finally:
            brain.stop()

    def test_fires_after_neglect_threshold(self):
        brain = _brain(initiative_neglect_threshold=5, initiative_cooldown=100)
        brain.start()
        try:
            returns = [brain.step() for _ in range(6)]
            events = _initiated(brain)
            self.assertEqual(len(events), 1, "exactly one initiative expected after neglect")
            self.assertIn(events[0]["payload"]["text"], ["hey — you still there?", "did you forget me?", "it's gone quiet — still around?", "hello? you still here?"])
            self.assertTrue(any(r.get("initiative") for r in returns), "the firing step must report the initiative")
        finally:
            brain.stop()

    def test_cooldown_prevents_rapid_repeat(self):
        brain = _brain(initiative_neglect_threshold=5, initiative_cooldown=100)
        brain.start()
        try:
            for _ in range(20):
                brain.step()
            self.assertEqual(len(_initiated(brain)), 1, "cooldown must prevent a second initiative")
        finally:
            brain.stop()

    def test_suppressed_while_goal_active(self):
        brain = _brain(initiative_neglect_threshold=5, initiative_cooldown=100)
        brain.start()
        try:
            brain.set_goal(Goal.reach(100.0, 100.0, max_steps=200))  # far target: stays active
            for _ in range(20):
                brain.step()
            self.assertEqual(_initiated(brain), [], "must not initiate during goal pursuit")
        finally:
            brain.stop()

    def test_addressing_resets_neglect(self):
        from novi.brain.models.stt import TranscriptionResult

        brain = _brain(initiative_neglect_threshold=5, initiative_cooldown=100)
        brain.start()
        try:
            for _ in range(4):  # just below threshold
                brain.step()
            self.assertEqual(_initiated(brain), [])
            brain.ingest_transcript(TranscriptionResult(text="hi novi", language="en", confidence=0.9, audio_path="", provider="test", model_id="test"))
            for _ in range(4):  # addressed recently -> still not neglected
                brain.step()
            self.assertEqual(_initiated(brain), [], "being addressed must reset the neglect counter")
        finally:
            brain.stop()

    def test_initiation_utterance_is_natural(self):
        brain = _brain()
        for kind in ("neglected_remark", "idle_remark"):
            for cycle in range(20):
                text = brain._initiation_utterance(kind, "alice", cycle)
                self.assertTrue(text)
                self.assertFalse(_is_forbidden(text), f"initiation must not be robotic: {text!r}")


if __name__ == "__main__":
    unittest.main()
