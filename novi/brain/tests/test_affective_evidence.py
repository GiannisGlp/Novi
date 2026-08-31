"""Tests for novi/brain/affective_evidence.py — canonical affective evidence.

Plan 24 Phase 1: every affective interpretation must be grounded in an
observable evidence record that preserves its source, modality, confidence,
reliability and provenance. No evidence record may claim direct access to a
private mental state — it describes an observable signal.
"""

from __future__ import annotations

import unittest

from novi.brain.affective_evidence import (
    AffectiveEvidence,
    make_evidence,
    utc_now_iso,
)


class AffectiveEvidenceTest(unittest.TestCase):
    def test_evidence_carries_all_contract_fields(self) -> None:
        ev = AffectiveEvidence(
            evidence_id="ev-001",
            timestamp="2026-08-31T10:00:00+00:00",
            source="microphone",
            modality="voice",
            signal_type="speech_volume",
            value="high",
            confidence=0.91,
            reliability=0.9,
            provenance="asr_energy_estimator",
            subject="person:owner_001",
        )
        self.assertEqual(ev.signal_type, "speech_volume")
        self.assertEqual(ev.value, "high")
        self.assertEqual(ev.source, "microphone")
        self.assertEqual(ev.modality, "voice")
        self.assertEqual(ev.confidence, 0.91)
        self.assertEqual(ev.reliability, 0.9)
        self.assertEqual(ev.provenance, "asr_energy_estimator")
        self.assertEqual(ev.subject, "person:owner_001")

    def test_make_evidence_generates_id_and_timestamp(self) -> None:
        ev = make_evidence(
            source="microphone",
            modality="voice",
            signal_type="speech_rate",
            value="high",
            confidence=0.8,
            subject="person:owner_001",
        )
        self.assertTrue(ev.evidence_id.startswith("ev-"))
        self.assertTrue(ev.timestamp)  # auto-filled
        self.assertEqual(ev.signal_type, "speech_rate")
        self.assertEqual(ev.value, "high")

    def test_confidence_and_reliability_clamped(self) -> None:
        ev = make_evidence(
            source="camera",
            modality="vision",
            signal_type="facial_signal",
            value="uncertain",
            confidence=1.7,
            reliability=-0.2,
            subject="person:owner_001",
        )
        self.assertLessEqual(ev.confidence, 1.0)
        self.assertGreaterEqual(ev.reliability, 0.0)

    def test_snapshot_roundtrip(self) -> None:
        ev = make_evidence(
            source="microphone",
            modality="voice",
            signal_type="pause_frequency",
            value="low",
            confidence=0.6,
            reliability=0.7,
            provenance="vad",
            subject="person:owner_001",
        )
        snap = ev.snapshot()
        self.assertEqual(snap["signal_type"], "pause_frequency")
        self.assertEqual(snap["value"], "low")
        self.assertEqual(snap["source"], "microphone")
        self.assertEqual(snap["modality"], "voice")
        restored = AffectiveEvidence.from_snapshot(snap)
        self.assertEqual(restored, ev)

    def test_observable_signal_types_are_grounded(self) -> None:
        # The plan's example signals are all observable, never mind-reading.
        for signal_type, value in [
            ("speech_rate", "high"),
            ("speech_volume", "high"),
            ("pause_frequency", "low"),
            ("lexical_marker", "correction"),
            ("facial_signal", "uncertain"),
            ("orientation", "toward_novi"),
        ]:
            ev = make_evidence(
                source="sensor",
                modality="multimodal",
                signal_type=signal_type,
                value=value,
                confidence=0.5,
                subject="person:owner_001",
            )
            self.assertEqual(ev.signal_type, signal_type)
            self.assertEqual(ev.value, value)

    def test_utc_now_iso_is_isoformat(self) -> None:
        ts = utc_now_iso()
        self.assertIn("T", ts)
        self.assertIn("+00:00", ts)


if __name__ == "__main__":
    unittest.main()
