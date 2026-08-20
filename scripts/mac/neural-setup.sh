#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  echo "No .venv found. Run: bash scripts/mac/setup.sh"
  exit 1
fi
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install torch torchvision pillow numpy opencv-python sounddevice faster-whisper

python - <<'PY'
import torch
import torchvision
print("PyTorch:", torch.__version__)
print("torchvision:", torchvision.__version__)
print("MPS built:", torch.backends.mps.is_built())
print("MPS available:", torch.backends.mps.is_available())
try:
    import faster_whisper
    print("faster-whisper:", faster_whisper.__version__)
except Exception as exc:
    print("faster-whisper: unavailable", exc)
PY

echo "Neural runtime setup complete."
