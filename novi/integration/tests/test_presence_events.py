"""Tests: MultimodalRuntime presence transitions + scene-change salience.

The runtime distills camera frames into brain-ready salience events:

- presence.entered / presence.left track who is in the room across an
  `absent_frames` hysteresis window; anonymous faces aggregate as
  'someone' and raw object detections never fabricate presence;
- scene.changed fires when the object-label set changes between
  consecutive frames, never on pure confidence jitter;
- pop_pending_events() drains those events atomically for the camera
  loop while .events keeps the full audit trail.
"""

from __future__ import annotations

import pytest

from novi.brain.agent import BrainDriver
from novi.brain.io import CameraFrame
from novi.integration.multimodal import MultimodalRuntime
from novi.integration.recognition_store import RecognitionStore
from novi.perception.detection import DeterministicObjectDetector
from novi.perception.faces import FaceIdentifier


ANNA_FACE = [1.0, 0.0]
STRANGER_FACE = [0.0, 1.0]


def _frame(fid: str) -> CameraFrame:
    return CameraFrame(frame_id=fid, captured_at=f"t-{fid}", width=64, height=48, payload=b"")


def _runtime(
    tmp_path,
    scripted=None,
    *,
    absent_frames: int = 2,
    scene_change_enabled: bool = True,
    with_faces: bool = True,
    enroll_anna: bool = False,
):
    detector = DeterministicObjectDetector(scripted=scripted or {})
    faces = FaceIdentifier(tau_match=0.90, tau_ambig=0.75) if with_faces else None
    store = RecognitionStore(tmp_path / "rec.db")
    rt = MultimodalRuntime(
        driver=BrainDriver(),
        detector=detector,
        face_identifier=faces,
        recognition=store,
        absent_frames=absent_frames,
        scene_change_enabled=scene_change_enabled,
    )
    if enroll_anna:
        rt.recognize_person("Anna", face_embedding=ANNA_FACE, frame_id="f0")
    return rt, faces, store


def _of_kind(events, kind):
    return [e for e in events if e["kind"] == kind]


class TestPresenceTransitions:
    def test_enter_fires_once_per_arrival_after_gap(self, tmp_path):
        rt, _, _ = _runtime(tmp_path, absent_frames=2, enroll_anna=True)

        rt.process_camera_frame(_frame("f1"), face_embedding=ANNA_FACE)  # arrival
        rt.process_camera_frame(_frame("f2"))  # absent
        rt.process_camera_frame(_frame("f3"))  # absent -> left fires here
        rt.process_camera_frame(_frame("f4"), face_embedding=ANNA_FACE)  # re-entry

        entered = _of_kind(rt.events, "presence.entered")
        left = _of_kind(rt.events, "presence.left")
        assert [e["person"] for e in entered] == ["Anna", "Anna"]
        assert [e["tier"] for e in entered] == ["recognized", "recognized"]
        assert [(e["person"]) for e in left] == ["Anna"]

    def test_left_fires_only_after_full_absence_window(self, tmp_path):
        rt, _, _ = _runtime(tmp_path, absent_frames=3, enroll_anna=True)
        rt.process_camera_frame(_frame("f1"), face_embedding=ANNA_FACE)
        rt.process_camera_frame(_frame("f2"))
        rt.process_camera_frame(_frame("f3"))
        assert _of_kind(rt.events, "presence.left") == [], "hysteresis window not yet exceeded"
        rt.process_camera_frame(_frame("f4"))
        left = _of_kind(rt.events, "presence.left")
        assert [(e["person"]) for e in left] == ["Anna"]

    def test_repeated_same_person_frames_do_not_spam(self, tmp_path):
        rt, _, _ = _runtime(tmp_path, absent_frames=2, enroll_anna=True)
        for i in range(1, 6):
            rt.process_camera_frame(_frame(f"f{i}"), face_embedding=ANNA_FACE)
        assert len(_of_kind(rt.events, "presence.entered")) == 1, "enter must fire once"
        assert _of_kind(rt.events, "presence.left") == []

    def test_brief_occlusion_does_not_cycle_presence(self, tmp_path):
        # Absent fewer than absent_frames frames -> no left/enter churn.
        rt, _, _ = _runtime(tmp_path, absent_frames=3, enroll_anna=True)
        rt.process_camera_frame(_frame("f1"), face_embedding=ANNA_FACE)
        rt.process_camera_frame(_frame("f2"))
        rt.process_camera_frame(_frame("f3"), face_embedding=ANNA_FACE)  # back in time
        assert _of_kind(rt.events, "presence.entered") and len(
            _of_kind(rt.events, "presence.entered")
        ) == 1
        assert _of_kind(rt.events, "presence.left") == []

    def test_anonymous_face_counts_as_someone(self, tmp_path):
        rt, _, _ = _runtime(tmp_path, absent_frames=2)
        rt.process_camera_frame(_frame("f1"), face_embedding=STRANGER_FACE)
        rt.process_camera_frame(_frame("f2"), face_embedding=STRANGER_FACE)  # no dupe

        entered = _of_kind(rt.events, "presence.entered")
        assert [(e["person"], e["tier"]) for e in entered] == [("someone", "unknown")]

        rt.process_camera_frame(_frame("f3"))
        rt.process_camera_frame(_frame("f4"))
        assert [(e["person"]) for e in _of_kind(rt.events, "presence.left")] == ["someone"]

    def test_no_presence_without_identity_decision(self, tmp_path):
        # Faces configured but no embedding supplied: a face stage that never
        # ran must never fabricate 'someone'.
        scripted = {"f1": [("cup", 0.9, (1, 1, 4, 4))]}
        rt, _, _ = _runtime(tmp_path, scripted=scripted)
        rt.process_camera_frame(_frame("f1"))
        assert _of_kind(rt.events, "presence.entered") == []
        assert _of_kind(rt.events, "presence.left") == []

    def test_no_face_identifier_stays_silent(self, tmp_path):
        scripted = {"f1": [("cup", 0.9, (1, 1, 4, 4))], "f2": [("book", 0.9, (30, 30, 4, 4))]}
        rt, faces, _ = _runtime(tmp_path, scripted=scripted, with_faces=False)
        assert faces is None
        rt.process_camera_frame(_frame("f1"), face_embedding=[1.0, 0.0])
        rt.process_camera_frame(_frame("f2"), face_embedding=[1.0, 0.0])
        assert _of_kind(rt.events, "presence.entered") == []
        assert _of_kind(rt.events, "presence.left") == []


class TestSceneChangeSalience:
    def test_scene_changed_reports_appeared_and_disappeared(self, tmp_path):
        scripted = {
            "f1": [("cup", 0.9, (1, 1, 4, 4))],
            "f2": [("cup", 0.9, (1, 1, 4, 4)), ("book", 0.8, (20, 20, 6, 6))],
            "f3": [("book", 0.8, (20, 20, 6, 6))],
        }
        rt, _, _ = _runtime(tmp_path, scripted=scripted)
        rt.process_camera_frame(_frame("f1"))  # baseline: no event
        rt.process_camera_frame(_frame("f2"))
        rt.process_camera_frame(_frame("f3"))

        changes = _of_kind(rt.events, "scene.changed")
        assert changes == [
            {"kind": "scene.changed", "appeared": ["book"], "disappeared": []},
            {"kind": "scene.changed", "appeared": [], "disappeared": ["cup"]},
        ]

    def test_confidence_jitter_does_not_fire(self, tmp_path):
        scripted = {
            "f1": [("cup", 0.9, (1, 1, 4, 4)), ("cup", 0.71, (30, 30, 4, 4))],
            "f2": [("cup", 0.65, (2, 2, 4, 4)), ("cup", 0.98, (31, 31, 4, 4))],
        }
        rt, _, _ = _runtime(tmp_path, scripted=scripted)
        rt.process_camera_frame(_frame("f1"))
        rt.process_camera_frame(_frame("f2"))
        assert _of_kind(rt.events, "scene.changed") == [], "same label set is not a scene change"

    def test_scene_change_can_be_disabled(self, tmp_path):
        scripted = {"f1": [("cup", 0.9, (1, 1, 4, 4))], "f2": [("book", 0.9, (30, 30, 4, 4))]}
        rt, _, _ = _runtime(tmp_path, scripted=scripted, scene_change_enabled=False)
        rt.process_camera_frame(_frame("f1"))
        rt.process_camera_frame(_frame("f2"))
        assert _of_kind(rt.events, "scene.changed") == []

    def test_scene_change_works_without_face_identifier(self, tmp_path):
        scripted = {
            "f1": [("cup", 0.9, (1, 1, 4, 4))],
            "f2": [("cup", 0.9, (1, 1, 4, 4)), ("lamp", 0.85, (9, 9, 3, 3))],
        }
        rt, _, _ = _runtime(tmp_path, scripted=scripted, with_faces=False)
        rt.process_camera_frame(_frame("f1"))
        rt.process_camera_frame(_frame("f2"))
        assert _of_kind(rt.events, "scene.changed") == [
            {"kind": "scene.changed", "appeared": ["lamp"], "disappeared": []}
        ]


class TestPopPendingEvents:
    def test_pop_drains_atomically_and_keeps_audit_trail(self, tmp_path):
        scripted = {"f1": [("cup", 0.9, (1, 1, 4, 4))], "f2": [("book", 0.9, (30, 30, 4, 4))]}
        rt, _, _ = _runtime(tmp_path, scripted=scripted, absent_frames=2)
        rt.process_camera_frame(_frame("f1"), face_embedding=STRANGER_FACE)  # someone enters
        rt.process_camera_frame(_frame("f2"), face_embedding=STRANGER_FACE)  # scene changes

        staged = rt.pop_pending_events()
        assert [e["kind"] for e in staged] == ["presence.entered", "scene.changed"]
        assert staged[0]["person"] == "someone"
        assert staged[1]["appeared"] == ["book"]

        assert rt.pop_pending_events() == [], "second pop must be empty after drain"

        trail_kinds = {e["kind"] for e in rt.events}
        assert {"presence.entered", "scene.changed"} <= trail_kinds, "audit trail keeps them"

    def test_absent_frames_must_be_positive(self, tmp_path):
        with pytest.raises(ValueError):
            _runtime(tmp_path, absent_frames=0)
