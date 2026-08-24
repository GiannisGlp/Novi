"""Tests: real speaker recognition via Resemblyzer voiceprints (doc 17 §8).

Uses macOS `say` to synthesize genuine speech for test fixtures — the
d-vector model is trained on real voices, so fixtures must be speech
(pure tones score ~0.45 and prove nothing).

Validated live: same-speaker similarity ~0.92, cross-speaker ~0.46.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

import pytest


def _say(text: str, out: Path, voice: str = "Samantha") -> None:
    subprocess.run(
        ["say", "-v", voice, "-o", str(out), "--data-format=LEI16@16000", text],
        check=True,
    )


@pytest.mark.skipif(not Path("/usr/bin/say").exists(), reason="macOS say required")
class TestSpeakerRecognizer(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        from novi.integration.real_io_voice import RealSpeakerRecognizer

        self.rec = RealSpeakerRecognizer()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _voice_wav(self, name: str, text: str, voice: str = "Samantha") -> Path:
        p = self.tmp / f"{name}.wav"
        _say(text, p, voice=voice)
        return p

    def test_enroll_and_match_same_speaker(self):
        v1 = self._voice_wav("anna1", "The weather today is quite pleasant for a long walk outside.")
        v2 = self._voice_wav("anna2", "I enjoy reading books about science and history in the evening.")
        self.rec.enroll("Anna", v1)
        m = self.rec.match(v2, min_similarity=0.75)
        self.assertIsNotNone(m)
        self.assertEqual(m.label, "Anna")
        self.assertGreater(m.similarity, 0.75)

    def test_different_speakers_distinguished(self):
        anna = self._voice_wav("anna", "The weather today is quite pleasant for a walk.")
        bob = self._voice_wav("bob", "Perhaps we should consider alternative solutions tomorrow.", voice="Daniel")
        probe_bob = self._voice_wav("probe", "I think this approach will work better than the last one.", voice="Daniel")
        self.rec.enroll("Anna", anna)
        self.rec.enroll("Bob", bob)
        m = self.rec.match(probe_bob, min_similarity=0.60)
        self.assertIsNotNone(m)
        self.assertEqual(m.label, "Bob")

    def test_unknown_voice_returns_none(self):
        anna = self._voice_wav("anna", "The weather today is quite pleasant.")
        stranger = self._voice_wav("stranger", "Hello there, this is a completely different person speaking now.", voice="Daniel")
        self.rec.enroll("Anna", anna)
        self.assertIsNone(self.rec.match(stranger, min_similarity=0.85))

    def test_persists_via_recognition_store(self):
        from novi.integration.recognition_store import RecognitionKind, RecognitionStore
        from novi.integration.real_io_voice import RealSpeakerRecognizer

        store = RecognitionStore(self.tmp / "rec.db")
        rec = RealSpeakerRecognizer(store=store)
        wav = self._voice_wav("anna", "Testing the durable enrollment path for voices.")
        pid = rec.enroll("Anna", wav)
        rows = store.all(RecognitionKind.VOICE)
        self.assertTrue(any(r["label"] == "Anna" and r["person_id"] == pid for r in rows))

    def test_embedder_normalizes(self):
        from novi.integration.real_io_voice import RealVoiceEmbedder

        emb = RealVoiceEmbedder()
        import numpy as np

        wav = self._voice_wav("norm", "Normalization check for the embedding vector output.")
        v = emb.embed_wav(wav)
        self.assertEqual(len(v), 256)
        self.assertAlmostEqual(float(np.linalg.norm(v)), 1.0, places=4)


if __name__ == "__main__":
    unittest.main()
