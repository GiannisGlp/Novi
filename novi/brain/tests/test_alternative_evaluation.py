"""Phase 3b (north-star gap analysis): explicit alternative evaluation.

docs/audits/NOVI_NORTH_STAR_GAP_ANALYSIS_2026-08-29.md §4 Phase 3b:
"Add explicit alternative evaluation (score options on expected-success/
cost/risk; select by score; persist scores)."

Acceptance:
- every candidate option carries an explicit expected_success/cost/risk
  triple; selection maximizes the weighted score, not an implicit heuristic;
- costs gate motion (a failed prior action is costlier), risk scales with
  uncertainty;
- the winning rationale is persisted with the scores (decision memory).
"""

from __future__ import annotations

import unittest
from typing import Any

from novi.brain.b2_perception import SpecialistPerception
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.io import CameraFrame
from novi.brain.models.deliberation import OptionScore
from novi.brain.models.reasoning import DeliberativeReasoningProvider


class OptionScoreTests(unittest.TestCase):
    def test_total_prefers_success_over_cost_risk(self):
        good = OptionScore(action="observe", expected_success=0.9, cost=0.1, risk=0.1)
        risky = OptionScore(action="move_forward", expected_success=0.9, cost=0.4, risk=0.6)
        self.assertGreater(good.total(), risky.total())

    def test_total_is_bounded_and_deterministic(self):
        s = OptionScore(action="wait", expected_success=1.0, cost=0.0, risk=0.0)
        self.assertAlmostEqual(s.total(), 1.0)
        self.assertAlmostEqual(s.total(), s.total())


class ScoreDimensionTests(unittest.TestCase):
    def test_causal_signal_gives_inspect_highest_success(self):
        provider = DeliberativeReasoningProvider()
        provider.decide(
            conclusion="causal_change_inferred",
            confidence=0.8,
            situation={"inferences": ("cup_moves_when_pushed",)},
            recall=(),
        )
        scores = provider.last_option_scores
        self.assertEqual(provider.last_action, "inspect")
        self.assertGreater(scores["inspect"].expected_success, scores["observe"].expected_success)

    def test_failure_reflection_raises_failed_action_cost(self):
        provider = DeliberativeReasoningProvider()
        situation: dict[str, Any] = {
            "reflection": {"action": "move_forward", "effective": False},
        }
        provider.decide(conclusion="goal_relevant_change", confidence=0.7, situation=situation, recall=())
        scores = provider.last_option_scores
        self.assertGreater(
            scores["move_forward"].cost,
            scores["observe"].cost,
            "a just-failed action must cost more than an alternative",
        )


class _Cam:
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


class PersistsScoresTests(unittest.TestCase):
    def test_engine_persists_option_scores(self):
        brain = MacBrain(
            camera=_Cam(),
            perception=SpecialistPerception(),
            config=MacBrainConfig(curiosity_enabled=False),
        )
        brain.start()
        try:
            brain.step()
            trace = brain._last_reasoning_trace
            self.assertIn("option_scores", trace)
            self.assertTrue(trace["option_scores"], "scores must be persisted in the reasoning trace")
        finally:
            brain.stop()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
