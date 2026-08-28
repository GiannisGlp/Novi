"""Tests: MultimodalRuntime wires ObservationRecorder (recognition plan §4.2).

Sightings must stream durably into the observations store as recognition
produces them:

- a recognized object instance becomes an OBJECT observation stamped with the
  current place and its entity_ref (the matched object id);
- an unresolved (novel) object becomes a stable OBJECT observation under the
  per-label unresolved ref, so repeated views coalesce (unbounded-free);
- a recognized/verified face becomes a FACE observation under the person id;
- when privacy is off, face sightings are refused but object sightings still
  record (biometric vs non-biometric boundary).
"""

from __future__ import annotations

from novi.brain.agent import BrainDriver
from novi.brain.io import CameraFrame
from novi.integration.multimodal import MultimodalRuntime
from novi.integration.observation_recorder import ObservationRecorder
from novi.integration.recognition_store import RecognitionKind, RecognitionStore
from novi.perception.detection import DeterministicObjectDetector
from novi.perception.faces import FaceIdentifier


def _frame(fid: str) -> CameraFrame:
    return CameraFrame(frame_id=fid, captured_at=f"t-{fid}", width=64, height=48, payload=b"")


def _runtime(tmp_path, *, privacy: bool = True):
    detector = DeterministicObjectDetector(
        scripted={"all": [("cup", 0.9, (10, 10, 8, 12)), ("book", 0.9, (40, 10, 8, 12))]}
    )
    faces = FaceIdentifier(tau_match=0.90, tau_ambig=0.75, privacy_enabled=privacy)
    store = RecognitionStore(tmp_path / "rec.db")
    obs = ObservationRecorder(tmp_path / "obs.db")
    obs.set_privacy(privacy, reason="test")
    driver = BrainDriver()
    rt = MultimodalRuntime(driver=driver, detector=detector, face_identifier=faces,
                           recognition=store, observations=obs)
    rt.current_place = "kitchen"
    return rt, faces, store, obs


class TestObjectSightings:
    def test_recognized_object_written_as_durable_sighting(self, tmp_path):
        rt, _, store, obs = _runtime(tmp_path)
        rt.recognize_object("my-mug", embedding=[1.0, 0.0], frame_id="f0")
        store.enroll(kind=RecognitionKind.OBJECT, label="my-mug",
                     embedding=[1.0, 0.0], person_id="object-my-mug", frame_id="f0")
        rt.recognize_objects([("cup", [1.0, 0.0])], frame_id="f1")

        last = obs.last_sighting(RecognitionKind.OBJECT, "object-my-mug")
        assert last is not None
        assert last.place == "kitchen" and last.label == "my-mug"

    def test_novel_object_coalesces_under_unresolved_ref(self, tmp_path):
        rt, _, _, obs = _runtime(tmp_path)
        rt.recognize_objects([("cup", [1.0, 0.0])], frame_id="f1")
        rt.recognize_objects([("cup", [1.0, 0.0])], frame_id="f2")
        rows = obs.all(kind=RecognitionKind.OBJECT)
        assert len(rows) == 1
        assert rows[0].entity_ref == "object-unresolved-cup"
        assert rows[0].frame_ref == "f2", "last-seen coalesced to the newest frame"


class TestFaceSightings:
    def test_recognized_face_written_under_person_id(self, tmp_path):
        rt, faces, _, obs = _runtime(tmp_path)
        rt.recognize_person("Anna", face_embedding=[1.0, 0.0], frame_id="f0")
        rt.process_camera_frame(_frame("f1"), face_embedding=[1.0, 0.0])
        last = obs.last_sighting(RecognitionKind.FACE, "person-anna")
        assert last is not None and last.place == "kitchen" and last.label == "Anna"

    def test_face_biometric_refused_when_privacy_off_objects_still_record(self, tmp_path):
        rt, faces, _, obs = _runtime(tmp_path, privacy=True)
        # enroll while privacy is on so the enrollment exists
        rt.recognize_person("Anna", face_embedding=[1.0, 0.0], frame_id="f0")
        # now disable privacy: face processing (and sightings) must stop,
        # while non-biometric object sightings still record
        rt.faces.set_privacy(False, reason="test")
        obs.set_privacy(False, reason="test")
        # face processing is silently skipped while privacy is off
        obs_out = rt.process_camera_frame(_frame("f1"), face_embedding=[1.0, 0.0])
        assert obs_out.identities == []
        assert obs.last_sighting(RecognitionKind.FACE, "person-anna") is None
        rt.recognize_objects([("cup", [1.0, 0.0])], frame_id="f1")
        assert obs.last_sighting(RecognitionKind.OBJECT, "object-unresolved-cup") is not None


class TestNamingLoopAndAutoPlace:
    def test_naming_proposal_rebinds_history(self, tmp_path):
        rt, faces, store, obs = _runtime(tmp_path)
        # a novel object appears, then a person names it
        rt.recognize_objects([("cup", [1.0, 0.0])], frame_id="f1")
        assert obs.last_sighting(RecognitionKind.OBJECT, "object-unresolved-cup") is not None
        # name it: enroll + rebind history
        res = rt.name_proposal_object("cup", "my-mug", embedding=[1.0, 0.0], frame_id="f2")
        assert res["object_id"] == "object-my-mug" and res["rebound"] >= 1
        assert obs.last_sighting(RecognitionKind.OBJECT, "object-my-mug") is not None
        assert obs.last_sighting(RecognitionKind.OBJECT, "object-unresolved-cup") is None

    def test_auto_place_enrolls_stable_scene(self, tmp_path):
        detector = DeterministicObjectDetector(
            scripted={
                "p0": [("book", 0.9, (10, 10, 8, 12)), ("lamp", 0.9, (40, 10, 8, 12))],
                "p1": [("book", 0.9, (10, 10, 8, 12)), ("lamp", 0.9, (40, 10, 8, 12))],
                "p2": [("book", 0.9, (10, 10, 8, 12)), ("lamp", 0.9, (40, 10, 8, 12))],
            }
        )
        store = RecognitionStore(tmp_path / "rec.db")
        obs = ObservationRecorder(tmp_path / "obs.db")
        rt = MultimodalRuntime(driver=BrainDriver(), detector=detector, recognition=store,
                               observations=obs, place_auto_enroll=True)
        # a stable scene across 3 frames triggers auto-enrollment as a place
        for i in range(3):
            rt.process_camera_frame(_frame(f"p{i}"))
        assert rt.current_place and "-room" in rt.current_place
        # subsequent observation in that scene carries the auto place
        rt.recognize_objects([("book", [1.0, 0.0])], frame_id="f99")
        last = obs.last_sighting(RecognitionKind.OBJECT, "object-unresolved-book")
        assert last is not None and last.place == rt.current_place

    def test_auto_place_can_be_disabled(self, tmp_path):
        detector = DeterministicObjectDetector(
            scripted={
                "p0": [("book", 0.9, (10, 10, 8, 12))],
                "p1": [("book", 0.9, (10, 10, 8, 12))],
                "p2": [("book", 0.9, (10, 10, 8, 12))],
            }
        )
        store = RecognitionStore(tmp_path / "rec.db")
        rt = MultimodalRuntime(driver=BrainDriver(), detector=detector,
                               recognition=store, place_auto_enroll=False)
        for i in range(3):
            rt.process_camera_frame(_frame(f"p{i}"))
        assert rt.current_place == ""
