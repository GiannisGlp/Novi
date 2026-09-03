"""Camera loop: single JPEG decode + VisionBudget gating for the web server.

The loop used to decode the JPEG 3-4x per frame (preview encode, SFace embed,
detector, object embedder) and run every expensive stage on every frame —
capping effective frame rate with no way to measure it. This module is the
rewritten per-frame body:

- decode the JPEG **once** with ``cv2.imdecode`` -> BGR ndarray; the detector,
  object embedder, SFace ``embed_bgr`` and preview encode all consume that
  array, so decoding never repeats;
- :class:`novi.perception.cadence.VisionBudget` gates the expensive stages
  (``preview`` / ``face_embed`` / ``object_embed``) to a cadence while
  detection + presence still run every frame; a popped ``scene.changed``
  event forces one full frame;
- every stage reports its elapsed ms back into the budget, so
  ``processed_fps`` + per-stage ``stage_ms`` telemetry reflects what the loop
  actually achieves.

``integration_api`` keeps thin ``_start_camera_loop`` / ``_store_preview_frame``
wrappers because tests call those by name; the heavy mechanics live here.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from novi.brain.io import CameraFrame

# detection classes that denote a person (face box + body classes)
PERSON_LABELS = ("person", "human", "face")


def decode_bgr(payload: Any):
    """JPEG bytes -> BGR ndarray; ndarray passes through unchanged; None on failure."""
    try:
        import cv2
        import numpy as np

        if isinstance(payload, (bytes, bytearray)):
            return cv2.imdecode(np.frombuffer(payload, dtype=np.uint8), cv2.IMREAD_COLOR)
        if isinstance(payload, np.ndarray) and payload.ndim == 3:
            return payload
    except Exception:  # noqa: BLE001 - undecodable frame => skip the frame
        return None
    return None


def encode_bgr_jpeg(bgr) -> bytes | None:
    """BGR ndarray -> JPEG bytes for on-demand enrollment (never per-frame)."""
    try:
        import cv2

        ok, buf = cv2.imencode(".jpg", bgr)
        return bytes(buf.tobytes()) if ok else None
    except Exception:  # noqa: BLE001 - enrollment encode is best-effort
        return None


def build_work_frame(rec, bgr) -> CameraFrame:
    """Re-wrap a decoded array as the work frame so downstream stages reuse it."""
    height, width = bgr.shape[:2]
    return CameraFrame(
        frame_id=rec.frame.frame_id,
        captured_at=rec.frame.captured_at,
        width=width,
        height=height,
        payload=bgr,
        metadata={**rec.frame.metadata, "format": "bgr"},
    )


def build_camera_loop(server) -> Callable[[], None]:
    """Return the camera-loop body; ``_start_camera_loop`` runs it on a thread.

    The loop owns only loop mechanics (poll loop + survive-anything guard);
    every per-frame stage lives in :func:`process_record` so tests drive it
    directly with fake records and an injected VisionBudget.
    """

    def _loop() -> None:
        while getattr(server, "mm_camera_feed", None) is not None and not server._stop.is_set():
            feed = server.mm_camera_feed
            if feed is None:
                break
            rec = feed.poll(timeout_s=0.5)
            if rec is None:
                continue
            try:
                process_record(server, rec)
            except Exception:  # noqa: BLE001 - preview loop must survive anything
                continue

    return _loop


def process_record(server, rec) -> None:
    """Run one camera frame through perception under the cost budget.

    Decodes the JPEG once, gates the expensive stages via
    ``server.mm_runtime.budget``, feeds per-stage timings back into the budget,
    and forwards presence/scene events onto the brain input bus.
    """
    budget = server.mm_runtime.budget
    bgr = decode_bgr(rec.frame.payload)
    if bgr is None:
        return
    work = build_work_frame(rec, bgr)
    decision = budget.decide(frame_seq=rec.seq)

    # Preview (gated): downscaled b64; the decoded array is always kept so
    # enrollment crops against the SAME resolution the tracks were computed on.
    if decision["preview"]:
        t0 = _now_ms()
        server._store_preview_frame(rec, bgr)
        budget.add_sample("preview", _now_ms() - t0)
        budget.record_run("preview")
    else:
        with server.mm_lock:
            server.mm_last_frame_bgr = bgr

    # Face identity (gated): reuse the last embedding when this frame's face
    # stage is skipped so identity matching keeps presence alive.
    embedding = None
    face_bbox = None
    if server.face_embedder is not None:
        if decision["face_embed"]:
            t0 = _now_ms()
            embedding, face_bbox = _embed_face(server, work)
            budget.add_sample("face_embed", _now_ms() - t0)
            budget.record_run("face_embed")
            server.mm_last_face_pair = (embedding, face_bbox)
        else:
            embedding, face_bbox = server.mm_last_face_pair or (None, None)

    # Detection + presence always run (the budget's "detect" stage).
    t0 = _now_ms()
    obs = server.mm_runtime.process_camera_frame(work, face_embedding=embedding)
    budget.add_sample("detect", _now_ms() - t0)
    budget.record_run("detect")

    # Instance-level object recognition (gated): embed each detection's crop
    # and match against enrolled objects, resolving any person-object overlap
    # into holding/novelevents.
    if server.object_embedder is not None and obs.detections and decision["object_embed"]:
        try:
            t0 = _now_ms()
            bboxes = [d.bbox for d in obs.detections]
            vecs = server.object_embedder.embed(work.payload, bboxes)
            pairs = [
                (d.label, v)
                for d, v in zip(obs.detections, vecs, strict=False)
                if v is not None
            ]
            if pairs:
                server.mm_runtime.recognize_objects(pairs, frame_id=rec.frame.frame_id)
                with server.mm_lock:
                    for label, vec in pairs:
                        server.mm_last_object_embeddings[label] = vec
                    _enforce_embedding_bound(server)
            server._note_person_holding(obs.detections, face_bbox, vecs, rec.frame.frame_id)
            budget.add_sample("object_embed", _now_ms() - t0)
            budget.record_run("object_embed")
        except Exception:  # noqa: BLE001 - object recognition is best-effort
            pass

    if embedding is not None and obs.identities:
        dec = obs.identities[-1]
        server.mm_last_face = {
            "bbox": face_bbox,
            "tier": dec.tier.value,
            "person": dec.person_id,
            "similarity": round(dec.similarity, 3),
            "proposal": bool(dec.new_person_proposal),
        }

    with server.mm_lock:
        server.mm_last_tracks = _build_overlay(server, obs, face_bbox)

    # Presence/scene salience -> the brain's input bus; a scene.changed event
    # forces every gated stage on the NEXT frame so novel content is embedded
    # immediately instead of waiting for the counters.
    events = server.mm_runtime.pop_pending_events()
    if any(str(ev.get("kind", "")) == "scene.changed" for ev in events):
        budget.mark_scene_change()
    server._forward_bus_events(events)
    budget.mark_processed()


def _enforce_embedding_bound(server, default_limit: int = 64) -> None:
    """FIFO-cap the label -> embedding cache used for GAP-3 naming.

    Each entry pins a full embedding vector; without a cap, every distinct
    label ever seen accumulates forever in a long-lived camera process. The
    cap comes from the server budgets so desktop/Jetson differ without code
    changes; servers without budgets (tests) use the default. Must run under
    ``server.mm_lock``.
    """
    budgets = getattr(server, "budgets", None)
    limit = max(1, int(getattr(budgets, "max_object_embeddings", default_limit)))
    cache = server.mm_last_object_embeddings
    while len(cache) > limit:
        cache.pop(next(iter(cache)))


def _embed_face(server, work) -> tuple[list[float] | None, tuple[int, int, int, int] | None]:
    """Largest-face embedding over the decoded array; legacy fallback re-encodes."""
    embedder = server.face_embedder
    if hasattr(embedder, "embed_bgr"):
        return embedder.embed_bgr(work.payload)
    jpeg = encode_bgr_jpeg(work.payload)
    if jpeg is None:
        return None, None
    return embedder.embed(jpeg)


def _build_overlay(server, obs, face_bbox) -> list[dict[str, Any]]:
    """Stable track labels for the camera overlay (named person boxes + objects)."""
    overlay: list[dict[str, Any]] = []
    for t in getattr(obs, "tracks", []) or []:
        entry: dict[str, Any] = {
            "track_id": t.track_id,
            "label": t.label,
            "bbox": list(t.bbox),
            "confirmed": bool(t.confirmed),
        }
        if t.label in PERSON_LABELS:
            name = server.mm_runtime.current_person or (
                "someone" if server.mm_last_face else None
            )
            if name:
                entry["name"] = f"{name} ({server.mm_runtime.current_person_tier or 'seen'})"
                entry["is_person"] = True
        overlay.append(entry)
    if server.mm_last_face and face_bbox:
        # the identified face box itself, named by tier
        overlay.append({
            "track_id": -1,
            "label": "face",
            "bbox": list(face_bbox),
            "confirmed": True,
            "is_person": True,
            "name": (
                server.mm_last_face.get("person")
                or ("new person — enroll" if server.mm_last_face.get("proposal") else "person?")
            ),
        })
    return overlay


def _now_ms() -> float:
    return time.monotonic() * 1000.0
