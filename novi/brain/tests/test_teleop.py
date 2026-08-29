"""Tests for TeleOp Phase 1 (keyboard demonstration over the simulated embodiment)."""

import unittest

from novi.brain.nvidia_experiments import OBSERVED
from novi.brain.teleop import (
    BACKWARD,
    END,
    FORWARD,
    INTERACT,
    KEY_MAP,
    RESET,
    SPEAK,
    TURN_LEFT,
    TURN_RIGHT,
    TeleOpSession,
)
from novi.brain.virtual_skills import SimBody, SimWorld


def make_session() -> TeleOpSession:
    body = SimBody(x_m=0.0, y_m=0.0, heading_deg=0.0, localized=True)
    world = SimWorld(object_locations={"cup_001": (0.0, 0.3), "phone_001": (4.0, -1.0)})
    return TeleOpSession(body, world)


class TeleOpCommandTests(unittest.TestCase):
    def test_key_map_covers_primary_keys(self):
        for key in ("w", "s", "a", "d", "f", "t", "r", "q"):
            self.assertIn(key, KEY_MAP)

    def test_forward_moves_along_heading(self):
        session = make_session()
        result = session.step(FORWARD)
        self.assertEqual(session.body.x_m, 0.5)
        self.assertAlmostEqual(session.body.y_m, 0.0, places=6)
        self.assertEqual(result.outcome_status, "RUNNING")

    def test_turn_changes_heading(self):
        session = make_session()
        session.step(TURN_RIGHT)
        self.assertAlmostEqual(session.body.heading_deg, 15.0, places=6)
        session.step(TURN_LEFT)
        self.assertAlmostEqual(session.body.heading_deg, 0.0, places=6)

    def test_backward_reverses(self):
        session = make_session()
        session.step(BACKWARD)
        self.assertAlmostEqual(session.body.x_m, -0.5, places=6)

    def test_reset_returns_to_origin(self):
        session = make_session()
        session.step(FORWARD)
        session.step(TURN_RIGHT)
        session.step(RESET)
        self.assertEqual(session.body.pose(), {"x_m": 0.0, "y_m": 0.0, "heading_deg": 0.0})

    def test_unknown_command_rejected(self):
        session = make_session()
        with self.assertRaises(ValueError):
            session.step("fly")  # type: ignore[arg-type]


class TeleOpInteractionTests(unittest.TestCase):
    def test_grasp_reachable_object(self):
        session = make_session()
        result = session.step(INTERACT)  # cup_001 is 0.3 m away (< 0.6 reach)
        self.assertEqual(result.outcome_status, "SUCCESS")
        self.assertEqual(result.object_grasped, "cup_001")
        self.assertEqual(session.held_object, "cup_001")

    def test_grasp_out_of_reach_fails(self):
        body = SimBody(x_m=0.0, y_m=0.0)
        world = SimWorld(object_locations={"phone_001": (4.0, -1.0)})
        session = TeleOpSession(body, world)
        result = session.step(INTERACT)
        self.assertEqual(result.outcome_status, "FAILURE")
        self.assertIsNone(session.held_object)

    def test_release_held_object(self):
        session = make_session()
        session.step(INTERACT)  # grasp
        result = session.step(INTERACT)  # release
        self.assertEqual(result.outcome_status, "SUCCESS")
        self.assertIn("released", result.outcome_detail)
        self.assertIsNone(session.held_object)
        self.assertIn("cup_001", session.world.object_locations)

    def test_visible_objects_report_spatial_relations(self):
        session = make_session()
        visible = session.visible_objects()
        ids = [o["object_id"] for o in visible]
        self.assertIn("cup_001", ids)  # 0.3 m away
        self.assertNotIn("phone_001", ids)  # > 3 m visibility radius
        cup = next(o for o in visible if o["object_id"] == "cup_001")
        self.assertAlmostEqual(cup["distance_m"], 0.3, places=3)
        self.assertTrue(cup["in_reach"])

    def test_speak_records_text(self):
        session = make_session()
        result = session.step(SPEAK, text="hello novi")
        self.assertEqual(result.outcome_status, "SUCCESS")
        self.assertEqual(result.outcome_detail["spoken"], "hello novi")


class TeleOpEpisodeTests(unittest.TestCase):
    def test_episode_records_every_command(self):
        session = make_session()
        session.step(FORWARD)
        session.step(TURN_RIGHT)
        session.step(SPEAK, text="hi")
        session.step(END)
        episode = session.build_episode()
        self.assertEqual(len(episode.steps), 4)
        self.assertEqual(episode.evidence_class, OBSERVED)
        self.assertIn("teleop_phase", episode.provenance)
        self.assertEqual(episode.provenance["teleop_phase"], "1_keyboard")
        self.assertEqual(episode.metadata["task_type"], "teleop_demonstration")

    def test_episode_steps_have_observation_action_outcome(self):
        session = make_session()
        session.step(FORWARD)
        session.step(INTERACT)
        episode = session.build_episode()
        first = episode.steps[0]
        self.assertIn("pose", first.observation)
        self.assertEqual(first.action["skill"], "teleop")
        self.assertEqual(first.action["command"], FORWARD)
        self.assertIn("status", first.outcome)
        self.assertEqual(first.evidence_class, OBSERVED)
        self.assertIn("source", first.provenance)

    def test_reset_clears_session(self):
        session = make_session()
        session.step(FORWARD)
        session.reset()
        self.assertEqual(session.step_count, 0)
        self.assertEqual(session.body.pose(), {"x_m": 0.0, "y_m": 0.0, "heading_deg": 0.0})
        self.assertIsNone(session.held_object)

    def test_provenance_preserves_command_order(self):
        session = make_session()
        session.step(FORWARD)
        session.step(TURN_RIGHT)
        session.step(BACKWARD)
        session.step(INTERACT)
        episode = session.build_episode()
        self.assertEqual(episode.provenance["commands"], [FORWARD, TURN_RIGHT, BACKWARD, INTERACT])


if __name__ == "__main__":
    unittest.main()
