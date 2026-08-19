#!/usr/bin/env bash
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
python3 scripts/mac/runner.py --suite brain
status=$?
echo "Brain test results: mac_test_results/latest/"
exit "$status"
