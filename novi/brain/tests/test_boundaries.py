"""Tests for novi/brain/boundaries.py — explicit boundary states.

Plan 24 Phase 14: NORMAL, REDUCE_CONTACT, DO_NOT_INTERRUPT, DO_NOT_PROBE,
TOPIC_LIMIT, PRIVACY_LIMIT, SAFETY_LIMIT. Boundaries are durable where
appropriate and revocable. "I don't want to talk about that." → record
boundary → stop probing.
"""

from __future__ import annotations

import unittest

from novi.brain.boundaries import BoundaryManager, BoundaryState


class BoundaryManagerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = BoundaryManager()

    def test_default_state_is_normal(self) -> None:
        self.assertEqual(self.manager.state_for("Vano", "camera"), BoundaryState.NORMAL)

    def test_record_boundary(self) -> None:
        # plan §14: "I don't want to talk about that." → record boundary
        self.manager.record("Vano", "camera", BoundaryState.DO_NOT_PROBE)
        self.assertEqual(self.manager.state_for("Vano", "camera"), BoundaryState.DO_NOT_PROBE)

    def test_revoke_boundary(self) -> None:
        self.manager.record("Vano", "camera", BoundaryState.DO_NOT_PROBE)
        self.manager.revoke("Vano", "camera")
        self.assertEqual(self.manager.state_for("Vano", "camera"), BoundaryState.NORMAL)

    def test_probing_blocked_under_do_not_probe(self) -> None:
        self.manager.record("Vano", "camera", BoundaryState.DO_NOT_PROBE)
        self.assertFalse(self.manager.allows("Vano", "camera", action="probe"))
        self.assertTrue(self.manager.allows("Vano", "camera", action="task"))

    def test_interrupt_blocked_under_do_not_interrupt(self) -> None:
        self.manager.record("Vano", "camera", BoundaryState.DO_NOT_INTERRUPT)
        self.assertFalse(self.manager.allows("Vano", "camera", action="interrupt"))
        self.assertTrue(self.manager.allows("Vano", "camera", action="task"))

    def test_emotional_signal_respects_boundary(self) -> None:
        # plan §14: emotional signal + user does not want discussion → continue task normally
        self.manager.record("Vano", "camera", BoundaryState.DO_NOT_PROBE)
        self.assertFalse(self.manager.allows("Vano", "camera", action="probe"))
        self.assertTrue(self.manager.allows("Vano", "camera", action="task"))

    def test_boundaries_are_per_person(self) -> None:
        self.manager.record("Vano", "camera", BoundaryState.DO_NOT_PROBE)
        self.assertEqual(self.manager.state_for("Other", "camera"), BoundaryState.NORMAL)

    def test_snapshot_roundtrip_durable(self) -> None:
        self.manager.record("Vano", "camera", BoundaryState.DO_NOT_PROBE)
        restored = BoundaryManager.from_snapshot(self.manager.snapshot())
        self.assertEqual(restored.state_for("Vano", "camera"), BoundaryState.DO_NOT_PROBE)


if __name__ == "__main__":
    unittest.main()
