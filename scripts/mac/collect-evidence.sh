#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

if [[ ! -d mac_test_results ]]; then
  echo "No Mac test results exist yet." >&2
  exit 1
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DEST="IMPLEMENTATION_PLAN/EVIDENCE/mac/$STAMP"
mkdir -p "$DEST"

if [[ -e mac_test_results/latest ]]; then
  cp -R mac_test_results/latest/* "$DEST/" 2>/dev/null || true
fi
if [[ -f mac_test_results/neural_environment.json ]]; then
  cp mac_test_results/neural_environment.json "$DEST/"
fi
if [[ -f mac_test_results/M1/latest.json ]]; then
  cp mac_test_results/M1/latest.json "$DEST/M1-latest.json"
fi
if [[ -f novi/assets/test-image.png ]]; then
  cp novi/assets/test-image.png "$DEST/"
fi

git rev-parse HEAD > "$DEST/commit_sha.txt"
printf 'Collected UTC: ' > "$DEST/collection_time.txt"
date -u +%Y-%m-%dT%H:%M:%SZ >> "$DEST/collection_time.txt"

echo "Evidence snapshot: $DEST"
find "$DEST" -maxdepth 1 -type f -print | sort
