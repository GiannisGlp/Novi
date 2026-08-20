#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
source .venv/bin/activate

python - <<'PY'
import json
import platform
import subprocess
import sys
from pathlib import Path

result = {
    "python": sys.version,
    "python_executable": sys.executable,
    "platform": platform.platform(),
    "machine": platform.machine(),
}

try:
    import torch
    result["torch"] = torch.__version__
    result["mps_built"] = bool(torch.backends.mps.is_built())
    result["mps_available"] = bool(torch.backends.mps.is_available())
except Exception as exc:
    result["torch_error"] = repr(exc)

try:
    import torchvision
    result["torchvision"] = torchvision.__version__
except Exception as exc:
    result["torchvision_error"] = repr(exc)

try:
    import PIL
    result["pillow"] = PIL.__version__
except Exception as exc:
    result["pillow_error"] = repr(exc)

try:
    import cv2
    result["opencv"] = cv2.__version__
except Exception as exc:
    result["opencv_error"] = repr(exc)

print(json.dumps(result, indent=2))
Path("mac_test_results").mkdir(exist_ok=True)
Path("mac_test_results/neural_environment.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

required = ["torch", "torchvision", "pillow"]
missing = [key for key in required if key not in result]
if missing:
    print("NEURAL DOCTOR: FAIL — missing:", ", ".join(missing))
    raise SystemExit(1)

print("NEURAL DOCTOR: PASS")
PY
