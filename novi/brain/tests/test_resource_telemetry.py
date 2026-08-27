"""Tests for `brain/resource_telemetry.py` and its wiring into MacBrain.

Covers the real-telemetry feed for gap-analysis Step 3, item 19: mapping host
CPU/memory pressure to a resource mode, combining the failure-handler mode
with telemetry (most conservative wins), and the MacBrain wiring that emits a
`resource.telemetry` event and sets the MultiSpeedRuntime resource mode.
"""

import unittest

from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.multi_speed_runtime import AutonomyState, ResourceMode
from novi.brain.resource_telemetry import (
    ResourceSample,
    ResourceTelemetry,
    combine_resource_modes,
)


class FakeTelemetry(ResourceTelemetry):
    """Deterministic telemetry for wiring tests."""

    def __init__(self, sample: ResourceSample) -> None:
        super().__init__(cpu_count=4)
        self._sample = sample

    def sample(self) -> ResourceSample:
        return self._sample


class CombineResourceModesTest(unittest.TestCase):
    def test_most_conservative_wins(self) -> None:
        self.assertEqual(
            combine_resource_modes(ResourceMode.FULL, ResourceMode.DEGRADED),
            ResourceMode.DEGRADED,
        )
        self.assertEqual(
            combine_resource_modes(ResourceMode.REACTIVE_ONLY, ResourceMode.SAFE_MINIMUM),
            ResourceMode.SAFE_MINIMUM,
        )
        self.assertEqual(
            combine_resource_modes(ResourceMode.DEGRADED, ResourceMode.FULL),
            ResourceMode.DEGRADED,
        )
        self.assertEqual(
            combine_resource_modes(ResourceMode.FULL, ResourceMode.FULL),
            ResourceMode.FULL,
        )


class ToResourceModeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tel = ResourceTelemetry(cpu_count=4)

    def test_full_when_idle(self) -> None:
        s = ResourceSample(cpu_load_1m=0.5, cpu_count=4, memory_available_ratio=0.6)
        self.assertEqual(self.tel.to_resource_mode(s), ResourceMode.FULL)

    def test_degraded_on_moderate_cpu(self) -> None:
        # 3.0 load on 4 cores = 0.75/core -> DEGRADED.
        s = ResourceSample(cpu_load_1m=3.0, cpu_count=4, memory_available_ratio=0.6)
        self.assertEqual(self.tel.to_resource_mode(s), ResourceMode.DEGRADED)

    def test_reactive_only_on_high_cpu(self) -> None:
        # 6.0 load on 4 cores = 1.5/core -> REACTIVE_ONLY.
        s = ResourceSample(cpu_load_1m=6.0, cpu_count=4, memory_available_ratio=0.6)
        self.assertEqual(self.tel.to_resource_mode(s), ResourceMode.REACTIVE_ONLY)

    def test_safe_minimum_on_extreme_cpu(self) -> None:
        # 9.0 load on 4 cores = 2.25/core -> SAFE_MINIMUM.
        s = ResourceSample(cpu_load_1m=9.0, cpu_count=4, memory_available_ratio=0.6)
        self.assertEqual(self.tel.to_resource_mode(s), ResourceMode.SAFE_MINIMUM)

    def test_degraded_on_low_memory(self) -> None:
        s = ResourceSample(cpu_load_1m=0.5, cpu_count=4, memory_available_ratio=0.30)
        self.assertEqual(self.tel.to_resource_mode(s), ResourceMode.DEGRADED)

    def test_reactive_only_on_critical_memory(self) -> None:
        s = ResourceSample(cpu_load_1m=0.5, cpu_count=4, memory_available_ratio=0.15)
        self.assertEqual(self.tel.to_resource_mode(s), ResourceMode.REACTIVE_ONLY)

    def test_safe_minimum_on_exhausted_memory(self) -> None:
        s = ResourceSample(cpu_load_1m=0.5, cpu_count=4, memory_available_ratio=0.05)
        self.assertEqual(self.tel.to_resource_mode(s), ResourceMode.SAFE_MINIMUM)

    def test_most_conservative_of_cpu_and_memory(self) -> None:
        # High CPU (REACTIVE_ONLY) + low memory (SAFE_MINIMUM) -> SAFE_MINIMUM.
        s = ResourceSample(cpu_load_1m=6.0, cpu_count=4, memory_available_ratio=0.05)
        self.assertEqual(self.tel.to_resource_mode(s), ResourceMode.SAFE_MINIMUM)

    def test_unknown_signals_do_not_degrade(self) -> None:
        s = ResourceSample(cpu_load_1m=None, cpu_count=None, memory_available_ratio=None)
        self.assertEqual(self.tel.to_resource_mode(s), ResourceMode.FULL)


class SampleTest(unittest.TestCase):
    def test_sample_returns_sane_values(self) -> None:
        s = ResourceTelemetry().sample()
        self.assertIsNotNone(s.cpu_load_1m)
        self.assertGreaterEqual(s.cpu_load_1m, 0.0)
        self.assertIsNotNone(s.cpu_count)
        self.assertGreater(s.cpu_count, 0)
        # Memory may be unavailable on some hosts; if present it must be sane.
        if s.total_memory_mib is not None:
            self.assertGreater(s.total_memory_mib, 0)
        self.assertIn("cpu_load_1m", s.snapshot())


class MacBrainWiringTest(unittest.TestCase):
    def _brain(self, telemetry: FakeTelemetry) -> MacBrain:
        return MacBrain(
            camera=None,
            perception=None,
            config=MacBrainConfig(curiosity_enabled=False),
            telemetry=telemetry,
        )

    def test_full_telemetry_keeps_full_mode(self) -> None:
        brain = self._brain(FakeTelemetry(ResourceSample(cpu_load_1m=0.5, cpu_count=4, memory_available_ratio=0.6)))
        brain._apply_resource_adaptation()
        self.assertEqual(brain.multi_speed.resource_mode, ResourceMode.FULL)
        self.assertEqual(brain.multi_speed.state, AutonomyState.ACTIVE)

    def test_high_pressure_degrades_runtime(self) -> None:
        brain = self._brain(FakeTelemetry(ResourceSample(cpu_load_1m=9.0, cpu_count=4, memory_available_ratio=0.05)))
        brain._apply_resource_adaptation()
        self.assertEqual(brain.multi_speed.resource_mode, ResourceMode.SAFE_MINIMUM)
        self.assertEqual(brain.multi_speed.state, AutonomyState.SAFE_MINIMUM)

    def test_emits_resource_telemetry_event(self) -> None:
        brain = self._brain(FakeTelemetry(ResourceSample(cpu_load_1m=0.5, cpu_count=4, memory_available_ratio=0.6)))
        brain._apply_resource_adaptation()
        events = [e for e in brain.events if e.get("event_type") == "resource.telemetry"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["payload"]["resource_mode"], ResourceMode.FULL.value)
        self.assertIn("cpu_load_1m", events[0]["payload"])

    def test_failure_mode_and_telemetry_combine(self) -> None:
        # Failure handler NORMAL (default) but telemetry reports SAFE_MINIMUM pressure.
        brain = self._brain(FakeTelemetry(ResourceSample(cpu_load_1m=9.0, cpu_count=4, memory_available_ratio=0.05)))
        brain._apply_resource_adaptation()
        self.assertEqual(brain.multi_speed.resource_mode, ResourceMode.SAFE_MINIMUM)


if __name__ == "__main__":
    unittest.main()
