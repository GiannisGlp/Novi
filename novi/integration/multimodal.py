"""MultimodalRuntime: the engine-integration bridge (doc 16 §2).

Binds the three capability packages into one runtime over a shared
BrainDriver:

    novi.perception  (camera frames -> objects/tracks/faces)
    novi.voice       (turns -> transcripts -> brain)
    RecognitionStore (faces/voices/noises/places, durable)

The brain stays the single mind: perception and voice results become
person/place context that `hear()`-style calls carry with them. Every
step emits an event for the web UI / audit trail.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any

from novi.brain.agent import BrainDriver
from novi.brain.io import CameraFrame
from novi.perception.detection import ObjectDetector
from novi.perception.faces import FaceIdentifier, IdentityTier
from novi.perception.pipeline import PerceptionPipeline

from .recognition_store import RecognitionKind, RecognitionStore


@dataclass
class RuntimeEvent:
    kind: str
    payload: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, **self.payload}


class MultimodalRuntime:
    """One bridge instance per brain; thread-safe via the driver's lock."""

    def __init__(
        self,
        *,
        driver: BrainDriver,
        detector: ObjectDetector,
        face_identifier: FaceIdentifier | None = None,
        recognition: RecognitionStore | None = None,
    ) -> None:
        self.driver = driver
        self.perception = PerceptionPipeline(detector=detector, face_identifier=face_identifier)
        self.faces = face_identifier
        self.recognition = recognition
        self._events: list[dict[str, Any]] = []
        self._lock = threading.RLock()
        self._id_to_label: dict[str, str] = {}  # FaceIdentifier pid -> human label
        # live conversational context
        self.current_person: str = ""
        self.current_person_tier: str = ""
        self.current_place: str = ""
        self.pending_enrollment_proposal: bool = False

    # -- events -----------------------------------------------------------

    @property
    def events(self) -> list[dict[str, Any]]:
        return list(self._events)

    def _emit(self, kind: str, **payload: Any) -> None:
        self._events.append({"kind": kind, **payload})

    # -- camera --------------------------------------------------------------

    def process_camera_frame(
        self,
        frame: CameraFrame,
        *,
        face_embedding: list[float] | None = None,
        speaker_person_id: str | None = None,
    ):
        obs = self.perception.process_frame(
            frame,
            face_embedding=face_embedding,
            speaker_person_id=speaker_person_id,
        )
        self._update_place([d.label for d in obs.detections])
        self._emit(
            "perception.frame",
            frame_id=frame.frame_id,
            detections=[d.label for d in obs.detections],
            tracks=len(obs.tracks),
            place=self.current_place or None,
        )

        # identity -> conversation context (+ durable enrollment linkage)
        if face_embedding is not None and self.faces is not None:
            dec = obs.identities[-1] if obs.identities else None
            if dec is not None:
                if dec.tier in (IdentityTier.RECOGNIZED, IdentityTier.VERIFIED):
                    label = self._label_for_person(dec.person_id) or (dec.person_id or "")
                    self.current_person = label
                    self.current_person_tier = dec.tier.value
                    self.pending_enrollment_proposal = False
                    self._emit("identity.recognized", person=label, tier=dec.tier.value)
                elif dec.reason == "ambiguous":
                    self._emit("identity.ambiguous", similarity=round(dec.similarity, 3))
                elif dec.new_person_proposal:
                    self.pending_enrollment_proposal = True
                    self._emit("identity.proposal", frame_id=frame.frame_id)

        return obs

    # -- enrollment -----------------------------------------------------------

    def recognize_person(self, name: str, *, face_embedding: list[float] | None = None,
                         voice_embedding: list[float] | None = None, frame_id: str = "") -> str:
        """Enroll a person across identifier + durable store under one id.

        Returns the canonical person id used by both systems, so recognized
        faces resolve to stable human labels ("Anna") rather than per-module
        internal ids.
        """
        if self.faces is None:
            raise RuntimeError("no FaceIdentifier configured")
        person_id = f"person-{name.lower().replace(' ', '-')}"
        if face_embedding is not None:
            internal_pid = self.faces.enroll(name, face_embedding, frame_id=frame_id or "enroll")
            self._id_to_label[internal_pid] = name
        if self.recognition is not None:
            if face_embedding is not None:
                self.recognition.enroll(
                    kind=RecognitionKind.FACE, label=name, embedding=face_embedding,
                    person_id=person_id, frame_id=frame_id,
                    provenance={"source": "enrollment"},
                )
            if voice_embedding is not None:
                self.recognition.enroll(
                    kind=RecognitionKind.VOICE, label=name, embedding=voice_embedding,
                    person_id=person_id,
                    provenance={"source": "enrollment"},
                )
        self._emit("person.enrolled", person=name)
        return person_id

    def _label_for_person(self, person_id: str | None) -> str:
        """Resolve a FaceIdentifier person id to its human label."""
        if not person_id:
            return ""
        if person_id in self._id_to_label:
            return self._id_to_label[person_id]
        # fall back to the durable store's label mapping
        for entry in (self.recognition.all(RecognitionKind.FACE) if self.recognition else []):
            if entry["person_id"] == person_id:
                return entry["label"]
        return person_id

    def _update_place(self, labels: list[str]) -> None:
        """Match seen landmarks against enrolled places; tag current place."""
        if not labels or self.recognition is None:
            return
        hits = self.recognition.lookup_by_descriptor(RecognitionKind.PLACE, {"landmarks": labels})
        if hits:
            self.current_place = hits[0]["label"]

    # -- voice -------------------------------------------------------------------

    def voice_turn(self, text: str, *, speaker_label: str | None = None, confidence: float = 0.9) -> dict[str, Any]:
        person = speaker_label or self.current_person
        outcome = self.driver.hear(text, person=person, source="voice")
        reply = outcome.reply or ""
        result = {
            "ok": True,
            "reply": reply,
            "person": person,
            "cycle": outcome.cycle,
            "modality": outcome.modality,
        }
        self._emit("voice.turn", text=text, person=person, replied=bool(reply))
        return result

    def say(self, text: str, *, via_voice: bool = True) -> dict[str, Any]:
        """Explicit chat/hear path; voice flag records intended output modality."""
        person = self.current_person
        outcome = self.driver.hear(text, person=person, source="chat" if not via_voice else "voice")
        self._emit("say", text=text, person=person, replied=bool(outcome.reply))
        return {
            "ok": True,
            "reply": outcome.reply or "",
            "person": person,
            "cycle": outcome.cycle,
            "via_voice": via_voice,
        }

    # -- snapshot ---------------------------------------------------------------

    def snapshot(self) -> dict[str, Any]:
        return {
            "person": self.current_person,
            "tier": self.current_person_tier,
            "place": self.current_place,
            "enrollment_proposal": self.pending_enrollment_proposal,
            "perception": self.perception.snapshot(),
            "recent_events": self._events[-12:],
        }
