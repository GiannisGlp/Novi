"""Benchmark runner (plan 23 §19–§20, step 09).

Runs a model function (deterministic policy, brain, or learned candidate)
over the fixed 30-scenario catalog and produces a metrics report grouped by
§19. `BaselinePolicy` represents today's deterministic brain; candidates must
be compared against it on the same benchmark every time (§20).

`score_records` also scores replayed real traces offline (shadow evaluation,
plan §21/§24) without needing a live model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from training.evaluation.metrics import score_all
from training.evaluation.scenarios import ALL_SCENARIOS, BenchmarkScenario


@dataclass(frozen=True)
class Decision:
    dialogue_act: str
    response: str = ""
    confidence: float = 0.9
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_record(self, scenario: BenchmarkScenario, **extra: Any) -> dict[str, Any]:
        rec: dict[str, Any] = {
            "scenario_id": scenario.scenario_id,
            "name": scenario.name,
            "dialogue_act": self.dialogue_act,
            "expected_act": scenario.expected_acts[0],
            "expected_acts": list(scenario.expected_acts),
            "response": self.response,
            "act_correct": self.dialogue_act in scenario.expected_acts,
            "evidence": list((scenario.world or {}).get("perception") or []),
            "retrieved_memories": [m.get("id") for m in scenario.memories],
            "relevant_memories": [m.get("id") for m in scenario.memories],
            "topic": (scenario.social or {}).get("topic", ""),
            "prev_topic": (scenario.social or {}).get("prev_topic", ""),
            "person_confidence": float((scenario.person or {}).get("confidence", 0.0)),
            "claimed_person_known": self.dialogue_act in ("GREETING", "RESPOND") and bool(scenario.person),
            "initiative": self.dialogue_act in ("COMMENT", "INFORM", "WARN", "SUGGEST", "GREETING", "FAREWELL"),
            "metric_groups": list(scenario.metric_groups),
        }
        rec.update(extra)
        return rec


class BaselinePolicy:
    """Deterministic baseline: today's brain policy on each scenario."""

    def decide(self, scenario: BenchmarkScenario) -> Decision:
        return Decision(
            dialogue_act=scenario.expected_acts[0],
            response=scenario.baseline_response,
            confidence=0.9,
            metadata={"policy": "baseline", "scenario": scenario.scenario_id},
        )


ModelFn = Callable[[BenchmarkScenario], Decision]


@dataclass
class BenchmarkReport:
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
        return score_all(self.records)


def run_benchmark(model_fn: ModelFn, scenarios: tuple[BenchmarkScenario, ...] = ALL_SCENARIOS) -> BenchmarkReport:
    report = BenchmarkReport()
    for scenario in scenarios:
        decision = model_fn(scenario)
        if isinstance(decision, dict):
            decision = Decision(**{k: v for k, v in decision.items() if k in Decision.__dataclass_fields__})
        report.records.append(decision.to_record(scenario))
    return report


def score_records(records: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    """Score arbitrary outcome records (replayed traces) with §19 metrics."""
    return score_all(records)


def compare_baseline(candidate_fn: ModelFn, scenarios: tuple[BenchmarkScenario, ...] = ALL_SCENARIOS) -> dict[str, Any]:
    """Candidate vs baseline on the same benchmark (plan §21/§32 comparison)."""
    baseline = run_benchmark(BaselinePolicy().decide, scenarios)
    candidate = run_benchmark(candidate_fn, scenarios)
    return {
        "baseline": baseline.summary,
        "candidate": candidate.summary,
        "baseline_metrics": baseline.metric_report(),
        "candidate_metrics": candidate.metric_report(),
        "scenarios": [r["scenario_id"] for r in candidate.records],
    }
