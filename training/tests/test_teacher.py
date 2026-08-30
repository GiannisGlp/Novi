"""Tests for the teacher/evaluator model (plan 23 §18)."""

from __future__ import annotations

from training.collection.teacher import (
    TeacherEvaluator,
    deterministic_scores,
    filter_dataset,
    rank_responses,
)


def _example(response: str = "The mug is on the desk.") -> dict:
    return {
        "example_id": "dlg-1",
        "task": "natural_dialogue",
        "situation": {
            "person": {"id": "person:owner_001", "name": "", "relationship": "owner", "confidence": 0.98},
            "world": {"location": "office", "perception": ["mug on desk"]},
            "conversation": {"topic": "mug", "input_event": "where is the mug?"},
            "memory": [],
            "social": {"engaged": True},
        },
        "decision": {"dialogue_act": "RESPOND", "reason": "", "verbosity": "short"},
        "response": response,
    }


class TestDeterministicScores:
    def test_plan_section18_output_shape(self):
        scores = deterministic_scores(_example("The mug is on the desk."))
        for key in ("grounding", "naturalness", "context_use", "verbosity", "unsupported_claim", "overall"):
            assert key in scores, key
        assert 0.0 <= scores["overall"] <= 1.0

    def test_assistant_phrase_penalizes_naturalness(self):
        bad = deterministic_scores(_example("I acknowledge your statement."))
        good = deterministic_scores(_example("Yeah, that makes sense."))
        assert good["naturalness"] > bad["naturalness"]
        assert good["overall"] > bad["overall"]

    def test_unsupported_claim_detected(self):
        # No perception evidence in the situation -> the claim is unsupported.
        ex = _example("I saw the teapot in the basement.")
        ex["situation"]["world"]["perception"] = []
        scores = deterministic_scores(ex)
        assert scores["unsupported_claim"] > 0.5
        assert scores["grounding"] < 0.5

    def test_verbosity_penalty(self):
        long_resp = "word " * 300
        scores = deterministic_scores(_example(long_resp))
        assert scores["verbosity"] < 0.5

    def test_grounded_response_scores_high(self):
        scores = deterministic_scores(_example("The mug is on the desk."))
        assert scores["grounding"] > 0.8
        assert scores["overall"] > 0.8


class TestRankResponses:
    def test_ranks_natural_over_assistant(self):
        ranked = rank_responses({"topic": "mug"}, [
            "I acknowledge your statement.",
            "Yeah, that makes sense.",
        ])
        assert ranked[0][0] == "Yeah, that makes sense."

    def test_deterministic(self):
        r1 = rank_responses({"topic": "mug"}, ["a", "b"])
        r2 = rank_responses({"topic": "mug"}, ["a", "b"])
        assert r1 == r2


class TestTeacherEvaluator:
    def test_deterministic_backend_no_network(self):
        teacher = TeacherEvaluator(backend="deterministic")
        scores = teacher.evaluate(_example())
        assert scores["overall"] > 0.5

    def test_filter_dataset_keeps_good(self):
        good = _example("Yeah, that makes sense.")
        good["example_id"] = "dlg-2"
        # Clearly bad: assistant-style phrasing + excessive verbosity (>200 chars).
        bad = _example("I acknowledge your statement. In my analysis, considering the full "
                       "context of our prior discussion, I believe it would be most appropriate "
                       "to proceed with the plan we outlined earlier, while also taking into "
                       "account the various factors and constraints that we identified during "
                       "our previous conversation on this subject matter.")
        bad["example_id"] = "dlg-1"
        kept, dropped = filter_dataset([good, bad], min_overall=0.7)
        assert [e["example_id"] for e in kept] == ["dlg-2"]
        assert [e["example_id"] for e in dropped] == ["dlg-1"]
        assert kept[0]["teacher_scores"]["overall"] >= 0.7

    def test_ollama_backend_falls_back_when_offline(self):
        teacher = TeacherEvaluator(backend="ollama", model="qwen3.8:27b", timeout_s=0.5)
        # If ollama is not reachable, evaluation must still return scores.
        scores = teacher.evaluate(_example())
        assert "overall" in scores
