#!/usr/bin/env bash
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

python3 scripts/mac/runner.py --suite all
status=$?

echo
echo "Mac test results are stored under: mac_test_results/"
echo "Latest summary: mac_test_results/latest/summary.json"
exit "$status"
