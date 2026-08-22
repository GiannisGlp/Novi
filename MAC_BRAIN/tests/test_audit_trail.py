"""Dedicated tests for `MAC_BRAIN/audit_trail.py` (gap-analysis Step 3, item 23).

Covers the doc-13 decision-trace contract: append-only audit records with
correlation ID / goal ID / plan ID / action ID / policy / safety / outcome,
retention controls, user audit view (privacy-safe), and correlation-grouped
reproducible traces.
"""

import unittest

from MAC_BRAIN.audit_trail import AuditEntry, AuditTrail


def rec(trail: AuditTrail, **kw) -> AuditEntry:
    defaults = {
        "correlation_id": "corr-1",
        "action": "move_forward",
        "decision_reason": "goal_pursuit",
        "policy_result": "R1",
        "safety_result": "executed",
        "outcome": "success",
    }
    defaults.update(kw)
    return trail.record(**defaults)


class AuditTrailRecordTests(unittest.TestCase):
    def test_record_creates_immutable_entry(self):
        trail = AuditTrail()
        e = rec(trail)
        self.assertIsInstance(e, AuditEntry)
        self.assertTrue(e.entry_id.startswith("audit-"))
        self.assertEqual(e.action, "move_forward")
        self.assertEqual(e.policy_result, "R1")
        self.assertEqual(e.safety_result, "executed")
        self.assertEqual(e.outcome, "success")
        self.assertTrue(e.timestamp)
        self.assertTrue(e.correlation_id)

    def test_record_captures_full_trace_metadata(self):
        trail = AuditTrail()
        e = rec(trail,
                correlation_id="c-9", goal_id="g-1", plan_id="p-1", action_id="a-1",
                actor="user", version="0.1.0", confidence=0.87)
        self.assertEqual(e.goal_id, "g-1")
        self.assertEqual(e.plan_id, "p-1")
        self.assertEqual(e.action_id, "a-1")
        self.assertEqual(e.actor, "user")
        self.assertEqual(e.version, "0.1.0")
        self.assertEqual(e.confidence, 0.87)

    def test_entries_are_append_only_ordered(self):
        trail = AuditTrail()
        rec(trail, action="wait")
        rec(trail, action="observe")
        snapshots = trail.snapshots()
        self.assertEqual([s["action"] for s in snapshots], ["wait", "observe"])


class AuditTrailPrivacyTests(unittest.TestCase):
    def test_raw_media_redacted(self):
        trail = AuditTrail()
        e = rec(trail, details={"audio": b"raw-bytes", "frame": [1, 2, 3], "note": "ok"})
        self.assertNotEqual(e.details["audio"], b"raw-bytes")
        self.assertNotEqual(e.details["frame"], [1, 2, 3])
        self.assertEqual(e.details["note"], "ok")

    def test_user_view_is_privacy_safe(self):
        trail = AuditTrail()
        rec(trail, details={"audio": b"xxxx", "frame": b"yyyy", "xyz": 1})
        view = trail.user_audit_view(limit=1)[0]
        self.assertNotIn("audio", view["details"])
        self.assertNotIn("frame", view["details"])
        self.assertEqual(view["details"]["xyz"], 1)


class AuditTrailRetentionTests(unittest.TestCase):
    def test_max_entries_cap(self):
        trail = AuditTrail(retention_max_entries=3)
        for i in range(6):
            rec(trail, action=f"act-{i}")
        self.assertEqual(len(trail.entries()), 3)
        # Oldest dropped; newest retained.
        acts = [e.action for e in trail.entries()]
        self.assertEqual(acts, ["act-3", "act-4", "act-5"])

    def test_age_retention_window(self):
        trail = AuditTrail(retention_seconds=0.0)  # everything is immediately stale
        rec(trail, action="a")
        self.assertEqual(len(trail.entries()), 0)

    def test_stats(self):
        trail = AuditTrail()
        rec(trail, action="observe", outcome="success")
        rec(trail, action="move_forward", outcome="success")
        rec(trail, action="move_forward", outcome="failure")
        stats = trail.stats()
        self.assertEqual(stats["records"], 3)
        self.assertEqual(stats["actions"]["move_forward"], 2)
        self.assertEqual(stats["outcomes"]["success"], 2)


class AuditTrailTraceTests(unittest.TestCase):
    def test_by_correlation_groups_trace(self):
        trail = AuditTrail()
        rec(trail, correlation_id="t1", action="sense")
        rec(trail, correlation_id="t1", action="decide")
        rec(trail, correlation_id="t1", action="act")
        rec(trail, correlation_id="t2", action="other")
        trace = trail.by_correlation("t1")
        self.assertEqual([e.action for e in trace], ["sense", "decide", "act"])
        self.assertEqual(trail.stats()["correlation_domains"], 2)

    def test_trace_by_action_and_goal(self):
        trail = AuditTrail()
        rec(trail, action="pick", action_id="a-1", goal_id="g-9")
        rec(trail, action="move", action_id="a-2", goal_id="g-9")
        rec(trail, action="speak", action_id="a-3", goal_id="g-0")
        self.assertEqual([e.action for e in trail.trace_for_action("a-1")], ["pick"])
        self.assertEqual({e.action for e in trail.by_goal("g-9")}, {"pick", "move"})


class RuntimeAuditWiringTests(unittest.TestCase):
    """Gap-analysis Step 3, item 23: the runtime records consequential actions
    into the persistent audit trail with the doc-13 decision-trace metadata."""

    def test_runtime_records_audit_entries_per_step(self):
        from MAC_BRAIN.runtime import MacBrain, MacBrainConfig
        from MAC_BRAIN.tests.test_mac_brain import FakeCamera

        brain = MacBrain(camera=FakeCamera(), config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.step()
        brain.stop()
        self.assertGreater(len(brain.audit_entries()), 0)
        entry = brain.audit_entries()[-1]
        self.assertTrue(entry["entry_id"].startswith("audit-"))
        self.assertTrue(entry["correlation_id"])
        self.assertEqual(entry["actor"], "runtime")
        self.assertIn(entry["safety_result"], {"executed", "blocked", "held"})
        self.assertIn("policy_result", entry)

    def test_user_audit_view_privacy_safe(self):
        from MAC_BRAIN.runtime import MacBrain, MacBrainConfig
        from MAC_BRAIN.tests.test_mac_brain import FakeCamera

        brain = MacBrain(camera=FakeCamera(), config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.stop()
        view = brain.audit_user_view(limit=1)
        self.assertGreaterEqual(len(view), 1)
        self.assertIn("action", view[0])
        self.assertIn("why", view[0])
        self.assertIn("result", view[0])

    def test_audit_stats_after_run(self):
        from MAC_BRAIN.runtime import MacBrain, MacBrainConfig
        from MAC_BRAIN.tests.test_mac_brain import FakeCamera

        brain = MacBrain(camera=FakeCamera(), config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.stop()
        stats = brain.audit_stats()
        self.assertGreater(stats["records"], 0)
        self.assertGreaterEqual(stats["correlation_domains"], 1)


if __name__ == "__main__":
    unittest.main()
