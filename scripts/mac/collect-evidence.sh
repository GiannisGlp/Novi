#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

if [[ ! -d mac_test_results ]]; then
  echo "No Mac test results exist yet. Run bash scripts/mac/test.sh first." >&2
  exit 1
fi

LATEST="mac_test_results/latest"
if [[ ! -e "$LATEST" ]]; then
  echo "No latest Mac test run found." >&2
  exit 1
fi

mkdir -p IMPLEMENTATION_PLAN/EVIDENCE/mac
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DEST="IMPLEMENTATION_PLAN/EVIDENCE/mac/$STAMP"
mkdir -p "$DEST"
cp -R "$LATEST"/* "$DEST"/

git rev-parse HEAD > "$DEST/commit_sha.txt"
printf 'Collected UTC: ' > "$DEST/collection_time.txt"
date -u +%Y-%m-%dT%H:%M:%SZ >> "$DEST/collection_time.txt"

echo "Evidence snapshot: $DEST"
