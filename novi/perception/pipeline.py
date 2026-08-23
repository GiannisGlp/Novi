"""PerceptionPipeline: frame -> detect -> track (+ optional face stage).

Doc-01/02 wiring: one call per frame produces a WorldObservation holding
detections, active tracks, and identity decisions — all provenance-stamped
with the frame id. The face stage is skipped silently when no embedding is
supplied and refused (with detections still running) when camera privacy
is off. This module never blocks and holds no hardware.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from novi.brain.io import CameraFrame

from .detection import Detection, ObjectDetector
from .faces import FaceIdentifier, FaceObservation, IdentityDecision
from .tracking import Track, ObjectTracker


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
    ) -> None:
        self.detector = detector
        self.faces = face_identifier
        self.tracker = tracker or ObjectTracker()
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
        if face_embedding is not None and self.faces is not None:
            if self.faces.privacy_enabled:
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

    # -- telemetry -------------------------------------------------------------

    def snapshot(self) -> dict[str, Any]:
        return {
            "frames_processed": self._frames_processed,
            "track_count": self.tracker.track_count,
            "tracks": [t.snapshot() for t in self.tracker.all_tracks],
            "privacy_enabled": self.faces.privacy_enabled if self.faces else None,
        }
