"""Tests for brain integration: reranker, policy scorer, claim validator, shadow."""

from __future__ import annotations

import json

from training.evaluation.benchmark import BaselinePolicy, Decision
from training.evaluation.shadow import ShadowRunner, should_promote
from training.integration.claim_validator import ClaimValidator, validate_response
from training.integration.policy_scorer import LearnedPolicyScorer, deterministic_rank, select_action
from training.integration.reranker import LearnedReranker, composite_rank

# ---------------------------------------------------------------------------
# reranker (plan §34)
# ---------------------------------------------------------------------------


class TestCompositeRerank:
    def test_ranks_by_composite_signal(self):
        candidates = [
            {"id": "mem-1", "summary": "irrelevant old memory", "semantic": 0.2, "recency": 0.1, "importance": 0.2},
            {"id": "mem-2", "summary": "exactly the topic", "semantic": 0.95, "recency": 0.8, "importance": 0.7},
        ]
        ranked = composite_rank("what did we decide about the camera?", candidates)
        assert ranked[0]["id"] == "mem-2"
        assert ranked[0]["score"] > ranked[1]["score"]

    def test_ranking_explainable(self):
        candidates = [{"id": "m1", "summary": "x", "semantic": 0.9}]
        ranked = composite_rank("q", candidates)
        assert "why" in ranked[0]
        assert ranked[0]["why"]

    def test_lexical_semantic_boost(self):
        c1 = {"id": "m1", "summary": "camera integration discussion", "semantic": 0.5}
        c2 = {"id": "m2", "summary": "bought milk", "semantic": 0.8}
        ranked = composite_rank("camera integration", [c1, c2])
        # m1 shares query tokens -> beats higher generic semantic score
        assert ranked[0]["id"] == "m1"


class TestLearnedReranker:
    def test_artifact_weights_applied(self, tmp_path):
        artifact = tmp_path / "reranker.json"
        artifact.write_text(json.dumps({
            "model": "linear", "features": ["semantic", "recency"],
            "weights": {"w_0": 1.0, "w_1": 0.0}, "bias": 0.0,
        }))
        r = LearnedReranker(str(artifact))
        candidates = [
            {"id": "a", "semantic": 0.9, "recency": 0.1},
            {"id": "b", "semantic": 0.1, "recency": 0.9},
        ]
        ranked = r.rerank("q", candidates)
        assert ranked[0]["id"] == "a"  # semantic weighted 1.0, recency 0.0

    def test_missing_artifact_falls_back_to_composite(self, tmp_path):
        r = LearnedReranker(str(tmp_path / "nope.json"))
        candidates = [{"id": "m1", "summary": "camera stuff", "semantic": 0.5}]
        ranked = r.rerank("camera", candidates)
        assert ranked  # deterministic fallback, never crashes


# ---------------------------------------------------------------------------
# policy scorer (plan §35)
# ---------------------------------------------------------------------------


class TestPolicyScorer:
    def test_deterministic_rank_orders_candidates(self):
        state = {"known_person": True, "new_event": True, "event_salience": 0.9}
        ranked = deterministic_rank(state, ["SILENCE", "GREETING", "CONTINUE"])
        assert ranked[0][0] in ("GREETING", "CONTINUE")  # something proactive wins

    def test_learned_scorer_uses_artifact(self, tmp_path):
        artifact = tmp_path / "policy.json"
        artifact.write_text(json.dumps({
            "state_features": ["event_salience", "known_person"],
            "weights": {"w_0": 1.0, "w_1": 0.0},
            "act_biases": {"COMMENT": 0.5, "SILENCE": 0.0},
        }))
        scorer = LearnedPolicyScorer(str(artifact))
        scores = scorer.score({"event_salience": 0.8, "known_person": 1.0}, ["COMMENT", "SILENCE"])
        assert scores["COMMENT"] > scores["SILENCE"]

    def test_missing_artifact_falls_back(self, tmp_path):
        scorer = LearnedPolicyScorer(str(tmp_path / "nope.json"))
        state = {"known_person": True, "new_event": True, "event_salience": 0.9}
        scores = scorer.score(state, ["GREETING", "SILENCE"])
        assert scores["GREETING"] > scores["SILENCE"]  # deterministic brain prior

    def test_select_action_enforces_guardrails(self, tmp_path):
        # user busy -> SILENCE wins even if scorer prefers COMMENT
        state = {"interruption_cost": 0.95, "user_busy": True}
        act, score, notes = select_action(state, ["COMMENT", "SILENCE"], scorer=None)
        assert act == "SILENCE"
        assert notes  # guardrail note present

    def test_select_action_respects_learned_ranking(self, tmp_path):
        artifact = tmp_path / "policy.json"
        artifact.write_text(json.dumps({
            "state_features": ["event_salience"], "weights": {"w_0": 1.0},
            "act_biases": {"COMMENT": 0.5, "SILENCE": 0.0},
        }))
        state = {"event_salience": 0.9, "user_busy": False}
        act, score, notes = select_action(state, ["SILENCE", "COMMENT"], scorer=LearnedPolicyScorer(str(artifact)))
        assert act == "COMMENT"


# ---------------------------------------------------------------------------
# claim validator (plan §38)
# ---------------------------------------------------------------------------


class TestClaimValidator:
    def _packet(self, **overrides) -> dict:
        p = {
            "known_persons": ["person:owner_001"],
            "world_entities": ["mug", "desk", "shelf"],
            "current_location": "office",
            "retrieved_memory_ids": ["mem-1"],
            "evidence": ["mug on desk"],
            "active_tasks": [],
        }
        p.update(overrides)
        return p

    def test_unknown_person_claimed_known(self):
        flags = validate_response("Hey Alice, good to see you.", self._packet())
        assert any(f["field"] == "person_claim" for f in flags)

    def test_known_person_ok(self):
        flags = validate_response("Hey.", self._packet())
        assert not any(f["field"] == "person_claim" for f in flags)

    def test_unknown_object_claimed(self):
        flags = validate_response("The teapot is on the desk.", self._packet())
        assert any(f["field"] == "object_claim" for f in flags)

    def test_known_object_ok(self):
        flags = validate_response("The mug is on the desk.", self._packet())
        assert not any(f["field"] == "object_claim" for f in flags)

    def test_memory_not_retrieved_but_referenced(self):
        flags = validate_response("We decided to try the side mount.", self._packet())
        assert any(f["field"] == "memory_claim" for f in flags)

    def test_location_not_in_world_state(self):
        flags = validate_response("The mug is in the basement.", self._packet())
        assert any(f["field"] == "location_claim" for f in flags)

    def test_unsupported_action_completion(self):
        flags = validate_response("Done, I moved it.", self._packet())
        assert any(f["field"] == "action_completion" for f in flags)

    def test_clean_response_no_flags(self):
        flags = validate_response("The mug is on the desk.", self._packet())
        assert flags == []

    def test_validator_aggregates(self):
        v = ClaimValidator()
        assert v.is_safe("The mug is on the desk.", self._packet()) is True
        assert v.is_safe("The teapot is in the basement.", self._packet()) is False


# ---------------------------------------------------------------------------
# shadow evaluation (plan §21/§24)
# ---------------------------------------------------------------------------


class TestShadow:
    def _runner(self) -> ShadowRunner:
        return ShadowRunner()

    def test_baseline_vs_baseline_is_parity_and_match(self):
        runner = self._runner()
        report = runner.compare(BaselinePolicy().decide, BaselinePolicy().decide)
        assert report["parity_scenarios"] == 30
        assert report["candidate_wins"] == 0
        # plan §21: candidate must beat *or match* the baseline — parity is fine.
        assert should_promote(report) is True

    def test_worse_candidate_detected(self):
        def worse(scenario):
            return Decision(dialogue_act="SILENCE", response="")
        report = self._runner().compare(BaselinePolicy().decide, worse)
        assert report["candidate_wins"] == 0
        assert report["candidate_losses"] > 0
        assert should_promote(report) is False

    def test_should_promote_requires_not_losing(self):
        report = {
            "candidate_wins": 5, "candidate_losses": 3, "parity_scenarios": 22,
            "candidate_safety_violations": 0, "latency_ok": True,
        }
        assert should_promote(report) is False  # losses exceed tolerance

    def test_should_promote_with_safety_violation(self):
        report = {
            "candidate_wins": 28, "candidate_losses": 0, "parity_scenarios": 2,
            "candidate_safety_violations": 1, "latency_ok": True,
        }
        assert should_promote(report) is False  # any safety violation blocks

    def test_clean_win_promotes(self):
        report = {
            "candidate_wins": 25, "candidate_losses": 0, "parity_scenarios": 5,
            "candidate_safety_violations": 0, "latency_ok": True,
        }
        assert should_promote(report) is True
