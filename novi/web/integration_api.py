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
from novi.perception.detection import DeterministicObjectDetector


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
        driver = BrainDriver(brain=self.brain, lock=self._lock)
        detector = DeterministicObjectDetector(scripted={})
        from novi.perception.faces import FaceIdentifier

        faces = FaceIdentifier()  # deterministic embeddings; privacy-gated
        self.mm_runtime = MultimodalRuntime(
            driver=driver,
            detector=detector,
            face_identifier=faces,
            recognition=self.mm_store,
        )
        self.mm_camera_feed = None
        self.mm_last_frame_b64: str | None = None
        self.mm_lock = threading.RLock()

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
                "image_data_url": self.mm_last_frame_b64,
            }
