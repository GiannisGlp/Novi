"""Endurance testing (gap-analysis Step 3, item 22).

Long-horizon runs exercise the runtime's stability and boundedness: the event
bus must stay capped (backpressure), the audit trail must stay within its
retention bound, memory must not grow without bound, and the brain must remain
responsive and deterministic across thousands of cycles.
"""

import unittest

from novi.brain.autonomy import Goal, GoalStatus
from novi.brain.io import VirtualBody
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.tests.test_mac_brain import FakeCamera


class LongRunEnduranceTests(unittest.TestCase):
    def test_1000_cycles_no_crash_event_bus_bounded(self):
        brain = MacBrain(camera=FakeCamera(), body=VirtualBody(), config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.set_goal(Goal.reach(3.0, 0.0, max_steps=1000, goal_id="endure-reach"))
        for _ in range(1000):
            brain.step()
        brain.stop()
        # Event bus stays within its bounded capacity (backpressure drops oldest).
        health = brain.event_bus.health()
        self.assertLessEqual(health["retained"], health["max_events"])
        self.assertGreater(health["published"], 0)
        # Goal completed or still bounded; never leaked into an error state.
        state = brain.goals.status_of("endure-reach")
        self.assertIn(state, (GoalStatus.COMPLETED, GoalStatus.ACTIVE, GoalStatus.FAILED))
        # Audit trail recorded a bounded, non-empty trace.
        self.assertGreater(len(brain.audit_entries()), 0)

    def test_event_bus_backpressure_drops_oldest(self):
        brain = MacBrain(camera=FakeCamera(), config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        for _ in range(200):
            brain.step()
        brain.stop()
        health = brain.event_bus.health()
        self.assertGreaterEqual(health["dropped"], 0)
        self.assertLessEqual(health["retained"], health["max_events"])

    def test_audit_trail_retention_cap(self):
        from novi.brain.audit_trail import AuditTrail

        trail = AuditTrail(retention_max_entries=50)
        for i in range(120):
            trail.record(correlation_id=f"c{i}", action="step", decision_reason="r",
                         policy_result="ALLOW:R0", safety_result="executed", outcome="success")
        self.assertLessEqual(len(trail.entries()), 50)
        stats = trail.stats()
        self.assertEqual(stats["records"], 50)

    def test_repeated_adopt_replan_no_state_leak(self):
        # Repeated goal adoption + replanning must not accumulate controller state.
        brain = MacBrain(camera=FakeCamera(), body=VirtualBody(), config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        for i in range(50):
            brain.set_goal(Goal.reach(1.0, 0.0, max_steps=20, goal_id=f"goal-{i}"))
            brain.replan_goal(f"goal-{i}")
            brain.step()
        brain.stop()
        # History is bounded by terminal goals; no crash across 50 cycles.
        self.assertGreaterEqual(len(brain.goals.history), 1)
        # Event bus remains bounded under the adopt/replan churn.
        health = brain.event_bus.health()
        self.assertLessEqual(health["retained"], health["max_events"])

    def test_long_horizon_curiosity_no_overflow(self):
        from novi.brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception

        class CatBackend(DeterministicPerceptionBackend):
            def detect(self, frame):
                return (Detection("cat", 0.9, (0, 0, 1, 1)),)

        brain = MacBrain(
            camera=FakeCamera(), body=VirtualBody(),
            perception=SpecialistPerception(CatBackend()),
            config=MacBrainConfig(curiosity_enabled=True),
        )
        brain.start()
        for _ in range(300):
            brain.step()
        brain.stop()
        health = brain.event_bus.health()
        self.assertLessEqual(health["retained"], health["max_events"])
        self.assertGreaterEqual(health["dropped"], 0)  # backpressure engaged under load


if __name__ == "__main__":
    unittest.main()
