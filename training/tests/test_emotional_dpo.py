"""Tests for the emotional DPO preference dataset (plan 24 §26, §51 item 26).

Phase 22 (§26) constructs preference pairs for the seven preference
dimensions (proportionality, naturalness, restraint, emotional timing,
humility, boundary respect, repair) and folds high-quality human-eval
pairwise results (§46) into the DPO dataset.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from training.datasets.build_emotional_datasets import (
    EMOTIONAL_DPO_FILE,
    build_emotional_dpo,
    fold_human_preferences,
)
from training.evaluation.emotional_scenarios import ALL_EMOTIONAL_SCENARIOS
from training.evaluation.human_eval import build_preference_record
from training.schemas import EMOTIONAL_PREFERENCE_CATEGORIES, validate_example

DATASETS = Path(__file__).resolve().parents[1] / "datasets"


def _load_dpo() -> list[dict]:
    return [json.loads(line) for line in EMOTIONAL_DPO_FILE.read_text().splitlines() if line.strip()]


class TestEmotionalDpoDataset:
    def test_dpo_file_exists_and_has_rows(self):
        assert EMOTIONAL_DPO_FILE.exists()
        assert len(_load_dpo()) >= 200

    def test_all_rows_schema_valid(self):
        for ex in build_emotional_dpo():
            assert validate_example(ex, kind="emotional") == [], ex["example_id"]

    def test_all_rows_are_preference_task(self):
        for ex in build_emotional_dpo():
            assert ex["task"] == "preference"

    def test_covers_all_plan_categories(self):
        cats = {ex["category"] for ex in build_emotional_dpo()}
        assert cats == EMOTIONAL_PREFERENCE_CATEGORIES

    def test_unique_ids(self):
        seen = set()
        for ex in build_emotional_dpo():
            assert ex["example_id"] not in seen, ex["example_id"]
            seen.add(ex["example_id"])

    def test_reproducible(self):
        script = DATASETS / "build_emotional_datasets.py"
        out = subprocess.run([sys.executable, str(script), "--check"], capture_output=True,
                             text=True, cwd=Path(__file__).resolve().parents[2])
        assert out.returncode == 0, out.stderr
        assert "OK" in out.stdout


class TestFoldHumanPreferences:
    def test_folds_preference_record(self):
        scenario = ALL_EMOTIONAL_SCENARIOS[0]
        rec = build_preference_record(scenario, "A response", "B response", "B")
        ex = fold_human_preferences([rec])[0]
        assert ex["task"] == "preference"
        assert ex["response_a"] == "A response"
        assert ex["response_b"] == "B response"
        assert ex["preferred"] == "B"
        assert ex["category"] in EMOTIONAL_PREFERENCE_CATEGORIES
        assert ex["synthetic"] is False
        assert validate_example(ex, kind="emotional") == []

    def test_derives_situation_from_scenario(self):
        scenario = ALL_EMOTIONAL_SCENARIOS[0]
        rec = build_preference_record(scenario, "a", "b", "A")
        ex = fold_human_preferences([rec])[0]
        sit = ex["situation"]
        assert sit["relationship"] == "owner"
        assert sit["conversation_phase"] == "tension"
        assert sit["interruptibility"] == 0.2
        assert sit["affective_hypotheses"] == [{"label": "frustration", "probability": 0.7}]

    def test_derives_desired_behavior_from_scenario(self):
        scenario = ALL_EMOTIONAL_SCENARIOS[0]
        rec = build_preference_record(scenario, "a", "b", "A")
        ex = fold_human_preferences([rec])[0]
        assert ex["desired_behavior"]["act"] == ["ACKNOWLEDGE", "APOLOGIZE", "SOLVE"]

    def test_category_derived_from_scenario_acts(self):
        # scenario 01 expects APOLOGIZE -> humility
        rec = build_preference_record(ALL_EMOTIONAL_SCENARIOS[0], "a", "b", "A")
        assert fold_human_preferences([rec])[0]["category"] == "humility"
        # scenario 11 expects GIVE_SPACE/SILENCE -> restraint
        rec = build_preference_record(ALL_EMOTIONAL_SCENARIOS[10], "a", "b", "A")
        assert fold_human_preferences([rec])[0]["category"] == "restraint"

    def test_unique_ids(self):
        scenario = ALL_EMOTIONAL_SCENARIOS[0]
        recs = [build_preference_record(scenario, "a", "b", "A") for _ in range(3)]
        exs = fold_human_preferences(recs)
        ids = {ex["example_id"] for ex in exs}
        assert len(ids) == 3

    def test_rejects_unknown_scenario(self):
        rec = {
            "kind": "preference",
            "scenario_id": "99",
            "scenario_name": "nope",
            "input_event": "x",
            "response_a": "a",
            "response_b": "b",
            "preferred": "A",
            "category": "emotional_maturity",
            "reviewer": "human",
        }
        with pytest.raises(ValueError):
            fold_human_preferences([rec])
