#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
fi

# Materialize the committed lowercase Python package separately from the
# uppercase MAC_BRAIN documentation directory. This avoids macOS
# case-insensitive filesystem collisions without changing the repository
# layout or executing stale working-tree copies.
PACKAGE_TMP="$(mktemp -d "${TMPDIR:-/tmp}/novi-mac-brain.XXXXXX")"
trap 'rm -rf "$PACKAGE_TMP"' EXIT

git archive --format=tar HEAD mac_brain | tar -x -C "$PACKAGE_TMP"
export PYTHONPATH="$PACKAGE_TMP:$ROOT${PYTHONPATH:+:$PYTHONPATH}"

exec "$PYTHON" -m mac_brain.cli "$@"
