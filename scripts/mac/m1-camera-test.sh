#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
source .venv/bin/activate
python scripts/mac/m1_neural.py camera --device "${1:-0}" --frames "${2:-5}"
