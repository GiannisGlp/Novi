"""Tests for the emotional evaluation suite (plan 24 §44–§45, §51 item 23)."""

from __future__ import annotations

import pytest

from training.evaluation.benchmark import Decision
from training.evaluation.emotional_benchmark import (
    EmotionalBaselinePolicy,
    compare_emotional_baseline,
    run_emotional_benchmark,
    score_emotional_records,
)
from training.evaluation.emotional_metrics import (
    affective_calibration,
    affective_classification_accuracy,
    appropriate_empathy_rate,
    appropriate_silence_rate,
    boundary_respect_rate,
    canned_empathy_rate,
    conflict_deescalation_rate,
    correction_retention,
    emotional_repetition_rate,
    emotional_verbosity_rate,
    failure_recurrence,
    false_certainty_rate,
    false_negative_emotional_claim_rate,
    false_positive_emotional_claim_rate,
    initiative_appropriateness,
    preference_adaptation,
    repair_success_rate,
    timing_appropriateness,
    unsupported_emotional_claim_rate,
)
from training.evaluation.emotional_scenarios import ALL_EMOTIONAL_SCENARIOS
from training.schemas import AFFECTIVE_LABELS, DIALOGUE_ACTS, EMOTIONAL_ACTS


def _record(**overrides) -> dict:
    rec = {
        "response": "Yeah, that's on me. Let me fix it.",
        "dialogue_act": "ACKNOWLEDGE",
        "expected_act": "ACKNOWLEDGE",
        "expected_acts": ["ACKNOWLEDGE", "APOLOGIZE", "SOLVE"],
        "act_correct": True,
        "affective_hypotheses": [{"label": "frustration", "probability": 0.7}],
        "expected_hypotheses": [{"label": "frustration", "probability": 0.7}],
        "expected_strategy": ["ACKNOWLEDGE", "SOLVE"],
        "expected_phase": "tension",
        "evidence": ["user voice raised"],
        "emotional_signal": {"frustration_likelihood": {"value": 0.8, "confidence": 0.9}},
        "boundary_state": "NORMAL",
        "conversation_temperature": "tense",
        "repeat_count": 0,
        "initiative": False,
    }
    rec.update(overrides)
    return rec


class TestEmotionalScenarioCatalog:
    def test_exactly_30_scenarios(self):
        assert len(ALL_EMOTIONAL_SCENARIOS) == 30

    def test_unique_ids_and_valid_acts(self):
        ids = [s.scenario_id for s in ALL_EMOTIONAL_SCENARIOS]
        assert len(ids) == len(set(ids))
        for s in ALL_EMOTIONAL_SCENARIOS:
            # expected_acts span the union of the dialogue-act and emotional-act
            # vocabularies (proactive acts like COMMENT/WARN and emotional acts
            # like APOLOGIZE are both legitimate emotional responses);
            # expected_strategy is the emotional-act subset.
            valid_acts = DIALOGUE_ACTS | EMOTIONAL_ACTS
            for act in s.expected_acts:
                assert act in valid_acts, (s.scenario_id, act)
            for act in s.expected_strategy:
                assert act in EMOTIONAL_ACTS, (s.scenario_id, act)

    def test_plan_scenario_names_present(self):
        names = {s.name for s in ALL_EMOTIONAL_SCENARIOS}
        for expected in ("user frustration", "user fatigue", "user excitement",
                         "user disappointment", "user success", "user embarrassment",
                         "user disagreement", "Novi mistake", "repeated Novi mistake",
                         "explicit correction", "user wants space", "user says stop",
                         "user asks for emotional support", "ambiguous emotion",
                         "conflicting modalities", "multi-person interaction",
                         "serious topic", "humor opportunity", "boundary violation attempt",
                         "proactive interaction", "inappropriate initiative",
                         "appropriate silence", "conversation repair", "apology",
                         "uncertainty", "user changes preference",
                         "long-term relationship continuity", "cross-session memory",
                         "noisy affective signals", "safety-critical situation"):
            assert expected in names

    def test_scenarios_carry_metric_groups(self):
        # Emotional groups (§45) plus the safety group (scenario 30 is a
        # safety-critical situation).
        allowed = ("recognition", "behavior", "naturalness", "trust", "learning", "safety")
        for s in ALL_EMOTIONAL_SCENARIOS:
            assert s.metric_groups
            for g in s.metric_groups:
                assert g in allowed

    def test_scenarios_carry_affective_ground_truth(self):
        for s in ALL_EMOTIONAL_SCENARIOS:
            assert s.expected_hypotheses
            for h in s.expected_hypotheses:
                assert h["label"] in AFFECTIVE_LABELS, (s.scenario_id, h)
                assert 0.0 <= h["probability"] <= 1.0

    def test_scenarios_carry_expected_strategy_and_phase(self):
        for s in ALL_EMOTIONAL_SCENARIOS:
            assert s.expected_strategy
            for act in s.expected_strategy:
                assert act in EMOTIONAL_ACTS, (s.scenario_id, act)
            assert s.expected_phase in ("tension", "support", "celebration", "silence",
                                        "repair", "disagreement", "correction", "normal")


class TestRecognitionMetrics:
    def test_affective_classification_accuracy(self):
        recs = [_record(affective_hypotheses=[{"label": "frustration", "probability": 0.7}]),
                _record(affective_hypotheses=[{"label": "fatigue", "probability": 0.7}])]
        assert affective_classification_accuracy(recs) == pytest.approx(0.5)

    def test_classification_miss_on_no_claim(self):
        recs = [_record(affective_hypotheses=[])]
        assert affective_classification_accuracy(recs) == 0.0

    def test_affective_calibration(self):
        recs = [_record(affective_hypotheses=[{"label": "frustration", "probability": 0.7}]),
                _record(affective_hypotheses=[{"label": "frustration", "probability": 0.3}])]
        assert affective_calibration(recs) == pytest.approx(0.5)

    def test_false_positive_emotional_claim(self):
        # Strong claim (0.8) on weak expected evidence (0.2) -> false positive.
        recs = [_record(affective_hypotheses=[{"label": "frustration", "probability": 0.8}],
                        expected_hypotheses=[{"label": "frustration", "probability": 0.2}]),
                _record(affective_hypotheses=[{"label": "frustration", "probability": 0.8}],
                        expected_hypotheses=[{"label": "frustration", "probability": 0.7}])]
        assert false_positive_emotional_claim_rate(recs) == pytest.approx(0.5)

    def test_false_negative_emotional_claim(self):
        # Strong expected signal (0.8) but model claims nothing -> miss.
        recs = [_record(affective_hypotheses=[],
                        expected_hypotheses=[{"label": "frustration", "probability": 0.8}]),
                _record(affective_hypotheses=[{"label": "frustration", "probability": 0.7}],
                        expected_hypotheses=[{"label": "frustration", "probability": 0.8}])]
        assert false_negative_emotional_claim_rate(recs) == pytest.approx(0.5)


class TestBehaviorMetrics:
    def test_appropriate_empathy_rate(self):
        recs = [_record(dialogue_act="SUPPORT", expected_strategy=["SUPPORT"]),
                _record(dialogue_act="RESPOND", expected_strategy=["SUPPORT"])]
        assert appropriate_empathy_rate(recs) == pytest.approx(0.5)

    def test_appropriate_silence_rate(self):
        recs = [_record(dialogue_act="SILENCE", expected_strategy=["SILENCE"]),
                _record(dialogue_act="RESPOND", expected_strategy=["SILENCE"])]
        assert appropriate_silence_rate(recs) == pytest.approx(0.5)

    def test_boundary_respect_rate(self):
        recs = [_record(dialogue_act="SILENCE", boundary_state="DO_NOT_INTERRUPT"),
                _record(dialogue_act="COMMENT", boundary_state="DO_NOT_INTERRUPT")]
        assert boundary_respect_rate(recs) == pytest.approx(0.5)

    def test_redirect_respects_privacy_boundary(self):
        # A PRIVACY_LIMIT boundary is respected by redirecting away from it.
        recs = [_record(dialogue_act="REDIRECT", boundary_state="PRIVACY_LIMIT"),
                _record(dialogue_act="RESPOND", boundary_state="PRIVACY_LIMIT")]
        assert boundary_respect_rate(recs) == pytest.approx(0.5)

    def test_repair_success_rate(self):
        recs = [_record(dialogue_act="APOLOGIZE", expected_strategy=["APOLOGIZE"]),
                _record(dialogue_act="RESPOND", expected_strategy=["APOLOGIZE"])]
        assert repair_success_rate(recs) == pytest.approx(0.5)

    def test_conflict_deescalation_rate(self):
        recs = [_record(dialogue_act="CLARIFY", conversation_temperature="tense"),
                _record(dialogue_act="COMMENT", conversation_temperature="tense")]
        assert conflict_deescalation_rate(recs) == pytest.approx(0.5)

    def test_initiative_appropriateness(self):
        recs = [_record(dialogue_act="COMMENT", expected_act="COMMENT", initiative=True),
                _record(dialogue_act="COMMENT", expected_act="SILENCE", initiative=True)]
        assert initiative_appropriateness(recs) == pytest.approx(0.5)


class TestNaturalnessMetrics:
    def test_canned_empathy_rate(self):
        recs = [_record(response="I understand how you feel."),
                _record(response="Yeah, that's on me.")]
        assert canned_empathy_rate(recs) == pytest.approx(0.5)

    def test_emotional_repetition_rate(self):
        recs = [_record(response="Okay.", dialogue_act="SILENCE"),
                _record(response="Okay.", dialogue_act="RESPOND"),
                _record(response="Different.", dialogue_act="RESPOND")]
        assert emotional_repetition_rate(recs) == pytest.approx(1 / 3)

    def test_same_act_repetition_is_natural(self):
        recs = [_record(response="Okay.", dialogue_act="SILENCE"),
                _record(response="Okay.", dialogue_act="SILENCE")]
        assert emotional_repetition_rate(recs) == 0.0

    def test_emotional_verbosity_rate(self):
        long = "word " * 200
        recs = [_record(response=long), _record(response="short.")]
        assert emotional_verbosity_rate(recs) == pytest.approx(0.5)

    def test_timing_appropriateness(self):
        recs = [_record(dialogue_act="SILENCE", expected_phase="silence"),
                _record(dialogue_act="COMMENT", expected_phase="silence")]
        assert timing_appropriateness(recs) == pytest.approx(0.5)

    def test_silence_is_well_timed_in_normal_phase(self):
        # Multi-person interaction: staying silent while the user talks to a
        # guest is well-timed even in a normal phase; interrupting is not.
        recs = [_record(dialogue_act="SILENCE", expected_phase="normal"),
                _record(dialogue_act="INTERRUPT", expected_phase="normal")]
        assert timing_appropriateness(recs) == pytest.approx(0.5)


class TestTrustMetrics:
    def test_unsupported_emotional_claim_rate(self):
        recs = [_record(affective_hypotheses=[{"label": "frustration", "probability": 0.8}],
                        emotional_signal={}),
                _record(affective_hypotheses=[{"label": "frustration", "probability": 0.8}],
                        emotional_signal={"frustration_likelihood": {"value": 0.8}})]
        assert unsupported_emotional_claim_rate(recs) == pytest.approx(0.5)

    def test_false_certainty_rate(self):
        recs = [_record(affective_hypotheses=[{"label": "frustration", "probability": 0.8}],
                        expected_hypotheses=[{"label": "frustration", "probability": 0.2}]),
                _record(affective_hypotheses=[{"label": "frustration", "probability": 0.8}],
                        expected_hypotheses=[{"label": "frustration", "probability": 0.7}])]
        assert false_certainty_rate(recs) == pytest.approx(0.5)


class TestLearningMetrics:
    def test_correction_retention(self):
        recs = [_record(dialogue_act="ACKNOWLEDGE", expected_phase="correction"),
                _record(dialogue_act="RESPOND", expected_phase="correction")]
        assert correction_retention(recs) == pytest.approx(0.5)

    def test_preference_adaptation(self):
        recs = [_record(dialogue_act="ACKNOWLEDGE", expected_strategy=["ACKNOWLEDGE"]),
                _record(dialogue_act="RESPOND", expected_strategy=["ACKNOWLEDGE"])]
        assert preference_adaptation(recs) == pytest.approx(0.5)

    def test_failure_recurrence(self):
        recs = [_record(act_correct=True, expected_phase="correction", repeat_count=2),
                _record(act_correct=False, expected_phase="correction", repeat_count=2)]
        assert failure_recurrence(recs) == pytest.approx(0.5)


class TestEmotionalBaselinePolicy:
    def test_baseline_picks_first_expected_act(self):
        policy = EmotionalBaselinePolicy()
        scenario = ALL_EMOTIONAL_SCENARIOS[0]  # user frustration -> ACKNOWLEDGE
        decision = policy.decide(scenario)
        assert decision.dialogue_act in scenario.expected_acts

    def test_baseline_reports_expected_hypotheses(self):
        policy = EmotionalBaselinePolicy()
        scenario = ALL_EMOTIONAL_SCENARIOS[0]
        decision = policy.decide(scenario)
        assert decision.metadata["affective_hypotheses"] == list(scenario.expected_hypotheses)

    def test_baseline_is_deterministic(self):
        policy = EmotionalBaselinePolicy()
        s = ALL_EMOTIONAL_SCENARIOS[1]
        assert policy.decide(s) == policy.decide(s)


class TestEmotionalBenchmarkRunner:
    def test_run_emotional_benchmark_over_all_scenarios(self):
        policy = EmotionalBaselinePolicy()
        report = run_emotional_benchmark(policy.decide, ALL_EMOTIONAL_SCENARIOS)
        assert len(report.records) == 30
        assert report.summary["scenarios_run"] == 30

    def test_baseline_achieves_perfect_act_accuracy(self):
        policy = EmotionalBaselinePolicy()
        report = run_emotional_benchmark(policy.decide, ALL_EMOTIONAL_SCENARIOS)
        assert report.summary["act_accuracy"] == 1.0

    def test_baseline_achieves_perfect_recognition(self):
        policy = EmotionalBaselinePolicy()
        report = run_emotional_benchmark(policy.decide, ALL_EMOTIONAL_SCENARIOS)
        metrics = report.metric_report()
        assert metrics["recognition"]["affective_classification_accuracy"] == 1.0
        assert metrics["recognition"]["affective_calibration"] == 1.0

    def test_metric_report_covers_all_groups(self):
        policy = EmotionalBaselinePolicy()
        report = run_emotional_benchmark(policy.decide, ALL_EMOTIONAL_SCENARIOS)
        metrics = report.metric_report()
        for group in ("recognition", "behavior", "naturalness", "trust", "learning"):
            assert group in metrics

    def test_score_emotional_records_computes_metrics(self):
        recs = [_record(), _record(dialogue_act="SILENCE", expected_acts=["SILENCE"],
                                   expected_strategy=["SILENCE"], expected_phase="silence")]
        scored = score_emotional_records(recs)
        assert "recognition" in scored
        assert "behavior" in scored
        assert 0.0 <= scored["recognition"]["affective_classification_accuracy"] <= 1.0

    def test_empty_records_safe(self):
        scored = score_emotional_records([])
        assert scored["recognition"]["affective_classification_accuracy"] == 0.0

    def test_compare_emotional_baseline(self):
        def candidate(scenario):
            return Decision(
                dialogue_act=scenario.expected_acts[0],
                response=scenario.baseline_response,
                metadata={"affective_hypotheses": list(scenario.expected_hypotheses)},
            )
        result = compare_emotional_baseline(candidate, ALL_EMOTIONAL_SCENARIOS)
        assert result["baseline"]["act_accuracy"] == 1.0
        assert result["candidate"]["act_accuracy"] == 1.0
        assert len(result["scenarios"]) == 30
