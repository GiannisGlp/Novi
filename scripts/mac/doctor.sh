#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

echo "=== Novi Mac Doctor ==="
printf 'OS: '; uname -a
printf 'Python: '; python3 --version || true
printf 'Git: '; git --version || true
printf 'Pytest: '; pytest --version 2>/dev/null || echo 'not installed'
printf 'Coverage: '; coverage --version 2>/dev/null || echo 'not installed'
printf 'Ruff: '; ruff --version 2>/dev/null || echo 'not installed'
printf 'Mypy: '; mypy --version 2>/dev/null || echo 'not installed'
printf 'Node: '; node --version 2>/dev/null || echo 'not installed'
printf 'Docker: '; docker --version 2>/dev/null || echo 'not installed'
echo
echo "Git branch: $(git branch --show-current)"
echo "Git commit: $(git rev-parse HEAD)"
echo "Working tree:"
git status --short

echo
echo "Result collector:"
python3 scripts/mac/runner.py --suite doctor
