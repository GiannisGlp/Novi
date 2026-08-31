"""Tests for the emotional social policy scorer (plan 24 §27, §51 item 29).

The learned scorer ranks candidate emotional acts; deterministic rules remain
authoritative. `select_emotional_act` always applies guardrails, so learning
improves emotional behavior without ever making it unconstrained.
"""

from __future__ import annotations

import json

from training.integration.emotional_policy_scorer import (
    EmotionalPolicyScorer,
    deterministic_emotional_rank,
    select_emotional_act,
)


def _state(**overrides) -> dict:
    s = {
        "relationship": "owner",
        "conversation_phase": "correction",
        "affective_hypotheses": [{"label": "frustration", "probability": 0.7}],
        "novi_caused_problem": True,
        "interruptibility": 0.2,
        "user_goal": "solve_problem",
    }
    s.update(overrides)
    return s


class TestDeterministicRank:
    def test_prefers_apologize_when_novi_caused_problem(self):
        ranked = deterministic_emotional_rank(
            _state(), ["ACKNOWLEDGE", "APOLOGIZE", "DEFEND", "IGNORE"])
        acts = [a for a, _s in ranked]
        assert acts[0] == "APOLOGIZE"
        assert acts.index("DEFEND") > acts.index("APOLOGIZE")

    def test_prefers_silence_when_interruptibility_low(self):
        ranked = deterministic_emotional_rank(
            _state(conversation_phase="tension", interruptibility=0.05),
            ["SILENCE", "RESPOND", "ASK", "SUPPORT"])
        assert ranked[0][0] == "SILENCE"

    def test_prefers_celebrate_on_enthusiasm(self):
        ranked = deterministic_emotional_rank(
            _state(conversation_phase="celebration",
                   affective_hypotheses=[{"label": "enthusiasm", "probability": 0.7}]),
            ["CELEBRATE", "RESPOND", "SILENCE", "SUPPORT"])
        assert ranked[0][0] == "CELEBRATE"

    def test_anti_patterns_rank_low(self):
        ranked = deterministic_emotional_rank(
            _state(), ["APOLOGIZE", "DEFEND", "IGNORE", "MINIMIZE"])
        acts = [a for a, _s in ranked]
        assert acts[0] == "APOLOGIZE"
        for anti in ("DEFEND", "IGNORE", "MINIMIZE"):
            assert acts.index(anti) > acts.index("APOLOGIZE")


class TestGuardrails:
    def test_silence_when_interruptibility_very_low(self):
        act, _score, notes = select_emotional_act(
            _state(interruptibility=0.05), ["SILENCE", "RESPOND", "ASK"], None)
        assert act == "SILENCE"
        assert notes

    def test_silence_on_boundary_state(self):
        act, _score, notes = select_emotional_act(
            _state(boundary_state="DO_NOT_INTERRUPT"), ["SILENCE", "RESPOND", "ASK"], None)
        assert act == "SILENCE"
        assert notes

    def test_anti_pattern_downgraded_even_when_learned_ranks_it_top(self, tmp_path):
        # a (bad) learned scorer ranks DEFEND top; the guardrail must downgrade it
        artifact = tmp_path / "bad.json"
        artifact.write_text(json.dumps({
            "state_features": ["interruptibility"],
            "act_weights": {"DEFEND": {"interruptibility": 10.0}},
            "act_biases": {"DEFEND": 10.0},
        }))
        scorer = EmotionalPolicyScorer(artifact)
        act, _score, notes = select_emotional_act(
            _state(), ["DEFEND", "APOLOGIZE", "ACKNOWLEDGE"], scorer)
        assert act != "DEFEND"
        assert notes

    def test_no_guardrail_normal_case(self):
        act, _score, notes = select_emotional_act(
            _state(), ["ACKNOWLEDGE", "APOLOGIZE", "SOLVE"], None)
        assert act in ("ACKNOWLEDGE", "APOLOGIZE", "SOLVE")
        assert notes == []


class TestEmotionalPolicyScorer:
    def test_no_artifact_uses_deterministic(self):
        scorer = EmotionalPolicyScorer("/nonexistent/artifact.json")
        scores = scorer.score(_state(), ["APOLOGIZE", "DEFEND"])
        assert scores["APOLOGIZE"] > scores["DEFEND"]

    def test_loads_artifact(self, tmp_path):
        artifact = tmp_path / "scorer.json"
        artifact.write_text(json.dumps({
            "state_features": ["interruptibility", "novi_caused_problem"],
            "act_weights": {"APOLOGIZE": {"interruptibility": 1.0, "novi_caused_problem": 2.0}},
            "act_biases": {"APOLOGIZE": 0.5},
        }))
        scorer = EmotionalPolicyScorer(artifact)
        assert scorer._state_features == ["interruptibility", "novi_caused_problem"]
        scores = scorer.score(_state(), ["APOLOGIZE", "SILENCE"])
        assert scores["APOLOGIZE"] > scores["SILENCE"]
