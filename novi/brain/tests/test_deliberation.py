"""Multi-step LLM deliberation (Reasoning 3.0).

Verifies the DeliberativeLLMReasoningProvider: structured analysis→options→
decision output, allowlist validation with safe fallback, and wiring into the
runtime reasoning trace.
"""

import json
import unittest
from unittest import mock

from novi.brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
from novi.brain.models.deliberation import DeliberativeLLMReasoningProvider, _deliberation_prompt, _extract_json
from novi.brain.models.reasoning import ActionIntent
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.tests.test_mac_brain import FakeCamera


class ExtractJsonTests(unittest.TestCase):
    def test_parses_plain_json(self):
        self.assertEqual(_extract_json('{"a": 1}'), {"a": 1})

    def test_parses_json_embedded_in_text(self):
        self.assertEqual(_extract_json('prefix {"a": 1} suffix'), {"a": 1})

    def test_empty_returns_empty(self):
        self.assertEqual(_extract_json(""), {})


class PromptTests(unittest.TestCase):
    def test_prompt_lists_allowed_actions_and_situation(self):
        prompt = _deliberation_prompt({"conclusion": "causal_change_inferred"}, (), frozenset({"inspect", "wait"}))
        self.assertIn("inspect", prompt)
        self.assertIn("wait", prompt)
        self.assertIn("causal_change_inferred", prompt)
        self.assertIn("ANALYSIS", prompt)
        self.assertIn("OPTIONS", prompt)
        self.assertIn("DECISION", prompt)


class _FakeResp:
    def __init__(self, data):
        self._data = data

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _fake_urlopen(deliberation: dict):
    def _urlopen(request, timeout=60):
        return _FakeResp(json.dumps({"response": json.dumps(deliberation)}).encode("utf-8"))

    return _urlopen


class DeliberativeProviderTests(unittest.TestCase):
    def test_decide_uses_deliberation_and_captures_trace(self):
        deliberation = {
            "analysis": "alice is present and a causal change was inferred",
            "options": [{"action": "inspect", "pros": "investigate cause", "cons": "none"}],
            "decision": {"action": "inspect", "parameters": {}, "rationale": "investigate the inferred cause"},
        }
        with mock.patch("urllib.request.urlopen", _fake_urlopen(deliberation)):
            p = DeliberativeLLMReasoningProvider()
            intent = p.decide(conclusion="causal_change_inferred", confidence=0.4, situation={"conclusion": "causal_change_inferred"}, recall=())
        self.assertEqual(intent.action, "inspect")
        self.assertIn("deliberated", intent.rationale)
        self.assertEqual(p.last_deliberation["analysis"], deliberation["analysis"])
        self.assertEqual(p.last_deliberation["decision"]["action"], "inspect")

    def test_out_of_allowlist_decision_falls_back_to_default(self):
        deliberation = {"analysis": "x", "options": [], "decision": {"action": "fly", "parameters": {}, "rationale": "bad"}}
        with mock.patch("urllib.request.urlopen", _fake_urlopen(deliberation)):
            p = DeliberativeLLMReasoningProvider(default_action="observe")
            intent = p.decide(conclusion="no_high_salience_change_detected", confidence=0.4, situation={}, recall=())
        self.assertEqual(intent.action, "observe")

    def test_missing_decision_falls_back_to_default(self):
        with mock.patch("urllib.request.urlopen", _fake_urlopen({"analysis": "x"})):
            p = DeliberativeLLMReasoningProvider(default_action="wait")
            intent = p.decide(conclusion="no_high_salience_change_detected", confidence=0.4, situation={}, recall=())
        self.assertEqual(intent.action, "wait")


def _queue_urlopen(responses):
    """Fake urlopen that returns each response in turn (one per LLM round)."""
    it = iter(responses)

    def _urlopen(request, timeout=60):
        return _FakeResp(json.dumps({"response": json.dumps(next(it))}).encode("utf-8"))

    return _urlopen


class MultiRoundDeliberationTests(unittest.TestCase):
    def test_critique_confirms_and_stops_early(self):
        round1 = {"analysis": "a", "options": [], "decision": {"action": "inspect", "parameters": {}, "rationale": "r1"}}
        critique = {"evaluation": "sound", "confirm": True, "decision": {"action": "inspect", "parameters": {}, "rationale": "confirmed"}}
        with mock.patch("urllib.request.urlopen", _queue_urlopen([round1, critique])):
            p = DeliberativeLLMReasoningProvider(max_rounds=3)
            intent = p.decide(conclusion="causal_change_inferred", confidence=0.4, situation={}, recall=())
        self.assertEqual(intent.action, "inspect")
        self.assertEqual(len(p.last_deliberation["rounds"]), 2, "confirmation should stop the loop early")

    def test_critique_revises_decision(self):
        round1 = {"analysis": "a", "options": [], "decision": {"action": "inspect", "parameters": {}, "rationale": "r1"}}
        critique = {"evaluation": "inspect is risky", "confirm": False, "decision": {"action": "observe", "parameters": {}, "rationale": "revised"}}
        with mock.patch("urllib.request.urlopen", _queue_urlopen([round1, critique])):
            p = DeliberativeLLMReasoningProvider(max_rounds=2)
            intent = p.decide(conclusion="causal_change_inferred", confidence=0.4, situation={}, recall=())
        self.assertEqual(intent.action, "observe", "revised decision should win")

    def test_max_rounds_bounds_loop(self):
        round1 = {"analysis": "a", "options": [], "decision": {"action": "inspect", "parameters": {}, "rationale": "r1"}}
        critique = {"evaluation": "keep revising", "confirm": False, "decision": {"action": "observe", "parameters": {}, "rationale": "r2"}}
        with mock.patch("urllib.request.urlopen", _queue_urlopen([round1, critique])):
            p = DeliberativeLLMReasoningProvider(max_rounds=2)
            intent = p.decide(conclusion="causal_change_inferred", confidence=0.4, situation={}, recall=())
        self.assertEqual(len(p.last_deliberation["rounds"]), 2, "loop must be bounded by max_rounds")
        self.assertEqual(intent.action, "observe")


class AliceBackend(DeterministicPerceptionBackend):
    def detect(self, frame):
        return (Detection("alice", 0.9, (0.0, 0.0, 1.0, 1.0)),)


class _FakeDeliberative:
    last_deliberation = {"analysis": "alice present", "options": [], "decision": {"action": "observe", "parameters": {}, "rationale": "attend"}}

    def decide(self, *, conclusion, confidence, situation, recall=()):
        return ActionIntent(action="observe", parameters={}, rationale="deliberated")


class DeliberationRuntimeTests(unittest.TestCase):
    def test_step_emits_deliberation_and_trace(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(AliceBackend()), reasoning=_FakeDeliberative(), config=MacBrainConfig())
        brain.start()
        try:
            brain.step()
            events = [e for e in brain.events if e["event_type"] == "reasoning.deliberation"]
            self.assertTrue(events)
            self.assertEqual(events[-1]["payload"]["action"], "observe")
            self.assertIn("analysis", events[-1]["payload"]["deliberation"])
            self.assertIn("deliberation", brain._last_reasoning_trace)
        finally:
            brain.stop()


if __name__ == "__main__":
    unittest.main()
