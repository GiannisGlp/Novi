"""Tests for novi/brain/backchannel.py — natural non-content responses.

Plan 24 Phase 17: backchannels (yeah, right, okay, mm-hm, I see, exactly) are
used only when appropriate and never interrupt speech.
"""

from __future__ import annotations

import unittest

from novi.brain.backchannel import BackchannelManager


class BackchannelTest(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = BackchannelManager()

    def test_has_natural_backchannels(self) -> None:
        for token in ("yeah", "right", "okay", "mm-hm", "I see", "exactly"):
            self.assertIn(token, self.manager.tokens)

    def test_never_interrupts_speech(self) -> None:
        # plan §17: backchannels should not interrupt speech
        self.assertIsNone(self.manager.opportunity(user_speaking=True, pause_seconds=0.5))

    def test_opportunity_during_pause(self) -> None:
        token = self.manager.opportunity(user_speaking=False, pause_seconds=1.0)
        self.assertIn(token, self.manager.tokens)

    def test_no_backchannel_when_inappropriate(self) -> None:
        # no backchannel when the user just finished a full turn and expects a response
        self.assertIsNone(self.manager.opportunity(user_speaking=False, pause_seconds=3.0, turn_complete=True))

    def test_backchannel_limited_by_cooldown(self) -> None:
        self.manager.opportunity(user_speaking=False, pause_seconds=1.0)
        # a second opportunity too soon is suppressed
        self.assertIsNone(self.manager.opportunity(user_speaking=False, pause_seconds=1.0))

    def test_snapshot_roundtrip(self) -> None:
        self.manager.opportunity(user_speaking=False, pause_seconds=1.0)
        restored = BackchannelManager.from_snapshot(self.manager.snapshot())
        self.assertEqual(restored.last_backchannel_cycle, self.manager.last_backchannel_cycle)


if __name__ == "__main__":
    unittest.main()
