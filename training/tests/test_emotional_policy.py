"""Tests for the emotional social policy ranking dataset (plan 24 §27, §51 item 28).

Phase 23 (§27) builds examples where multiple behaviors are possible: an
emotional/social state, candidate acts (including anti-patterns), and the
preferred mature act. The learned scorer ranks candidates; deterministic
rules remain authoritative.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from training.datasets.build_emotional_datasets import build_all
from training.schemas import (
    EMOTIONAL_ACTS,
    SOCIAL_POLICY_ACTS,
    validate_example,
)

DATASETS = Path(__file__).resolve().parents[1] / "datasets"
EMOTIONAL_DIR = DATASETS / "emotional"


def _load() -> list[dict]:
    path = EMOTIONAL_DIR / "policy_ranking.jsonl"
    assert path.exists(), f"missing: {path}"
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


class TestSocialPolicyActs:
    def test_includes_emotional_acts(self):
        assert EMOTIONAL_ACTS <= SOCIAL_POLICY_ACTS

    def test_includes_anti_patterns(self):
        assert {"DEFEND", "IGNORE", "OVER_ASK", "CHANGE_TOPIC", "MINIMIZE"} <= SOCIAL_POLICY_ACTS


class TestEmotionalPolicyDataset:
    def test_file_exists_and_has_rows(self):
        assert len(_load()) >= 200

    def test_all_rows_schema_valid(self):
        for ex in _load():
            assert validate_example(ex, kind="emotional_policy") == [], ex["example_id"]

    def test_builder_output_valid(self):
        for ex in build_all()["policy_ranking"]:
            assert validate_example(ex, kind="emotional_policy") == [], ex["example_id"]

    def test_all_rows_are_policy_ranking_task(self):
        for ex in _load():
            assert ex["task"] == "policy_ranking"

    def test_preferred_among_candidates(self):
        for ex in _load():
            assert ex["preferred"] in ex["candidates"], ex["example_id"]

    def test_candidates_are_social_policy_acts(self):
        for ex in _load():
            for c in ex["candidates"]:
                assert c in SOCIAL_POLICY_ACTS, (ex["example_id"], c)

    def test_unique_ids(self):
        seen = set()
        for ex in _load():
            assert ex["example_id"] not in seen, ex["example_id"]
            seen.add(ex["example_id"])

    def test_reproducible(self):
        script = DATASETS / "build_emotional_datasets.py"
        out = subprocess.run([sys.executable, str(script), "--check"], capture_output=True,
                             text=True, cwd=Path(__file__).resolve().parents[2])
        assert out.returncode == 0, out.stderr
        assert "OK" in out.stdout
