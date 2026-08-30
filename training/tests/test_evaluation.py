"""Tests for the behavioral evaluation suite (plan 23 §19–§20)."""

from __future__ import annotations

import pytest

from training.evaluation.benchmark import BaselinePolicy, run_benchmark, score_records
from training.evaluation.metrics import (
    ambiguous_action_execution_rate,
    appropriate_initiative_rate,
    assistant_phrase_rate,
    context_continuity,
    false_grounding_rate,
    identity_false_positive_rate,
    object_grounding_accuracy,
    person_grounding_accuracy,
    repetition_rate,
    retrieval_precision,
    retrieval_recall,
    unnecessary_verbosity_rate,
    unsafe_action_proposal_rate,
    unsupported_claim_rate,
)
from training.evaluation.scenarios import ALL_SCENARIOS
from training.schemas import DIALOGUE_ACTS


def _record(**overrides) -> dict:
    rec = {
        "response": "The mug is on the desk.",
        "dialogue_act": "RESPOND",
        "expected_act": "RESPOND",
        "evidence": ["mug on desk"],
        "retrieved_memories": ["mem-1"],
        "relevant_memories": ["mem-1"],
        "topic": "mug",
        "prev_topic": "mug",
        "person_confidence": 0.98,
        "claimed_person_known": True,
    }
    rec.update(overrides)
    return rec


class TestScenarioCatalog:
    def test_exactly_30_scenarios(self):
        assert len(ALL_SCENARIOS) == 30

    def test_unique_ids_and_valid_acts(self):
        ids = [s.scenario_id for s in ALL_SCENARIOS]
        assert len(ids) == len(set(ids))
        for s in ALL_SCENARIOS:
            for act in s.expected_acts:
                assert act in DIALOGUE_ACTS, (s.scenario_id, act)

    def test_plan_scenario_names_present(self):
        names = {s.name for s in ALL_SCENARIOS}
        for expected in ("simple greeting", "memory recall", "contradictory memory",
                         "ambiguous object reference", "unknown person", "proactive silence",
                         "safety-critical event", "noisy ASR", "multi-person conversation"):
            assert expected in names

    def test_scenarios_carry_metric_groups(self):
        for s in ALL_SCENARIOS:
            assert s.metric_groups
            for g in s.metric_groups:
                assert g in ("naturalness", "grounding", "memory", "initiative", "safety")


class TestNaturalnessMetrics:
    def test_assistant_phrase_rate(self):
        recs = [_record(response="Yeah, that makes sense."),
                _record(response="I acknowledge your statement."),
                _record(response="I can confirm that the mug is there.")]
        assert assistant_phrase_rate(recs) == pytest.approx(2 / 3)

    def test_repetition_rate(self):
        recs = [_record(response="The mug is here.", topic="mug"),
                _record(response="The mug is here.", topic="mug"),
                _record(response="Different.", topic="mug")]
        assert repetition_rate(recs) == pytest.approx(1 / 3)

    def test_unnecessary_verbosity(self):
        long = "word " * 200
        recs = [_record(response=long), _record(response="short.")]
        assert unnecessary_verbosity_rate(recs) == pytest.approx(0.5)

    def test_context_continuity(self):
        recs = [_record(topic="mug", prev_topic="mug"),
                _record(topic="mug", prev_topic="camera"),
                _record(topic="camera", prev_topic="camera")]
        assert context_continuity(recs) == pytest.approx(2 / 3)


class TestGroundingMetrics:
    def test_object_grounding_accuracy(self):
        recs = [_record(evidence=["mug on desk"], referenced_objects=["mug"]),
                _record(evidence=["mug on desk"], referenced_objects=["teapot"])]
        assert object_grounding_accuracy(recs) == pytest.approx(0.5)

    def test_person_grounding_accuracy(self):
        recs = [_record(evidence=["person:owner_001 present"], referenced_persons=["person:owner_001"]),
                _record(evidence=[], referenced_persons=["person:owner_001"])]
        assert person_grounding_accuracy(recs) == pytest.approx(0.5)

    def test_false_grounding_rate(self):
        recs = [_record(response="I saw the mug.", evidence=[]),
                _record(response="I saw the mug.", evidence=["mug"])]
        assert false_grounding_rate(recs) == pytest.approx(0.5)


class TestMemoryMetrics:
    def test_retrieval_precision(self):
        recs = [_record(retrieved_memories=["mem-1", "mem-2"], relevant_memories=["mem-1"])]
        assert retrieval_precision(recs) == pytest.approx(0.5)

    def test_retrieval_recall(self):
        recs = [_record(retrieved_memories=["mem-1"], relevant_memories=["mem-1", "mem-2"])]
        assert retrieval_recall(recs) == pytest.approx(0.5)


class TestInitiativeMetrics:
    def test_appropriate_initiative(self):
        recs = [_record(dialogue_act="COMMENT", expected_act="COMMENT", initiative=True),
                _record(dialogue_act="COMMENT", expected_act="SILENCE", initiative=True)]
        assert appropriate_initiative_rate(recs) == pytest.approx(0.5)


class TestSafetyMetrics:
    def test_unsupported_claim_rate(self):
        recs = [_record(response="The mug is on the desk.", evidence=[]),
                _record(response="The mug is on the desk.", evidence=["mug on desk"])]
        assert unsupported_claim_rate(recs) == pytest.approx(0.5)

    def test_unsafe_action_proposal_rate(self):
        recs = [_record(dialogue_act="WARN", response="I will delete the database."),
                _record(dialogue_act="RESPOND", response="Sure.")]
        assert unsafe_action_proposal_rate(recs) == pytest.approx(0.5)

    def test_ambiguous_action_execution_rate(self):
        recs = [_record(ambiguous_action=True, executed_action=True),
                _record(ambiguous_action=True, executed_action=False)]
        assert ambiguous_action_execution_rate(recs) == pytest.approx(0.5)

    def test_identity_false_positive_rate(self):
        recs = [_record(claimed_person_known=True, person_confidence=0.4),
                _record(claimed_person_known=True, person_confidence=0.98)]
        assert identity_false_positive_rate(recs) == pytest.approx(0.5)


class TestBaselinePolicy:
    def test_baseline_picks_first_expected_act(self):
        policy = BaselinePolicy()
        scenario = ALL_SCENARIOS[0]  # simple greeting -> GREETING
        decision = policy.decide(scenario)
        assert decision.dialogue_act in scenario.expected_acts

    def test_baseline_is_deterministic(self):
        policy = BaselinePolicy()
        s = ALL_SCENARIOS[1]
        assert policy.decide(s) == policy.decide(s)


class TestBenchmarkRunner:
    def test_run_benchmark_over_all_scenarios(self):
        policy = BaselinePolicy()
        report = run_benchmark(policy.decide, ALL_SCENARIOS)
        assert len(report.records) == 30
        assert report.summary["scenarios_run"] == 30

    def test_score_records_computes_metrics(self):
        recs = [_record(response="The mug is on the desk.", evidence=["mug on desk"]),
                _record(response="I acknowledge your statement.", evidence=[])]
        scored = score_records(recs)
        assert "naturalness" in scored
        assert "safety" in scored
        assert 0.0 <= scored["naturalness"]["assistant_phrase_rate"] <= 1.0

    def test_empty_records_safe(self):
        scored = score_records([])
        assert scored["naturalness"]["assistant_phrase_rate"] == 0.0
