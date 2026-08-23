"""Tests: RecognitionStore — durable recognition memory (doc 16 §3).

Novi must save and later recognize voices, noises, places, and people:

- enroll face/voice/noise/place embeddings or descriptors under a person
  or place label; persisted to SQLite; survives store reopen;
- nearest-match lookup with confidence; empty store -> no match;
- privacy: biometric kinds refused when disabled; transitions audited;
- provenance required on every write.
"""

from __future__ import annotations

import pytest

from novi.integration.recognition_store import RecognitionKind, RecognitionStore


def _tmp_store(tmp_path):
    return RecognitionStore(tmp_path / "recognition.db")


class TestEnrollmentAndMatch:
    def test_enroll_face_and_match_exact(self, tmp_path):
        st = _tmp_store(tmp_path)
        pid = st.enroll(kind=RecognitionKind.FACE, label="Anna", embedding=[1.0, 0.0], frame_id="f0")
        m = st.match(RecognitionKind.FACE, [1.0, 0.0])
        assert m is not None
        assert m.label == "Anna" and m.person_id == pid and m.similarity == pytest.approx(1.0)

    def test_empty_store_matches_nothing(self, tmp_path):
        st = _tmp_store(tmp_path)
        assert st.match(RecognitionKind.VOICE, [1.0]) is None

    def test_voice_enrollment_and_best_match(self, tmp_path):
        st = _tmp_store(tmp_path)
        st.enroll(kind=RecognitionKind.VOICE, label="Anna", embedding=[1.0, 0.2], provenance={"source": "diarization"})
        st.enroll(kind=RecognitionKind.VOICE, label="Bob", embedding=[0.1, 1.0], provenance={"source": "diarization"})
        m = st.match(RecognitionKind.VOICE, [0.95, 0.25])
        assert m.label == "Anna"

    def test_noises_and_places_are_first_class(self, tmp_path):
        st = _tmp_store(tmp_path)
        st.enroll(kind=RecognitionKind.NOISE, label="kettle-whistle", descriptor={"band": "high", "repeats": 3}, provenance={"source": "sed"})
        st.enroll(kind=RecognitionKind.PLACE, label="kitchen", descriptor={"landmarks": ["cup", "book"]}, provenance={"source": "slam"})
        noise_hits = st.lookup_by_descriptor(RecognitionKind.NOISE, {"band": "high"})
        place_hits = st.lookup_by_descriptor(RecognitionKind.PLACE, {"landmarks": ["cup"]})
        assert [h["label"] for h in noise_hits] == ["kettle-whistle"]
        assert [h["label"] for h in place_hits] == ["kitchen"]

    def test_persistence_across_reopen(self, tmp_path):
        path = tmp_path / "rec.db"
        st = RecognitionStore(path)
        pid = st.enroll(kind=RecognitionKind.FACE, label="Anna", embedding=[1.0, 0.0], frame_id="f0")
        st.close()
        st2 = RecognitionStore(path)
        m = st2.match(RecognitionKind.FACE, [1.0, 0.0])
        assert m is not None and m.person_id == pid and m.label == "Anna"
        st2.close()

    def test_provenance_required(self, tmp_path):
        st = _tmp_store(tmp_path)
        with pytest.raises(ValueError):
            st.enroll(kind=RecognitionKind.FACE, label="X", embedding=[1.0])


class TestPrivacy:
    def test_biometrics_refused_when_disabled(self, tmp_path):
        st = _tmp_store(tmp_path)
        st.set_privacy(False, reason="owner request")
        with pytest.raises(PermissionError):
            st.enroll(kind=RecognitionKind.FACE, label="X", embedding=[1.0], frame_id="f")
        with pytest.raises(PermissionError):
            st.match(RecognitionKind.VOICE, [1.0])

    def test_places_and_noises_still_work_when_privacy_off(self, tmp_path):
        st = _tmp_store(tmp_path)
        st.enroll(kind=RecognitionKind.PLACE, label="kitchen", descriptor={"a": 1}, frame_id="f")
        st.set_privacy(False, reason="owner request")
        hits = st.lookup_by_descriptor(RecognitionKind.PLACE, {"a": 1})
        assert len(hits) == 1

    def test_audit_trail_records_transitions(self, tmp_path):
        st = _tmp_store(tmp_path)
        st.set_privacy(False, reason="test-off")
        st.set_privacy(True, reason="test-on")
        kinds = [(e["kind"], e["reason"]) for e in st.audit_log]
        assert ("privacy-disabled", "test-off") in kinds
        assert ("privacy-enabled", "test-on") in kinds
