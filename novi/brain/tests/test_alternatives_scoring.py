"""Shallow hypothesis/alternative reasoning fixes.

Pins:
- IntentHypothesis.alternatives carries real competing hypotheses (never
  hard-coded empty); each hypothesis keeps its confidence + provenance.
- The deliberative LLM path scores options explicitly on
  expected-success/cost/risk under documented fixed weights, selects by
  score, and persists scores on the deliberation trace.
- Dialogue reasoning is non-isolated: discourse topic + prior-turn
  conclusions feed the next turn's input (bounded).

Socket-free: the LLM wire is mocked at the urlopen boundary (the
test_chat_server.py convention); the chat path uses an injected llm_chat
stub, so no test here opens a socket.
"""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from unittest import mock

from novi.brain.b1_world import SensorObservation, WorldEntityState, WorldModelState
from novi.brain.b2_perception import DeterministicPerceptionBackend, SpecialistPerception
from novi.brain.cognition2 import MacCognition
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.models.deliberation import COST_WEIGHT, RISK_WEIGHT, SUCCESS_WEIGHT, DeliberativeLLMReasoningProvider
from novi.brain.tests.test_mac_brain import FakeCamera


def _llm_response(payload: object) -> mock.MagicMock:
    """urlopen double speaking the Ollama /api/generate dialect (no sockets)."""
    resp = mock.MagicMock()
    resp.read.return_value = json.dumps({"response": json.dumps(payload)}).encode("utf-8")
    resp.__enter__.return_value = resp
    return resp


def _state_with_alice() -> WorldModelState:
    return WorldModelState(entities={
        "alice": WorldEntityState(entity="alice", location="kitchen", state="present",
                                  confidence=0.95, last_observed_cycle=1),
        "door": WorldEntityState(entity="door", location="kitchen", state="open",
                                 confidence=0.9, last_observed_cycle=1),
    })


def _observations() -> tuple[SensorObservation, ...]:
    return (
        SensorObservation(source="camera", entity="alice", captured_cycle=1,
                          confidence=0.95, cycle=1, location="kitchen", state="present"),
        SensorObservation(source="camera", entity="door", captured_cycle=1,
                          confidence=0.9, cycle=1, location="kitchen", state="open"),
    )


_KNOWLEDGE = (
    {"subject": "alice", "predicate": "moved", "object": "cup", "confidence": 0.8, "status": "active"},
    {"subject": "door", "predicate": "opened", "object": "door", "confidence": 0.7, "status": "active"},
)
_GOAL = {"kind": "investigate", "target": "cup", "distance_to_goal": 1.0}
_RECALLED = ({"memory_id": "m1", "content": "alice keeps a cup in the kitchen"},)


class AlternativesPopulatedTests(unittest.TestCase):
    def test_alternatives_carry_real_competing_hypotheses(self):
        cog = MacCognition()
        out = cog.cycle_typed(
            _state_with_alice(), _observations(), cycle=1, world_revision=1,
            knowledge=_KNOWLEDGE, goal=_GOAL, recalled=_RECALLED,
        )
        self.assertGreaterEqual(len(out.intent_hypotheses), 2)
        intents = [h.intent for h in out.intent_hypotheses]
        for h in out.intent_hypotheses:
            self.assertTrue(h.alternatives, "alternatives must never be hard-coded empty")
            for alt in h.alternatives:
                self.assertTrue(isinstance(alt, str) and alt)
            self.assertNotIn(h.intent, h.alternatives, "a hypothesis is not its own alternative")
            for alt in h.alternatives:
                self.assertIn(alt, [i for i in intents if i != h.intent] + list(out.decision.recommended_next_states),
                              "alternatives must be real rivals from this cycle, not filler")
            # Confidence + provenance ride on the hypothesis itself.
            self.assertGreaterEqual(h.confidence, 0.0)
            self.assertLessEqual(h.confidence, 1.0)
            self.assertIsNotNone(h.uncertainty)
            self.assertEqual(h.provenance.source, "cognition")
            self.assertTrue(h.supporting_evidence_ids)

    def test_single_hypothesis_still_reports_an_alternative(self):
        from novi.brain.cognition_typed import emit_cognitive_typed
        situation = SimpleNamespace(
            salient_entities=("alice",),
            recent_events=("alice present",),
            uncertainty=(),
            evidence=[SimpleNamespace(source="camera", entity="alice", confidence=0.9)],
            entities=(),
            relations=(),
            recalled=(),
        )
        reasoning = SimpleNamespace(
            conclusion="person_alice_is_relevant_to_current_situation",
            confidence=0.9,
            hypotheses=({"hypothesis": "alice greeting", "confidence": 0.9},),
            inferences=(),
        )
        out = emit_cognitive_typed(situation, reasoning, cycle=1)
        self.assertEqual(len(out.intent_hypotheses), 1)
        self.assertTrue(out.intent_hypotheses[0].alternatives)

    def test_snapshot_stays_json_serializable(self):
        cog = MacCognition()
        out = cog.cycle_typed(
            _state_with_alice(), _observations(), cycle=1, world_revision=1,
            knowledge=_KNOWLEDGE, goal=_GOAL, recalled=_RECALLED,
        )
        json.dumps(out.snapshot())  # must not raise


class ExplicitScoringTests(unittest.TestCase):
    def test_scoring_picks_safest_best_over_risky_llm_pick(self):
        deliberation = {
            "analysis": "goal is near but the last move failed",
            "options": [
                {"action": "move_forward", "pros": "closes distance", "cons": "just failed"},
                {"action": "observe", "pros": "safe", "cons": "slower"},
                {"action": "fly", "pros": "fast", "cons": "impossible"},
            ],
            "decision": {"action": "move_forward", "parameters": {}, "rationale": "push ahead"},
        }
        situation = {"reflection": {"action": "move_forward", "effective": False}}
        with mock.patch("urllib.request.urlopen", return_value=_llm_response(deliberation)):
            provider = DeliberativeLLMReasoningProvider(max_rounds=1)
            intent = provider.decide(
                conclusion="goal_relevant_change", confidence=0.4, situation=situation, recall=(),
            )
        self.assertEqual(intent.action, "observe")
        self.assertIn("deliberated", intent.rationale)
        scores = provider.last_deliberation["scores"]
        self.assertNotIn("fly", scores, "out-of-allowlist options are never scored")
        self.assertEqual(set(scores), {"move_forward", "observe"})
        for entry in scores.values():
            self.assertEqual(set(entry), {"action", "expected_success", "cost", "risk", "total"})
        self.assertGreater(scores["observe"]["total"], scores["move_forward"]["total"])
        self.assertEqual(
            provider.last_deliberation["weights"],
            {"success": SUCCESS_WEIGHT, "cost": COST_WEIGHT, "risk": RISK_WEIGHT},
        )
        self.assertEqual(provider.last_deliberation["selected_by"], "explicit_score:expected_success/cost/risk")

    def test_documented_weights_are_success_half_cost_risk_quarters(self):
        self.assertEqual((SUCCESS_WEIGHT, COST_WEIGHT, RISK_WEIGHT), (0.5, 0.25, 0.25))

    def test_allowlist_fallback_unchanged(self):
        deliberation = {"analysis": "x", "options": [], "decision": {"action": "fly", "parameters": {}, "rationale": "bad"}}
        with mock.patch("urllib.request.urlopen", return_value=_llm_response(deliberation)):
            provider = DeliberativeLLMReasoningProvider(default_action="observe", max_rounds=1)
            intent = provider.decide(conclusion="no_high_salience_change_detected", confidence=0.4, situation={}, recall=())
        self.assertEqual(intent.action, "observe")
        self.assertEqual(provider.last_deliberation["scores"], {})


class ScoresPersistedTests(unittest.TestCase):
    def test_engine_trace_carries_option_scores(self):
        deliberation = {
            "analysis": "nothing salient",
            "options": [{"action": "wait", "pros": "calm", "cons": "none"}],
            "decision": {"action": "wait", "parameters": {}, "rationale": "nothing to do"},
        }
        with mock.patch("urllib.request.urlopen", return_value=_llm_response(deliberation)):
            brain = MacBrain(
                camera=FakeCamera(),
                perception=SpecialistPerception(DeterministicPerceptionBackend()),
                reasoning=DeliberativeLLMReasoningProvider(max_rounds=1),
                config=MacBrainConfig(curiosity_enabled=False),
                store_path=None,
            )
            brain.start()
            try:
                brain.step()
                trace = brain._last_reasoning_trace
            finally:
                brain.stop()
        self.assertTrue(trace["option_scores"], "scores must persist on the decision trace")
        self.assertIn("wait", trace["option_scores"])
        self.assertIn("scores", trace["deliberation"])
        self.assertTrue(trace["deliberation"]["scores"])
        self.assertIn(trace["action"], trace["option_scores"])


class PriorTurnContextTests(unittest.TestCase):
    def test_prior_turn_context_influences_next_decision(self):
        brain = MacBrain(
            camera=FakeCamera(),
            perception=SpecialistPerception(DeterministicPerceptionBackend()),
            config=MacBrainConfig(curiosity_enabled=False),
        )
        brain.start()
        try:
            users: list[str] = []

            def fake_llm_chat(*, system: str, user: str) -> str:
                users.append(user)
                return "The plant on the shelf looks healthy."

            first = brain.respond("tell me about the plant on the shelf", llm_chat=fake_llm_chat)
            self.assertIsNotNone(first["text"])
            second = brain.respond("is it still there?", llm_chat=fake_llm_chat)
            self.assertIsNotNone(second["text"])
        finally:
            brain.stop()
        self.assertEqual(len(users), 2)
        first_payload = json.loads(users[0])
        second_payload = json.loads(users[1])
        self.assertEqual(first_payload["dialogue_context"]["prior_conclusions"], [])
        priors = second_payload["dialogue_context"]["prior_conclusions"]
        self.assertTrue(priors, "the next turn must see prior-turn conclusions")
        self.assertTrue(any("looks healthy" in p for p in priors))
        self.assertTrue(second_payload["dialogue_context"]["topic"], "the ongoing topic must carry over")
        facts = " ".join(second_payload["facts_i_know"])
        self.assertIn("Earlier we concluded:", facts)
        # Bounded: at most 3 prior conclusions, each short.
        self.assertLessEqual(len(priors), 3)
        self.assertTrue(all(len(p) <= 160 for p in priors))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
