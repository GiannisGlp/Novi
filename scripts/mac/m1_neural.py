#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Running a file under scripts/mac directly makes sys.path point at scripts/mac,
# not the repository root. Add the root explicitly so the canonical brain
# package can always be imported from any working directory.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RESULTS = ROOT / "mac_test_results" / "M1"


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def base_evidence() -> dict:
    import torch
    import torchvision
    return {
        "timestamp_utc": now(),
        "repository": "GiannisGlp/Novi",
        "commit_sha": __import__("subprocess").check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": sys.version,
        "pytorch": torch.__version__,
        "torchvision": torchvision.__version__,
        "mps_built": bool(torch.backends.mps.is_built()),
        "mps_available": bool(torch.backends.mps.is_available()),
    }


def run_image(path: Path) -> int:
    from PIL import Image
    from novi.brain.models.torchvision_detector import TorchvisionSSDLiteDetector

    evidence = base_evidence()
    evidence["test"] = "M1-image"
    evidence["input"] = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    image = Image.open(path).convert("RGB")

    start = time.perf_counter()
    detector = TorchvisionSSDLiteDetector()
    load_seconds = time.perf_counter() - start

    start = time.perf_counter()
    detections = detector.detect(image)
    inference_seconds = time.perf_counter() - start

    evidence.update({
        "model_id": detector.model_id,
        "device": detector.device,
        "model_load_seconds": round(load_seconds, 6),
        "inference_seconds": round(inference_seconds, 6),
        "detections": [
            {"label": d.label, "confidence": d.confidence, "bbox": list(d.bbox), "provenance": d.provenance}
            for d in detections
        ],
        "status": "PASS",
    })
    write_evidence(evidence, "image")
    print(json.dumps(evidence, indent=2))
    return 0


def run_camera(device: int, frames: int) -> int:
    from novi.brain.io import MacCamera
    from novi.brain.models.torchvision_detector import TorchvisionSSDLiteDetector

    evidence = base_evidence()
    evidence["test"] = "M1-camera"
    evidence["camera_device"] = device
    evidence["requested_frames"] = frames

    detector = TorchvisionSSDLiteDetector()
    camera = MacCamera(device=device)
    frame_results = []
    try:
        camera.open()
        for _ in range(frames):
            frame = camera.read()
            start = time.perf_counter()
            detections = detector.detect(frame.payload)
            elapsed = time.perf_counter() - start
            frame_results.append({
                "frame_id": frame.frame_id,
                "captured_at": frame.captured_at,
                "width": frame.width,
                "height": frame.height,
                "inference_seconds": round(elapsed, 6),
                "detections": [
                    {"label": d.label, "confidence": d.confidence, "bbox": list(d.bbox), "provenance": d.provenance}
                    for d in detections
                ],
            })
    finally:
        camera.close()

    evidence.update({"model_id": detector.model_id, "device": detector.device, "frames": frame_results, "status": "PASS"})
    write_evidence(evidence, "camera")
    print(json.dumps(evidence, indent=2))
    return 0


def write_evidence(evidence: dict, name: str) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = RESULTS / f"{name}-{stamp}.json"
    path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    (RESULTS / "latest.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(f"Evidence: {path.relative_to(ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    image = sub.add_parser("image")
    image.add_argument("path", nargs="?", default="test-image.png")
    camera = sub.add_parser("camera")
    camera.add_argument("--device", type=int, default=0)
    camera.add_argument("--frames", type=int, default=5)
    args = parser.parse_args()

    if args.command == "image":
        path = ROOT / args.path
        if not path.exists():
            print(f"Input image not found: {path}", file=sys.stderr)
            return 2
        return run_image(path)
    return run_camera(args.device, args.frames)


if __name__ == "__main__":
    raise SystemExit(main())
