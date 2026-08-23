"""Tests: PerceptionPipeline — frame -> detect -> track (+face stage).

Wiring contract:
- process_frame returns a WorldObservation with detections, active tracks,
  and face identity decisions, all carrying frame provenance;
- world-state entity updates keep first/last_seen coherent across frames;
- privacy off disables the face stage but detection still runs;
- pipeline snapshot exposes track + health telemetry.
"""

from __future__ import annotations

from novi.brain.io import CameraFrame
from novi.perception.detection import DeterministicObjectDetector
from novi.perception.faces import FaceIdentifier, IdentityTier
from novi.perception.pipeline import PerceptionPipeline


def _frame(fid: str) -> CameraFrame:
    return CameraFrame(frame_id=fid, captured_at=f"t-{fid}", width=640, height=480, payload=b"")


ANNA = [1.0, 0.0, 0.0, 0.0]


def _build(**kw):
    detector = DeterministicObjectDetector(
        scripted={
            "f1": [("cup", 0.91, (100, 100, 80, 120))],
            "f2": [("cup", 0.88, (104, 102, 80, 120))],
        }
    )
    faces = FaceIdentifier()
    pipe = PerceptionPipeline(detector=detector, face_identifier=faces, **kw)
    return pipe, faces


class TestWorldObservation:
    def test_detections_and_tracks_flow_through(self):
        pipe, _ = _build()
        obs1 = pipe.process_frame(_frame("f1"))
        assert [d.label for d in obs1.detections] == ["cup"]
        assert len(obs1.tracks) == 1
        assert obs1.frame_id == "f1"

        obs2 = pipe.process_frame(_frame("f2"))
        assert len(obs2.tracks) == 1
        assert obs2.tracks[0].track_id == obs1.tracks[0].track_id, "same cup keeps its track"
        assert (obs2.tracks[0].first_frame_id, obs2.tracks[0].last_frame_id) == ("f1", "f2")

    def test_face_stage_runs_when_face_embedding_supplied(self):
        pipe, faces = _build()
        anna = faces.enroll("Anna", ANNA, frame_id="f0")
        obs = pipe.process_frame(_frame("f1"), face_embedding=ANNA)
        assert len(obs.identities) == 1
        assert obs.identities[0].tier is IdentityTier.RECOGNIZED
        assert obs.identities[0].person_id == anna

    def test_no_face_embedding_no_identity_entries(self):
        pipe, _ = _build()
        obs = pipe.process_frame(_frame("f1"))
        assert obs.identities == []

    def test_privacy_off_disables_face_stage_only(self):
        pipe, faces = _build()
        faces.set_privacy(False, reason="test")
        obs = pipe.process_frame(_frame("f1"), face_embedding=ANNA)
        assert obs.identities == []          # biometrics refused
        assert [d.label for d in obs.detections] == ["cup"]  # objects still seen

    def test_provenance_on_everything(self):
        pipe, faces = _build()
        obs = pipe.process_frame(_frame("f1"), face_embedding=ANNA)
        for d in obs.detections:
            assert d.frame_id == "f1"
        for t in obs.tracks:
            assert t.last_frame_id == "f1"
        for i in obs.identities:
            assert i.frame_id == "f1"
        assert obs.captured_at.startswith("t-f1")


class TestSnapshotAndCounts:
    def test_snapshot_reports_tracks_and_frames(self):
        pipe, _ = _build()
        pipe.process_frame(_frame("f1"))
        snap = pipe.snapshot()
        assert snap["frames_processed"] == 1
        assert snap["track_count"] == 1
