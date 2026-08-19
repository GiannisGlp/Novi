import unittest

from brain.b1_world import DeterministicWorld, SensorObservation, TemporalWorldModel, run_world_scenario


class B1WorldTests(unittest.TestCase):
    def test_scenario_is_deterministic(self) -> None:
        first = run_world_scenario()
        second = run_world_scenario()
        self.assertEqual(first, second)

    def test_multiple_entities_and_changes_are_tracked(self) -> None:
        result = run_world_scenario()
        self.assertEqual(result.final_world["alice"].location, "living_room")
        self.assertEqual(result.final_world["door"].state, "closed")
        self.assertEqual(result.final_world["object_a"].location, "shelf")
        self.assertEqual(len(result.correlated_events), 6)
        self.assertGreaterEqual(result.observation_count, 18)

    def test_stale_observation_cannot_regress_state(self) -> None:
        model = TemporalWorldModel()
        model.apply(SensorObservation(1, "camera", "alice", "kitchen", "present", 0.9, 1))
        model.apply(SensorObservation(2, "camera", "alice", "living_room", "present", 0.9, 2))
        accepted = model.apply(SensorObservation(3, "replay", "alice", "kitchen", "present", 0.5, 1))
        self.assertFalse(accepted)
        self.assertEqual(model.current("alice").location, "living_room")
        self.assertEqual(len(model.state.stale_observations), 1)

    def test_duplicate_event_correlation_is_suppressed(self) -> None:
        world = DeterministicWorld()
        model = TemporalWorldModel()
        events = world.advance()
        self.assertEqual(len(model.correlate(events)), 1)
        self.assertEqual(len(model.correlate(events)), 0)
        self.assertEqual(len(model.state.correlated_events), 1)

    def test_world_can_distinguish_ground_truth_from_observed_state(self) -> None:
        world = DeterministicWorld()
        model = TemporalWorldModel()
        world.advance()
        observations = world.observe()
        model.apply_many(observations)
        self.assertNotEqual(world.entities["alice"].location, "kitchen")
        self.assertEqual(model.current("alice").location, "living_room")


if __name__ == "__main__":
    unittest.main()
