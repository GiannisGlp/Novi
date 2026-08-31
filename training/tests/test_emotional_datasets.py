"""Tests for the emotional maturity datasets (plan 24 §23-§28).

Phase 19 (§23) dataset structure, Phase 20 (§24) emotional example schema,
Phase 21 (§25) SFT emotional behavior, Phase 22 (§26) DPO preference pairs,
Phase 23 (§27) social policy ranking, Phase 24 (§28) perspective-taking.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from training.schemas import (
    EMOTIONAL_PREFERENCE_CATEGORIES,
    EMOTIONAL_SFT_TASKS,
    EmotionalExample,
    validate_example,
)

DATASETS = Path(__file__).resolve().parents[1] / "datasets"
EMOTIONAL_DIR = DATASETS / "emotional"

EMOTIONAL_FILES = (
    "affective_context", "perspective", "empathy", "regulation", "frustration",
    "conflict", "apology", "disagreement", "boundaries", "encouragement",
    "celebration", "silence", "timing", "repair", "preference_pairs",
)


def _load(name: str) -> list[dict]:
    path = EMOTIONAL_DIR / f"{name}.jsonl"
    assert path.exists(), f"missing: {path}"
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _emotional(**overrides) -> dict:
    ex = {
        "example_id": "emo-00182",
        "task": "appropriate_acknowledgement",
        "situation": {
            "relationship": "owner",
            "conversation_phase": "repair",
            "user_goal": "solve_problem",
            "affective_hypotheses": [
                {"label": "frustration", "probability": 0.76},
                {"label": "fatigue", "probability": 0.14},
            ],
            "novi_caused_problem": True,
            "interruptibility": 0.30,
        },
        "desired_behavior": {
            "act": ["ACKNOWLEDGE", "APOLOGIZE", "SOLVE"],
            "verbosity": "short",
            "defensiveness": "none",
            "certainty": "moderate",
        },
        "preferred_response": "Yeah, I took that the wrong way. Let me reset.",
    }
    ex.update(overrides)
    return ex


class TestEmotionalSchema:
    def test_plan_section24_example_valid(self):
        assert validate_example(_emotional(), kind="emotional") == []

    def test_plan_section24_example_roundtrips(self):
        e = EmotionalExample.from_dict(_emotional())
        assert e.example_id == "emo-00182"
        assert e.desired_behavior["act"] == ["ACKNOWLEDGE", "APOLOGIZE", "SOLVE"]
        assert validate_example(e.to_dict(), kind="emotional") == []

    def test_rejects_unknown_affective_label(self):
        ex = _emotional()
        ex["situation"]["affective_hypotheses"][0]["label"] = "telepathy"
        assert validate_example(ex, kind="emotional")

    def test_rejects_probability_out_of_range(self):
        ex = _emotional()
        ex["situation"]["affective_hypotheses"][0]["probability"] = 1.7
        assert validate_example(ex, kind="emotional")

    def test_rejects_unknown_act(self):
        ex = _emotional()
        ex["desired_behavior"]["act"] = ["TELEPORT"]
        assert validate_example(ex, kind="emotional")

    def test_rejects_unknown_defensiveness(self):
        ex = _emotional()
        ex["desired_behavior"]["defensiveness"] = "aggressive"
        assert validate_example(ex, kind="emotional")

    def test_rejects_unknown_certainty(self):
        ex = _emotional()
        ex["desired_behavior"]["certainty"] = "absolute"
        assert validate_example(ex, kind="emotional")

    def test_rejects_unknown_conversation_phase(self):
        ex = _emotional()
        ex["situation"]["conversation_phase"] = "telepathy"
        assert validate_example(ex, kind="emotional")

    def test_silence_allows_empty_response(self):
        ex = _emotional(task="appropriate_silence")
        ex["desired_behavior"]["act"] = ["SILENCE"]
        ex["preferred_response"] = ""
        assert validate_example(ex, kind="emotional") == []

    def test_missing_response_rejected_for_spoken_acts(self):
        ex = _emotional()
        ex["preferred_response"] = ""
        assert validate_example(ex, kind="emotional")

    def test_preference_task_requires_pair(self):
        ex = _emotional(task="preference")
        ex["category"] = "naturalness"
        ex["response_a"] = "I sincerely apologize for any frustration this misunderstanding may have caused."
        ex["response_b"] = "Yeah, I got that wrong. Let me reset."
        ex["preferred"] = "B"
        assert validate_example(ex, kind="emotional") == []

    def test_preference_rejects_bad_preferred(self):
        ex = _emotional(task="preference")
        ex["category"] = "naturalness"
        ex["response_a"] = "a"
        ex["response_b"] = "b"
        ex["preferred"] = "C"
        assert validate_example(ex, kind="emotional")

    def test_preference_rejects_unknown_category(self):
        ex = _emotional(task="preference")
        ex["category"] = "telepathy"
        ex["response_a"] = "a"
        ex["response_b"] = "b"
        ex["preferred"] = "B"
        assert validate_example(ex, kind="emotional")

    def test_perspective_task_requires_evidence_and_interpretations(self):
        ex = _emotional(task="perspective")
        ex["evidence"] = "Fine. Whatever."
        ex["interpretations"] = [
            {"label": "frustration", "probability": 0.55},
            {"label": "fatigue", "probability": 0.20},
            {"label": "disengagement", "probability": 0.15},
            {"label": "casualness", "probability": 0.10},
        ]
        ex["robust_action"] = "reduce pressure"
        assert validate_example(ex, kind="emotional") == []

    def test_perspective_rejects_probabilities_not_summing_to_one(self):
        ex = _emotional(task="perspective")
        ex["evidence"] = "Fine."
        ex["interpretations"] = [{"label": "frustration", "probability": 0.3}]
        ex["robust_action"] = "reduce pressure"
        assert validate_example(ex, kind="emotional")

    def test_perspective_requires_robust_action(self):
        ex = _emotional(task="perspective")
        ex["evidence"] = "Fine."
        ex["interpretations"] = [{"label": "frustration", "probability": 1.0}]
        ex["robust_action"] = ""
        assert validate_example(ex, kind="emotional")

    def test_sft_tasks_match_plan_section25(self):
        assert frozenset({
            "appropriate_acknowledgement", "appropriate_silence", "repair", "apology",
            "calm_disagreement", "support", "encouragement", "celebration",
            "boundary_respect", "uncertainty",
        }) == EMOTIONAL_SFT_TASKS

    def test_preference_categories_match_plan_section26(self):
        assert frozenset({
            "proportionality", "naturalness", "restraint", "emotional_timing",
            "humility", "boundary_respect", "repair",
        }) == EMOTIONAL_PREFERENCE_CATEGORIES


class TestEmotionalDatasets:
    def test_all_plan_files_exist(self):
        for name in EMOTIONAL_FILES:
            assert (EMOTIONAL_DIR / f"{name}.jsonl").exists(), name

    def test_all_rows_schema_valid(self):
        for name in EMOTIONAL_FILES:
            for ex in _load(name):
                assert validate_example(ex, kind="emotional") == [], (name, ex["example_id"])

    def test_unique_ids_across_all_files(self):
        seen = set()
        for name in EMOTIONAL_FILES:
            for ex in _load(name):
                assert ex["example_id"] not in seen, ex["example_id"]
                seen.add(ex["example_id"])

    def test_preference_pairs_cover_plan_categories(self):
        pairs = _load("preference_pairs")
        cats = {p["category"] for p in pairs}
        assert cats == EMOTIONAL_PREFERENCE_CATEGORIES

    def test_sft_tasks_covered_by_non_preference_files(self):
        tasks = set()
        for name in EMOTIONAL_FILES:
            if name == "preference_pairs":
                continue
            for ex in _load(name):
                tasks.add(ex["task"])
        assert tasks >= EMOTIONAL_SFT_TASKS

    def test_perspective_interpretations_sum_to_one(self):
        for ex in _load("perspective"):
            total = sum(i["probability"] for i in ex["interpretations"])
            assert abs(total - 1.0) < 1e-6, ex["example_id"]

    def test_reproducible(self):
        script = DATASETS / "build_emotional_datasets.py"
        out = subprocess.run([sys.executable, str(script), "--check"], capture_output=True,
                             text=True, cwd=Path(__file__).resolve().parents[2])
        assert out.returncode == 0, out.stderr
        assert "OK" in out.stdout
