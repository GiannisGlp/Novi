#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON="${PYTHON:-$ROOT/.venv/bin/python3}"

if [[ ! -x "$PYTHON" ]]; then
  echo "Missing Novi virtualenv Python: $PYTHON" >&2
  exit 2
fi

IMAGE="${1:-}"
if [[ -z "$IMAGE" ]]; then
  echo "Usage: bash scripts/mac/neural-smoke.sh /path/to/image.jpg" >&2
  exit 2
fi

exec "$PYTHON" - "$ROOT" "$IMAGE" <<'PY'
import json
import sys
import time
from pathlib import Path

root = Path(sys.argv[1])
image_path = Path(sys.argv[2]).expanduser().resolve()
sys.path.insert(0, str(root))

import torch
from PIL import Image
from novi.brain.models.torchvision_detector import TorchvisionSSDLiteDetector

mps = bool(hasattr(torch.backends, "mps") and torch.backends.mps.is_available())
start_load = time.perf_counter()
detector = TorchvisionSSDLiteDetector()
load_seconds = time.perf_counter() - start_load

image = Image.open(image_path).convert("RGB")
start_infer = time.perf_counter()
detections = detector.detect(image)
infer_seconds = time.perf_counter() - start_infer

result = {
    "result": "PASS",
    "image": str(image_path),
    "image_size": list(image.size),
    "python": sys.version,
    "pytorch": torch.__version__,
    "mps_available": mps,
    "device": detector.device,
    "model_id": detector.model_id,
    "load_seconds": round(load_seconds, 4),
    "inference_seconds": round(infer_seconds, 4),
    "detections": [
        {
            "label": d.label,
            "confidence": d.confidence,
            "bbox": list(d.bbox),
            "provenance": d.provenance,
        }
        for d in detections
    ],
}
print(json.dumps(result, indent=2))
PY
