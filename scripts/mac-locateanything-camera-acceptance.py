#!/usr/bin/env python3
"""Real camera acceptance (plan Step 27).

Chain under test:
    real camera -> real frame -> LocateAnything -> typed grounding -> tracker

Runs the real SSDLite detector + real LocateAnything-3B (MPS) over one live
webcam frame, then ground_frame with generic queries. Privacy (plan §16):
- queries are generic object descriptions (no person/identity queries);
- the raw frame is NEVER persisted — evidence records typed observations,
  detections, latencies, and associations only.

Usage (requires camera permission for the calling app):
    HF_HOME=~/.cache/novi/models/locateanything-hf \
    .venv-locateanything/bin/python scripts/mac-locateanything-camera-acceptance.py

Writes docs/07-locate-anything/evidence/camera-acceptance-<ts>.json
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
os.environ.setdefault("HF_HOME", os.path.expanduser("~/.cache/novi/models/locateanything-hf"))

from novi.brain.io import MacCamera  # noqa: E402
from novi.perception.grounding import SpatialInferencePolicy, SpatialQuery  # noqa: E402
from novi.perception.locate_anything import LocateAnythingBackend  # noqa: E402
from novi.perception.locate_anything_runtime import LocateAnythingRuntime  # noqa: E402
from novi.perception.pipeline import PerceptionPipeline  # noqa: E402
from novi.perception.real_backends import TorchvisionPerceptionDetector  # noqa: E402

QUERIES = ("locate all objects visible in the image", "locate the largest object")


def _to_jpeg(frame) -> bytes | None:
    import cv2  # noqa: PLC0415

    ok, buf = cv2.imencode(".jpg", frame.payload)
    return bytes(buf.tobytes()) if ok else None


def main() -> int:
    evidence: dict = {
        "scenario": "real camera -> LocateAnything -> grounding -> tracker",
        "model": "nvidia/LocateAnything-3B @ c32291ca5e996f5a7a485845b4f57a233936bba0",
        "backend": "mps/bf16",
        "results": [],
    }

    print("[camera] opening MacCamera(device=0) ...")
    cam = MacCamera(device=0, width=640, height=480)
    try:
        cam.open()
    except Exception as exc:  # noqa: BLE001 — report honestly, don't guess
        print(f"[camera] UNAVAILABLE: {exc}")
        print("[camera] If this is a permission error: System Settings > Privacy & Security > Camera,")
        print("[camera] grant camera access to the terminal/host app, then re-run.")
        evidence["camera_status"] = f"unavailable: {exc}"
        _write(evidence)
        return 2

    try:
        warm = cam.read()  # discard warm-up frame (auto-exposure)
        frame = cam.read()
    except Exception as exc:  # noqa: BLE001
        print(f"[camera] read failed: {exc} (permission denied or device busy?)")
        evidence["camera_status"] = f"read_failed: {exc}"
        _write(evidence)
        return 2
    finally:
        cam.close()

    payload = _to_jpeg(frame)
    if payload is None:
        print("[camera] could not encode frame")
        return 2
    from dataclasses import replace  # noqa: PLC0415

    frame = replace(frame, payload=payload)
    evidence["frame"] = {
        "frame_id": frame.frame_id,
        "width": frame.width,
        "height": frame.height,
        "captured_at": frame.captured_at,
        "raw_frame_persisted": False,
    }
    print(f"[camera] frame {frame.frame_id} {frame.width}x{frame.height}")

    print("[model] loading SSDLite + LocateAnything ...")
    detector = TorchvisionPerceptionDetector(device="mps")
    backend = LocateAnythingBackend()
    backend.attach_runtime(LocateAnythingRuntime())
    caps = backend.capabilities()
    print(f"[model] grounding state={caps.state.value} device={caps.device}")
    if not caps.usable:
        print("[model] grounding backend not usable; aborting")
        return 2

    pipeline = PerceptionPipeline(detector=detector, grounding_backend=backend)

    t0 = time.perf_counter()
    world = pipeline.process_frame(frame)
    evidence["ssdlite"] = {
        "wall_ms": round((time.perf_counter() - t0) * 1000.0, 1),
        "detections": [
            {"label": d.label, "confidence": round(d.confidence, 3), "bbox": list(d.bbox)}
            for d in world.detections
        ],
        "tracks": [t.snapshot() for t in world.tracks],
    }
    print(f"[ssdlite] {len(world.detections)} detections, {len(world.tracks)} tracks")

    for query_text in QUERIES:
        query = SpatialQuery(text=query_text, frame_id=frame.frame_id, timestamp=frame.captured_at)
        t0 = time.perf_counter()
        outcome = pipeline.ground_frame(frame, query, SpatialInferencePolicy())
        rec = {
            "query": query_text,
            "wall_ms": round((time.perf_counter() - t0) * 1000.0, 1),
            "latency_ms": outcome.result.latency_ms,
            "success": outcome.result.success,
            "no_object": outcome.result.no_object,
            "validation_errors": list(outcome.result.validation_errors),
            "observations": [
                {
                    "label": o.label,
                    "source_box": getattr(o, "source_box", None),
                    "pixel_box": getattr(o, "pixel_box", None),
                    "provenance": o.provenance,
                }
                for o in outcome.result.observations
            ],
            "track_associations": [
                {"observation_label": a.observation.label, "track_id": a.track_id, "status": a.status}
                for a in outcome.associations
            ],
        }
        evidence["results"].append(rec)
        print(
            f"[grounding] {query_text[:45]:47s} ok={outcome.result.success} "
            f"obs={len(outcome.result.observations)} lat={outcome.result.latency_ms}ms"
        )
        _write(evidence)

    print("[done] evidence written (raw frame not persisted)")
    return 0


def _write(evidence: dict) -> None:
    out_dir = REPO_ROOT / "docs" / "07-locate-anything" / "evidence"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"camera-acceptance-{time.strftime('%Y%m%d-%H%M%S')}.json"
    path.write_text(json.dumps(evidence, indent=2))
    print(f"[evidence] {path}")


if __name__ == "__main__":
    raise SystemExit(main())
