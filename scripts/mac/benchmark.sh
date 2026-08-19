#!/usr/bin/env bash
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

RUNNER="scripts/mac/runner.py"
if [[ ! -f "$RUNNER" ]]; then
  echo "Missing Mac runner: $RUNNER" >&2
  exit 1
fi

echo "=== Novi Mac benchmark/evidence entrypoint ==="
echo "This command records deterministic test timing and environment metadata."
echo "It is NOT NVIDIA GPU performance evidence."
python3 "$RUNNER" --suite brain
status=$?
echo "Benchmark/test evidence: mac_test_results/latest/"
exit "$status"
