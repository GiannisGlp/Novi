"""Tests for novi/brain/affect_fusion.py — multimodal affect fusion.

Plan 24 Phase 3: combine voice, language, face/expression, body orientation,
gaze, gesture, conversation context and interaction history into per-dimension
likelihoods, weighted by source reliability. Conflicting modalities retain
uncertainty. A neutral face never means "emotion = false".
"""

from __future__ import annotations

import unittest

from novi.brain.affective_evidence import make_evidence
from novi.brain.affect_fusion import AffectFusion, FusedAffect


class AffectFusionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fusion = AffectFusion()

    def test_fuses_voice_language_context(self) -> None:
        # plan §7 example: combined frustration likelihood ≈ .76
        evidence = [
            make_evidence(source="voice", modality="voice", signal_type="speech_volume", value="0.70", confidence=0.70, reliability=0.8, subject="p"),
            make_evidence(source="language", modality="language", signal_type="lexical_marker", value="correction", confidence=0.88, reliability=0.9, subject="p"),
            make_evidence(source="face", modality="vision", signal_type="facial_signal", value="uncertain", confidence=0.45, reliability=0.5, subject="p"),
            make_evidence(source="context", modality="context", signal_type="conversation_context", value="0.82", confidence=0.82, reliability=0.85, subject="p"),
        ]
        result = self.fusion.fuse(evidence)
        fr = result["frustration_likelihood"]
        self.assertAlmostEqual(fr.value, 0.76, delta=0.05)
        self.assertGreater(fr.confidence, 0.0)

    def test_conflicting_modalities_retain_uncertainty(self) -> None:
        evidence = [
            make_evidence(source="voice", modality="voice", signal_type="speech_volume", value="0.9", confidence=0.9, reliability=0.9, subject="p"),
            make_evidence(source="face", modality="vision", signal_type="facial_signal", value="calm", confidence=0.8, reliability=0.8, subject="p"),
        ]
        result = self.fusion.fuse(evidence)
        fr = result["frustration_likelihood"]
        self.assertTrue(fr.conflict)
        self.assertLessEqual(fr.confidence, 0.5)  # uncertainty retained

    def test_neutral_face_does_not_zero_out_emotion(self) -> None:
        # never: neutral face → emotion = false
        evidence = [
            make_evidence(source="voice", modality="voice", signal_type="speech_volume", value="0.8", confidence=0.8, reliability=0.8, subject="p"),
            make_evidence(source="face", modality="vision", signal_type="facial_signal", value="neutral", confidence=0.7, reliability=0.7, subject="p"),
        ]
        result = self.fusion.fuse(evidence)
        fr = result["frustration_likelihood"]
        self.assertGreater(fr.value, 0.5)

    def test_reliability_weighting(self) -> None:
        # a low-reliability source barely moves the estimate
        evidence = [
            make_evidence(source="voice", modality="voice", signal_type="speech_volume", value="0.8", confidence=0.8, reliability=0.9, subject="p"),
            make_evidence(source="noisy", modality="vision", signal_type="facial_signal", value="0.2", confidence=0.8, reliability=0.1, subject="p"),
        ]
        result = self.fusion.fuse(evidence)
        fr = result["frustration_likelihood"]
        self.assertGreater(fr.value, 0.7)

    def test_contributions_preserved(self) -> None:
        evidence = [
            make_evidence(source="voice", modality="voice", signal_type="speech_volume", value="0.7", confidence=0.7, reliability=0.8, subject="p"),
        ]
        result = self.fusion.fuse(evidence)
        fr = result["frustration_likelihood"]
        self.assertEqual(len(fr.contributions), 1)
        self.assertEqual(fr.contributions[0].source, "voice")

    def test_unknown_signal_type_is_ignored(self) -> None:
        evidence = [
            make_evidence(source="x", modality="x", signal_type="not_a_signal", value="0.9", confidence=0.9, reliability=0.9, subject="p"),
        ]
        result = self.fusion.fuse(evidence)
        self.assertEqual(result, {})

    def test_snapshot_roundtrip(self) -> None:
        evidence = [
            make_evidence(source="voice", modality="voice", signal_type="speech_volume", value="0.7", confidence=0.7, reliability=0.8, subject="p"),
        ]
        result = self.fusion.fuse(evidence)
        snap = {k: v.snapshot() for k, v in result.items()}
        restored = {k: FusedAffect.from_snapshot(v) for k, v in snap.items()}
        self.assertAlmostEqual(restored["frustration_likelihood"].value, result["frustration_likelihood"].value, places=2)
        self.assertEqual(restored["frustration_likelihood"].conflict, result["frustration_likelihood"].conflict)


if __name__ == "__main__":
    unittest.main()
