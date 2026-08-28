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


class TestObjectKind:
    def test_enroll_object_and_match_exact(self, tmp_path):
        st = _tmp_store(tmp_path)
        oid = st.enroll(kind=RecognitionKind.OBJECT, label="my-mug", embedding=[1.0, 0.0], frame_id="f0")
        m = st.match(RecognitionKind.OBJECT, [1.0, 0.0])
        assert m is not None
        assert m.label == "my-mug" and m.person_id == oid and m.similarity == pytest.approx(1.0)

    def test_object_best_match_among_instances(self, tmp_path):
        st = _tmp_store(tmp_path)
        st.enroll(kind=RecognitionKind.OBJECT, label="mug-a", embedding=[1.0, 0.0], frame_id="f0")
        st.enroll(kind=RecognitionKind.OBJECT, label="mug-b", embedding=[0.1, 1.0], frame_id="f0")
        m = st.match(RecognitionKind.OBJECT, [0.95, 0.25])
        assert m is not None and m.label == "mug-a"

    def test_object_persists_across_reopen(self, tmp_path):
        path = tmp_path / "obj.db"
        st = RecognitionStore(path)
        oid = st.enroll(kind=RecognitionKind.OBJECT, label="my-mug", embedding=[1.0, 0.0], frame_id="f0")
        st.close()
        st2 = RecognitionStore(path)
        m = st2.match(RecognitionKind.OBJECT, [1.0, 0.0])
        assert m is not None and m.person_id == oid and m.label == "my-mug"
        st2.close()

    def test_object_is_non_biometric_works_with_privacy_off(self, tmp_path):
        st = _tmp_store(tmp_path)
        st.enroll(kind=RecognitionKind.OBJECT, label="my-mug", embedding=[1.0, 0.0], frame_id="f0")
        st.set_privacy(False, reason="owner request")
        m = st.match(RecognitionKind.OBJECT, [1.0, 0.0])
        assert m is not None and m.label == "my-mug"


class TestVoiceFaceFusion:
    """Face + voice enroll under one canonical person id; re-enroll upserts.

    Plan 21 fix for "Perception page shows Voice: Vano twice": voices no longer
    enroll under a separate ``voice-{label}`` id, and repeated enrollments
    replace the stored embedding instead of inserting duplicate rows.
    """

    def test_voice_defaults_to_canonical_person_id(self, tmp_path):
        st = _tmp_store(tmp_path)
        pid = st.enroll(kind=RecognitionKind.VOICE, label="Vano", embedding=[1.0, 0.0], provenance={"source": "test"})
        assert pid == "person-vano"

    def test_face_and_voice_share_one_person_id(self, tmp_path):
        st = _tmp_store(tmp_path)
        face_pid = st.enroll(kind=RecognitionKind.FACE, label="Vano", embedding=[1.0, 0.0], frame_id="f0")
        voice_pid = st.enroll(kind=RecognitionKind.VOICE, label="Vano", embedding=[1.0, 0.0], provenance={"source": "test"})
        assert voice_pid == face_pid == "person-vano"
        assert len(st.all(RecognitionKind.VOICE)) == 1

    def test_reenrolling_voice_upserts_single_row(self, tmp_path):
        st = _tmp_store(tmp_path)
        st.enroll(kind=RecognitionKind.VOICE, label="Vano", embedding=[1.0, 0.0], provenance={"source": "a"})
        st.enroll(kind=RecognitionKind.VOICE, label="Vano", embedding=[0.0, 1.0], provenance={"source": "b"})
        rows = st.all(RecognitionKind.VOICE)
        assert len(rows) == 1, "voice re-enrollment must upsert, not duplicate"
        m = st.match(RecognitionKind.VOICE, [0.0, 1.0])
        assert m is not None and m.person_id == "person-vano"

    def test_reenrolling_face_upserts_single_row(self, tmp_path):
        st = _tmp_store(tmp_path)
        st.enroll(kind=RecognitionKind.FACE, label="Anna", embedding=[1.0, 0.0], frame_id="f0")
        st.enroll(kind=RecognitionKind.FACE, label="Anna", embedding=[0.0, 1.0], frame_id="f1")
        assert len(st.all(RecognitionKind.FACE)) == 1

    def test_backfill_rewrites_legacy_voice_pids_and_dedupes(self, tmp_path):
        import sqlite3

        path = tmp_path / "legacy.db"
        conn = sqlite3.connect(str(path))
        conn.executescript(
            "CREATE TABLE recognition_enrollments ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, label TEXT NOT NULL,"
            " person_id TEXT NOT NULL, embedding_json TEXT NOT NULL DEFAULT '[]',"
            " descriptor_json TEXT NOT NULL DEFAULT '{}', frame_ref TEXT NOT NULL DEFAULT '',"
            " provenance_json TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL DEFAULT '')"
        )
        conn.execute(
            "INSERT INTO recognition_enrollments (kind, label, person_id, embedding_json)"
            " VALUES ('voice', 'Vano', 'voice-vano', '[1.0]')"
        )
        conn.execute(
            "INSERT INTO recognition_enrollments (kind, label, person_id, embedding_json)"
            " VALUES ('voice', 'Vano', 'voice-vano', '[2.0]')"
        )
        conn.execute(
            "INSERT INTO recognition_enrollments (kind, label, person_id, embedding_json)"
            " VALUES ('face', 'Vano', 'person-vano', '[3.0]')"
        )
        conn.commit()
        conn.close()

        st = RecognitionStore(path)
        voices = st.all(RecognitionKind.VOICE)
        assert len(voices) == 1, "legacy duplicates must collapse to one row"
        assert voices[0]["person_id"] == "person-vano"
        # the unique index is in place: a fresh enrollment upserts cleanly
        st.enroll(kind=RecognitionKind.VOICE, label="Vano", embedding=[4.0], provenance={"source": "new"})
        assert len(st.all(RecognitionKind.VOICE)) == 1


class TestRenameEntity:
    """Conversational naming re-keys a placeholder person to a real name."""

    def test_rename_placeholder_to_canonical(self, tmp_path):
        st = _tmp_store(tmp_path)
        st.enroll(kind=RecognitionKind.FACE, label="new-person-1",
                  embedding=[1.0, 0.0], person_id="person-new-person-1", frame_id="f0")
        moved = st.rename_entity(RecognitionKind.FACE, "person-new-person-1", "person-anna", label="Anna")
        assert moved == 1
        rows = st.all(RecognitionKind.FACE)
        assert len(rows) == 1
        assert rows[0]["person_id"] == "person-anna"
        assert rows[0]["label"] == "Anna"
        m = st.match(RecognitionKind.FACE, [1.0, 0.0])
        assert m is not None and m.person_id == "person-anna" and m.label == "Anna"

    def test_rename_onto_existing_target_merges(self, tmp_path):
        st = _tmp_store(tmp_path)
        st.enroll(kind=RecognitionKind.FACE, label="new-person-1",
                  embedding=[1.0, 0.0], person_id="person-new-person-1", frame_id="f0")
        st.enroll(kind=RecognitionKind.FACE, label="Anna",
                  embedding=[0.5, 0.5], person_id="person-anna", frame_id="f1")
        moved = st.rename_entity(RecognitionKind.FACE, "person-new-person-1", "person-anna", label="Anna")
        assert moved == 1
        rows = st.all(RecognitionKind.FACE)
        assert len(rows) == 1, "target identity wins; placeholder row is dropped"
        assert rows[0]["person_id"] == "person-anna"

    def test_rename_unknown_source_returns_zero(self, tmp_path):
        st = _tmp_store(tmp_path)
        assert st.rename_entity(RecognitionKind.FACE, "person-nobody", "person-anna", label="Anna") == 0

    def test_rename_same_ref_is_noop(self, tmp_path):
        st = _tmp_store(tmp_path)
        st.enroll(kind=RecognitionKind.FACE, label="Anna", embedding=[1.0, 0.0], frame_id="f0")
        assert st.rename_entity(RecognitionKind.FACE, "person-anna", "person-anna") == 0


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
