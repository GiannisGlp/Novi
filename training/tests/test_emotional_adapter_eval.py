"""Tests for emotional adapter parity evaluation (plan 24 §45, §51 item 27).

Candidates must be compared against the deterministic emotional baseline on
the same benchmark every time (§45). The train_dpo note requires the SFT vs
SFT+DPO parity to be measured before registry staging; this module runs a
saved LoRA adapter over the 30 emotional scenarios (deterministic act from
the brain, learned verbalization from the adapter, plan §43) and scores the
§45 metric groups.

Model-bound pieces (loading an 8B adapter, generating) stay behind
`make_emotional_adapter_candidate`; the pure pieces — scenario -> prompt,
metric deltas, report assembly — are tested deterministically with fakes.
"""

from __future__ import annotations

from training.evaluation.benchmark import Decision
from training.evaluation.emotional_adapter_eval import (
    _deterministic_act,
    _metric_deltas,
    evaluate_adapter_parity,
    scenario_to_emotional_prompt,
)
from training.evaluation.emotional_scenarios import (
    ALL_EMOTIONAL_SCENARIOS,
    EmotionalScenario,
)

SCENARIO = ALL_EMOTIONAL_SCENARIOS[0]


def _fake_candidate(act_override: str | None = None):
    """Deterministic candidate: expected act (or an override) + neutral response."""

    def decide(scenario: EmotionalScenario) -> Decision:
        act = act_override if act_override else _deterministic_act(scenario)
        return Decision(
            dialogue_act=act,
            response="Okay.",
            confidence=0.9,
            metadata={"affective_hypotheses": list(scenario.expected_hypotheses)},
        )

    return decide


class TestScenarioToEmotionalPrompt:
    def test_renders_social_context(self):
        prompt = scenario_to_emotional_prompt(SCENARIO, "ACKNOWLEDGE")
        assert "Relationship: owner" in prompt
        assert "Conversation phase:" in prompt
        assert "Affective hypotheses:" in prompt
        assert "frustration" in prompt

    def test_includes_chosen_act(self):
        prompt = scenario_to_emotional_prompt(SCENARIO, "ACKNOWLEDGE")
        assert "Communicative act: ACKNOWLEDGE" in prompt

    def test_interruptibility_rendered_when_present(self):
        prompt = scenario_to_emotional_prompt(SCENARIO, "ACKNOWLEDGE")
        assert "Interruptibility:" in prompt

    def test_different_act_changes_prompt(self):
        a = scenario_to_emotional_prompt(SCENARIO, "ACKNOWLEDGE")
        b = scenario_to_emotional_prompt(SCENARIO, "REPAIR")
        assert a != b
        assert "Communicative act: REPAIR" in b


class TestDeterministicAct:
    def test_matches_baseline_strategy_choice(self):
        from training.evaluation.emotional_benchmark import EmotionalBaselinePolicy

        for scenario in ALL_EMOTIONAL_SCENARIOS:
            bl = EmotionalBaselinePolicy().decide(scenario)
            assert _deterministic_act(scenario) == bl.dialogue_act

    def test_falls_back_to_first_acceptable(self):
        scenario = EmotionalScenario(
            scenario_id="t", name="t", description="", input_event="",
            person=None, world={}, social={},
            expected_acts=("SILENCE", "ACKNOWLEDGE"),
            expected_strategy=("REPAIR",),  # not acceptable -> fall back
            expected_hypotheses=(), expected_phase="", metric_groups=("behavior",),
        )
        assert _deterministic_act(scenario) == "SILENCE"


class TestMetricDeltas:
    def test_delta_between_two_reports(self):
        a = {"recognition": {"affective_classification_accuracy": 0.5},
             "behavior": {"appropriate_empathy_rate": 0.8}}
        b = {"recognition": {"affective_classification_accuracy": 0.9},
             "behavior": {"appropriate_empathy_rate": 0.7}}
        d = _metric_deltas(a, b)
        assert d["affective_classification_accuracy"] == 0.4
        assert d["appropriate_empathy_rate"] == -0.1

    def test_missing_metric_treated_as_zero(self):
        a = {"behavior": {"appropriate_empathy_rate": 0.8}}
        b = {}
        d = _metric_deltas(a, b)
        assert d["appropriate_empathy_rate"] == -0.8

    def test_empty_reports(self):
        assert _metric_deltas({}, {}) == {}


class TestEvaluateAdapterParity:
    def test_reports_baseline_and_candidates(self):
        report = evaluate_adapter_parity({"sft": _fake_candidate()})
        assert report["scenarios_run"] == len(ALL_EMOTIONAL_SCENARIOS)
        assert "baseline" in report
        assert report["baseline"]["metrics"]
        assert set(report["candidates"]) == {"sft"}
        assert report["candidates"]["sft"]["metrics"]

    def test_parity_deltas_when_two_candidates(self):
        report = evaluate_adapter_parity({"sft": _fake_candidate(),
                                          "dpo": _fake_candidate()})
        assert "parity" in report
        # identical responses/acts -> all deltas zero
        assert all(v == 0.0 for v in report["parity"].values())

    def test_no_parity_with_single_candidate(self):
        report = evaluate_adapter_parity({"sft": _fake_candidate()})
        assert "parity" not in report

    def test_candidate_behaving_worse_shows_delta(self):
        sft = _fake_candidate()
        bad = _fake_candidate(act_override="SILENCE")  # wrong act for most scenarios
        report = evaluate_adapter_parity({"sft": sft, "dpo": bad})
        assert report["parity"]["appropriate_empathy_rate"] <= 0.0
        assert report["candidates"]["sft"]["summary"]["act_accuracy"] >= \
            report["candidates"]["dpo"]["summary"]["act_accuracy"]

    def test_responses_recorded_per_scenario(self):
        report = evaluate_adapter_parity({"sft": _fake_candidate()})
        responses = report["candidates"]["sft"]["responses"]
        assert len(responses) == len(ALL_EMOTIONAL_SCENARIOS)
        assert all(v == "Okay." for v in responses.values())

    def test_erroring_candidate_isolated_and_skipped_in_parity(self):
        def boom(scenario):
            raise RuntimeError("generation failed")

        report = evaluate_adapter_parity({"sft": _fake_candidate(), "dpo": boom})
        assert report["candidates"]["dpo"]["error"]
        assert "metrics" not in report["candidates"]["dpo"]
        # only one healthy candidate -> no parity section
        assert "parity" not in report
        # healthy candidate's results still landed
        assert report["candidates"]["sft"]["metrics"]
        assert report["candidates"]["sft"]["summary"]["act_accuracy"] == 1.0

    def test_healthy_candidate_survives_erroring_first(self):
        report = evaluate_adapter_parity(
            {"bad": lambda s: (_ for _ in ()).throw(RuntimeError("boom")),
             "sft": _fake_candidate()}
        )
        assert "error" in report["candidates"]["bad"]
        assert report["candidates"]["sft"]["metrics"]
