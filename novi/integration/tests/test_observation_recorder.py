"""Tests: ObservationRecorder — durable spatial/sighting memory (plan 02 §4).

Novi must remember WHAT it saw, WHERE, WHEN, and its vector:

- record() persists a sighting (kind, entity, label, place, bbox, time, vector,
  provenance) into the canonical SQLite DB;
- repeated sightings of the same entity in the same place COALESCE into one
  row (last-seen advanced), not unbounded disk growth;
- last_sighting(entity_ref) returns the most recent place/time/vector;
- in_place(place) returns what is currently known to be at that place;
- search() returns top-k episodes ranked by cosine over saved vectors;
- privacy: biometric (face) sightings refused when disabled, audited;
  non-biometric (object) sightings always allowed;
- restarts (fresh recorder on the same DB) still answer — durable provability.
"""

from __future__ import annotations

import pytest

from novi.integration.observation_recorder import ObservationRecorder
from novi.integration.recognition_store import RecognitionKind


def _tmp(tmp_path) -> ObservationRecorder:
    return ObservationRecorder(tmp_path / "observation.db")


def _record(oc: ObservationRecorder, **kw):
    """record() with mandatory provenance injected (invariant: every write)."""
    kw.setdefault("provenance", {"source": "recognition"})
    return oc.record(**kw)


class TestRecordAndCoalesce:
    def test_record_inserts_an_observation(self, tmp_path):
        oc = _tmp(tmp_path)
        rec = _record(
            oc, kind=RecognitionKind.OBJECT, entity_ref="object-my-mug",
            label="my blue mug", category="cup", place="kitchen",
            vector=[1.0, 0.0], frame_id="f0",
        )
        assert rec.entity_ref == "object-my-mug"
        assert rec.place == "kitchen" and rec.label == "my blue mug"
        assert oc.count() >= 1

    def test_repeated_sighting_of_same_entity_place_coalesces(self, tmp_path):
        oc = _tmp(tmp_path)
        _record(oc, kind=RecognitionKind.OBJECT, entity_ref="object-my-mug",
                place="kitchen", label="my blue mug", vector=[1.0, 0.0], frame_id="f0")
        _record(oc, kind=RecognitionKind.OBJECT, entity_ref="object-my-mug",
                place="kitchen", label="my blue mug", vector=[1.0, 0.0], frame_id="f1")
        assert oc.count() == 1, "same entity+place must coalesce, not grow"

    def test_distinct_place_is_a_separate_observation(self, tmp_path):
        oc = _tmp(tmp_path)
        _record(oc, kind=RecognitionKind.OBJECT, entity_ref="object-my-mug",
                place="kitchen", label="my blue mug", vector=[1.0, 0.0])
        _record(oc, kind=RecognitionKind.OBJECT, entity_ref="object-my-mug",
                place="living-room", label="my blue mug", vector=[1.0, 0.0])
        assert oc.count() == 2
        assert {r.place for r in oc.all(kind=RecognitionKind.OBJECT)} == {
            "kitchen", "living-room"}

    def test_later_observation_advances_last_seen(self, tmp_path):
        oc = _tmp(tmp_path)
        _record(oc, kind=RecognitionKind.OBJECT, entity_ref="object-mug",
                place="kitchen", label="mug", vector=[1.0, 0.0], frame_id="f0")
        _record(oc, kind=RecognitionKind.OBJECT, entity_ref="object-mug",
                place="kitchen", label="mug", vector=[1.0, 0.0], frame_id="f9")
        last = oc.last_sighting(RecognitionKind.OBJECT, "object-mug")
        assert last is not None and last.frame_ref == "f9"


class TestRetrieval:
    def test_last_sighting_returns_place_time_vector(self, tmp_path):
        oc = _tmp(tmp_path)
        _record(oc, kind=RecognitionKind.OBJECT, entity_ref="object-mug",
                place="kitchen", label="my blue mug", vector=[1.0, 0.0],
                frame_id="f0")
        hit = oc.last_sighting(RecognitionKind.OBJECT, "object-mug")
        assert hit is not None
        assert hit.place == "kitchen"
        assert hit.vector == pytest.approx([1.0, 0.0])
        assert hit.temporal_at  # present timestamp

    def test_last_sighting_none_when_never_seen(self, tmp_path):
        oc = _tmp(tmp_path)
        assert oc.last_sighting(RecognitionKind.OBJECT, "object-nope") is None

    def test_in_place_returns_current_objects(self, tmp_path):
        oc = _tmp(tmp_path)
        _record(oc, kind=RecognitionKind.OBJECT, entity_ref="object-mug", place="kitchen",
                label="my blue mug", vector=[1.0, 0.0])
        _record(oc, kind=RecognitionKind.OBJECT, entity_ref="object-book", place="kitchen",
                label="a red book", vector=[0.0, 1.0])
        _record(oc, kind=RecognitionKind.OBJECT, entity_ref="object-plant", place="living",
                label="a plant", vector=[1.0, 1.0])
        in_kitchen = oc.in_place("kitchen")
        assert {r.entity_ref for r in in_kitchen} == {"object-mug", "object-book"}

    def test_search_ranks_by_cosine(self, tmp_path):
        oc = _tmp(tmp_path)
        _record(oc, kind=RecognitionKind.OBJECT, entity_ref="object-mug", place="kitchen",
                label="my blue mug", vector=[1.0, 0.0])
        _record(oc, kind=RecognitionKind.OBJECT, entity_ref="object-book", place="kitchen",
                label="a red book", vector=[0.0, 1.0])
        hits = oc.search([0.95, 0.1], kind=RecognitionKind.OBJECT, limit=2)
        assert hits and hits[0][0] == "object-mug"


class TestPrivacyAndPersistence:
    def test_face_biometric_refused_when_privacy_off(self, tmp_path):
        oc = _tmp(tmp_path)
        oc.set_privacy(False, reason="owner request")
        with pytest.raises(PermissionError):
            _record(oc, kind=RecognitionKind.FACE, entity_ref="person-anna",
                    place="kitchen", label="Anna", vector=[1.0, 0.0])
        # non-biometric still allowed
        _record(oc, kind=RecognitionKind.OBJECT, entity_ref="object-mug",
                place="kitchen", label="my blue mug", vector=[1.0, 0.0])
        assert oc.count(kind=RecognitionKind.OBJECT) == 1

    def test_face_allowed_when_privacy_on(self, tmp_path):
        oc = _tmp(tmp_path)
        _record(oc, kind=RecognitionKind.FACE, entity_ref="person-anna",
                place="living", label="Anna", vector=[1.0, 0.0])
        assert oc.last_sighting(RecognitionKind.FACE, "person-anna") is not None

    def test_persistence_across_reopen(self, tmp_path):
        path = tmp_path / "obs.db"
        oc = ObservationRecorder(path)
        _record(oc, kind=RecognitionKind.OBJECT, entity_ref="object-mug", place="kitchen",
                label="my blue mug", vector=[1.0, 0.0])
        oc.close()
        oc2 = ObservationRecorder(path)
        hit = oc2.last_sighting(RecognitionKind.OBJECT, "object-mug")
        oc2.close()
        assert hit is not None and hit.place == "kitchen" and hit.label == "my blue mug"

    def test_provenance_required(self, tmp_path):
        oc = _tmp(tmp_path)
        with pytest.raises(ValueError):
            oc.record(kind=RecognitionKind.OBJECT, entity_ref="object-x",
                      place="kitchen", label="x", vector=[1.0, 0.0])


class TestRenameEntity:
    def test_rename_rebinds_sightings_and_preserves_history(self, tmp_path):
        oc = _tmp(tmp_path)
        _record(oc, kind=RecognitionKind.OBJECT, entity_ref="object-unresolved-cup",
                place="kitchen", label="cup", vector=[1.0, 0.0])
        _record(oc, kind=RecognitionKind.OBJECT, entity_ref="object-unresolved-cup",
                place="living", label="cup", vector=[1.0, 0.0])
        moved = oc.rename_entity(RecognitionKind.OBJECT, "object-unresolved-cup", "object-my-mug")
        assert moved == 2
        # history now answerable under the canonical id
        last = oc.last_sighting(RecognitionKind.OBJECT, "object-my-mug")
        assert last is not None and last.place == "living"
        # unresolved ref gone
        assert oc.last_sighting(RecognitionKind.OBJECT, "object-unresolved-cup") is None

    def test_rename_noop_when_unknown_or_same_ref(self, tmp_path):
        oc = _tmp(tmp_path)
        assert oc.rename_entity(RecognitionKind.OBJECT, "object-x", "object-y") == 0
        _record(oc, kind=RecognitionKind.OBJECT, entity_ref="object-a",
                place="p", label="a", vector=[1.0])
        assert oc.rename_entity(RecognitionKind.OBJECT, "object-a", "object-a") == 0
        assert oc.last_sighting(RecognitionKind.OBJECT, "object-a") is not None
