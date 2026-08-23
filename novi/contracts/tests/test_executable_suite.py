#!/usr/bin/env python3
"""Pytest shim for the executable contracts validation suite.

The contracts suite is a set of standalone executable validators (registry,
schema, fixtures, compatibility, integration, persistence, semantic). This
shim runs every validator as a subprocess and fails the pytest run when any
validator exits non-zero, so the suite is CI-runnable via ``pytest contract``
as required by the brain-phase gap analysis (Step 0, item 3).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]  # repo root (novi/contracts/tests -> repo)
SUITE_ROOT = Path(__file__).resolve().parent

# Generator that must run first (fixtures are not committed; they are
# regenerated from the registry schemas before validation).
GENERATORS = [
    SUITE_ROOT / "generate_fixtures.py",
]

# Validators, in dependency order (fixture generator must run first).
VALIDATORS = sorted(
    path for path in SUITE_ROOT.rglob("*.py") if path.is_file()
    and "__main__" in path.read_text(encoding="utf-8")
    and path.name != "generate_fixtures.py"
    and path.name != "event_envelope_adapter.py"
)


@pytest.fixture(scope="session", autouse=True)
def generated_fixtures() -> None:
    """Regenerate deterministic fixtures from registry schemas before validation."""
    for script in GENERATORS:
        result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, cwd=ROOT)
        assert result.returncode == 0, (
            f"fixture generator {script.name} failed:\n{result.stdout}\n{result.stderr}"
        )


@pytest.mark.parametrize(
    "script",
    [pytest.param(p, id=p.relative_to(SUITE_ROOT).as_posix()) for p in VALIDATORS],
)
def test_contract_validator_runs_clean(script: Path) -> None:
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, cwd=ROOT)
    assert result.returncode == 0, (
        f"validator {script.name} failed:\n{result.stdout}\n{result.stderr}"
    )
