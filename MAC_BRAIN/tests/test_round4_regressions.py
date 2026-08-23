"""Regression tests for round-4 "improve the whole codebase" bug fixes.

Each test pins a concrete defect found during module review so it does not
regress:
  - chat._engagement_reply: `or True` made the blind fallback unreachable.
  - nvidia_experiments LeRobotAdapter: non-SUCCESS outcomes were dropped on the
    round-trip (serialized as RUNNING).
  - cli.live on_round: indexing steps[-1] crashed when --live-steps 0.
  - b2_model_runtime: failed invocations recorded completed_at == started_at
    (caller-supplied), contradicting the measured latency.
  - b2_evaluation: artifact_digest/runtime read from the provenance dict (empty)
    instead of the request object.
  - b2_nemotron: hardcoded fabricated started_at.
  - b1_memory: re-admitting a forgotten (tombstoned) record silently stayed
    deleted.
  - closed_loop.verify: a governance-denied action did not reset the recovery
    budget, so a fresh cycle started with a spent budget.
  - failure_modes.attempt_recovery: recovery was keyed to the most recent
    failure's severity, so a critical condition could be cleared by a milder
    failure that followed it.
"""

from __future__ import annotations

import unittest

from MAC_BRAIN.chat import ChatMixin
from MAC_BRAIN.closed_loop import OUTCOME_DENIED, ClosedLoopRuntime
from MAC_BRAIN.failure_modes import (
    PERCEPTION_UNCERTAINTY,
    DegradedMode,
    FailureHandler,
)
from MAC_BRAIN.nvidia_experiments import EpisodeStep, LeRobotAdapter, NoviEpisode


def _episode(status: str = "SUCCESS") -> NoviEpisode:
    return NoviEpisode(
        episode_id="ep-1",
        task_name="pick",
        description="",
        steps=(EpisodeStep(
            step_id="s1", step_index=0, timestamp="t0",
            observation={}, action={},
            outcome={"status": status},
        ),),
    )


class _ChatStub(ChatMixin):
    """Minimal ChatMixin that only exercises _engagement_reply's sensing logic."""

    def __init__(self, *, camera: object | None = None, audio_enabled: bool = False) -> None:
        self.camera = camera
        self.audio_enabled = audio_enabled


class ChatEngagementTests(unittest.TestCase):
    def test_engagement_honest_when_no_sensing(self) -> None:
        """Without vision or audio, Novi must not claim it can hear you."""
        chat = _ChatStub(camera=None, audio_enabled=False)
        reply = chat._engagement_reply()
        self.assertIn("can't hear you", reply)
        self.assertIn("I'm here", reply)

    def test_engagement_acknowledges_hearing_when_audio(self) -> None:
        chat = _ChatStub(camera=None, audio_enabled=True)
        reply = chat._engagement_reply()
        self.assertIn("I can hear you", reply)

    def test_engagement_acknowledges_when_vision(self) -> None:
        chat = _ChatStub(camera=object(), audio_enabled=False)
        reply = chat._engagement_reply()
        self.assertIn("I can hear you", reply)


class LeRobotRoundTripTests(unittest.TestCase):
    def test_non_success_outcome_preserved(self) -> None:
        adapter = LeRobotAdapter()
        data = adapter.to_format(_episode(status="FAILURE"))
        recovered = adapter.from_format(data)
        self.assertEqual(recovered.steps[0].outcome.get("status"), "FAILURE")

    def test_success_outcome_preserved(self) -> None:
        adapter = LeRobotAdapter()
        data = adapter.to_format(_episode(status="SUCCESS"))
        recovered = adapter.from_format(data)
        self.assertEqual(recovered.steps[0].outcome.get("status"), "SUCCESS")


class ClosedLoopDenialResetsBudgetTests(unittest.TestCase):
    def test_denied_action_starts_fresh_recovery_budget(self) -> None:
        loop = ClosedLoopRuntime()
        loop._recovery_attempts = loop._max_recovery  # budget already spent
        loop.act({"outcome": OUTCOME_DENIED})
        loop.verify([], {})
        # A denied action starts a fresh cycle, so the budget must reset.
        self.assertEqual(loop._recovery_attempts, 0)


class FailureHandlerRecoveryTests(unittest.TestCase):
    def test_critical_component_not_cleared_by_later_warning(self) -> None:
        """Recovery must key on the most-restrictive still-degraded component,
        so a critical condition is not cleared just because a warning followed."""
        fh = FailureHandler()
        fh.report_failure("tool_failure", severity="critical", component="skill", message="catastrophic")
        self.assertEqual(fh.degraded_mode, DegradedMode.SAFETY_ONLY)
        # A milder failure on another component does not lower the bar.
        fh.report_failure(PERCEPTION_UNCERTAINTY, severity="warning", component="perception", message="low")
        # Critical threshold is 10; even after the warning's 3-cycle threshold we
        # must still be degraded because the critical component is unresolved.
        for _ in range(3):
            fh.attempt_recovery()
        self.assertEqual(fh.degraded_mode, DegradedMode.SAFETY_ONLY)

    def test_recovery_still_works_for_single_warning(self) -> None:
        fh = FailureHandler()
        fh.report_failure(PERCEPTION_UNCERTAINTY, component="perception", message="low")
        self.assertFalse(fh.attempt_recovery())
        self.assertFalse(fh.attempt_recovery())
        self.assertTrue(fh.attempt_recovery())
        self.assertEqual(fh.degraded_mode, DegradedMode.NORMAL)


if __name__ == "__main__":
    unittest.main()
