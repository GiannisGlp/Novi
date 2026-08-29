"""Phase 3c (north-star gap analysis): close the prediction-error →
plan-revision loop.

docs/audits/NOVI_NORTH_STAR_GAP_ANALYSIS_2026-08-29.md §4 Phase 3c:
"Close prediction-error → plan-revision loop."

Acceptance:
- a violating observation marks the active plan failed, REPLANS, and the new
  plan becomes the goal's active plan;
- idle brains do not crash (no plan to revise);
- the loop is throttled (at most one violation-driven replan per cycle) and
  recorded for audit.
"""

from __future__ import annotations

import unittest

from novi.brain.autonomy import Goal
from novi.brain.b2_perception import SpecialistPerception
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.io import CameraFrame


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


def _brain() -> MacBrain:
    return MacBrain(
        camera=FrameCamera(),
        perception=SpecialistPerception(),
        config=MacBrainConfig(curiosity_enabled=False),
    )


def _report_violation(brain: MacBrain, entity: str, kind: str) -> dict:
    """Fire a synthetic prediction violation through the real revision path."""
    return brain._maybe_replan_for_violation(entity, kind)


class PlanRevisionTests(unittest.TestCase):
    def test_violating_observation_fails_and_replaces_the_active_plan(self):
        brain = _brain()
        brain.start()
        try:
            goal = brain.set_goal(Goal.reach(1.0, 2.0, max_steps=50, created_cycle=0))
            original_plan = brain.current_plan()
            self.assertIsNotNone(original_plan)
            self.assertEqual(original_plan.status, "running")

            _report_violation(brain, "cup", "sequence_violated")

            new_plan = brain.current_plan()
            self.assertIsNotNone(new_plan)
            self.assertNotEqual(new_plan.plan_id, original_plan.plan_id)
            self.assertEqual(new_plan.status, "running")
            self.assertEqual(original_plan.status, "failed")
            events = [e["event_type"] for e in brain.events]
            self.assertIn("plan.replanned", events)
            self.assertIn("plan.revised", events)
        finally:
            brain.stop()

    def test_violation_without_active_plan_is_a_no_op(self):
        brain = _brain()
        brain.start()
        try:
            result = _report_violation(brain, "cup", "expectation_violated")
            self.assertEqual(result, "no_active_goal")
            # No plan churned.
            self.assertEqual(list(brain._plans), [])
        finally:
            brain.stop()

    def test_revision_is_throttled(self):
        brain = _brain()
        brain.start()
        try:
            brain.set_goal(Goal.investigate("cup", max_steps=50, created_cycle=0))
            first = _report_violation(brain, "cup", "sequence_violated")
            self.assertIsNotNone(first)
            self.assertFalse(isinstance(first, str))
            plan_after_first = brain.current_plan().plan_id
            # Same cycle: no second revision (throttled).
            second = _report_violation(brain, "cup", "sequence_violated")
            self.assertEqual(second, "throttled")
            self.assertEqual(brain.current_plan().plan_id, plan_after_first)
            # A new cycle allows a violation-driven revision again.
            brain.step()
            third = _report_violation(brain, "cup", "sequence_violated")
            self.assertIsNotNone(third)
            self.assertFalse(isinstance(third, str))
            self.assertNotEqual(brain.current_plan().plan_id, plan_after_first)
        finally:
            brain.stop()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
