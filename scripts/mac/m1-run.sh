#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

source .venv/bin/activate

echo "=== NOVI MAC BRAIN — M1 ==="
echo "Root: $ROOT"
echo

echo "[1/4] Neural environment"
bash scripts/mac/neural-doctor.sh

echo

echo "[2/4] Known-image neural inference"
bash scripts/mac/m1-image-test.sh "${1:-test-image.png}"
echo

echo "[3/4] Mac Brain deterministic integration"
bash scripts/mac-brain-test.sh
echo

echo "[4/4] Evidence locations"
find mac_test_results/M1 -maxdepth 1 -type f -print 2>/dev/null | sort || true

echo
echo "M1 image stage complete. Run camera validation separately with:"
echo "  bash scripts/mac/m1-camera-test.sh"
echo "Do not treat M1 as accepted until image and camera evidence are reviewed."
