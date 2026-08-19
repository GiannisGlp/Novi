#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

echo "=== Novi Mac setup ==="
command -v python3 >/dev/null || { echo "Python 3 is required"; exit 1; }
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip

if [[ -f pyproject.toml ]]; then
  python -m pip install -e ".[test]" 2>/dev/null || python -m pip install -e .
elif [[ -f requirements.txt ]]; then
  python -m pip install -r requirements.txt
fi

if [[ -f requirements-dev.txt ]]; then
  python -m pip install -r requirements-dev.txt
fi

echo
echo "Setup complete. Activate with: source .venv/bin/activate"
echo "Next: bash scripts/mac/doctor.sh"
