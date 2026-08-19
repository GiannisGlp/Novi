#!/usr/bin/env bash
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
python3 scripts/mac/runner.py --suite full
exit $?
