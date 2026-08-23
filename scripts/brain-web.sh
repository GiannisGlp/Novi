#!/usr/bin/env bash
# Launch the Novi Mac Brain live web app (stdlib http.server, no installs).
#
#   ./scripts/mac-web.sh [--host 127.0.0.1] [--port 8080] [--store ~/novi_web.db]
#                        [--tick 0.8] [--no-auto-step]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
fi
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
# PyAV (faster-whisper) + OpenCV each bundle libavdevice; silence the benign
# duplicate-class objc notice on macOS (verified harmless in this setup).
export OBJC_DEBUG_DUPLICATE_CLASSES=0

HOST="${NOVI_HOST:-127.0.0.1}"
PORT="${NOVI_PORT:-8080}"
STORE="${NOVI_STORE:-$ROOT/novi/db/novi_web.db}"
TICK="${NOVI_TICK:-0.8}"

echo "Starting Novi web app -> http://$HOST:$PORT"
echo "  durable store : $STORE"
echo "  auto-step every ${TICK}s (Ctrl-C to stop)"
exec "$PYTHON" -m novi.web.server --host "$HOST" --port "$PORT" --store "$STORE" --tick "$TICK" "$@"
