#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PYTHON="${PYTHON:-python3}"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
fi

# macOS commonly uses a case-insensitive filesystem. The repository contains
# the documentation directory MAC_BRAIN and the executable Python package
# MAC_BRAIN. A case-insensitive checkout can merge those paths in the working
# tree even though Git stores them separately. Materialize the tracked Python
# package into an isolated temporary directory from Git's object database so
# tests always execute the exact committed package.
PACKAGE_TMP="$(mktemp -d "${TMPDIR:-/tmp}/novi-mac-brain.XXXXXX")"
trap 'rm -rf "$PACKAGE_TMP"' EXIT

git archive --format=tar HEAD MAC_BRAIN | tar -x -C "$PACKAGE_TMP"
export PYTHONPATH="$PACKAGE_TMP:$ROOT${PYTHONPATH:+:$PYTHONPATH}"

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$ROOT/mac_test_results/MAC_BRAIN/$RUN_ID"
mkdir -p "$OUT"

set +e
"$PYTHON" -m unittest discover -s "$PACKAGE_TMP/MAC_BRAIN/tests" -t "$PACKAGE_TMP" -p 'test_*.py' >"$OUT/tests.log" 2>&1
TEST_STATUS=$?
"$PYTHON" -m MAC_BRAIN.cli --cycles 3 --evidence "$OUT/runtime.json" >"$OUT/runtime.log" 2>&1
RUNTIME_STATUS=$?
set -e

cat >"$OUT/summary.json" <<EOF
{
  "run_id": "$RUN_ID",
  "test_status": $TEST_STATUS,
  "runtime_status": $RUNTIME_STATUS,
  "result": "$([ "$TEST_STATUS" -eq 0 ] && [ "$RUNTIME_STATUS" -eq 0 ] && echo PASS || echo FAIL)"
}
EOF

cat "$OUT/summary.json"
exit $(( TEST_STATUS != 0 || RUNTIME_STATUS != 0 ))
