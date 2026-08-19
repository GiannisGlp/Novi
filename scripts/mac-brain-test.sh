#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PYTHON="${PYTHON:-python3}"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
fi

# Always make the repository root the Python import root. This keeps unittest
# discovery stable across macOS shells, Python versions and invocation paths.
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$ROOT/mac_test_results/mac_brain/$RUN_ID"
mkdir -p "$OUT"

set +e
"$PYTHON" -m unittest discover -s "$ROOT/mac_brain/tests" -t "$ROOT" -p 'test_*.py' >"$OUT/tests.log" 2>&1
TEST_STATUS=$?
"$PYTHON" -m mac_brain.cli --cycles 3 --evidence "$OUT/runtime.json" >"$OUT/runtime.log" 2>&1
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
