#!/usr/bin/env bash
# Isolated LocateAnything environment (docs/plans/LOCATE_ANYTHING_IMPLEMENTATION_PLAN_2026-08-28.md,
# Phase 4 Step 4.1 / §19 step 8).
#
# Deliberately does NOT touch the default Novi .venv: LocateAnything brings a large
# optional dependency set (transformers, timm, sentencepiece, ...) that must not
# contaminate the stdlib-first core until Mac compatibility is proven.
#
# Creates:
#   .venv-locateanything/          Python 3.11 venv (gitignored)
#   ~/.cache/novi/models/locateanything-hf/   pinned model snapshot (gitignored)
#
# Usage:  scripts/mac-locateanything-env.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$REPO_ROOT/.venv-locateanything"
PY=3.11
MODEL_REPO="nvidia/LocateAnything-3B"
# Pinned revision (freeze record: docs/07-locate-anything/06_ARCHITECTURE_DECISION.md §0.2).
MODEL_REV="c32291ca5e996f5a7a485845b4f57a233936bba0"
HF_HOME="$HOME/.cache/novi/models/locateanything-hf"
LOG="$REPO_ROOT/.venv-locateanything-setup.log"

mkdir -p "$HF_HOME"
echo "==> Creating $VENV (python $PY)"
uv venv "$VENV" --python "$PY"

echo "==> Installing runtime deps (torch/transformers/accelerate/sentencepiece/peft/timm)"
uv pip install --python "$VENV/bin/python" \
    "transformers==4.57.1" "tokenizers==0.22.0" \
    torch accelerate sentencepiece peft timm \
    2>&1 | tee -a "$LOG"

echo "==> Installing remote-code deps (required by the model's remote modeling files)"
# Note: decord (upstream dep for video decoding) has no macOS arm64 wheel;
# a loud-failing stub is installed instead (see below). The released
# image-grounding path never imports decord's VideoReader.
uv pip install --python "$VENV/bin/python" \
    torchvision opencv-python-headless lmdb requests \
    2>&1 | tee -a "$LOG"

echo "==> Installing decord stub (no macOS arm64 wheel; video path unsupported)"
cat > "$VENV/lib/python3.11/site-packages/decord.py" <<'PY'
class VideoReader:
    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            "decord is unavailable on macOS arm64 (no wheel); "
            "video decoding is not supported in this environment"
        )
PY

echo "==> Downloading $MODEL_REPO @ $MODEL_REV (excluding demo assets)"
HF_HOME="$HF_HOME" "$VENV/bin/python" - <<'PY' 2>&1 | tee -a "$LOG"
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="nvidia/LocateAnything-3B",
    revision="c32291ca5e996f5a7a485845b4f57a233936bba0",
    allow_patterns=[
        "*.safetensors", "*.json", "*.txt", "*.model", "*.py", "*.md",
    ],
    ignore_patterns=["assets/*"],
)
print("snapshot_download complete")
PY

echo "==> Done. Python:"
"$VENV/bin/python" --version
"$VENV/bin/python" -c "import torch, transformers; print('torch', torch.__version__, '| transformers', transformers.__version__)"
