"""Phase 1c (north-star gap analysis): world model ↔ spatial map link +
robot self-state.

docs/audits/NOVI_NORTH_STAR_GAP_ANALYSIS_2026-08-29.md §4 Phase 1c:
"Give WorldEntity a spatial_ref; maintain a ROBOT entity; resolve
visible_entities by region via SpatialMap.region_at."

Acceptance:
- robot pose at (x, y) resolves to "kitchen" via region_at (wired into the
  engine's world model as the robot self-entity);
- pose_in(frame) converts a pose through parent transforms.
"""

from __future__ import annotations

import math
import unittest

from novi.brain.spatial_map import Pose2D, SpatialFrame, SpatialMap, default_home_map
from novi.brain.world_model import ROBOT


class PoseInTests(unittest.TestCase):
    def test_region_at_resolves_kitchen(self):
        m = default_home_map()
        self.assertEqual(m.region_at(1.0, 1.0), "kitchen")
        self.assertEqual(m.region_at(6.0, 2.0), "living_room")
        self.assertIsNone(m.region_at(100.0, 100.0))

    def test_pose_in_converts_through_parent_transform(self):
        m = SpatialMap()
        m.register_frame(SpatialFrame(name="map"))
        m.register_frame(SpatialFrame(
            name="base", parent="map",
            origin=Pose2D(x_m=1.0, y_m=0.5, heading_rad=math.pi / 2),
        ))
        pose = Pose2D(x_m=0.0, y_m=0.0, heading_rad=0.0)
        converted = m.pose_in(pose, from_frame="base", to_frame="map")
        self.assertIsNotNone(converted)
        self.assertAlmostEqual(converted.x_m, 1.0, places=6)
        self.assertAlmostEqual(converted.y_m, 0.5, places=6)
        self.assertAlmostEqual(converted.heading_rad, math.pi / 2, places=6)

    def test_pose_in_composes_two_levels(self):
        m = SpatialMap()
        m.register_frame(SpatialFrame(name="root"))
        m.register_frame(SpatialFrame(name="mid", parent="root",
                                      origin=Pose2D(x_m=2.0, y_m=0.0, heading_rad=0.0)))
        m.register_frame(SpatialFrame(name="leaf", parent="mid",
                                      origin=Pose2D(x_m=0.0, y_m=1.0, heading_rad=0.0)))
        converted = m.pose_in(Pose2D(x_m=0.5, y_m=0.0), from_frame="leaf", to_frame="root")
        self.assertIsNotNone(converted)
        self.assertAlmostEqual(converted.x_m, 2.5, places=6)
        self.assertAlmostEqual(converted.y_m, 1.0, places=6)

    def test_pose_in_fails_closed_for_unknown_frame(self):
        m = default_home_map()
        self.assertIsNone(m.pose_in(Pose2D(), from_frame="nope", to_frame="map"))
        # Disconnected frames (no common ancestor) also fail closed.
        m.register_frame(SpatialFrame(name="island"))
        self.assertIsNone(m.pose_in(Pose2D(), from_frame="island", to_frame="map"))


class RobotWorldStateTests(unittest.TestCase):
    def _brain(self):
        from novi.brain.b2_perception import SpecialistPerception
        from novi.brain.engine import MacBrain, MacBrainConfig
        from novi.brain.io import CameraFrame

        class Camera:
            def __init__(self) -> None:
                self.seq = 0

            def close(self) -> None:
                self.seq = self.seq

            def read(self) -> CameraFrame:
                self.seq += 1
                return CameraFrame(frame_id=f"f-{self.seq}", captured_at="2026-08-29T12:00:00Z",
                                   width=2, height=2, payload=b"x", metadata={})

        return MacBrain(
            camera=Camera(),
            perception=SpecialistPerception(),
            config=MacBrainConfig(curiosity_enabled=False),
        )

    def test_robot_entity_exists_with_region_from_pose(self):
        brain = self._brain()
        brain.start()
        try:
            brain.body.x_m = 1.0
            brain.body.y_m = 1.0  # inside the default kitchen bounds
            brain.step()
            robot = brain.unified_world.resolve("robot")
            self.assertIsNotNone(robot, "the brain must maintain a ROBOT world-model entity")
            self.assertEqual(robot.entity_type, ROBOT)
            self.assertEqual(robot.state_value("location"), "kitchen")
            # The spatial ref carries the live metric pose for reachability
            # and visibility queries (world model ↔ SpatialMap link).
            ref = robot.spatial_ref
            self.assertIsNotNone(ref)
            self.assertEqual(ref["frame"], "map")
            self.assertAlmostEqual(ref["x"], 1.0)
            self.assertAlmostEqual(ref["y"], 1.0)
            # Region is also resolvable through the spatial map itself.
            self.assertEqual(brain.spatial.region_at(brain.body.x_m, brain.body.y_m), "kitchen")
        finally:
            brain.stop()

    def test_robot_region_updates_after_move(self):
        brain = self._brain()
        brain.start()
        try:
            brain.body.x_m = 1.0
            brain.body.y_m = 1.0
            brain.step()
            self.assertEqual(brain.unified_world.resolve("robot").state_value("location"), "kitchen")
            brain.body.x_m = 5.0  # living_room (4..8, 0..4)
            brain.step()
            self.assertEqual(brain.unified_world.resolve("robot").state_value("location"), "living_room")
        finally:
            brain.stop()

    def test_robot_pose_is_observed_with_low_sigma(self):
        brain = self._brain()
        brain.start()
        try:
            brain.step()
            robot = brain.unified_world.resolve("robot")
            # Local odometry is certain in the virtual phase: σ = 0.
            self.assertEqual(robot.state_status("pose_2d"), "OBSERVED")
            self.assertAlmostEqual(robot.state_sigma("pose_2d"), 0.0)
        finally:
            brain.stop()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
