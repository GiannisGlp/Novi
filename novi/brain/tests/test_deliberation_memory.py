"""Plan P5: deliberation memory — persist winning rationale, recall on similar
situations, cite "last time I chose X because Y" in the reasoning trace.

Pins:
  - a deliberative decision is admitted as memory_type="decision" with the
    situation, chosen action, rejected alternatives, and reason;
  - prior decisions are recalled by situation and surfaced in the trace;
  - decisions survive restart (single canonical DB).
"""

import tempfile
import unittest
from pathlib import Path

from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.models.reasoning import ActionIntent
from novi.brain.tests.test_mac_brain import FakeCamera


class _DeliberativeStub:
    """Reasoning provider that sets last_deliberation like the LLM provider."""

    def __init__(self):
        self.last_deliberation = None

    def decide(self, *, conclusion, confidence, situation, recall=()):
        self.last_deliberation = {
            "analysis": "a person spoke and is relevant",
            "options": ["observe", "inspect", "wait"],
            "decision": {"action": "observe", "parameters": {}, "rationale": "attend to the speaker"},
            "rounds": [],
        }
        return ActionIntent(action="observe", parameters={}, rationale="deliberated:attend")


class DeliberationMemoryTests(unittest.TestCase):
    def _brain(self, store_path):
        brain = MacBrain(
            camera=FakeCamera(),
            reasoning=_DeliberativeStub(),
            store_path=store_path,
            config=MacBrainConfig(curiosity_enabled=False),
        )
        brain.start()
        return brain

    def test_decision_memory_persisted_and_recalled(self):
        with tempfile.TemporaryDirectory() as td:
            store = str(Path(td) / "novi.db")
            brain = self._brain(store)
            try:
                # Persist a decision directly.
                deliberation = {
                    "analysis": "a person spoke",
                    "options": ["observe", "inspect", "wait"],
                    "decision": {"action": "observe", "parameters": {}, "rationale": "attend to the speaker"},
                }
                brain._persist_decision_memory(
                    deliberation, {"conclusion": "human_speech_observed"}, ActionIntent(action="observe", parameters={}, rationale="x"), 0.9
                )
                prior = brain._recall_prior_decisions({"conclusion": "human_speech_observed"})
                self.assertTrue(prior)
                self.assertEqual(prior[0]["chosen_action"], "observe")
                self.assertEqual(prior[0]["reason"], "attend to the speaker")
            finally:
                brain.stop()

    def test_decision_survives_restart(self):
        with tempfile.TemporaryDirectory() as td:
            store = str(Path(td) / "novi.db")
            brain = self._brain(store)
            try:
                brain._persist_decision_memory(
                    {"analysis": "a", "options": ["observe", "wait"], "decision": {"action": "observe", "parameters": {}, "rationale": "r"}},
                    {"conclusion": "human_speech_observed"},
                    ActionIntent(action="observe", parameters={}, rationale="x"),
                    0.9,
                )
            finally:
                brain.stop()
            # New brain over the same DB.
            brain2 = self._brain(store)
            try:
                prior = brain2._recall_prior_decisions({"conclusion": "human_speech_observed"})
                self.assertTrue(prior)
                self.assertEqual(prior[0]["chosen_action"], "observe")
            finally:
                brain2.stop()

    def test_trace_includes_prior_decisions(self):
        with tempfile.TemporaryDirectory() as td:
            store = str(Path(td) / "novi.db")
            brain = self._brain(store)
            try:
                brain._persist_decision_memory(
                    {"analysis": "a", "options": ["observe", "wait"], "decision": {"action": "observe", "parameters": {}, "rationale": "attend"}},
                    {"conclusion": "human_speech_observed"},
                    ActionIntent(action="observe", parameters={}, rationale="x"),
                    0.9,
                )
                # Step once so the reasoning path runs and the trace is built.
                brain.step()
                trace = brain._last_reasoning_trace
                self.assertIn("prior_decisions", trace)
            finally:
                brain.stop()


if __name__ == "__main__":
    unittest.main()
