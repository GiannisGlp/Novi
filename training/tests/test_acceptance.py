"""Tests for production acceptance gates (plan 24 §53, §51 item 36).

The ten acceptance gates E1-E10 are deterministic checks over the §45 metric
report. A model is accepted for production only when every gate passes:

    E1 uncertainty  -> trust: no confident claims on weak evidence
    E2 restraint    -> behavior: appropriate silence
    E3 regulation   -> behavior: appropriate empathy + de-escalation
    E4 repair       -> behavior: repair success
    E5 boundaries   -> behavior: boundary respect
    E6 naturalness  -> naturalness: no canned/repetitive/verbose responses
    E7 continuity   -> structural: persistent memory
    E8 learning     -> learning: corrections measurably improve behavior
    E9 replacement  -> structural: registered model + surviving dataset
    E10 safety      -> structural: zero safety violations
"""

from __future__ import annotations

from training.evaluation.acceptance import (
    AcceptanceReport,
    acceptance_from_records,
    acceptance_verdict,
    evaluate_acceptance,
)
from training.evaluation.emotional_benchmark import (
    EmotionalBaselinePolicy,
    run_emotional_benchmark,
)
from training.evaluation.emotional_metrics import score_emotional_all


def _metrics(**overrides) -> dict:
    """A passing §45 metric report; override any metric by name."""
    m = {
        "recognition": {
            "affective_classification_accuracy": 1.0,
            "affective_calibration": 1.0,
            "false_positive_emotional_claim_rate": 0.0,
            "false_negative_emotional_claim_rate": 0.0,
        },
        "behavior": {
            "appropriate_empathy_rate": 1.0,
            "appropriate_silence_rate": 1.0,
            "boundary_respect_rate": 1.0,
            "repair_success_rate": 1.0,
            "conflict_deescalation_rate": 1.0,
            "initiative_appropriateness": 1.0,
        },
        "naturalness": {
            "canned_empathy_rate": 0.0,
            "emotional_repetition_rate": 0.0,
            "emotional_verbosity_rate": 0.0,
            "timing_appropriateness": 1.0,
        },
        "trust": {
            "unsupported_emotional_claim_rate": 0.0,
            "false_certainty_rate": 0.0,
        },
        "learning": {
            "correction_retention": 1.0,
            "preference_adaptation": 1.0,
            "failure_recurrence": 1.0,
        },
    }
    for key, value in overrides.items():
        for group in m.values():
            if key in group:
                group[key] = value
                break
        else:
            raise KeyError(f"unknown metric: {key}")
    return m


def _structural(**overrides) -> dict:
    s = {"safety_violations": 0, "memory_persistent": True, "registered": True, "dataset_exists": True}
    s.update(overrides)
    return s


def _record(**overrides) -> dict:
    """A perfect emotional outcome record (plan §45)."""
    r = {
        "response": "Got it, I'll fix that.",
        "dialogue_act": "ACKNOWLEDGE",
        "expected_act": "ACKNOWLEDGE",
        "expected_acts": ["ACKNOWLEDGE", "APOLOGIZE", "REPAIR"],
        "act_correct": True,
        "affective_hypotheses": [{"label": "frustration", "probability": 0.7}],
        "expected_hypotheses": [{"label": "frustration", "probability": 0.7}],
        "expected_strategy": ["ACKNOWLEDGE", "APOLOGIZE"],
        "expected_phase": "correction",
        "evidence": ["user voice raised"],
        "emotional_signal": {"frustration_likelihood": 0.8},
        "boundary_state": "NORMAL",
        "conversation_temperature": "tense",
        "repeat_count": 2,
        "initiative": False,
        "metric_groups": ["recognition", "behavior", "trust", "learning"],
    }
    r.update(overrides)
    return r


def _passing_records() -> list[dict]:
    """A record set that exercises every §45 metric denominator and passes."""
    return [
        _record(response="I'm here for you.", dialogue_act="SUPPORT", expected_acts=["SUPPORT"],
                expected_strategy=["SUPPORT"], expected_phase="support",
                conversation_temperature="calm", repeat_count=0),
        _record(response="Okay.", dialogue_act="SILENCE", expected_acts=["SILENCE"],
                expected_strategy=["SILENCE"], expected_phase="silence",
                conversation_temperature="calm", repeat_count=0),
        _record(response="Got it, I'll leave it alone.", dialogue_act="GIVE_SPACE",
                expected_acts=["GIVE_SPACE"], expected_strategy=["GIVE_SPACE"],
                expected_phase="silence", boundary_state="DO_NOT_INTERRUPT",
                conversation_temperature="calm", repeat_count=0),
        _record(response="My bad, let me fix that.", dialogue_act="REPAIR",
                expected_acts=["REPAIR"], expected_strategy=["REPAIR"],
                expected_phase="repair", conversation_temperature="calm", repeat_count=0),
        _record(response="You're right, I'll fix it.", dialogue_act="ACKNOWLEDGE",
                expected_acts=["ACKNOWLEDGE"], expected_strategy=["ACKNOWLEDGE"],
                expected_phase="correction", conversation_temperature="tense", repeat_count=0),
        _record(response="Coffee's out, by the way.", dialogue_act="COMMENT",
                expected_acts=["COMMENT"], expected_strategy=["RESPOND"],
                expected_phase="normal", conversation_temperature="calm",
                repeat_count=0, initiative=True),
        _record(response="I keep missing that, let me fix it properly.", dialogue_act="ACKNOWLEDGE",
                expected_acts=["ACKNOWLEDGE"], expected_strategy=["ACKNOWLEDGE"],
                expected_phase="correction", conversation_temperature="tense", repeat_count=2),
        _record(response="Got it, no more summaries.", dialogue_act="ACKNOWLEDGE",
                expected_acts=["ACKNOWLEDGE"], expected_strategy=["ACKNOWLEDGE"],
                expected_phase="normal", conversation_temperature="calm", repeat_count=0),
    ]


class TestAcceptanceGates:
    def test_all_gates_pass_with_clean_report(self):
        report = evaluate_acceptance(_metrics(), **_structural())
        assert report.passed
        assert report.failed_gates == []

    def test_e1_fails_on_unsupported_claim(self):
        report = evaluate_acceptance(_metrics(unsupported_emotional_claim_rate=0.2), **_structural())
        assert not report.passed
        assert "E1_uncertainty" in report.failed_gates

    def test_e1_fails_on_false_certainty(self):
        report = evaluate_acceptance(_metrics(false_certainty_rate=0.1), **_structural())
        assert "E1_uncertainty" in report.failed_gates

    def test_e1_fails_on_false_positive_claim(self):
        report = evaluate_acceptance(_metrics(false_positive_emotional_claim_rate=0.05), **_structural())
        assert "E1_uncertainty" in report.failed_gates

    def test_e2_fails_on_low_silence(self):
        report = evaluate_acceptance(_metrics(appropriate_silence_rate=0.5), **_structural())
        assert "E2_restraint" in report.failed_gates

    def test_e3_fails_on_low_empathy(self):
        report = evaluate_acceptance(_metrics(appropriate_empathy_rate=0.6), **_structural())
        assert "E3_regulation" in report.failed_gates

    def test_e3_fails_on_low_deescalation(self):
        report = evaluate_acceptance(_metrics(conflict_deescalation_rate=0.7), **_structural())
        assert "E3_regulation" in report.failed_gates

    def test_e4_fails_on_low_repair(self):
        report = evaluate_acceptance(_metrics(repair_success_rate=0.4), **_structural())
        assert "E4_repair" in report.failed_gates

    def test_e5_fails_on_low_boundary(self):
        report = evaluate_acceptance(_metrics(boundary_respect_rate=0.5), **_structural())
        assert "E5_boundaries" in report.failed_gates

    def test_e6_fails_on_canned_empathy(self):
        report = evaluate_acceptance(_metrics(canned_empathy_rate=0.2), **_structural())
        assert "E6_naturalness" in report.failed_gates

    def test_e6_fails_on_repetition(self):
        report = evaluate_acceptance(_metrics(emotional_repetition_rate=0.3), **_structural())
        assert "E6_naturalness" in report.failed_gates

    def test_e6_fails_on_verbosity(self):
        report = evaluate_acceptance(_metrics(emotional_verbosity_rate=0.4), **_structural())
        assert "E6_naturalness" in report.failed_gates

    def test_e7_fails_without_persistent_memory(self):
        report = evaluate_acceptance(_metrics(), **_structural(memory_persistent=False))
        assert "E7_continuity" in report.failed_gates

    def test_e8_fails_on_low_correction_retention(self):
        report = evaluate_acceptance(_metrics(correction_retention=0.5), **_structural())
        assert "E8_learning" in report.failed_gates

    def test_e8_fails_on_low_preference_adaptation(self):
        report = evaluate_acceptance(_metrics(preference_adaptation=0.6), **_structural())
        assert "E8_learning" in report.failed_gates

    def test_e8_fails_on_low_failure_recurrence(self):
        report = evaluate_acceptance(_metrics(failure_recurrence=0.0), **_structural())
        assert "E8_learning" in report.failed_gates

    def test_e9_fails_without_registration(self):
        report = evaluate_acceptance(_metrics(), **_structural(registered=False))
        assert "E9_replacement" in report.failed_gates

    def test_e9_fails_without_dataset(self):
        report = evaluate_acceptance(_metrics(), **_structural(dataset_exists=False))
        assert "E9_replacement" in report.failed_gates

    def test_e10_fails_on_safety_violation(self):
        report = evaluate_acceptance(_metrics(), **_structural(safety_violations=1))
        assert "E10_safety" in report.failed_gates

    def test_multiple_failures_are_all_reported(self):
        report = evaluate_acceptance(
            _metrics(appropriate_silence_rate=0.0, canned_empathy_rate=0.5),
            **_structural(memory_persistent=False, safety_violations=2),
        )
        assert set(report.failed_gates) == {"E2_restraint", "E6_naturalness", "E7_continuity", "E10_safety"}

    def test_missing_metric_fails_the_gate(self):
        # a report that omits a required metric cannot pass that gate
        metrics = _metrics()
        del metrics["trust"]["unsupported_emotional_claim_rate"]
        report = evaluate_acceptance(metrics, **_structural())
        assert "E1_uncertainty" in report.failed_gates


class TestAcceptanceReport:
    def test_verdict_accepted(self):
        report = evaluate_acceptance(_metrics(), **_structural())
        assert acceptance_verdict(report) == "accepted"

    def test_verdict_rejected(self):
        report = evaluate_acceptance(_metrics(appropriate_empathy_rate=0.5), **_structural())
        assert acceptance_verdict(report) == "rejected"

    def test_to_dict_round_trip(self):
        report = evaluate_acceptance(_metrics(), **_structural())
        d = report.to_dict()
        assert d["passed"] is True
        assert d["failed_gates"] == []
        assert d["gates"]["E1_uncertainty"] is True

    def test_report_is_immutable_dataclass(self):
        report = evaluate_acceptance(_metrics(), **_structural())
        assert isinstance(report, AcceptanceReport)
        assert report.gates["E10_safety"] is True


class TestAcceptanceFromRecords:
    def test_passing_records_pass_all_gates(self):
        report = acceptance_from_records(_passing_records(), **_structural())
        assert report.passed
        assert report.failed_gates == []

    def test_delegates_to_evaluate_acceptance(self):
        records = run_emotional_benchmark(EmotionalBaselinePolicy().decide).records
        expected = evaluate_acceptance(score_emotional_all(records), **_structural())
        got = acceptance_from_records(records, **_structural())
        assert got == expected

    def test_baseline_rejected_without_learning_data(self):
        # the scenario catalog has no repeated-failure record (repeat_count >= 2),
        # so failure_recurrence has an empty denominator -> E8 cannot pass
        records = run_emotional_benchmark(EmotionalBaselinePolicy().decide).records
        report = acceptance_from_records(records, **_structural())
        assert not report.passed
        assert "E8_learning" in report.failed_gates

    def test_structural_flags_flow_through(self):
        report = acceptance_from_records(_passing_records(), **_structural(memory_persistent=False))
        assert "E7_continuity" in report.failed_gates
