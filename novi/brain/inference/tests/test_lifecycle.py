"""Runtime lifecycle state-machine tests (plan 12, §18 Phase 13, §37 Phase 37).

These were part of the removed AirLLM lifecycle test module; the state machines
themselves are backend-neutral and retained with the inference runtime.
"""

from __future__ import annotations

import unittest

from novi.brain.inference.lifecycle import (
    LifecycleTransitionError,
    ModelLifecycle,
    ModelResidency,
    new_model_lifecycle,
    new_residency,
)


class LifecycleMachineTests(unittest.TestCase):
    def test_valid_transition(self) -> None:
        machine = new_model_lifecycle()
        machine.transition(ModelLifecycle.REGISTERED)
        machine.transition(ModelLifecycle.VALIDATING)
        machine.transition(ModelLifecycle.READY)
        machine.transition(ModelLifecycle.LOADING)
        machine.transition(ModelLifecycle.LOADED)
        machine.transition(ModelLifecycle.RUNNING)
        self.assertEqual(machine.state, ModelLifecycle.RUNNING)

    def test_forbidden_transition_failed_to_running(self) -> None:
        # plan 12, §18: FAILED -> RUNNING is forbidden.
        machine = new_model_lifecycle()
        machine.transition(ModelLifecycle.REGISTERED)
        machine.transition(ModelLifecycle.VALIDATING)
        machine.transition(ModelLifecycle.FAILED)
        with self.assertRaises(LifecycleTransitionError):
            machine.transition(ModelLifecycle.RUNNING)

    def test_unloaded_can_reenter_registered(self) -> None:
        machine = new_model_lifecycle()
        machine.transition(ModelLifecycle.REGISTERED)
        machine.transition(ModelLifecycle.VALIDATING)
        machine.transition(ModelLifecycle.READY)
        machine.transition(ModelLifecycle.UNLOADED)
        machine.transition(ModelLifecycle.REGISTERED)
        self.assertEqual(machine.state, ModelLifecycle.REGISTERED)

    def test_residency_transitions(self) -> None:
        residency = new_residency()
        residency.transition(ModelResidency.PREPARED)
        residency.transition(ModelResidency.COLD)
        residency.transition(ModelResidency.WARM)
        residency.transition(ModelResidency.ACTIVE)
        residency.transition(ModelResidency.DRAINING)
        self.assertEqual(residency.state, ModelResidency.DRAINING)

    def test_snapshot_records_transitions(self) -> None:
        machine = new_model_lifecycle()
        machine.transition(ModelLifecycle.REGISTERED)
        snapshot = machine.snapshot()
        self.assertEqual(snapshot["state"], "REGISTERED")
        self.assertEqual(len(snapshot["transitions"]), 1)

    def test_transition_to_walks_validated_path(self) -> None:
        machine = new_model_lifecycle()
        machine.transition_to(ModelLifecycle.RUNNING)
        self.assertEqual(machine.state, ModelLifecycle.RUNNING)
        # Every hop of the walked path was a validated transition.
        self.assertGreaterEqual(len(machine.snapshot()["transitions"]), 4)


if __name__ == "__main__":
    unittest.main()
