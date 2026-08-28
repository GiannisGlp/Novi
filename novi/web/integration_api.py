"""Multimodal + recognition API surface for NoviWebServer.

Additive mixin: NoviWebServer gains these methods via inheritance; the
only edit to server.py is the base-class entry and lazy runtime setup.
Keeps the integration seam isolated so parallel brain work stays
undisturbed (doc 16 §4).
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any

from novi.brain.agent import BrainDriver
from novi.integration.multimodal import MultimodalRuntime
from novi.integration.recognition_store import RecognitionKind, RecognitionStore
from novi.perception.camera import CameraFeed

# enrollment input bounds (HTTP boundary validation)
MAX_ENROLL_NAME_LEN = 80
MAX_EMBEDDING_DIMS = 4096


class IntegrationMixin:
    """Voice/perception/recognition endpoints for NoviWebServer."""

    # populated by _integration_init() in __init__
    mm_runtime: MultimodalRuntime
    mm_store: RecognitionStore
    mm_camera_feed: CameraFeed | None
    mm_last_frame_bytes: bytes | None

    def _integration_init(self) -> None:
        db = Path(self.store_path) if getattr(self, "store_path", None) else None
        self.mm_store = RecognitionStore(db or ":memory:")
        # Durable sighting memory (what/where/when + vector) — same canonical
        # DB file, non-biometric alongside the RecognitionStore enrollments.
        from novi.integration.observation_recorder import ObservationRecorder

        self.observation_recorder = ObservationRecorder(db or ":memory:")
        # Voice turns get the same LLM transport as chat so spoken dialogue is
        # real dialogue (router-grade), not just the deterministic fallback.
        llm_transport = self._llm_chat if getattr(self, "chat_llm", False) else None
        driver = BrainDriver(brain=self.brain, lock=self._lock, llm_chat=llm_transport)
        # Real object detection when torch/torchvision are installed (MPS on
        # Apple Silicon); honest fallback to the scripted detector otherwise.
        detector: Any = None
        self.detector_backend = "deterministic"
        try:
            from novi.perception.real_backends import TorchvisionPerceptionDetector

            detector = TorchvisionPerceptionDetector()
            self.detector_backend = f"torchvision:ssdlite ({detector.device})"
        except Exception:  # noqa: BLE001 - neural deps optional
            detector = None
        if detector is None:
            from novi.perception.detection import DeterministicObjectDetector

            detector = DeterministicObjectDetector(scripted={})
        from novi.perception.detection import DeterministicObjectDetector as _DD  # type check only

        assert not isinstance(detector, _DD) or self.detector_backend == "deterministic"
        # Real face identity when OpenCV YuNet/SFace models can be loaded;
        # falls back to the deterministic identifier (POST-supplied embeddings).
        self.face_embedder = None
        faces = None
        try:
            from novi.perception.real_backends import build_face_identifier

            faces, self.face_embedder = build_face_identifier()
        except Exception:  # noqa: BLE001 - biometrics optional
            faces = None
        if faces is None:
            from novi.perception.faces import FaceIdentifier

            faces = FaceIdentifier()  # deterministic embeddings; privacy-gated
        from novi.perception.faces import FaceIdentifier  # noqa: F401 - re-import for typing

        self._faces_real = self.face_embedder is not None
        # Real object embedding (ResNet18) for instance-level object memory;
        # lazy — no model download until the camera loop first uses it.
        self.object_embedder = None
        try:
            from novi.perception.real_backends import build_object_embedder

            self.object_embedder = build_object_embedder()
        except Exception:  # noqa: BLE001 - neural deps optional
            self.object_embedder = None
        self._objects_real = self.object_embedder is not None
        self.mm_runtime = MultimodalRuntime(
            driver=driver,
            detector=detector,
            face_identifier=faces,
            recognition=self.mm_store,
            observations=self.observation_recorder,
        )
        self.mm_camera_feed = None
        self.mm_last_frame_b64: str | None = None
        # last face identity seen by the camera loop (tier/person/similarity)
        self.mm_last_face: dict[str, Any] | None = None
        # stable tracked objects/people for the camera overlay (named boxes)
        self.mm_last_tracks: list[dict[str, Any]] = []
        self.mm_lock = threading.RLock()
        # Real I/O state (doc 17) — off until real_enable() is called.
        self.real_io = {"camera": False, "mic": False, "speaker": False}
        self.real_io_enabled = False
        self._real_speaker = None
        self._real_stt = None
        self._voice_recognizer: Any | None = None
        self._camera_thread: threading.Thread | None = None
        self.speak_back_enabled = True

    # ---- real I/O (doc 17) -------------------------------------------------

    def real_enable(self, *, camera: bool = False, mic: bool = False, speaker: bool = False) -> dict[str, Any]:
        """Attach real devices. Each degrades honestly when hardware is absent."""
        results: dict[str, Any] = {}
        if camera and not self.real_io["camera"]:
            try:
                from novi.brain.io import MacCamera
                from novi.perception.camera import CameraFeed
                from novi.integration.real_io import MacCameraAdapter

                adapter = MacCameraAdapter(MacCamera())
                feed = CameraFeed(adapter, queue_size=4)
                feed.start()
                self.mm_camera_feed = feed
                self._start_camera_loop()
                self.real_io["camera"] = True
                results["camera"] = True
            except Exception as exc:  # noqa: BLE001 - honest degradation
                self.real_io["camera"] = False
                results["camera"] = False
                results["camera_error"] = str(exc)
        elif camera:
            results["camera"] = True

        if mic and not self.real_io["mic"]:
            from novi.brain.io import MacMicrophone
            from novi.brain.models.stt import WhisperSTTProvider
            from novi.integration.real_io import RealMicrophone, RealSTT

            stt_provider = None
            existing = getattr(self.brain, "stt", None)
            if existing is not None and type(existing).__name__ == "WhisperSTTProvider":
                stt_provider = existing  # reuse the brain's warm model
            else:
                stt_provider = WhisperSTTProvider(model_size="base", device="cpu")
            self._real_stt = RealSTT(stt_provider, mac_microphone=RealMicrophone(MacMicrophone()))
            self.real_io["mic"] = True
            results["mic"] = True

        if speaker and not self.real_io["speaker"]:
            import shutil

            from novi.voice.tts import SayTTSProvider

            from novi.integration.real_io import RealSpeaker

            say_bin = "/usr/bin/say" if shutil.which("say") else "/nonexistent/say"
            self._real_speaker = RealSpeaker(SayTTSProvider(say_bin=say_bin))
            self.real_io["speaker"] = True
            results["speaker"] = True

        self.real_io_enabled = any(self.real_io.values())
        return results

    def _start_camera_loop(self) -> None:
        """Background loop: poll frames → perception → preview b64."""

        def _loop() -> None:
            while getattr(self, "mm_camera_feed", None) is not None and not getattr(self, "_stop").is_set():
                feed = self.mm_camera_feed
                if feed is None:
                    break
                rec = feed.poll(timeout_s=0.5)
                if rec is None:
                    continue
                try:
                    from novi.integration.real_io import encode_preview_jpeg_b64

                    # Preview is downscaled + quality-capped; detection below
                    # runs on the full-res frame.payload untouched.
                    data_url = encode_preview_jpeg_b64(rec.frame)
                    with self.mm_lock:
                        self.mm_last_frame_b64 = data_url
                    # Real face identity: embed the largest face in this frame
                    # when the SFace backend is available; None = skip stage.
                    embedding: list[float] | None = None
                    face_bbox = None
                    embedder = getattr(self, "face_embedder", None)
                    if embedder is not None:
                        payload = rec.frame.payload
                        if isinstance(payload, (bytes, bytearray)):
                            embedding, face_bbox = embedder.embed(payload)
                    obs = self.mm_runtime.process_camera_frame(
                        rec.frame,
                        face_embedding=embedding,
                    )
                    # Instance-level object recognition: embed each detection's
                    # crop and match against enrolled objects (durable memory).
                    if self.object_embedder is not None and obs.detections:
                        try:
                            bboxes = [d.bbox for d in obs.detections]
                            vecs = self.object_embedder.embed(rec.frame.payload, bboxes)
                            pairs = [
                                (d.label, v)
                                for d, v in zip(obs.detections, vecs, strict=False)
                                if v is not None
                            ]
                            if pairs:
                                self.mm_runtime.recognize_objects(pairs, frame_id=rec.frame.frame_id)
                        except Exception:  # noqa: BLE001 - object recognition best-effort
                            pass
                    if embedding is not None and obs.identities:
                        dec = obs.identities[-1]
                        self.mm_last_face = {
                            "bbox": face_bbox,
                            "tier": dec.tier.value,
                            "person": dec.person_id,
                            "similarity": round(dec.similarity, 3),
                            "proposal": bool(dec.new_person_proposal),
                        }
                    # Stable track labels for the overlay: person tracks get
                    # identity names (Vano / someone), objects keep their class
                    # label + track id. Stored under mm_lock for /api/preview.
                    overlay: list[dict[str, Any]] = []
                    for t in getattr(obs, "tracks", []) or []:
                        entry: dict[str, Any] = {
                            "track_id": t.track_id,
                            "label": t.label,
                            "bbox": list(t.bbox),
                            "confirmed": bool(t.confirmed),
                        }
                        if t.label in ("person", "human", "face"):
                            name = self.mm_runtime.current_person or (
                                "someone" if self.mm_last_face else None
                            )
                            if name:
                                entry["name"] = f"{name} ({self.mm_runtime.current_person_tier or 'seen'})"
                                entry["is_person"] = True
                        overlay.append(entry)
                    if self.mm_last_face and face_bbox:
                        # the identified face box itself, named by tier
                        overlay.append({
                            "track_id": -1,
                            "label": "face",
                            "bbox": list(face_bbox),
                            "confirmed": True,
                            "is_person": True,
                            "name": (
                                self.mm_last_face.get("person")
                                or ("new person — enroll" if self.mm_last_face.get("proposal") else "person?")
                            ),
                        })
                    with self.mm_lock:
                        self.mm_last_tracks = overlay
                    # Presence/scene salience -> the brain's input bus (north
                    # star §4.2): room transitions become real cognition inputs.
                    try:
                        for ev in self.mm_runtime.pop_pending_events():
                            kind = str(ev.get("kind", ""))
                            if kind.startswith("presence.") or kind == "scene.changed":
                                self.brain.submit(
                                    "camera", kind,
                                    {k: v for k, v in ev.items() if k != "kind"},
                                    coalesce_key=f"{kind}:{ev.get('person', 'scene')}",
                                )
                    except Exception:  # noqa: BLE001 - event feed is best-effort
                        pass
                except Exception:  # noqa: BLE001 - preview loop must survive anything
                    continue

        t = threading.Thread(target=_loop, daemon=True, name="novi-real-camera")
        t.start()
        self._camera_thread = t

    def voice_listen(self, seconds: float = 3.0) -> dict[str, Any]:
        """Record from the real mic → STT → brain → reply (+ optional speak-back).

        When a RealSpeakerRecognizer is wired, the same recording is also
        voice-matched: the recognized speaker becomes the addressee.
        """
        if not self.real_io.get("mic"):
            raise RuntimeError("microphone not enabled — call real_enable(mic=True)")
        assert self._real_stt is not None
        tr = self._real_stt.listen_and_transcribe(seconds)
        if not tr.get("text"):
            return {**tr, "reply": "", "spoken": False}

        # speaker recognition on the same audio (doc 17 §8)
        speaker_label = None
        speaker_sim = None
        audio_path = tr.get("audio_path")
        if self._voice_recognizer is not None and audio_path:
            try:
                m = self._voice_recognizer.match(audio_path)
                if m is not None:
                    speaker_label = m.label
                    speaker_sim = round(m.similarity, 3)
            except Exception:  # noqa: BLE001 - identification is best-effort
                pass

        turn = self.mm_runtime.voice_turn(tr["text"], speaker_label=speaker_label)
        reply_text = str(turn.get("reply", ""))
        spoken = {"spoken": False}
        if self.speak_back_enabled and self._real_speaker is not None and reply_text:
            spoken = self._real_speaker.speak(reply_text)
        out = {
            **tr,
            "reply": reply_text,
            "person": turn.get("person", ""),
            "spoken": spoken,
        }
        if speaker_label is not None:
            out["speaker"] = speaker_label
            out["speaker_similarity"] = speaker_sim
        return out

    def enroll_voice(self, body_or_name: Any, wav_path: str | None = None) -> dict[str, Any]:
        """Enroll a voiceprint for a person (from body dict or direct call)."""
        if isinstance(body_or_name, dict):
            name = str(body_or_name.get("name", "")).strip()
            wav_path = str(body_or_name.get("wav_path", "")).strip() or None
        else:
            name = str(body_or_name or "").strip()
        if not name:
            return {"error": "name required"}
        if not wav_path:
            # convenience: record a fresh sample right now
            if not self.real_io.get("mic"):
                raise RuntimeError("microphone not enabled — call real_enable(mic=True)")
            assert self._real_stt is not None
            rec = self._real_stt._mic.record(4.0) if hasattr(self._real_stt, "_mic") else None
            wav_path = rec["path"] if isinstance(rec, dict) else str(getattr(rec, "path", ""))
        if self._voice_recognizer is None:
            from novi.integration.real_io_voice import RealSpeakerRecognizer

            self._voice_recognizer = RealSpeakerRecognizer(store=self.mm_store)
        pid = self._voice_recognizer.enroll(name, wav_path)
        self._emit_enrollment(name)
        return {"ok": True, "person_id": pid}

    def enroll_face_from_camera(self, name: str) -> dict[str, Any]:
        """Embed the newest live camera frame and store it as `name`'s face.

        Uses the same SFace embedder as recognition so enrollment and later
        matching share one embedding space. Durable via RecognitionStore.
        """
        name = (name or "").strip()
        if not name:
            return {"error": "name required"}
        embedder = getattr(self, "face_embedder", None)
        if embedder is None:
            return {"error": "face embedding backend unavailable (opencv models failed to load)"}
        with self.mm_lock:
            data_url = self.mm_last_frame_b64
        if not data_url:
            return {"error": "no camera frame yet — enable the camera and try again"}
        import base64

        try:
            jpeg = base64.b64decode(data_url.split(",", 1)[1])
        except Exception:  # noqa: BLE001 - malformed frame payload
            return {"error": "could not decode latest frame"}
        vec, bbox = embedder.embed(jpeg)
        if vec is None:
            return {"error": "no face visible — sit facing the camera and retry"}
        # store under the canonical person id + durable recognition entry
        person_id = f"person-{name.lower().replace(' ', '-')}"
        if self.mm_runtime.faces is not None:
            internal_pid = self.mm_runtime.faces.enroll(name, vec, frame_id="enroll-webcam")
            self.mm_runtime._id_to_label[internal_pid] = name
        if self.mm_store is not None:
            from novi.integration.recognition_store import RecognitionKind

            self.mm_store.enroll(
                kind=RecognitionKind.FACE,
                label=name,
                embedding=vec,
                person_id=person_id,
                frame_id="enroll-webcam",
                provenance={"source": "web-enroll"},
            )
        self.mm_runtime._emit("person.face-enrolled", person=name)
        return {"ok": True, "person_id": person_id, "bbox": list(bbox or ())}

    def enroll_object_from_camera(self, name: str) -> dict[str, Any]:
        """Embed the largest detected object crop and store it as `name`.

        Uses the same ResNet18 embedder as recognition so enrollment and
        later matching share one embedding space. Durable via RecognitionStore.
        """
        name = (name or "").strip()
        if not name or len(name) > MAX_ENROLL_NAME_LEN:
            return {"error": f"name required (1-{MAX_ENROLL_NAME_LEN} chars)"}
        embedder = getattr(self, "object_embedder", None)
        if embedder is None:
            return {"error": "object embedding backend unavailable (torch/torchvision missing)"}
        # frame and overlay must come from the same loop iteration — capture
        # both under one lock hold or a fresh frame pairs with a stale bbox
        with self.mm_lock:
            data_url = self.mm_last_frame_b64
            tracks = list(self.mm_last_tracks or [])
        if not data_url:
            return {"error": "no camera frame yet — enable the camera and try again"}
        import base64

        try:
            jpeg = base64.b64decode(data_url.split(",", 1)[1])
        except Exception:  # noqa: BLE001 - malformed frame payload
            return {"error": "could not decode latest frame"}
        # largest non-person track bbox from the latest frame overlay
        best: tuple[int, tuple[int, int, int, int]] | None = None
        for t in tracks:
            if t.get("is_person"):
                continue
            bbox = t.get("bbox")
            if not bbox or len(bbox) != 4:
                continue
            area = int(bbox[2]) * int(bbox[3])
            if best is None or area > best[0]:
                best = (area, (int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])))
        if best is None:
            return {"error": "no object visible — point the camera at an object and retry"}
        vecs = embedder.embed(jpeg, [best[1]])
        vec = vecs[0] if vecs else None
        if vec is None:
            return {"error": "could not embed the object crop"}
        object_id = self.mm_runtime.recognize_object(name, embedding=vec, frame_id="enroll-webcam")
        return {"ok": True, "object_id": object_id, "bbox": list(best[1])}

    def recognize_object(self, body: dict[str, Any]) -> dict[str, Any]:
        """Enroll an object instance from a supplied embedding (API path)."""
        name = str(body.get("name", "")).strip()
        embedding = body.get("embedding")
        if not name or len(name) > MAX_ENROLL_NAME_LEN:
            return {"error": f"name required (1-{MAX_ENROLL_NAME_LEN} chars)"}
        if (
            not isinstance(embedding, list)
            or not embedding
            or len(embedding) > MAX_EMBEDDING_DIMS
            or not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in embedding)
        ):
            return {"error": f"embedding must be a list of numbers (1-{MAX_EMBEDDING_DIMS} dims)"}
        with self.mm_lock:
            oid = self.mm_runtime.recognize_object(
                name,
                embedding=[float(v) for v in embedding],
                frame_id=str(body.get("frame_id", "")),
            )
            return {"ok": True, "object_id": oid}

    def enroll_voice_live(self, name: str) -> dict[str, Any]:
        """Record ~4s from the real mic now and enroll the voiceprint."""
        name = (name or "").strip()
        if not name:
            return {"error": "name required"}
        if not self.real_io.get("mic"):
            raise RuntimeError("microphone not enabled")
        return self.enroll_voice({"name": name})

    def _emit_enrollment(self, name: str) -> None:
        try:
            self.mm_runtime._emit("person.voice-enrolled", person=name)
        except Exception:  # noqa: BLE001
            pass

    def tts_speak(self, body: dict[str, Any]) -> dict[str, Any]:
        """Speak arbitrary text through the real speaker."""
        if self._real_speaker is None:
            self.real_enable(speaker=True)
        text = str(body.get("text", "")).strip()
        if not text:
            return {"error": "empty text"}
        assert self._real_speaker is not None
        return {**self._real_speaker.speak(text)}

    # ---- perception -------------------------------------------------------

    def perception_frame(self, body: dict[str, Any]) -> dict[str, Any]:
        """Process one frame descriptor through the pipeline (scripted/real)."""
        with self.mm_lock:
            frame_id = str(body.get("frame_id") or f"web-{int(time.time() * 1000)}")
            from novi.brain.io import CameraFrame

            frame = CameraFrame(
                frame_id=frame_id,
                captured_at=str(body.get("captured_at") or ""),
                width=int(body.get("width", 0)),
                height=int(body.get("height", 0)),
                payload=body.get("payload", b""),
                metadata={"source": "web"},
            )
            face_embedding = body.get("face_embedding")
            obs = self.mm_runtime.process_camera_frame(
                frame, face_embedding=face_embedding,
                speaker_person_id=body.get("speaker_person_id"),
            )
            return {
                "frame_id": frame.frame_id,
                "detections": [{"label": d.label, "confidence": d.confidence} for d in obs.detections],
                "tracks": [t.snapshot() for t in obs.tracks],
                "identities": [
                    {"tier": i.tier.value, "person": i.person_id, "reason": i.reason}
                    for i in obs.identities
                ],
                "place": self.mm_runtime.current_place or None,
                "proposal": self.mm_runtime.pending_enrollment_proposal,
            }

    def perception_state(self) -> dict[str, Any]:
        with self.mm_lock:
            return {
                "runtime": self.mm_runtime.snapshot(),
                "camera_health": (self.mm_camera_feed.health.value if self.mm_camera_feed else None),
                "enrollments": self.mm_store.all(),
            }

    # ---- voice ---------------------------------------------------------------

    def voice_turn(self, body: dict[str, Any]) -> dict[str, Any]:
        text = str(body.get("text", "")).strip()
        if not text:
            return {"error": "empty text"}
        with self.mm_lock:
            res = self.mm_runtime.voice_turn(
                text,
                speaker_label=body.get("speaker_label"),
                confidence=float(body.get("confidence", 0.9)),
            )
            # mirror into the shared web chat log so the UI shows the exchange
            try:
                self._append_chat({"role": "user", "text": f"[voice] {text}"})
                if res.get("reply"):
                    self._append_chat({"role": "novi", "text": str(res["reply"])})
            except Exception:  # noqa: BLE001 - chat mirroring is best-effort
                pass
            return res

    # ---- recognition ------------------------------------------------------------

    def recognize_person(self, body: dict[str, Any]) -> dict[str, Any]:
        name = str(body.get("name", "")).strip()
        if not name:
            return {"error": "name required"}
        with self.mm_lock:
            pid = self.mm_runtime.recognize_person(
                name,
                face_embedding=body.get("face_embedding"),
                voice_embedding=body.get("voice_embedding"),
                frame_id=str(body.get("frame_id", "")),
            )
            return {"ok": True, "person_id": pid}

    def recognition_list(self, kind: str | None = None) -> dict[str, Any]:
        k = RecognitionKind(kind) if kind else None
        return {"enrollments": self.mm_store.all(k)}

    # ---- observation memory (spatial/sighting retrieval) --------------------

    def _require_observations(self):
        if self.observation_recorder is None:
            raise RuntimeError("observation memory unavailable")
        return self.observation_recorder

    def observation_last_sighting(self, body: dict[str, Any]) -> dict[str, Any]:
        """Most recent where/when/vector for a recognized person or object."""
        kind = str(body.get("kind", "")).strip().lower()
        entity_ref = str(body.get("entity_ref", "")).strip()
        if kind not in ("face", "object"):
            return {"error": "kind must be face|object"}
        if not entity_ref:
            return {"error": "entity_ref required"}
        with self.mm_lock:
            oc = self._require_observations()
            hit = oc.last_sighting(RecognitionKind(kind), entity_ref)
            return {"sighting": hit.as_dict() if hit else None}

    def observation_in_place(self, body: dict[str, Any]) -> dict[str, Any]:
        """What Novi currently knows to have been seen at this place."""
        place = str(body.get("place", "")).strip()
        if not place:
            return {"error": "place required"}
        kind_raw = str(body.get("kind", "") or "").strip().lower()
        with self.mm_lock:
            oc = self._require_observations()
            kind = RecognitionKind(kind_raw) if kind_raw in ("face", "object", "place") else None
            return {"observations": [o.as_dict() for o in oc.in_place(place, kind)]}

    def observation_search(self, body: dict[str, Any]) -> dict[str, Any]:
        """Top-k instances ranked by cosine over saved sighting vectors."""
        query = body.get("query_vector")
        if not isinstance(query, list) or not query:
            return {"error": "query_vector required"}
        kind_raw = str(body.get("kind", "") or "").strip().lower()
        kind = RecognitionKind(kind_raw) if kind_raw in ("face", "object") else None
        place = str(body.get("place", "") or "").strip() or None
        limit = max(1, min(int(body.get("limit", 5)), 100))
        with self.mm_lock:
            oc = self._require_observations()
            hits = oc.search([float(v) for v in query], kind=kind, place=place, limit=limit)
            return {"matches": [{"entity_ref": ref, "similarity": round(sim, 3)} for ref, sim in hits]}

    def proposal_list(self) -> dict[str, Any]:
        """Pending novel-object proposals awaiting a name (GAP-S3)."""
        with self.mm_lock:
            oc = self._require_observations()
            rows = oc.all(kind=RecognitionKind.OBJECT)
            unresolved = [
                {"entity_ref": o.entity_ref, "category": o.category or o.label,
                 "label": o.label, "place": o.place, "seen_at": o.temporal_at}
                for o in rows if o.entity_ref.startswith("object-unresolved-")
            ]
            return {"proposals": unresolved}

    def name_proposal_object(self, body: dict[str, Any]) -> dict[str, Any]:
        """Bind a novel object to a name + rebind its observed history."""
        category = str(body.get("category", "") or "").strip()
        name = str(body.get("name", "")).strip()
        embedding = body.get("embedding")
        if not category or not name:
            return {"error": "category and name required"}
        if (not isinstance(embedding, list) or not embedding
                or not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in embedding)):
            return {"error": "embedding must be a list of numbers"}
        with self.mm_lock:
            result = self.mm_runtime.name_proposal_object(
                category, name, embedding=[float(v) for v in embedding],
                frame_id=str(body.get("frame_id", "") or ""),
            )
            return {"ok": True, **result}

    def enroll_place_or_noise(self, body: dict[str, Any]) -> dict[str, Any]:
        kind = str(body.get("kind", ""))
        label = str(body.get("label", "")).strip()
        if kind not in ("noise", "place"):
            return {"error": "kind must be noise|place"}
        if not label:
            return {"error": "label required"}
        with self.mm_lock:
            pid = self.mm_store.enroll(
                kind=RecognitionKind(kind),
                label=label,
                descriptor=dict(body.get("descriptor", {})),
                provenance={"source": "web", **(body.get("provenance") or {})},
            )
            return {"ok": True, "person_id": pid}

    def recognition_privacy(self, body: dict[str, Any]) -> dict[str, Any]:
        enabled = bool(body.get("enabled", True))
        reason = str(body.get("reason", "web request"))
        with self.mm_lock:
            self.mm_store.set_privacy(enabled, reason=reason)
            if self.mm_runtime.faces is not None:
                self.mm_runtime.faces.set_privacy(enabled, reason=reason)
            return {"ok": True, "privacy_enabled": enabled}

    # ---- preview -----------------------------------------------------------------

    def preview_frame(self) -> dict[str, Any]:
        """Latest camera snapshot for the /preview page."""
        with self.mm_lock:
            feed = self.mm_camera_feed
            health = feed.health.value if feed else "offline"
            stale = feed.is_stale(stale_after_s=2.0) if feed else True
            snap = self.mm_runtime.snapshot()
            last_evt = snap["recent_events"][-1] if snap["recent_events"] else {}
            return {
                "camera_health": health,
                "stale": stale,
                "person": snap["person"],
                "tier": snap["tier"],
                "place": snap["place"],
                "detections": last_evt.get("detections", []),
                "face": self.mm_last_face,
                "tracks": self.mm_last_tracks,
                "detector_backend": getattr(self, "detector_backend", "deterministic"),
                "faces_backend": ("opencv:sface" if getattr(self, "_faces_real", False) else "deterministic"),
                "objects": snap.get("objects", []),
                "objects_backend": ("torchvision:resnet18" if getattr(self, "_objects_real", False) else "deterministic"),
                "image_data_url": self.mm_last_frame_b64,
            }
