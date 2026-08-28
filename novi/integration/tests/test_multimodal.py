"""Tests: MultimodalRuntime — the engine integration bridge (doc 16 §2).

Binds novi.voice + novi.perception + RecognitionStore into one runtime
that drives a BrainDriver:

- process_camera_frame: perception runs, recognized faces become person
  context for subsequent replies; unknown faces propose enrollment;
- voice_turn: transcript -> brain.hear(voice) with recognized speaker
  identity attached;
- current_place: descriptor lookup tags observations with place labels;
- every turn emits an event trail for the web UI.
"""

from __future__ import annotations

from novi.brain.agent import BrainDriver
from novi.brain.io import CameraFrame
from novi.integration.multimodal import MultimodalRuntime
from novi.integration.observation_recorder import ObservationRecorder
from novi.integration.recognition_store import RecognitionKind, RecognitionStore
from novi.perception.detection import DeterministicObjectDetector
from novi.perception.faces import FaceIdentifier, IdentityTier


def _frame(fid: str) -> CameraFrame:
    return CameraFrame(frame_id=fid, captured_at=f"t-{fid}", width=64, height=48, payload=b"")


ANNA_FACE = [1.0, 0.0]


def _runtime(tmp_path):
    detector = DeterministicObjectDetector(
        scripted={
            "f1": [("cup", 0.9, (10, 10, 8, 12))],
            "f2": [("cup", 0.9, (11, 11, 8, 12))],
        }
    )
    faces = FaceIdentifier(tau_match=0.90, tau_ambig=0.75)
    store = RecognitionStore(tmp_path / "rec.db")
    driver = BrainDriver()
    rt = MultimodalRuntime(driver=driver, detector=detector, face_identifier=faces, recognition=store)
    return rt, faces, store


class TestCameraIntegration:
    def test_frame_produces_world_observation_and_event(self, tmp_path):
        rt, _, _ = _runtime(tmp_path)
        obs = rt.process_camera_frame(_frame("f1"))
        assert [d.label for d in obs.detections] == ["cup"]
        assert rt.events[-1]["kind"] == "perception.frame"

    def test_enrolled_face_recognized_and_used_as_person(self, tmp_path):
        rt, faces, store = _runtime(tmp_path)
        rt.recognize_person("Anna", face_embedding=ANNA_FACE, frame_id="f0")

        obs = rt.process_camera_frame(_frame("f1"), face_embedding=ANNA_FACE)
        assert obs.identities[0].tier is IdentityTier.RECOGNIZED
        assert rt.current_person == "Anna", "recognized face becomes conversation context"

        # The brain reply path now knows who is present.
        out = rt.say("hello", via_voice=False)
        assert out["person"] == "Anna"

    def test_identity_recognized_staged_for_bus(self, tmp_path):
        """GAP-1b: a recognized face must reach the brain's input bus."""
        rt, _, _ = _runtime(tmp_path)
        rt.recognize_person("Anna", face_embedding=ANNA_FACE, frame_id="f0")
        rt.process_camera_frame(_frame("f1"), face_embedding=ANNA_FACE)
        kinds = [e["kind"] for e in rt.pop_pending_events()]
        assert "identity.recognized" in kinds

    def test_object_recognized_staged_for_bus(self, tmp_path):
        """GAP-1b: a recognized object must reach the brain's input bus."""
        rt, _, _ = _runtime(tmp_path)
        rt.recognize_object("my mug", embedding=[1.0, 0.0], frame_id="f0")
        rt.recognize_objects([("cup", [1.0, 0.0])], frame_id="f1")
        kinds = [e["kind"] for e in rt.pop_pending_events()]
        assert "object.recognized" in kinds

    def test_unknown_face_proposes_enrollment_once_flagged(self, tmp_path):
        rt, _, _ = _runtime(tmp_path)
        obs = rt.process_camera_frame(_frame("f1"), face_embedding=[0.0, 1.0])
        assert obs.identities[0].new_person_proposal is True
        assert rt.pending_enrollment_proposal is True

    def test_place_auto_enrolls_after_stable_landmarks(self, tmp_path):
        """GAP-2: a stable landmark set seen 3+ frames auto-enrolls a place."""
        rt, _, _ = _runtime(tmp_path)
        rt._place_auto_enroll = True
        for _ in range(3):
            rt.process_camera_frame(_frame("f1"))  # f1 scripted: ["cup"]
        assert rt.current_place == "cup-room"
        assert any(e["kind"] == "place.auto_enrolled" for e in rt.events)

    def test_place_does_not_auto_enroll_when_disabled(self, tmp_path):
        rt, _, _ = _runtime(tmp_path)
        for _ in range(3):
            rt.process_camera_frame(_frame("f1"))
        assert rt.current_place == ""
        assert not any(e["kind"] == "place.auto_enrolled" for e in rt.events)


class TestVoiceIntegration:
    def test_voice_turn_reaches_brain_with_speaker(self, tmp_path):
        rt, _, _ = _runtime(tmp_path)
        result = rt.voice_turn(text="hello novi", speaker_label=None)
        assert result["ok"] is True
        assert result["reply"], "brain must answer"

    def test_known_speaker_label_attached(self, tmp_path):
        rt, _, _ = _runtime(tmp_path)
        res = rt.voice_turn(text="what do you see", speaker_label="Anna")
        assert res["person"] == "Anna"


class TestObjectRecognition:
    def test_recognize_object_enrolls_under_canonical_id(self, tmp_path):
        rt, _, store = _runtime(tmp_path)
        oid = rt.recognize_object("my mug", embedding=[1.0, 0.0], frame_id="f0")
        assert oid == "object-my-mug"
        m = store.match(RecognitionKind.OBJECT, [1.0, 0.0])
        assert m is not None and m.label == "my mug"
        assert rt.events[-1]["kind"] == "object.enrolled"

    def test_recognize_objects_recognized_vs_proposal(self, tmp_path):
        rt, _, store = _runtime(tmp_path)
        rt.recognize_object("my mug", embedding=[1.0, 0.0], frame_id="f0")
        decisions = rt.recognize_objects([("cup", [1.0, 0.0]), ("book", [0.0, 1.0])])
        assert decisions[0]["recognized"] is True and decisions[0]["object"] == "my mug"
        assert decisions[1]["recognized"] is False and decisions[1]["object"] is None
        assert rt.current_objects == ["my mug"]

    def test_recognize_objects_no_store_returns_empty(self, tmp_path):
        detector = DeterministicObjectDetector(scripted={})
        faces = FaceIdentifier(tau_match=0.90, tau_ambig=0.75)
        rt = MultimodalRuntime(driver=BrainDriver(), detector=detector, face_identifier=faces, recognition=None)
        assert rt.recognize_objects([("cup", [1.0, 0.0])]) == []

    def test_objects_surface_in_snapshot(self, tmp_path):
        rt, _, _ = _runtime(tmp_path)
        rt.recognize_object("my mug", embedding=[1.0, 0.0], frame_id="f0")
        rt.recognize_objects([("cup", [1.0, 0.0])])
        assert rt.snapshot()["objects"] == ["my mug"]

    def test_reenrollment_replaces_previous_embedding(self, tmp_path):
        rt, _, store = _runtime(tmp_path)
        rt.recognize_object("my mug", embedding=[1.0, 0.0], frame_id="f0")
        rt.recognize_object("my mug", embedding=[0.0, 1.0], frame_id="f1")
        rows = store.all(RecognitionKind.OBJECT)
        assert len(rows) == 1, "re-enrollment must upsert, not duplicate"
        m = store.match(RecognitionKind.OBJECT, [0.0, 1.0])
        assert m is not None and m.label == "my mug"

    def test_object_events_fire_on_transitions_not_every_frame(self, tmp_path):
        rt, _, _ = _runtime(tmp_path)
        rt.recognize_object("my mug", embedding=[1.0, 0.0], frame_id="f0")
        # same object seen repeatedly: recognized fires once, then stays quiet
        rt.recognize_objects([("cup", [1.0, 0.0])])
        rt.recognize_objects([("cup", [1.0, 0.0])])
        rt.recognize_objects([("cup", [1.0, 0.0])])
        recognized = [e for e in rt.events if e["kind"] == "object.recognized"]
        assert len(recognized) == 1
        # object leaves and returns: proposal fires once per appearance
        rt.recognize_objects([("book", [0.0, 1.0])])  # new label -> proposal
        rt.recognize_objects([("book", [0.0, 1.0])])  # same frame state -> quiet
        proposals = [e for e in rt.events if e["kind"] == "object.proposal"]
        assert len(proposals) == 1


class TestPersonHolding:
    """Person-object co-occurrence (plan 20 WS5): held object resolve + novelty."""

    def test_known_object_stages_person_holding(self, tmp_path):
        rt, _, store = _runtime(tmp_path)
        rt.recognize_object("my mug", embedding=[1.0, 0.0], frame_id="f0")
        res = rt.note_person_holding("Anna", "mug", embedding=[1.0, 0.0], frame_id="f1")
        assert res == {"person": "Anna", "object": "my mug", "recognized": True, "enrolled": False}
        holding = [e for e in rt.events if e["kind"] == "person.holding"]
        assert len(holding) == 1
        assert holding[0]["person"] == "Anna"
        assert holding[0]["object"] == "my mug"
        assert not any(e["kind"] == "object.novel" for e in rt.events)

    def test_novel_object_auto_enrolls_and_stages_object_novel(self, tmp_path):
        rt, _, store = _runtime(tmp_path)
        rt.recognize_object("my mug", embedding=[1.0, 0.0], frame_id="f0")
        res = rt.note_person_holding("Anna", "cup", embedding=[0.0, 1.0], frame_id="f1")
        assert res["enrolled"] is True and res["recognized"] is False
        assert res["object"] == "new-object-1"
        m = store.match(RecognitionKind.OBJECT, [0.0, 1.0])
        assert m is not None and m.label == "new-object-1"
        assert m.person_id == "object-new-object-1"
        novel = [e for e in rt.events if e["kind"] == "object.novel"]
        assert len(novel) == 1
        assert novel[0]["object"] == "new-object-1"
        assert novel[0]["novelty"] == 1.0

    def test_novel_placeholders_number_sequentially(self, tmp_path):
        rt, _, _ = _runtime(tmp_path)
        rt.note_person_holding("Anna", "cup", embedding=[0.0, 1.0], frame_id="f1")
        rt.note_person_holding("Bob", "book", embedding=[0.0, 0.0], frame_id="f2")
        assert rt.events[-1]["object"] == "new-object-2"

    def test_no_store_is_a_safe_noop(self, tmp_path):
        detector = DeterministicObjectDetector(scripted={})
        faces = FaceIdentifier(tau_match=0.90, tau_ambig=0.75)
        rt = MultimodalRuntime(driver=BrainDriver(), detector=detector, face_identifier=faces, recognition=None)
        res = rt.note_person_holding("Anna", "cup", embedding=[1.0, 0.0])
        assert res == {"person": "Anna", "object": "cup", "recognized": False, "enrolled": False}


class TestPlaceAndPersistence:
    def test_place_lookup_tags_events(self, tmp_path):
        rt, _, store = _runtime(tmp_path)
        store.enroll(kind=RecognitionKind.PLACE, label="kitchen",
                     descriptor={"landmarks": ["cup"]}, provenance={"source": "slam"})
        rt.process_camera_frame(_frame("f1"))
        assert rt.current_place == "kitchen"
        assert rt.events[-1].get("place") == "kitchen"

    def test_recognition_persists_across_runtimes(self, tmp_path):
        rt, _, store = _runtime(tmp_path)
        store.enroll(kind=RecognitionKind.PLACE, label="kitchen",
                     descriptor={"landmarks": ["cup"]}, provenance={"source": "slam"})
        path = tmp_path / "rec.db"
        store.close()
        store2 = RecognitionStore(path)
        assert store2.lookup_by_descriptor(RecognitionKind.PLACE, {"landmarks": ["cup"]})


class TestAutoEnrollAndNaming:
    """Unknown faces auto-enroll as placeholders; introductions bind the name."""

    def test_unknown_face_auto_enrolls_placeholder(self, tmp_path):
        rt, faces, store = _runtime(tmp_path)
        rt.process_camera_frame(_frame("f1"), face_embedding=[0.0, 1.0])
        assert rt.current_person == "new-person-1"
        rows = store.all(RecognitionKind.FACE)
        assert len(rows) == 1
        assert rows[0]["person_id"] == "person-new-person-1"
        assert rows[0]["label"] == "new-person-1"
        assert any(e["kind"] == "identity.auto_enrolled" for e in rt.events)
        # next frame the placeholder is recognized, not re-proposed
        obs = rt.process_camera_frame(_frame("f2"), face_embedding=[0.0, 1.0])
        assert obs.identities[0].tier is IdentityTier.RECOGNIZED

    def test_same_unknown_face_not_re_enrolled_each_frame(self, tmp_path):
        rt, _, store = _runtime(tmp_path)
        rt.process_camera_frame(_frame("f1"), face_embedding=[0.0, 1.0])
        # a slightly different embedding of the same face (cosine ~0.99)
        rt.process_camera_frame(_frame("f2"), face_embedding=[0.01, 0.99995])
        assert len(store.all(RecognitionKind.FACE)) == 1, "one placeholder per face"

    def test_distinct_unknown_face_gets_its_own_placeholder(self, tmp_path):
        rt, _, store = _runtime(tmp_path)
        rt.process_camera_frame(_frame("f1"), face_embedding=[0.0, 1.0])
        # wait for the first placeholder to be recognized so a new proposal is fresh
        rt.process_camera_frame(_frame("f2"), face_embedding=[0.0, 1.0])
        # second, genuinely different face (cosine ~0)
        rt.process_camera_frame(_frame("f3"), face_embedding=[1.0, 0.0])
        assert len(store.all(RecognitionKind.FACE)) == 2
        assert sorted(r["label"] for r in store.all(RecognitionKind.FACE)) == [
            "new-person-1",
            "new-person-2",
        ]

    def test_known_face_recalled_from_store_after_restart(self, tmp_path):
        path = tmp_path / "rec.db"
        store = RecognitionStore(path)
        rt = MultimodalRuntime(driver=BrainDriver(), detector=DeterministicObjectDetector(scripted={}),
                               face_identifier=FaceIdentifier(), recognition=store)
        rt.recognize_person("Anna", face_embedding=ANNA_FACE, frame_id="f0")
        store.close()
        # a fresh runtime over the same durable store has no in-memory faces
        store2 = RecognitionStore(path)
        rt2 = MultimodalRuntime(driver=BrainDriver(), detector=DeterministicObjectDetector(scripted={}),
                                face_identifier=FaceIdentifier(), recognition=store2)
        obs = rt2.process_camera_frame(_frame("f1"), face_embedding=ANNA_FACE)
        assert rt2.current_person == "Anna", "store recall binds the known name, not a placeholder"
        assert obs.identities[0].new_person_proposal is True  # this frame still proposed
        assert not any(e["kind"] == "identity.auto_enrolled" for e in rt2.events)
        # and the face is recognized from the next frame on
        obs2 = rt2.process_camera_frame(_frame("f2"), face_embedding=ANNA_FACE)
        assert obs2.identities[0].tier is IdentityTier.RECOGNIZED

    def test_name_person_renames_store_and_sightings(self, tmp_path):
        obs = ObservationRecorder(tmp_path / "obs.db")
        rt, _, store = _runtime(tmp_path)
        rt.observations = obs
        rt.process_camera_frame(_frame("f1"), face_embedding=[0.0, 1.0])
        assert rt.current_person == "new-person-1"
        # the recognized placeholder frame records a durable sighting under the
        # placeholder ref — the naming loop then re-keys it to the real name
        rt.process_camera_frame(_frame("f2"), face_embedding=[0.0, 1.0])
        assert len(obs.all(RecognitionKind.FACE)) == 1
        res = rt.name_person("new-person-1", "Anna")
        assert res["person_id"] == "person-anna"
        rows = store.all(RecognitionKind.FACE)
        assert len(rows) == 1 and rows[0]["label"] == "Anna" and rows[0]["person_id"] == "person-anna"
        assert rt.current_person == "Anna"
        # sighting bound to the placeholder was re-keyed to the canonical id
        sightings = obs.all(RecognitionKind.FACE)
        assert len(sightings) == 1
        assert sightings[0].entity_ref == "person-anna"
        # the face now resolves to the real name
        obs2 = rt.process_camera_frame(_frame("f3"), face_embedding=[0.0, 1.0])
        assert obs2.identities[0].tier is IdentityTier.RECOGNIZED
        assert rt.current_person == "Anna"

    def test_name_person_on_unknown_placeholder_moves_nothing(self, tmp_path):
        rt, _, _ = _runtime(tmp_path)
        res = rt.name_person("new-person-9", "Bob")
        assert res["moved"] == 0
        assert res["person_id"] == "person-bob"
