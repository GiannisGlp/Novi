"""Emotional maturity benchmark runner (plan 24 §44–§45, §51 item 23).

Runs a model function (deterministic policy, brain, or learned candidate)
over the fixed 30 emotional-scenario catalog and produces an emotional
metrics report grouped by §45. `EmotionalBaselinePolicy` represents today's
deterministic brain; candidates must be compared against it on the same
emotional benchmark every time (§45).

`score_emotional_records` also scores replayed real traces offline (shadow
evaluation) without needing a live model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from training.evaluation.benchmark import Decision
from training.evaluation.emotional_metrics import score_emotional_all
from training.evaluation.emotional_scenarios import ALL_EMOTIONAL_SCENARIOS, EmotionalScenario


class EmotionalBaselinePolicy:
    """Deterministic baseline: today's brain policy on each emotional scenario.

    The baseline follows the scenario's expected strategy (the emotional
    behavior the plan wants) when that act is acceptable, falling back to the
    first acceptable act otherwise. It emits the scenario's baseline response
    and reports the expected affective hypotheses verbatim (a
    perfect-recognition, rule-following policy).
    """

    def decide(self, scenario: EmotionalScenario) -> Decision:
        act = scenario.expected_strategy[0]
        if act not in scenario.expected_acts:
            act = scenario.expected_acts[0]
        return Decision(
            dialogue_act=act,
            response=scenario.baseline_response,
            confidence=0.9,
            metadata={
                "policy": "emotional_baseline",
                "scenario": scenario.scenario_id,
                "affective_hypotheses": list(scenario.expected_hypotheses),
            },
        )


EmotionalModelFn = Callable[[EmotionalScenario], Decision]


@dataclass
class EmotionalBenchmarkReport:
    records: list[dict[str, Any]] = field(default_factory=list)

    @property
    def summary(self) -> dict[str, Any]:
        if not self.records:
            return {"scenarios_run": 0, "act_accuracy": 0.0}
        correct = sum(1 for r in self.records if r["act_correct"])
        return {
            "scenarios_run": len(self.records),
            "act_accuracy": round(correct / len(self.records), 3),
        }

    def metric_report(self) -> dict[str, dict[str, float]]:
        return score_emotional_all(self.records)


def _to_record(decision: Decision, scenario: EmotionalScenario) -> dict[str, Any]:
    social = scenario.social or {}
    rec: dict[str, Any] = {
        "scenario_id": scenario.scenario_id,
        "name": scenario.name,
        "dialogue_act": decision.dialogue_act,
        "expected_act": scenario.expected_acts[0],
        "expected_acts": list(scenario.expected_acts),
        "response": decision.response,
        "act_correct": decision.dialogue_act in scenario.expected_acts,
        "affective_hypotheses": list(decision.metadata.get("affective_hypotheses") or []),
        "expected_hypotheses": list(scenario.expected_hypotheses),
        "expected_strategy": list(scenario.expected_strategy),
        "expected_phase": scenario.expected_phase,
        "evidence": list((scenario.world or {}).get("perception") or []),
        "emotional_signal": social.get("emotional_signal") or {},
        "boundary_state": social.get("boundary_state") or "NORMAL",
        "conversation_temperature": social.get("conversation_temperature") or "calm",
        "repeat_count": social.get("repeat_count") or 0,
        "initiative": decision.dialogue_act in ("COMMENT", "INFORM", "WARN", "SUGGEST", "GREETING", "FAREWELL", "CONTINUE"),
        "metric_groups": list(scenario.metric_groups),
    }
    return rec


def run_emotional_benchmark(
    model_fn: EmotionalModelFn,
    scenarios: tuple[EmotionalScenario, ...] = ALL_EMOTIONAL_SCENARIOS,
) -> EmotionalBenchmarkReport:
    report = EmotionalBenchmarkReport()
    for scenario in scenarios:
        decision = model_fn(scenario)
        if isinstance(decision, dict):
            decision = Decision(**{k: v for k, v in decision.items() if k in Decision.__dataclass_fields__})
        report.records.append(_to_record(decision, scenario))
    return report


def score_emotional_records(records: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    """Score arbitrary emotional outcome records (replayed traces) with §45 metrics."""
    return score_emotional_all(records)


def compare_emotional_baseline(
    candidate_fn: EmotionalModelFn,
    scenarios: tuple[EmotionalScenario, ...] = ALL_EMOTIONAL_SCENARIOS,
) -> dict[str, Any]:
    """Candidate vs emotional baseline on the same benchmark (plan §45 comparison)."""
    baseline = run_emotional_benchmark(EmotionalBaselinePolicy().decide, scenarios)
    candidate = run_emotional_benchmark(candidate_fn, scenarios)
    return {
        "baseline": baseline.summary,
        "candidate": candidate.summary,
        "baseline_metrics": baseline.metric_report(),
        "candidate_metrics": candidate.metric_report(),
        "scenarios": [r["scenario_id"] for r in candidate.records],
    }
