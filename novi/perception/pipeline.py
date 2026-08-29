"""PerceptionPipeline: frame -> detect -> track (+ optional face stage).

Doc-01/02 wiring: one call per frame produces a WorldObservation holding
detections, active tracks, and identity decisions — all provenance-stamped
with the frame id. The face stage is skipped silently when no embedding is
supplied and refused (with detections still running) when camera privacy
is off. This module never blocks and holds no hardware.

Optional language-conditioned grounding (LocateAnything workstream, plan
Step 5.2/5.3): `ground_frame` runs only when asked — grounding is never
forced through ObjectDetector and never runs on every frame. Without a
grounding backend it degrades fail-closed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from novi.brain.io import CameraFrame

from .detection import Detection, ObjectDetector
from .faces import FaceIdentifier, FaceObservation, IdentityDecision
from .grounding import GroundingResult, SpatialInferencePolicy, SpatialPerceptionBackend, SpatialQuery
from .grounding_association import GroundingOutcome, associate_grounding_to_tracks
from .tracking import ObjectTracker, Track


@dataclass
class WorldObservation:
    """Everything one frame contributed to world state."""

    frame_id: str
    captured_at: str
    detections: list[Detection] = field(default_factory=list)
    tracks: list[Track] = field(default_factory=list)
    identities: list[IdentityDecision] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class PerceptionPipeline:
    """Deterministic perception pipeline over scripted-or-real providers."""

    def __init__(
        self,
        *,
        detector: ObjectDetector,
        face_identifier: FaceIdentifier | None = None,
        tracker: ObjectTracker | None = None,
        grounding_backend: SpatialPerceptionBackend | None = None,
    ) -> None:
        self.detector = detector
        self.faces = face_identifier
        self.tracker = tracker or ObjectTracker()
        self.grounding_backend = grounding_backend
        self._frames_processed = 0

    # -- main entry ----------------------------------------------------------

    def process_frame(
        self,
        frame: CameraFrame,
        *,
        face_embedding: list[float] | tuple[float, ...] | None = None,
        speaker_person_id: str | None = None,
    ) -> WorldObservation:
        detections = self.detector.detect(frame)
        active = self.tracker.update(detections, frame_id=frame.frame_id)

        identities: list[IdentityDecision] = []
        if face_embedding is not None and self.faces is not None and self.faces.privacy_enabled:
            d = self.faces.observe_observation(
                FaceObservation(
                    embedding=tuple(face_embedding),
                    frame_id=frame.frame_id,
                    captured_at=frame.captured_at,
                ),
                speaker_person_id=speaker_person_id,
            )
            identities.append(d)
        # privacy off: biometrics refused — detection/tracking still ran

        self._frames_processed += 1
        return WorldObservation(
            frame_id=frame.frame_id,
            captured_at=frame.captured_at,
            detections=detections,
            tracks=active,
            identities=identities,
        )

    # -- optional language grounding ----------------------------------------

    def ground_frame(
        self,
        frame: CameraFrame,
        query: SpatialQuery,
        policy: SpatialInferencePolicy,
    ) -> GroundingOutcome:
        """Ground one query against one frame; associate to the track table.

        Explicit capability (plan Step 5.3): never runs implicitly on every
        frame. Fail-closed when no backend is attached: the outcome reports
        unavailable, it never guesses absence. Provenance integrity: the
        query's frame_id must match the frame being grounded.
        """
        if query.frame_id != frame.frame_id:
            raise ValueError(
                f"query frame_id {query.frame_id!r} does not match frame {frame.frame_id!r}"
            )
        if self.grounding_backend is None:
            result = GroundingResult(
                query=query.text,
                observations=(),
                backend_status="unavailable",
                model_id="none",
                model_revision="none",
                backend_version="0.1.0",
                inference_mode=policy.mode,
                frame_id=frame.frame_id,
                timestamp=query.timestamp,
                latency_ms=None,
                success=False,
                validation_errors=("no grounding backend attached",),
            )
        else:
            result = self.grounding_backend.ground(frame, query, policy)
        return associate_grounding_to_tracks(
            result,
            self.tracker.all_tracks,
            frame_id=frame.frame_id,
            query=query.text,
        )

    # -- telemetry -------------------------------------------------------------

    def snapshot(self) -> dict[str, Any]:
        caps = self.grounding_backend.capabilities() if self.grounding_backend else None
        return {
            "frames_processed": self._frames_processed,
            "track_count": self.tracker.track_count,
            "tracks": [t.snapshot() for t in self.tracker.all_tracks],
            "privacy_enabled": self.faces.privacy_enabled if self.faces else None,
            "grounding_backend": caps.state.value if caps else None,
        }
