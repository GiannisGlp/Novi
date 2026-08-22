"""Tests for the spatial model (roadmap item 11; docs/03-cognition/02 + /22 §20).

Covers coordinate frames with explicit units, region bounds + occupancy,
the metric-vs-semantic link, topology via doors, reachability, visibility,
and runtime wiring (brain.spatial, WorldState.spatial_state).
"""

import unittest

from cognition.contracts.common import SpatialReference
from MAC_BRAIN.spatial_map import (
    SpatialFrame,
    SpatialMap,
    default_home_map,
)


class SpatialFrameTests(unittest.TestCase):
    def test_frames_registered_with_units(self):
        m = SpatialMap()
        m.register_frame(SpatialFrame(name="map", units="m"))
        m.register_frame(SpatialFrame(name="base", parent="map", units="m"))
        snap = m.snapshot()
        self.assertEqual(len(snap["frames"]), 2)
        self.assertEqual(snap["frames"][1]["parent"], "map")

    def test_position_without_frame_is_invalid(self):
        m = default_home_map()
        with self.assertRaises(KeyError):
            m.place("cup_001", SpatialReference(frame_id="nope", pose={"x": 1.0, "y": 1.0}))


class RegionOccupancyTests(unittest.TestCase):
    def test_region_bounds_containment(self):
        m = default_home_map()
        self.assertEqual(m.region_of("robot"), None)  # not placed yet
        m.place("robot_001", SpatialReference(frame_id="map", pose={"x": 1.0, "y": 1.0}))
        self.assertEqual(m.region_of("robot_001"), "kitchen")

    def test_occupancy_lifecycle(self):
        m = default_home_map()
        self.assertEqual(m.occupancy("kitchen"), "free")
        m.set_occupancy("kitchen", "occupied")
        self.assertEqual(m.occupancy("kitchen"), "occupied")
        with self.assertRaises(ValueError):
            m.set_occupancy("kitchen", "bogus")
        with self.assertRaises(KeyError):
            m.set_occupancy("nowhere", "free")


class MetricSemanticLinkTests(unittest.TestCase):
    def test_pose_maps_to_semantic_region(self):
        m = default_home_map()
        m.place("cup_001", SpatialReference(
            frame_id="map", pose={"x": 2.0, "y": 2.0}, semantic_location=["table_zone"],
        ))
        self.assertEqual(m.region_of("cup_001"), "kitchen")
        self.assertIn("table_zone", m.semantic_location_of("cup_001"))
        self.assertIn("kitchen", m.semantic_location_of("cup_001"))

    def test_declared_semantic_fallback_without_pose(self):
        m = default_home_map()
        m.place("cup_002", SpatialReference(frame_id="map", semantic_location=["living_room"]))
        self.assertEqual(m.region_of("cup_002"), "living_room")


class TopologyTests(unittest.TestCase):
    def test_door_connects_regions(self):
        m = default_home_map()
        self.assertIn("kitchen", m.reachable_regions("living_room"))
        self.assertIn("living_room", m.reachable_regions("kitchen"))
        self.assertTrue(m.visibility_between("kitchen", "living_room"))

    def test_no_visibility_without_door(self):
        m = default_home_map()
        # table_zone is a zone inside kitchen; no direct door to living_room.
        self.assertFalse(m.visibility_between("table_zone", "living_room"))
        # But still reachable through kitchen.
        self.assertIn("living_room", m.reachable_regions("table_zone"))

    def test_unknown_region_not_reachable(self):
        m = default_home_map()
        self.assertEqual(m.reachable_regions("basement"), set())


class VisibilityTests(unittest.TestCase):
    def test_visible_entities_in_region(self):
        m = default_home_map()
        m.place("cup_001", SpatialReference(frame_id="map", pose={"x": 1.0, "y": 1.0}))
        m.place("alice", SpatialReference(frame_id="map", semantic_location=["kitchen"]))
        m.place("bob", SpatialReference(frame_id="map", semantic_location=["living_room"]))
        self.assertEqual(sorted(m.visible_entities("kitchen")), ["alice", "cup_001"])


class SnapshotAndTypedStateTests(unittest.TestCase):
    def test_snapshot_shape(self):
        m = default_home_map()
        m.place("cup_001", SpatialReference(frame_id="map", pose={"x": 2.0, "y": 2.0}))
        snap = m.snapshot()
        self.assertIn("version", snap)
        self.assertEqual(len(snap["regions"]), 4)
        self.assertEqual(len(snap["entity_poses"]), 1)

    def test_to_spatial_state_fills_world_state(self):
        m = default_home_map()
        m.place("cup_001", SpatialReference(frame_id="map", pose={"x": 2.0, "y": 2.0}))
        state = m.to_spatial_state()
        self.assertIn("frames", state)
        self.assertIn("regions", state)
        self.assertIn("occupancy", state)
        self.assertEqual(state["occupancy"]["kitchen"], "free")
        self.assertIn("cup_001", state["entity_poses"])


class RuntimeWiringTests(unittest.TestCase):
    def _brain(self):
        from brain.b2_perception import DeterministicPerceptionBackend, SpecialistPerception
        from MAC_BRAIN.runtime import MacBrain, MacBrainConfig
        from MAC_BRAIN.tests.test_mac_brain import FakeCamera
        return MacBrain(
            camera=FakeCamera(),
            perception=SpecialistPerception(DeterministicPerceptionBackend()),
            config=MacBrainConfig(curiosity_enabled=False),
            store_path=None,
        )

    def test_runtime_has_spatial_model(self):
        brain = self._brain()
        brain.start()
        try:
            self.assertIsNotNone(brain.spatial)
            self.assertGreater(len(brain.spatial._regions), 0)
            # Place the robot in the model and resolve its region.
            brain.spatial.place("robot_001", SpatialReference(
                frame_id="map", pose={"x": 5.0, "y": 2.0},
            ))
            self.assertEqual(brain.spatial.region_of("robot_001"), "living_room")
        finally:
            brain.stop()

    def test_spatial_state_exposed_to_cognition(self):
        brain = self._brain()
        brain.start()
        try:
            state = brain.spatial.to_spatial_state()
            self.assertIn("frames", state)
            self.assertIn("occupancy", state)
        finally:
            brain.stop()


if __name__ == "__main__":
    unittest.main()
