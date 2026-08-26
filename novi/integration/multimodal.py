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
from collections import deque
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


_ANONYMOUS_PERSON = "someone"  # label for a genuinely-observed but unresolved face


@dataclass
class _PresenceTrack:
    """Per-label presence bookkeeping (recently-seen table row)."""

    last_seen_seq: int = -1  # frame seq when this label was last identified
    present: bool = False  # currently considered in the room


class MultimodalRuntime:
    """One bridge instance per brain; thread-safe via the driver's lock.

    Besides routing modalities, the runtime distills camera frames into
    brain-ready salience events: ``presence.entered`` / ``presence.left``
    (who is in the room, with `absent_frames` hysteresis) and
    ``scene.changed`` (object-label set shifts). Downstream consumers poll
    :meth:`pop_pending_events`; the full trail stays in ``.events``.
    """

    def __init__(
        self,
        *,
        driver: BrainDriver,
        detector: ObjectDetector,
        face_identifier: FaceIdentifier | None = None,
        recognition: RecognitionStore | None = None,
        absent_frames: int = 8,
        scene_change_enabled: bool = True,
    ) -> None:
        if absent_frames < 1:
            raise ValueError("absent_frames must be >= 1")
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
        # salience: presence transitions + scene-change detection
        self._absent_frames = absent_frames
        self._scene_change_enabled = scene_change_enabled
        self._frame_seq = 0  # monotonically increasing per processed frame
        self._presence_tracks: dict[str, _PresenceTrack] = {}
        self._last_scene_labels: set[str] | None = None
        self._pending_events: deque[dict[str, Any]] = deque()

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
        self._frame_seq += 1
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
        self._update_scene({d.label for d in obs.detections})

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

        # presence salience: who did the face stage actually resolve this
        # frame? Only identity decisions count — raw object detections never
        # fabricate presence, and frames without a face stage count as
        # absence frames for everyone.
        presence_now: dict[str, str] = {}
        for dec in obs.identities:
            if dec.tier in (IdentityTier.RECOGNIZED, IdentityTier.VERIFIED):
                label = self._label_for_person(dec.person_id) or (dec.person_id or "")
                if label:
                    presence_now[label] = dec.tier.value
            else:
                # unknown tier: a face was genuinely observed but unresolved
                presence_now[_ANONYMOUS_PERSON] = IdentityTier.UNKNOWN.value
        self._update_presence(presence_now)

        return obs

    # -- presence & scene salience ---------------------------------------------

    def _update_scene(self, labels: set[str]) -> None:
        """Fire scene.changed when the object-label set shifts between frames."""
        if not self._scene_change_enabled:
            return
        previous = self._last_scene_labels
        if previous is not None and labels != previous:
            self._stage_event(
                "scene.changed",
                appeared=sorted(labels - previous),
                disappeared=sorted(previous - labels),
            )
        self._last_scene_labels = labels

    def _update_presence(self, seen: dict[str, str]) -> None:
        """Advance presence bookkeeping by one processed frame.

        `seen` maps labels identified this frame to their identity tier.
        A label enters when it is identified after >= absent_frames
        consecutive prior frames without identification; it leaves after
        >= absent_frames consecutive frames without identification.
        """
        if self.faces is None:
            return  # honest degradation: no identifier -> no presence claims
        n = self._frame_seq
        for label, track in self._presence_tracks.items():
            if (
                track.present
                and label not in seen
                and n - track.last_seen_seq >= self._absent_frames
            ):
                track.present = False
                self._stage_event("presence.left", person=label)
        for label in sorted(seen):  # sorted for deterministic emission order
            track = self._presence_tracks.get(label)
            if track is None:
                track = _PresenceTrack()
                self._presence_tracks[label] = track
                arrived = True  # first-ever sighting counts as an arrival
            else:
                # arrival only after >= absent_frames consecutive unseen frames
                arrived = (n - track.last_seen_seq - 1) >= self._absent_frames
            track.last_seen_seq = n
            if arrived and not track.present:
                track.present = True
                self._stage_event("presence.entered", person=label, tier=seen[label])
        # bound the recently-seen table; a departed label past retention is
        # indistinguishable from a first-ever arrival on re-entry (entered
        # fires either way), so pruning cannot change observable behavior
        retention = max(64, 8 * self._absent_frames)
        expired = [
            label
            for label, track in self._presence_tracks.items()
            if not track.present and n - track.last_seen_seq > retention
        ]
        for label in expired:
            del self._presence_tracks[label]

    def _stage_event(self, kind: str, **payload: Any) -> None:
        """Emit into the shared trail AND stage for pop_pending_events()."""
        with self._lock:
            self._pending_events.append({"kind": kind, **payload})
        self._emit(kind, **payload)

    def pop_pending_events(self) -> list[dict[str, Any]]:
        """Atomically drain staged presence/scene events (camera-loop safe)."""
        with self._lock:
            staged = list(self._pending_events)
            self._pending_events.clear()
            return staged

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
