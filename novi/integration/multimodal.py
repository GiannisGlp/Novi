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
from typing import TYPE_CHECKING, Any

from novi.brain.agent import BrainDriver
from novi.brain.io import CameraFrame
from novi.perception.detection import ObjectDetector
from novi.perception.faces import FaceIdentifier, IdentityTier
from novi.perception.pipeline import PerceptionPipeline

from .observation_recorder import ObservationRecorder
from .recognition_store import RecognitionKind, RecognitionStore

if TYPE_CHECKING:
    from novi.perception.cadence import VisionBudget

    from .person_object_store import PersonObjectAssociationStore


@dataclass
class RuntimeEvent:
    kind: str
    payload: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, **self.payload}


_ANONYMOUS_PERSON = "someone"  # label for a genuinely-observed but unresolved face

# Minimum cosine between two proposal embeddings to treat them as the same
# face. A placeholder is auto-enrolled once per face: embeddings from the same
# person across frames sit well above this (typically >0.9); a genuinely new
# face drops below it and gets its own placeholder.
_PROPOSAL_SAME_FACE_SIM = 0.7


def _cosine_sim(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


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
        observations: ObservationRecorder | None = None,
        associations: PersonObjectAssociationStore | None = None,
        absent_frames: int = 8,
        scene_change_enabled: bool = True,
        place_auto_enroll: bool = False,
        budget: VisionBudget | None = None,
    ) -> None:
        if absent_frames < 1:
            raise ValueError("absent_frames must be >= 1")
        self.driver = driver
        self.perception = PerceptionPipeline(detector=detector, face_identifier=face_identifier)
        self.faces = face_identifier
        self.recognition = recognition
        self.observations = observations
        self.associations = associations
        self._events: list[dict[str, Any]] = []
        self._lock = threading.RLock()
        self._id_to_label: dict[str, str] = {}  # FaceIdentifier pid -> human label
        # live conversational context
        self.current_person: str = ""
        self.current_person_tier: str = ""
        self.current_place: str = ""
        self.current_objects: list[str] = []
        # per-detection-label resolution state, used to gate object events so
        # recognized/proposal fire on transitions, not every frame
        self._object_state: dict[str, str] = {}
        # person -> currently held object ref, gating person.holding/object.novel
        # so they fire on a change of (person, held object), not every frame
        self._holding_state: dict[str, str] = {}
        self.pending_enrollment_proposal: bool = False
        # auto-enroll bookkeeping: last proposal embedding (so a placeholder is
        # enrolled once per face, not every frame) + placeholder -> FaceIdentifier pid
        self._last_proposal_embedding: list[float] | None = None
        self._placeholder_internal: dict[str, str] = {}
        # label auto-enrolled on the current frame, if any (presence uses it so
        # one arrival fires one presence.entered — the placeholder, not "someone")
        self._last_auto_enrolled: str = ""
        # salience: presence transitions + scene-change detection
        self._absent_frames = absent_frames
        self._scene_change_enabled = scene_change_enabled
        self._place_auto_enroll = place_auto_enroll
        self._place_landmarks_count: dict[frozenset[str], int] = {}
        self._frame_seq = 0  # monotonically increasing per processed frame
        self._presence_tracks: dict[str, _PresenceTrack] = {}
        self._last_scene_labels: set[str] | None = None
        self._pending_events: deque[dict[str, Any]] = deque()
        # per-stage cost gate + telemetry for the camera loop (plan 26 A); the
        # camera_loop drives it and snapshot() exposes its telemetry.
        if budget is not None:
            self.budget = budget
        else:
            from novi.perception.cadence import VisionBudget

            self.budget = VisionBudget()

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
                    # canonical person id (same scheme as recognize_person) so
                    # sightings are retrievable by the durable person record
                    canonical_pid = f"person-{label.lower().replace(' ', '-')}"
                    self._record_sighting(RecognitionKind.FACE, canonical_pid, label,
                                          place=self.current_place, frame_id=frame.frame_id)
                    self._stage_event("identity.recognized", person=label, tier=dec.tier.value)
                elif dec.reason == "ambiguous":
                    self._emit("identity.ambiguous", similarity=round(dec.similarity, 3))
                elif dec.new_person_proposal:
                    self.pending_enrollment_proposal = True
                    self._emit("identity.proposal", frame_id=frame.frame_id)
                    # auto-enroll (plan 20 WS4): a genuinely new face becomes a
                    # placeholder person immediately; a face the durable store
                    # already knows (post-restart) is re-bound instead. The
                    # embedding gate stops re-enrolling the same face each frame.
                    if face_embedding is not None and not self._proposal_face_recent(face_embedding):
                        self._last_proposal_embedding = face_embedding
                        enrolled = self._handle_proposal_face(face_embedding, frame_id=frame.frame_id)
                        if enrolled:
                            self._last_auto_enrolled = enrolled
                            self._stage_event("identity.auto_enrolled", person=enrolled)

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
        if self._last_auto_enrolled:
            # a just-enrolled placeholder is the resolved identity for this
            # frame — one arrival, one presence.entered (not "someone")
            presence_now.pop(_ANONYMOUS_PERSON, None)
            presence_now[self._last_auto_enrolled] = IdentityTier.RECOGNIZED.value
        self._update_presence(presence_now)
        self._last_auto_enrolled = ""

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

    def _emit_holding(self, kind: str, person: str, obj: str, **payload: Any) -> None:
        """Stage a holding/novel event only when the (person, object) changes.

        The camera loop calls ``note_person_holding`` every frame; without this
        gate the trail would replay the same remark indefinitely. A person
        switching hands to a new object re-fires, as does putting it down and
        picking it up again.
        """
        with self._lock:
            if self._holding_state.get(person) == obj:
                return
            self._holding_state[person] = obj
            self._pending_events.append({"kind": kind, "person": person, "object": obj, **payload})
        self._emit(kind, person=person, object=obj, **payload)

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

    # -- auto-enroll & conversational naming -------------------------------------

    def _proposal_face_recent(self, embedding: list[float]) -> bool:
        """True when this proposal embedding matches the last auto-enrolled one."""
        last = self._last_proposal_embedding
        return last is not None and _cosine_sim(last, embedding) >= _PROPOSAL_SAME_FACE_SIM

    def _next_placeholder_ref(self) -> str:
        """First free ``new-person-N`` label across in-memory + durable names."""
        taken = set(self._id_to_label.values())
        if self.recognition is not None:
            taken.update(e["label"] for e in self.recognition.all(RecognitionKind.FACE))
        n = 1
        while f"new-person-{n}" in taken:
            n += 1
        return f"new-person-{n}"

    def _handle_proposal_face(self, embedding: list[float], *, frame_id: str) -> str:
        """Resolve an unknown-face proposal into an identity ('' = no new person).

        Durable recall first: a face the RecognitionStore already knows (e.g. it
        survived a restart) is re-bound into the in-memory FaceIdentifier under
        its stored name instead of being proposed as new again. Otherwise the
        face is auto-enrolled as a ``new-person-N`` placeholder in both systems,
        and that ref triggers the conversational "what's your name?" ask.
        """
        if self.recognition is not None:
            # Durable recall must use the SAME threshold as the in-memory
            # matcher (issue 5): the SFace embedder scores same-person cosine
            # ~0.40-0.80, so the store's 0.90 default never matched → every
            # session re-enrolled a fresh new-person-N and learned names
            # "forgot" the person. self.faces.tau_match is the calibrated tau
            # (0.42 real SFace pipeline / 0.90 deterministic fallback).
            m = self.recognition.match(
                RecognitionKind.FACE, embedding,
                min_similarity=getattr(self.faces, "tau_match", 0.90),
            )
            if m is not None:
                if self.faces is not None:
                    internal_pid = self.faces.enroll(m.label, embedding, frame_id=frame_id or "recall")
                    self._id_to_label[internal_pid] = m.label
                self.current_person = m.label
                self.current_person_tier = "recognized"
                self.pending_enrollment_proposal = False
                self._stage_event("identity.recognized", person=m.label, tier="recognized")
                return ""
        if self.faces is None:
            return ""
        ref = self._next_placeholder_ref()
        internal_pid = self.faces.enroll(ref, embedding, frame_id=frame_id or "auto")
        self._id_to_label[internal_pid] = ref
        self._placeholder_internal[ref] = internal_pid
        if self.recognition is not None:
            self.recognition.enroll(
                kind=RecognitionKind.FACE,
                label=ref,
                embedding=embedding,
                person_id=f"person-{ref}",
                frame_id=frame_id,
                provenance={"source": "auto-enroll"},
            )
        self.current_person = ref
        self.current_person_tier = "unknown"
        self._emit("person.enrolled", person=ref)
        return ref

    def name_person(self, placeholder_ref: str, name: str) -> dict[str, Any]:
        """Bind a real name to a placeholder person (conversational naming).

        Renames the durable FACE enrollment and any observation sightings from
        ``person-{placeholder_ref}`` to the canonical ``person-{name}``, and
        re-labels the in-memory FaceIdentifier binding so future frames resolve
        the real name. Returns the canonical person id + store rows moved.
        """
        if self.recognition is None:
            raise RuntimeError("no RecognitionStore configured")
        if not name.strip():
            return {"person_id": "", "moved": 0}
        canonical = f"person-{name.lower().replace(' ', '-')}"
        old_ref = f"person-{placeholder_ref}"
        moved = self.recognition.rename_entity(RecognitionKind.FACE, old_ref, canonical, label=name.title())
        internal_pid = self._placeholder_internal.pop(placeholder_ref, None)
        if internal_pid is not None:
            self._id_to_label[internal_pid] = name.title()
        if self.observations is not None:
            self.observations.rename_entity(RecognitionKind.FACE, old_ref, canonical)
        if self.associations is not None:
            # co-occurrence memory follows the identity to its canonical ref
            self.associations.rename_person(old_ref, canonical)
        if self.current_person == placeholder_ref:
            self.current_person = name.title()
        self.pending_enrollment_proposal = False
        self._emit("person.named", old=placeholder_ref, person=name.title(), person_id=canonical)
        return {"person_id": canonical, "moved": moved}

    # -- object recognition ---------------------------------------------------

    def recognize_object(self, name: str, *, embedding: list[float], frame_id: str = "") -> str:
        """Enroll a specific object instance under a canonical id.

        Mirrors recognize_person: the object is stored durably in the
        RecognitionStore (OBJECT kind) so Novi remembers it across restarts.
        Re-enrollment under the same name replaces the stored embedding
        (upsert semantics) so the per-frame match scan stays bounded.
        """
        if self.recognition is None:
            raise RuntimeError("no RecognitionStore configured")
        object_id = f"object-{name.lower().replace(' ', '-')}"
        # store.enroll upserts by (kind, person_id): re-enrollment replaces
        # the stored embedding rather than inserting a duplicate row
        self.recognition.enroll(
            kind=RecognitionKind.OBJECT,
            label=name,
            embedding=embedding,
            person_id=object_id,
            frame_id=frame_id or "enroll",
            provenance={"source": "enrollment"},
        )
        self._emit("object.enrolled", object=name)
        return object_id

    def recognize_objects(
        self,
        observations: list[tuple[str, list[float]]],
        *,
        min_similarity: float = 0.85,
        frame_id: str = "",
    ) -> list[dict[str, Any]]:
        """Match per-detection embeddings against enrolled objects.

        Each (label, embedding) is matched by cosine against the durable
        OBJECT store. A match marks the decision recognized and adds the
        label to current_objects; no match leaves it unresolved (novel
        object, named later by dialogue — doc 02 §1.5). Events fire only on
        transitions (object.recognized / object.proposal), mirroring the
        presence/scene hysteresis so the trail stays per-change, per-frame.
        """
        decisions: list[dict[str, Any]] = []
        if self.recognition is None:
            return decisions
        recognized: list[str] = []
        next_state: dict[str, str] = {}
        for label, embedding in observations:
            m = self.recognition.match(RecognitionKind.OBJECT, embedding, min_similarity=min_similarity)
            resolved = m.label if m is not None else ""
            if m is not None:
                decisions.append(
                    {"label": label, "object": m.label, "similarity": round(m.similarity, 3), "recognized": True}
                )
                recognized.append(m.label)
                # durable sighting of the recognized instance at the current place
                self._record_sighting(RecognitionKind.OBJECT, m.person_id, m.label,
                                      place=self.current_place, frame_id=frame_id)
                # who is in view was seen with this recognized instance, here
                self._note_cooccurrence(m.person_id, label=m.label, category=label,
                                        frame_id=frame_id)
                if self._object_state.get(label) != resolved:
                    self._stage_event(
                        "object.recognized", label=label, object=m.label, similarity=round(m.similarity, 3)
                    )
            else:
                decisions.append({"label": label, "object": None, "recognized": False})
                # novel (unresolved) instance: stable per-label ref so it coalesces
                self._record_sighting(RecognitionKind.OBJECT, f"object-unresolved-{label}", label,
                                      place=self.current_place, frame_id=frame_id)
                if self._object_state.get(label) != "":
                    self._emit("object.proposal", label=label)
            next_state[label] = resolved
        self._object_state = next_state
        with self._lock:
            self.current_objects = sorted(set(recognized))
        return decisions

    def name_proposal_object(self, category: str, name: str, *, embedding: list[float],
                             frame_id: str = "") -> dict[str, Any]:
        """Naming loop (doc 02 §1.5 / GAP-S3): name a novel (unresolved) object.

        Enrolls the instance under the given name, then re-binds any prior
        observations recorded under the unresolved per-label ref to the new
        canonical id, so "where did I last see {name}" answers across the
        whole history. Returns the canonical object id + how many sightings
        were re-bound.
        """
        if self.recognition is None or self.observations is None:
            raise RuntimeError("no RecognitionStore/ObservationRecorder configured")
        object_id = self.recognize_object(name, embedding=embedding, frame_id=frame_id)
        unresolved = f"object-unresolved-{category}"
        moved = self.observations.rename_entity(RecognitionKind.OBJECT, unresolved, object_id)
        self._emit("object.named", category=category, name=name, object=object_id, rebound=moved)
        return {"object_id": object_id, "rebound": moved}

    def _next_placeholder_object_ref(self) -> str:
        """First free ``new-object-N`` label across durable object names."""
        taken: set[str] = set()
        if self.recognition is not None:
            taken.update(e["label"] for e in self.recognition.all(RecognitionKind.OBJECT))
        n = 1
        while f"new-object-{n}" in taken:
            n += 1
        return f"new-object-{n}"

    def note_person_holding(
        self,
        person: str,
        object_label: str,
        *,
        embedding: list[float],
        frame_id: str = "",
    ) -> dict[str, Any]:
        """Person-object co-occurrence (plan 20 WS5): resolve a held object.

        The camera loop has established bbox overlap between a recognized
        person and a detected object; this resolves the held instance against
        durable OBJECT memory. A known instance stages ``person.holding``; a
        novel one is auto-enrolled as an ``object-{new-N}`` placeholder and
        stages ``object.novel`` so the salience evaluator can comment on it.
        """
        if self.recognition is None:
            return {"person": person, "object": object_label, "recognized": False, "enrolled": False}
        m = self.recognition.match(RecognitionKind.OBJECT, embedding)
        if m is not None:
            self._record_sighting(RecognitionKind.OBJECT, m.person_id, m.label,
                                  place=self.current_place, frame_id=frame_id)
            self._note_cooccurrence(m.person_id, label=m.label, category=object_label,
                                    frame_id=frame_id)
            self._emit_holding("person.holding", person, m.label)
            return {"person": person, "object": m.label, "recognized": True, "enrolled": False}
        ref = self._next_placeholder_object_ref()
        self.recognition.enroll(
            kind=RecognitionKind.OBJECT,
            label=ref,
            embedding=embedding,
            person_id=f"object-{ref}",
            frame_id=frame_id,
            provenance={"source": "auto-enroll"},
        )
        if self.observations is not None:
            # re-key any sightings recorded under the unresolved per-class ref
            self.observations.rename_entity(RecognitionKind.OBJECT, f"object-unresolved-{object_label}", f"object-{ref}")
        self._note_cooccurrence(f"object-{ref}", label=ref, category=object_label,
                                frame_id=frame_id)
        self._emit_holding("object.novel", person, ref, novelty=1.0)
        return {"person": person, "object": ref, "recognized": False, "enrolled": True}

    def _record_sighting(
        self,
        kind: RecognitionKind,
        entity_ref: str | None,
        label: str,
        *,
        place: str,
        frame_id: str = "",
    ) -> None:
        """Persist a durable sighting via the optional ObservationRecorder.

        Best-effort by design: observation memory never breaks recognition —
        if no recorder (or a storage fault) is present, the frame that was
        recognized simply has no durable spatial record. Face is biometric and
        is refused-anyway when the recorder's privacy switch is off; objects
        are non-biometric and always allowed.
        """
        if self.observations is None:
            return
        if not entity_ref:
            return
        try:
            self.observations.record(
                kind=kind,
                entity_ref=entity_ref,
                label=label,
                place=place,
                frame_id=frame_id,
                provenance={"source": "recognition"},
            )
        except PermissionError:
            # biometric refused while privacy off -> sighting not recorded
            pass
        except Exception:  # noqa: BLE001 - observation memory is best-effort
            pass

    def _note_cooccurrence(
        self,
        object_ref: str,
        *,
        label: str,
        category: str,
        frame_id: str = "",
    ) -> None:
        """Durable person-object co-occurrence (plan 26 D).

        Records *"the person currently in view was seen with this object,
        here"* in the PersonObjectAssociationStore — the memory that lets Novi
        answer "have I seen Anna with the blue mug?" Only a *recognized*
        identity (tier in {recognized, verified}) is recorded; a placeholder /
        "someone" / empty current person never grows the store with anonymous
        rows. Best-effort by the same rule as :meth:`_record_sighting`: a
        storage fault or a privacy-off write never breaks recognition.
        """
        if self.associations is None or not object_ref:
            return
        if not self.current_person or self.current_person_tier not in ("recognized", "verified"):
            return
        canonical = f"person-{self.current_person.lower().replace(' ', '-')}"
        try:
            self.associations.note(
                canonical,
                object_ref,
                label=label,
                category=category,
                place=self.current_place,
                frame_id=frame_id,
                provenance={"source": "recognition"},
            )
        except PermissionError:
            # privacy-off session: co-occurrence memory simply doesn't grow
            pass
        except Exception:  # noqa: BLE001 - association memory is best-effort
            pass

    def association_summary(self, limit: int = 3) -> list[dict[str, Any]]:
        """Bounded association memory for the current recognized person.

        Fed to snapshot() so the web API and vision status can carry what Novi
        remembers seeing with the person in view (plan 26 D).
        """
        if self.associations is None or not self.current_person:
            return []
        if self.current_person_tier not in ("recognized", "verified"):
            return []
        canonical = f"person-{self.current_person.lower().replace(' ', '-')}"
        return [a.as_dict() for a in self.associations.objects_with(canonical, limit=limit)]

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
        """Match seen landmarks against enrolled places; tag current place.

        When a place is already enrolled and its landmarks are in view,
        current_place tags it. If ``place_auto_enroll`` is enabled, a stable
        landmark set seen across consecutive frames is auto-enrolled as a new
        place (from the most salient landmark) so observations that follow get
        a durable spatial anchor even before a human names the room.
        """
        if not labels or self.recognition is None:
            return
        hits = self.recognition.lookup_by_descriptor(RecognitionKind.PLACE, {"landmarks": labels})
        if hits:
            self.current_place = hits[0]["label"]
            return
        # auto-enroll a stable scene as a place when enabled
        signature = frozenset(labels)
        self._place_landmarks_count[signature] = self._place_landmarks_count.get(signature, 0) + 1
        if self._place_auto_enroll and self._place_landmarks_count[signature] >= 3:
            # pick the most salient landmark as a tentative room name
            name = sorted(signature)[0] if signature else "unnamed"
            try:
                self.recognition.enroll(
                    kind=RecognitionKind.PLACE, label=f"{name}-room",
                    descriptor={"landmarks": sorted(signature)},
                    provenance={"source": "auto-enroll"},
                )
                self.current_place = f"{name}-room"
                self._emit("place.auto_enrolled", place=f"{name}-room", landmarks=sorted(signature))
            except Exception:  # noqa: BLE001 - auto-place is best-effort
                pass

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
            "objects": self.current_objects,
            "enrollment_proposal": self.pending_enrollment_proposal,
            "perception": self.perception.snapshot(),
            "cadence": self.budget.telemetry(),
            "associations": self.association_summary(),
            "recent_events": self._events[-12:],
        }
