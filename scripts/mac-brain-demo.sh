#!/usr/bin/env bash
# Convenience launcher for the Novi Mac Brain.
#
#   ./scripts/mac-brain-demo.sh [MODE] [extra CLI args...]
#
# MODE (default: live):
#   live    full interactive demo: webcam + neural vision + STT + reasoning
#           router (local qwen) + Soul + TTS + durable memory  (default)
#   neural  real neural (MPS) object detection on a static image, no camera
#   hear    offline demo-hear session (deterministic speech, no microphone)
#   quick   deterministic brain, no camera/mic/model (works anywhere)
#   *       anything else is passed straight through to the CLI
#
# Tune with env vars (overrides the defaults):
#   NOVI_ROUNDS=3 NOVI_LIVE_STEPS=1 NOVI_LISTEN_SECONDS=3 NOVI_STT_MODEL=base
#   NOVI_VOICE=Samantha NOVI_STORE=~/novi_demo.db NOVI_GOAL_TARGET=1,2
#   NOVI_NO_CAMERA=1   (use the deterministic camera instead of the webcam)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
fi
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
# PyAV (needed by faster-whisper) and OpenCV each bundle libavdevice; loading
# both prints a duplicate-class objc notice on macOS. Verified benign here
# (camera uses cv2, mic uses sounddevice), so silence the noise.
export OBJC_DEBUG_DUPLICATE_CLASSES=0

MODE="${1:-live}"
shift || true

ROUNDS="${NOVI_ROUNDS:-3}"
LIVE_STEPS="${NOVI_LIVE_STEPS:-8}"
LISTEN_SECONDS="${NOVI_LISTEN_SECONDS:-2}"
STT_MODEL="${NOVI_STT_MODEL:-base}"
VOICE="${NOVI_VOICE:-Samantha}"
STORE="${NOVI_STORE:-$ROOT/novi_demo.db}"
CAMERA_FLAG="--live-camera"
if [[ "${NOVI_NO_CAMERA:-0}" == "1" ]]; then
  CAMERA_FLAG=""
fi

note() { printf "\n\033[1;36m[NOVI] %s\033[0m\n" "$*" >&2; }

case "$MODE" in
  live)
    note "full live demo: webcam + neural vision + STT + router reasoning + TTS"
    if [[ -z "$CAMERA_FLAG" ]]; then
      note "NOVI_NO_CAMERA=1 -> deterministic camera (no webcam needed)"
    fi
    if ! command -v say >/dev/null 2>&1; then
      note "macOS 'say' not found; TTS will be skipped"
    fi
    exec "$PYTHON" -m MAC_BRAIN.cli \
      --live --rounds "$ROUNDS" --live-steps "$LIVE_STEPS" \
      $CAMERA_FLAG --neural \
      --reasoning router --listen-seconds "$LISTEN_SECONDS" --stt-model "$STT_MODEL" \
      --say --say-voice "$VOICE" --store "$STORE" "$@"
    ;;
  neural)
    note "real neural (MPS) object detection on test-image.png (no camera)"
    exec "$PYTHON" -m MAC_BRAIN.cli --cycles "${NOVI_CYCLES:-5}" --neural \
      --neural-image test-image.png --store "$STORE" "$@"
    ;;
  image)
    note "real neural (MPS) object detection on test-image.png (alias of 'neural')"
    exec "$PYTHON" -m MAC_BRAIN.cli --cycles "${NOVI_CYCLES:-5}" --neural \
      --neural-image test-image.png --store "$STORE" "$@"
    ;;
  hear)
    note "offline demo-hear session (deterministic speech, no microphone)"
    exec "$PYTHON" -m MAC_BRAIN.cli --cycles "${NOVI_CYCLES:-8}" \
      --demo-hear "${NOVI_DEMO_HEAR:-alice moved the door}" --store "$STORE" "$@"
    ;;
  quick)
    note "deterministic brain snapshot (no camera/mic/model needed)"
    exec "$PYTHON" -m MAC_BRAIN.cli --cycles "${NOVI_CYCLES:-10}" --store "$STORE" "$@"
    ;;
  *)
    note "passing arguments straight through to MAC_BRAIN.cli"
    exec "$PYTHON" -m MAC_BRAIN.cli "$@"
    ;;
esac
