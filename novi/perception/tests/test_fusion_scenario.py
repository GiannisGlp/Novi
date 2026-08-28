"""Doc-02 §3 acceptance: multi-channel fusion.

> person walks in -> face detect -> recognized: "Anna"
> Anna speaks     -> diarization + voiceprint -> same person (verified)
> Novi greets Anna by name while continuing to track objects;
> owner's chat message arrives mid-exchange -> turn_taking arbitrates (doc 15)

Perception half, simulated deterministically: Anna appears (unknown ->
recognized), speaks (verified via speaker id), objects keep their tracks
throughout, and an ambiguous stranger stays unknown.
"""

from __future__ import annotations

from novi.brain.io import CameraFrame
from novi.perception.detection import DeterministicObjectDetector
from novi.perception.faces import FaceIdentifier, IdentityTier
from novi.perception.pipeline import PerceptionPipeline

ANNA = [1.0, 0.0, 0.0, 0.0]
ANNA_VOICEPRINT = "vp-anna"   # diarization label bound to Anna upstream
STRANGER_AT_COS_082 = [0.82, 0.572577, 0.0, 0.0]  # between tau_ambig and tau_match


def _frame(fid: str) -> CameraFrame:
    return CameraFrame(frame_id=fid, captured_at=f"t-{fid}", width=640, height=480, payload=b"")


def _build() -> tuple[PerceptionPipeline, FaceIdentifier, str]:
    detector = DeterministicObjectDetector(
        scripted={
            "f-kitchen-1": [("cup", 0.91, (100, 100, 80, 120)), ("book", 0.84, (400, 220, 90, 40))],
            "f-anna-1": [("cup", 0.89, (100, 100, 80, 120))],
            "f-anna-2": [("cup", 0.90, (103, 101, 80, 120))],
        }
    )
    faces = FaceIdentifier(tau_match=0.90, tau_ambig=0.75)
    pipe = PerceptionPipeline(detector=detector, face_identifier=faces)
    anna_id = faces.enroll("Anna", ANNA, frame_id="f-past", quality=0.97)
    return pipe, faces, anna_id


class TestFusionScenario:
    def test_annas_journey_and_object_continuity(self):
        pipe, _, anna_id = _build()

        # --- beat 1: kitchen scene, nobody in frame -------------------------
        obs = pipe.process_frame(_frame("f-kitchen-1"))
        assert sorted(d.label for d in obs.detections) == ["book", "cup"]
        assert obs.identities == []
        cup_track = obs.tracks[[t.label for t in obs.tracks].index("cup")]

        # --- beat 2: Anna walks in; face seen but she is far/blurry ----------
        obs = pipe.process_frame(_frame("f-anna-1"), face_embedding=STRANGER_AT_COS_082)
        assert obs.identities[0].tier is IdentityTier.UNKNOWN
        assert obs.identities[0].reason == "ambiguous", "never best-guesses"

        # --- beat 3: closer now — recognized ---------------------------------
        obs = pipe.process_frame(_frame("f-anna-2"), face_embedding=ANNA)
        ident = obs.identities[0]
        assert ident.tier is IdentityTier.RECOGNIZED
        assert ident.person_id == anna_id

        # --- beat 4: Anna speaks — cross-modal escalation ---------------------
        obs = pipe.process_frame(_frame("f-anna-2"), face_embedding=ANNA, speaker_person_id=ANNA_VOICEPRINT)
        # speaker id must be the same enrolled person for verification:
        # in production the diarization->person binding maps vp-anna -> anna_id;
        # simulate that binding by passing the enrolled id directly.
        obs_verified = pipe.process_frame(_frame("f-anna-2"), face_embedding=ANNA, speaker_person_id=anna_id)
        assert obs_verified.identities[0].tier is IdentityTier.VERIFIED

        # --- object continuity throughout --------------------------------------
        cups = [t for t in pipe.tracker.all_tracks if t.label == "cup"]
        assert len(cups) == 1 and cups[0].track_id == cup_track.track_id
        snap = pipe.snapshot()
        assert snap["frames_processed"] == 5  # kitchen + ambiguous + recognized + verify + verify-replay

    def test_stranger_gets_proposal_not_identity(self):
        pipe, faces, _ = _build()
        stranger = [0.0, 0.0, 1.0, 0.0]
        obs = pipe.process_frame(_frame("f-kitchen-1"), face_embedding=stranger)
        d = obs.identities[0]
        assert d.tier is IdentityTier.UNKNOWN
        assert d.new_person_proposal is True, "enrollment happens via dialogue upstream"
