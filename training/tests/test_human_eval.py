"""Tests for the emotional human evaluation tool (plan 24 §46, §51 item 25).

Reviewers score each response 1-5 on the nine §46 dimensions and record
pairwise A/B preferences; high-quality pairwise results feed the DPO
preference dataset (§26, §51 item 26).
"""

from __future__ import annotations

import json

import pytest

from training.evaluation.emotional_scenarios import ALL_EMOTIONAL_SCENARIOS
from training.evaluation.human_eval import (
    HUMAN_EVAL_DIMENSIONS,
    build_preference_record,
    build_rating_record,
    write_records,
)


def _scores(**overrides) -> dict:
    s = {d: 4 for d in HUMAN_EVAL_DIMENSIONS}
    s.update(overrides)
    return s


class TestHumanEvalDimensions:
    def test_nine_plan_dimensions(self):
        assert HUMAN_EVAL_DIMENSIONS == (
            "emotional_appropriateness", "social_maturity", "naturalness",
            "restraint", "humility", "context_awareness", "boundary_respect",
            "repair_quality", "supportiveness",
        )


class TestRatingRecord:
    def test_build_rating_record(self):
        scenario = ALL_EMOTIONAL_SCENARIOS[0]
        rec = build_rating_record(scenario, "Yeah, that's on me.",
                                  _scores(), model_id="emotional_baseline")
        assert rec["scenario_id"] == "01"
        assert rec["scenario_name"] == "user frustration"
        assert rec["input_event"] == scenario.input_event
        assert rec["response"] == "Yeah, that's on me."
        assert rec["model_id"] == "emotional_baseline"
        assert rec["reviewer"] == "human"
        assert len(rec["scores"]) == 9
        assert all(1 <= v <= 5 for v in rec["scores"].values())

    def test_rejects_out_of_range_score(self):
        scenario = ALL_EMOTIONAL_SCENARIOS[0]
        with pytest.raises(ValueError):
            build_rating_record(scenario, "x", _scores(naturalness=6))

    def test_rejects_below_range_score(self):
        scenario = ALL_EMOTIONAL_SCENARIOS[0]
        with pytest.raises(ValueError):
            build_rating_record(scenario, "x", _scores(restraint=0))

    def test_requires_all_dimensions(self):
        scenario = ALL_EMOTIONAL_SCENARIOS[0]
        with pytest.raises(ValueError):
            build_rating_record(scenario, "x", {"naturalness": 4})

    def test_unknown_dimension_rejected(self):
        scenario = ALL_EMOTIONAL_SCENARIOS[0]
        with pytest.raises(ValueError):
            build_rating_record(scenario, "x", _scores(telepathy=4))


class TestPreferenceRecord:
    def test_build_preference_record(self):
        scenario = ALL_EMOTIONAL_SCENARIOS[0]
        rec = build_preference_record(scenario, "A response", "B response", "B")
        assert rec["scenario_id"] == "01"
        assert rec["response_a"] == "A response"
        assert rec["response_b"] == "B response"
        assert rec["preferred"] == "B"
        assert rec["category"] == "emotional_maturity"
        assert rec["reviewer"] == "human"

    def test_rejects_bad_preferred(self):
        scenario = ALL_EMOTIONAL_SCENARIOS[0]
        with pytest.raises(ValueError):
            build_preference_record(scenario, "a", "b", "C")

    def test_rejects_empty_responses(self):
        scenario = ALL_EMOTIONAL_SCENARIOS[0]
        with pytest.raises(ValueError):
            build_preference_record(scenario, "", "b", "B")


class TestWriteRecords:
    def test_writes_jsonl(self, tmp_path):
        scenario = ALL_EMOTIONAL_SCENARIOS[0]
        recs = [build_rating_record(scenario, "x", _scores())]
        out = tmp_path / "results.jsonl"
        write_records(recs, out)
        lines = out.read_text().splitlines()
        assert len(lines) == 1
        assert json.loads(lines[0])["scenario_id"] == "01"

    def test_writes_mixed_records(self, tmp_path):
        scenario = ALL_EMOTIONAL_SCENARIOS[0]
        recs = [
            build_rating_record(scenario, "x", _scores()),
            build_preference_record(scenario, "a", "b", "A"),
        ]
        out = tmp_path / "results.jsonl"
        write_records(recs, out)
        assert len(out.read_text().splitlines()) == 2

    def test_empty_records_writes_empty_file(self, tmp_path):
        out = tmp_path / "results.jsonl"
        write_records([], out)
        assert out.read_text() == ""
