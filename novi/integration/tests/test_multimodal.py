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

    def test_unknown_face_proposes_enrollment_once_flagged(self, tmp_path):
        rt, _, _ = _runtime(tmp_path)
        obs = rt.process_camera_frame(_frame("f1"), face_embedding=[0.0, 1.0])
        assert obs.identities[0].new_person_proposal is True
        assert rt.pending_enrollment_proposal is True


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
