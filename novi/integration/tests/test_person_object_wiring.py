"""Tests: MultimodalRuntime records durable person-object co-occurrence (plan 26 D).

The runtime knows WHO is in view and WHICH object instance was recognized —
these tests prove that knowledge lands in the PersonObjectAssociationStore as
durable "person was seen with object, here" facts, gated the same way the other
person-keyed stores are gated:

- a recognized/verified current person + a recognized object instance ->
  one coalescing association row (person, object, place);
- a placeholder / "someone" / empty person is NEVER recorded — anonymous
  co-occurrence rows would just pollute the memory;
- a privacy-off session refuses the write (fail-closed) but never breaks
  recognition;
- conversational object-naming and person-naming re-key the memory (held
  object placeholder ref; name_person merges rows under the canonical id).
"""

from __future__ import annotations

from novi.brain.agent import BrainDriver
from novi.integration.multimodal import MultimodalRuntime
from novi.integration.observation_recorder import ObservationRecorder
from novi.integration.person_object_store import PersonObjectAssociationStore
from novi.integration.recognition_store import RecognitionKind, RecognitionStore
from novi.perception.detection import DeterministicObjectDetector


def _runtime(tmp_path, *, privacy: bool = True):
    detector = DeterministicObjectDetector(scripted={})
    store = RecognitionStore(tmp_path / "rec.db")
    obs = ObservationRecorder(tmp_path / "obs.db")
    assoc = PersonObjectAssociationStore(tmp_path / "assoc.db")
    assoc.set_privacy(privacy, reason="test")
    rt = MultimodalRuntime(
        driver=BrainDriver(),
        detector=detector,
        recognition=store,
        observations=obs,
        associations=assoc,
    )
    rt.current_place = "kitchen"
    return rt, store, assoc


def _enroll_mug(store: RecognitionStore) -> None:
    store.enroll(
        kind=RecognitionKind.OBJECT, label="my-mug",
        embedding=[1.0, 0.0], person_id="object-my-mug", frame_id="f0",
    )


class TestCooccurrenceRecording:
    def test_recognized_person_object_cooccurrence_written(self, tmp_path):
        rt, store, assoc = _runtime(tmp_path)
        rt.current_person = "Anna"
        rt.current_person_tier = "recognized"
        _enroll_mug(store)
        rt.recognize_objects([("cup", [1.0, 0.0])], frame_id="f1")

        rows = assoc.objects_with("person-anna")
        assert len(rows) == 1
        assert rows[0].object_ref == "object-my-mug"
        assert rows[0].label == "my-mug"
        assert rows[0].category == "cup"
        assert rows[0].places == ("kitchen",)
        assert rows[0].saw_count == 1

    def test_verified_tier_records_too(self, tmp_path):
        rt, store, assoc = _runtime(tmp_path)
        rt.current_person = "Anna"
        rt.current_person_tier = "verified"
        _enroll_mug(store)
        rt.recognize_objects([("cup", [1.0, 0.0])], frame_id="f1")
        assert assoc.objects_with("person-anna") != []

    def test_repeated_sighting_coalesces(self, tmp_path):
        rt, store, assoc = _runtime(tmp_path)
        rt.current_person = "Anna"
        rt.current_person_tier = "recognized"
        _enroll_mug(store)
        rt.recognize_objects([("cup", [1.0, 0.0])], frame_id="f1")
        rt.recognize_objects([("cup", [1.0, 0.0])], frame_id="f2")
        rows = assoc.objects_with("person-anna")
        assert len(rows) == 1
        assert rows[0].saw_count == 2

    def test_placeholder_person_not_recorded(self, tmp_path):
        rt, store, assoc = _runtime(tmp_path)
        rt.current_person = "new-person-1"
        rt.current_person_tier = "unknown"
        _enroll_mug(store)
        rt.recognize_objects([("cup", [1.0, 0.0])], frame_id="f1")
        assert assoc.count() == 0

    def test_someone_not_recorded(self, tmp_path):
        rt, store, assoc = _runtime(tmp_path)
        rt.current_person = "someone"
        rt.current_person_tier = "unknown"
        _enroll_mug(store)
        rt.recognize_objects([("cup", [1.0, 0.0])], frame_id="f1")
        assert assoc.count() == 0

    def test_no_current_person_not_recorded(self, tmp_path):
        rt, store, assoc = _runtime(tmp_path)
        _enroll_mug(store)
        rt.recognize_objects([("cup", [1.0, 0.0])], frame_id="f1")
        assert assoc.count() == 0

    def test_privacy_off_skips_writes_without_error(self, tmp_path):
        rt, store, assoc = _runtime(tmp_path, privacy=False)
        rt.current_person = "Anna"
        rt.current_person_tier = "recognized"
        _enroll_mug(store)
        # recognition still works; the association write is silently refused
        decisions = rt.recognize_objects([("cup", [1.0, 0.0])], frame_id="f1")
        assert decisions and decisions[0]["recognized"] is True
        assert assoc.count() == 0

    def test_holding_matched_enrolled_object_records(self, tmp_path):
        rt, store, assoc = _runtime(tmp_path)
        rt.current_person = "Anna"
        rt.current_person_tier = "recognized"
        rt.recognize_object("my-mug", embedding=[1.0, 0.0], frame_id="f0")
        res = rt.note_person_holding("Anna", "cup", embedding=[1.0, 0.0], frame_id="f2")
        assert res["recognized"] is True
        rows = assoc.objects_with("person-anna")
        assert len(rows) == 1
        assert rows[0].object_ref == "object-my-mug"
        assert rows[0].category == "cup"

    def test_holding_novel_object_records_under_placeholder_ref(self, tmp_path):
        rt, store, assoc = _runtime(tmp_path)
        rt.current_person = "Anna"
        rt.current_person_tier = "recognized"
        res = rt.note_person_holding("Anna", "lamp", embedding=[0.0, 1.0], frame_id="f3")
        assert res["enrolled"] is True
        rows = assoc.objects_with("person-anna")
        assert len(rows) == 1
        assert rows[0].object_ref == "object-new-object-1"
        assert rows[0].category == "lamp"


class TestSnapshotAndRename:
    def test_snapshot_includes_recognized_person_associations(self, tmp_path):
        rt, store, assoc = _runtime(tmp_path)
        rt.current_person = "Anna"
        rt.current_person_tier = "recognized"
        _enroll_mug(store)
        rt.recognize_objects([("cup", [1.0, 0.0])], frame_id="f1")

        snap = rt.snapshot()
        assert "associations" in snap
        assert snap["associations"][0]["object_ref"] == "object-my-mug"

    def test_snapshot_associations_empty_for_unknown_person(self, tmp_path):
        rt, _, _ = _runtime(tmp_path)
        rt.current_person = "someone"
        rt.current_person_tier = "unknown"
        assert rt.snapshot()["associations"] == []

    def test_snapshot_associations_empty_without_store(self, tmp_path):
        detector = DeterministicObjectDetector(scripted={})
        rt = MultimodalRuntime(
            driver=BrainDriver(), detector=detector,
            recognition=RecognitionStore(tmp_path / "r.db"),
        )
        rt.current_person = "Anna"
        rt.current_person_tier = "recognized"
        assert rt.snapshot()["associations"] == []

    def test_name_person_merges_association_memory(self, tmp_path):
        rt, store, assoc = _runtime(tmp_path)
        # co-occurrence accumulated while the placeholder "new-person-1" was current
        rt.current_person = "new-person-1"
        rt.current_person_tier = "recognized"
        _enroll_mug(store)
        rt.recognize_objects([("cup", [1.0, 0.0])], frame_id="f1")
        assert assoc.objects_with("person-new-person-1") != []

        out = rt.name_person("new-person-1", "Anna")
        assert out["person_id"] == "person-anna"
        assert assoc.objects_with("person-anna") != []
        assert assoc.objects_with("person-new-person-1") == []
