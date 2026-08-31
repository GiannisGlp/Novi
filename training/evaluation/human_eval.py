"""Emotional human evaluation tool (plan 24 §46, §51 item 25).

Reviewers score each response 1-5 on the nine §46 dimensions and record
pairwise A/B preferences. High-quality pairwise results feed the DPO
preference dataset (§26, §51 item 26).

The record builders are pure and deterministic; the interactive CLI is a thin
wrapper so the tool is scriptable and testable.

    # interactive rating walk-through (all 30 scenarios, baseline responses)
    python -m training.evaluation.human_eval --interactive --out results.jsonl

    # interactive pairwise preference (A/B, "which is more emotionally mature?")
    python -m training.evaluation.human_eval --pairwise --out results.jsonl

    # restrict to one scenario
    python -m training.evaluation.human_eval --interactive --scenario 01 --out results.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from training.evaluation.emotional_scenarios import ALL_EMOTIONAL_SCENARIOS

# The nine §46 dimensions reviewers score 1-5.
HUMAN_EVAL_DIMENSIONS: tuple[str, ...] = (
    "emotional_appropriateness", "social_maturity", "naturalness",
    "restraint", "humility", "context_awareness", "boundary_respect",
    "repair_quality", "supportiveness",
)

MIN_SCORE = 1
MAX_SCORE = 5


def _validate_scores(scores: dict) -> None:
    """Reject missing, unknown, or out-of-range dimension scores."""
    missing = [d for d in HUMAN_EVAL_DIMENSIONS if d not in scores]
    if missing:
        raise ValueError(f"missing dimensions: {', '.join(missing)}")
    unknown = [d for d in scores if d not in HUMAN_EVAL_DIMENSIONS]
    if unknown:
        raise ValueError(f"unknown dimensions: {', '.join(unknown)}")
    for dim, value in scores.items():
        if not isinstance(value, int) or not MIN_SCORE <= value <= MAX_SCORE:
            raise ValueError(f"{dim} score {value!r} out of range {MIN_SCORE}-{MAX_SCORE}")


def build_rating_record(scenario, response: str, scores: dict, model_id: str = "") -> dict:
    """One reviewer's 1-5 rating of a response to an emotional scenario.

    The record is self-contained (scenario id/name/input event + response +
    scores) so it can be aggregated across reviewers and models.
    """
    _validate_scores(scores)
    return {
        "kind": "rating",
        "scenario_id": scenario.scenario_id,
        "scenario_name": scenario.name,
        "input_event": scenario.input_event,
        "response": response,
        "model_id": model_id,
        "scores": {d: scores[d] for d in HUMAN_EVAL_DIMENSIONS},
        "reviewer": "human",
    }


def build_preference_record(scenario, response_a: str, response_b: str, preferred: str) -> dict:
    """One pairwise A/B preference ("which response is more emotionally mature?").

    The record matches the emotional preference-pair schema fields
    (response_a, response_b, preferred, category) so high-quality results can
    be folded into the DPO preference dataset (§26).
    """
    if not response_a or not response_b:
        raise ValueError("both responses are required for a preference record")
    if preferred not in ("A", "B"):
        raise ValueError("preferred must be 'A' or 'B'")
    return {
        "kind": "preference",
        "scenario_id": scenario.scenario_id,
        "scenario_name": scenario.name,
        "input_event": scenario.input_event,
        "response_a": response_a,
        "response_b": response_b,
        "preferred": preferred,
        "category": "emotional_maturity",
        "reviewer": "human",
    }


def write_records(records: list[dict], path: Path) -> None:
    """Append records as JSONL (one record per line)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _prompt_scores() -> dict:
    """Read nine comma-separated 1-5 scores from stdin (interactive mode)."""
    print(f"dimensions: {', '.join(HUMAN_EVAL_DIMENSIONS)}")
    while True:
        raw = input("scores (comma-separated 1-5, in order): ").strip()
        parts = [p.strip() for p in raw.split(",")]
        try:
            values = [int(p) for p in parts]
        except ValueError:
            print("  enter integers, e.g. 4,4,5,4,4,4,5,4,3")
            continue
        if len(values) != len(HUMAN_EVAL_DIMENSIONS):
            print(f"  need {len(HUMAN_EVAL_DIMENSIONS)} scores")
            continue
        scores = dict(zip(HUMAN_EVAL_DIMENSIONS, values, strict=True))
        try:
            _validate_scores(scores)
        except ValueError as exc:
            print(f"  {exc}")
            continue
        return scores


def _run_interactive(out: Path, scenario_ids: list[str], pairwise: bool) -> int:
    scenarios = [s for s in ALL_EMOTIONAL_SCENARIOS if s.scenario_id in scenario_ids]
    if not scenarios:
        print("no scenarios match", file=sys.stderr)
        return 2
    for scenario in scenarios:
        print(f"\n=== {scenario.scenario_id} — {scenario.name} ===")
        print(f"event: {scenario.input_event}")
        if pairwise:
            print(f"A: {scenario.baseline_response or '(silence)'}")
            print(f"B: {scenario.expected_strategy[0]}")
            while True:
                pref = input("which is more emotionally mature? A / B (or s to skip): ").strip().upper()
                if pref == "S":
                    break
                if pref in ("A", "B"):
                    write_records(
                        [build_preference_record(scenario, scenario.baseline_response, scenario.expected_strategy[0], pref)],
                        out,
                    )
                    break
                print("  enter A, B, or s")
        else:
            response = scenario.baseline_response or "(silence)"
            print(f"response: {response}")
            scores = _prompt_scores()
            write_records([build_rating_record(scenario, response, scores, model_id="emotional_baseline")], out)
    print(f"\nwrote records to {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interactive", action="store_true", help="walk through scenarios and prompt for scores")
    parser.add_argument("--pairwise", action="store_true", help="walk through scenarios and prompt for A/B preference")
    parser.add_argument("--out", default="training/evaluation/results/human_eval.jsonl", help="output JSONL path")
    parser.add_argument("--scenario", default=None, help="restrict to one scenario id (e.g. 01)")
    args = parser.parse_args(argv)

    if not args.interactive and not args.pairwise:
        parser.error("choose --interactive or --pairwise")
    scenario_ids = [args.scenario] if args.scenario else [s.scenario_id for s in ALL_EMOTIONAL_SCENARIOS]
    return _run_interactive(Path(args.out), scenario_ids, pairwise=args.pairwise)


if __name__ == "__main__":
    raise SystemExit(main())
