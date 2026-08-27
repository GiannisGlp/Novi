"""Tests for voice/face recognition and place/building typing (rule 6).

Locks in docs/03-cognition/06 (face/voice recognition as identity evidence)
and docs/04-memory-and-knowledge/06 (cross-modal entity resolution): voice and
face providers feed PersonIdentity as additional modalities so identity can reach
the verified tier, and the knowledge graph types places vs buildings.
"""

from __future__ import annotations

import unittest

from novi.brain.b2_perception import Detection, SpecialistPerception
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.io import CameraFrame
from novi.brain.kgraph import infer_entity_type
from novi.brain.models.recognition import DeterministicFaceId, DeterministicSpeakerId


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
    cfg = MacBrainConfig(curiosity_enabled=False)
    return MacBrain(camera=FakeCamera(), perception=SpecialistPerception(PersonBackend()), config=cfg, **kw)


class RecognitionTests(unittest.TestCase):
    def test_face_recognition_feeds_identity(self):
        brain = _brain(face_id=DeterministicFaceId({"person": "alice"}))
        brain.start()
        try:
            brain.step()
            belief = brain.identity.identity_for("person")
            self.assertIsNotNone(belief)
            self.assertEqual(belief.name, "alice")
            self.assertIn("face", belief.modalities)
            self.assertTrue(any(e.get("event_type") == "identity.face" for e in brain.events))
        finally:
            brain.stop()

    def test_speaker_recognition_feeds_identity(self):
        brain = _brain(speaker_id=DeterministicSpeakerId({"voice_vano": "Vano"}))
        brain.start()
        try:
            r = brain._identify_speaker({"voiceprint": "voice_vano"})
            self.assertEqual(r["name"], "Vano")
            belief = brain.identity.identity_for("person")
            self.assertEqual(belief.name, "Vano")
            self.assertIn("voice", belief.modalities)
            self.assertTrue(any(e.get("event_type") == "identity.voice" for e in brain.events))
        finally:
            brain.stop()

    def test_no_provider_is_safe(self):
        brain = _brain()
        brain.start()
        try:
            brain.step()
            self.assertFalse(any(e.get("event_type") == "identity.face" for e in brain.events))
            self.assertIsNone(brain._identify_speaker({"voiceprint": "x"}))
        finally:
            brain.stop()

    def test_cross_modal_voice_plus_face_verifies(self):
        brain = _brain(face_id=DeterministicFaceId({"person": "alice"}), speaker_id=DeterministicSpeakerId({"voice_alice": "alice"}))
        brain.start()
        try:
            brain.step()  # face evidence
            brain._identify_speaker({"voiceprint": "voice_alice"})  # voice evidence
            belief = brain.identity.identity_for("person")
            self.assertEqual(belief.name, "alice")
            self.assertIn("face", belief.modalities)
            self.assertIn("voice", belief.modalities)
            self.assertGreaterEqual(belief.confidence, 0.8)
            self.assertEqual(belief.tier, "verified")
        finally:
            brain.stop()

    def test_speech_self_intro_plus_face_verifies(self):
        """Plan 19, Phase 4 acceptance: 'I am Maya' (speech) + matching face
        promotes the identity to the verified tier."""
        from novi.brain.models.stt import TranscriptionResult

        brain = _brain(face_id=DeterministicFaceId({"person": "maya"}))
        brain.start()
        try:
            brain.ingest_transcript(TranscriptionResult(
                text="I am Maya", language="en", confidence=0.9,
                audio_path="", provider="test", model_id="test",
            ))  # speech self-introduction binds the name
            brain.step()  # face evidence for the same person
            belief = brain.identity.identity_for("person")
            self.assertIsNotNone(belief)
            self.assertEqual((belief.name or "").lower(), "maya")
            self.assertIn("speech", belief.modalities)
            self.assertIn("face", belief.modalities)
            self.assertEqual(belief.tier, "verified")
        finally:
            brain.stop()

    def test_place_and_building_typing(self):
        self.assertEqual(infer_entity_type("door"), "place")
        self.assertEqual(infer_entity_type("kitchen"), "place")
        self.assertEqual(infer_entity_type("hospital"), "building")
        self.assertEqual(infer_entity_type("tower"), "building")
        self.assertEqual(infer_entity_type("alice"), "person")
        self.assertEqual(infer_entity_type("lamp"), "object")


if __name__ == "__main__":
    unittest.main()
