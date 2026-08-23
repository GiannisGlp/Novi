#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PYTHON="${PYTHON:-python3}"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
fi
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$ROOT/mac_test_results/brain/$RUN_ID"
mkdir -p "$OUT"

set +e
"$PYTHON" -m unittest discover -s "$ROOT/novi/brain/tests" -t "$ROOT" -p 'test_*.py' >"$OUT/tests.log" 2>&1
TEST_STATUS=$?
"$PYTHON" -m novi.brain.cli --cycles 3 --evidence "$OUT/runtime.json" >"$OUT/runtime.log" 2>&1
RUNTIME_STATUS=$?
set -e

RESULT=PASS
if [[ "$TEST_STATUS" -ne 0 || "$RUNTIME_STATUS" -ne 0 ]]; then RESULT=FAIL; fi
cat >"$OUT/summary.json" <<EOF
{
  "run_id": "$RUN_ID",
  "test_status": $TEST_STATUS,
  "runtime_status": $RUNTIME_STATUS,
  "result": "$RESULT"
}
EOF

cat "$OUT/summary.json"
exit $(( TEST_STATUS != 0 || RUNTIME_STATUS != 0 ))
