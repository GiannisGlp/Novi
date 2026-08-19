import unittest

from brain.b1_loop import ClosedSimulatedLoop
from brain.runtime import BrainSupervisor, Lifecycle


class B1LoopTests(unittest.TestCase):
    def test_three_cycle_loop_is_continuous_and_stateful(self) -> None:
        loop = ClosedSimulatedLoop()
        experiences = loop.run(3)

        self.assertEqual(len(experiences), 3)
        self.assertEqual(loop.state.cycle, 3)
        self.assertEqual(len(loop.state.experiences), 3)
        self.assertIn("test_object", loop.state.world)
        self.assertEqual(loop.state.active_goals[0].name, "inspect_familiar_entity")
        self.assertEqual(loop.brain.lifecycle, Lifecycle.SHUTTING_DOWN)

    def test_memory_changes_next_cycle_context(self) -> None:
        loop = ClosedSimulatedLoop()
        loop.brain.start()

        first = loop.step()
        second = loop.step()

        self.assertEqual(first.cycle, 1)
        self.assertEqual(second.cycle, 2)
        self.assertEqual(len(loop.memory.recall("test_object")), 2)
        goal_events = [event for event in loop.brain.events.events if event.event_type == "autonomy.goal.selected"]
        self.assertEqual(goal_events[0].payload["memory_count"], 0)
        self.assertEqual(goal_events[1].payload["memory_count"], 1)

    def test_event_lineage_is_preserved(self) -> None:
        loop = ClosedSimulatedLoop()
        loop.brain.start()
        loop.step()

        events = loop.brain.events.events
        simulation = next(event for event in events if event.event_type == "simulation.observation")
        proposed = next(event for event in events if event.event_type == "action.proposed")
        completed = next(event for event in events if event.event_type == "action.completed")
        stored = next(event for event in events if event.event_type == "memory.experience.stored")

        self.assertEqual(proposed.correlation_id, simulation.correlation_id)
        self.assertEqual(completed.correlation_id, simulation.correlation_id)
        self.assertEqual(stored.correlation_id, simulation.correlation_id)
        self.assertEqual(proposed.causation_id, simulation.correlation_id)
        self.assertEqual(stored.causation_id, completed.correlation_id)

    def test_loop_rejects_non_active_brain(self) -> None:
        loop = ClosedSimulatedLoop(BrainSupervisor())
        with self.assertRaises(RuntimeError):
            loop.step()

    def test_deterministic_scenario_produces_same_semantics(self) -> None:
        first = ClosedSimulatedLoop().run(3)
        second = ClosedSimulatedLoop().run(3)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
