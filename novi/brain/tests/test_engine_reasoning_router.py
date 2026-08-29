"""Phase 3a (north-star gap analysis): grounded reasoning is the engine default.

docs/audits/NOVI_NORTH_STAR_GAP_ANALYSIS_2026-08-29.md §4 Phase 3a:
"Wire ReasoningRouter + LLM deliberation into the engine by default, with
cost-aware routing (LLM only when warranted; per-route cost tracked)."

Acceptance:
- the engine's default reasoning provider is a ReasoningRouter (route tracked,
  cost-aware: LLM only when warranted, graceful degradation on LLM errors);
- surfaces may inject an LLM reasoning provider (`llm_reasoning`) which the
  default router escalates to for factual questions and low-confidence
  conclusions;
- route counts + per-route cost are recorded (metrics + step result);
- a deterministic override still works (full injection unchanged).
"""

from __future__ import annotations

import unittest
from typing import Any

from novi.brain.b2_perception import SpecialistPerception
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.io import CameraFrame
from novi.brain.models.reasoning import ActionIntent
from novi.brain.models.router import ReasoningRouter


class FrameCamera:
    def __init__(self) -> None:
        self.sequence = 0

    def close(self) -> None:
        self.sequence = self.sequence

    def read(self) -> CameraFrame:
        self.sequence += 1
        return CameraFrame(
            frame_id=f"f-{self.sequence}",
            captured_at="2026-08-29T12:00:00Z",
            width=2,
            height=2,
            payload=b"frame",
            metadata={"backend": "test"},
        )


class QuietPerception:
    def detect(self, frame):
        return ()

    def depth(self, frame):
        return None

    def segment(self, frame):
        return None


class ScriptedLLM:
    """A scripted LLM reasoning provider (decide protocol only)."""

    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls = 0

    def decide(self, *, conclusion: str, confidence: float, situation: Any, recall: Any = ()) -> ActionIntent:
        self.calls += 1
        if self.fail:
            raise RuntimeError("ollama down")
        return ActionIntent(
            action="speak",
            parameters={"text": "deliberated-answer"},
            rationale="deliberated via scripted llm",
        )


def _brain(llm=None, reasoning=None) -> MacBrain:
    return MacBrain(
        camera=FrameCamera(),
        perception=SpecialistPerception(QuietPerception()),
        llm_reasoning=llm,
        reasoning=reasoning,
        config=MacBrainConfig(curiosity_enabled=False),
    )


class DefaultWiringTests(unittest.TestCase):
    def test_default_reasoning_is_router(self):
        brain = _brain()
        self.assertIsInstance(brain.reasoning, ReasoningRouter)
        snap = brain.reasoning.snapshot()
        self.assertEqual(snap["confidence_threshold"], 0.6)
        self.assertIsNone(brain.reasoning.llm, "no LLM by default (stdlib-first)")
        # With no LLM configured the router degrades to deterministic on
        # every route — behavior-preserving default.
        self.assertEqual(snap["route_counts"], {})

    def test_deterministic_override_still_works(self):
        from novi.brain.models.reasoning import DeterministicReasoningProvider

        reasoning = DeterministicReasoningProvider()
        brain = _brain(reasoning=reasoning)
        self.assertIs(brain.reasoning, reasoning)


class RoutedStepTests(unittest.TestCase):
    def _question_brain(self, llm) -> MacBrain:
        brain = _brain(llm=llm)
        brain.start()
        try:
            brain.submit("web", "chat", {"text": "what is 47 times 83?"})
            return brain, brain.step()
        finally:
            brain.stop()

    def test_step_routes_factual_question_to_llm(self):
        llm = ScriptedLLM()
        brain, result = self._question_brain(llm)
        self.assertEqual(llm.calls, 1, "the question escalated to the LLM exactly once")
        self.assertEqual(result["reasoning_route"]["route"], "llm")
        self.assertEqual(result["reasoning_route"]["reason"], "factual_needs_llm")
        # The deliberated intent from the LLM drove the cycle's action.
        self.assertEqual(result["action"], "speak")

    def test_llm_error_degrades_to_deterministic(self):
        brain, result = self._question_brain(ScriptedLLM(fail=True))
        self.assertEqual(result["reasoning_route"]["route"], "deterministic")
        self.assertTrue(result["reasoning_route"]["reason"].startswith("llm_error"))
        events = [e["event_type"] for e in brain.events]
        self.assertIn("reasoning.route", events)

    def test_social_fast_path_skips_llm(self):
        llm = ScriptedLLM()
        brain = _brain(llm=llm)
        brain.start()
        try:
            brain.submit("web", "chat", {"text": "hey, thanks so much!"})
            result = brain.step()
            self.assertEqual(llm.calls, 0, "social fast path never pays the LLM round-trip")
            self.assertEqual(result["reasoning_route"]["route"], "deterministic")
        finally:
            brain.stop()

    def test_route_counts_and_cost_recorded(self):
        llm = ScriptedLLM()
        brain = _brain(llm=llm)
        brain.start()
        try:
            brain.submit("web", "chat", {"text": "what is 47 times 83?"})
            result = brain.step()
            self.assertTrue(result["reasoning_route"]["counts"]["llm"] >= 1)
            mapping = {m["name"]: m for m in brain.metrics_snapshot()}
            self.assertIn("reasoning_route_llm", mapping)
            self.assertIn("reasoning_route_deterministic", mapping)
        finally:
            brain.stop()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
