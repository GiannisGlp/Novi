"""Phase B2 (gap-audit plan 13): concrete identity providers.

Pins:
  - VoiceprintSpeakerID: deterministic voiceprints from WAV; enroll → identify
    round-trip; threshold rejects unknown voices; engine-contract signature.
  - OpenCVFaceID: deterministic faceprints on synthetic crops; enroll →
    identify; graceful None on unusable payloads.
  - Engine wiring: a face provider receives the camera frame payload through
    _identify_face and its match feeds PersonIdentity (identity.face event).
"""

import dataclasses
import math
import struct
import tempfile
import unittest
import wave
from pathlib import Path

from novi.brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.face_id import OpenCVFaceID
from novi.brain.speaker_id import VoiceprintSpeakerID
from novi.brain.tests.test_mac_brain import FakeCamera


def _write_wav(path: Path, freq: float, seconds: float = 0.6, rate: int = 16000) -> Path:
    """Write a deterministic sine-wave mono WAV."""
    n = int(rate * seconds)
    frames = b"".join(
        struct.pack("<h", int(12000 * math.sin(2 * math.pi * freq * i / rate))) for i in range(n)
    )
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(frames)
    return path


class SpeakerIDTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_enroll_then_identify_same_voice(self):
        spk = VoiceprintSpeakerID(threshold=0.9)
        wav = _write_wav(self.dir / "maya.wav", 220.0)
        self.assertTrue(spk.enroll("maya", str(wav)))
        probe = _write_wav(self.dir / "probe.wav", 220.0)
        m = spk.identify({"audio_path": str(probe)})
        self.assertIsNotNone(m)
        self.assertEqual(m.name, "maya")
        self.assertEqual(m.modality, "voice")

    def test_unknown_voice_below_threshold_returns_none(self):
        spk = VoiceprintSpeakerID(threshold=0.99)
        wav = _write_wav(self.dir / "a.wav", 220.0)
        spk.enroll("a", str(wav))
        other = _write_wav(self.dir / "b.wav", 880.0)
        self.assertIsNone(spk.identify({"audio_path": str(other)}))

    def test_missing_file_is_none_not_crash(self):
        spk = VoiceprintSpeakerID()
        self.assertIsNone(spk.identify({"audio_path": str(self.dir / "nope.wav")}))
        self.assertIsNone(spk.identify({}))

    def test_deterministic_features(self):
        spk = VoiceprintSpeakerID()
        wav = _write_wav(self.dir / "d.wav", 300.0)
        self.assertEqual(spk.features(str(wav)), spk.features(str(wav)))


class FaceIDTests(unittest.TestCase):
    def setUp(self):
        try:
            import cv2  # noqa: F401
            import numpy as np
        except Exception:
            self.skipTest("opencv not available")
        self.np = np

    def _image(self, seed: int):
        """A deterministic *textured* image (flat images have no gradients)."""
        np = self.np
        rng = np.random.default_rng(seed)
        return rng.integers(0, 255, size=(96, 96, 3), dtype=np.uint8)

    def test_identify_on_garbage_payload_is_none(self):
        fid = OpenCVFaceID()
        self.assertIsNone(fid.identify({"bbox": [0, 0, 10, 10], "image": None}))

    def test_enroll_identify_roundtrip_synthetic_face(self):
        fid = OpenCVFaceID(threshold=0.95)
        img = self._image(7)
        self.assertTrue(fid.enroll("vano", img))
        m = fid.identify({"bbox": [0, 0, 96, 96], "image": img})
        self.assertIsNotNone(m)
        self.assertEqual(m.name, "vano")
        self.assertEqual(m.modality, "face")

    def test_different_face_below_threshold(self):
        fid = OpenCVFaceID(threshold=0.999999)
        fid.enroll("a", self._image(1))
        different = self._image(2)
        self.assertIsNone(fid.identify({"bbox": [0, 0, 96, 96], "image": different}))

    def test_deterministic_features(self):
        fid = OpenCVFaceID()
        img = self._image(42)
        self.assertEqual(fid.features(img), fid.features(img))


class _FaceBackend(DeterministicPerceptionBackend):
    def detect(self, frame):
        return (Detection("person", 0.9, (10.0, 10.0, 80.0, 80.0)),)


class EngineFaceWiringTests(unittest.TestCase):
    def setUp(self):
        try:
            import cv2  # noqa: F401
            import numpy as np
        except Exception:
            self.skipTest("opencv not available")
        self.np = np

    def _image(self, seed: int):
        np = self.np
        rng = np.random.default_rng(seed)
        return rng.integers(0, 255, size=(96, 96, 3), dtype=np.uint8)

    def test_face_provider_receives_frame_payload_and_feeds_identity(self):
        payload = self._image(9)

        class PixelCamera(FakeCamera):
            def read(self):
                fr = super().read()
                return dataclasses.replace(fr, payload=payload)

        fid = OpenCVFaceID(threshold=0.9)
        fid.enroll("vano", payload)
        brain = MacBrain(
            camera=PixelCamera(),
            perception=SpecialistPerception(_FaceBackend()),
            config=MacBrainConfig(curiosity_enabled=False),
            face_id=fid,
        )
        brain.start()
        try:
            brain.step()
            belief = brain.identity.identity_for("person")
            self.assertIsNotNone(belief)
            self.assertEqual((belief.name or ""), "vano")
            self.assertIn("face", belief.modalities)
            self.assertIn("identity.face", [e["event_type"] for e in brain.events])
        finally:
            brain.stop()


if __name__ == "__main__":
    unittest.main()
