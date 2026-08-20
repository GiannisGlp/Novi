import unittest

from brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
from brain.runtime import Lifecycle

from MAC_BRAIN.io import CameraFrame, VirtualBody
from MAC_BRAIN.runtime import MacBrain, MacBrainConfig


class FakeCamera:
    def __init__(self) -> None:
        self.sequence = 0
        self.closed = False

    def read(self) -> CameraFrame:
        self.sequence += 1
        return CameraFrame(
            frame_id=f"fake-{self.sequence}",
            captured_at="2026-08-19T14:00:00Z",
            width=2,
            height=2,
            payload=b"frame",
            metadata={"backend": "test"},
        )

    def close(self) -> None:
        self.closed = True


class PersonBackend(DeterministicPerceptionBackend):
    def detect(self, frame):
        return (Detection("person", 0.95, (0.0, 0.0, 1.0, 1.0)),)


class MacBrainTests(unittest.TestCase):
    def test_MAC_BRAIN_composes_existing_brain_runtime(self) -> None:
        camera = FakeCamera()
        # curiosity disabled: exercise the pure reactive conclusion->action path
        brain = MacBrain(camera=camera, perception=SpecialistPerception(PersonBackend()), config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        result = brain.step()
        brain.stop()
        self.assertEqual(result["cycle"], 1)
        self.assertEqual(result["detections"], ["person"])
        self.assertEqual(result["action"], "wait")
        self.assertTrue(result["authorized"])
        self.assertEqual(brain.brain.lifecycle, Lifecycle.SHUTTING_DOWN)
        self.assertTrue(camera.closed)

    def test_MAC_BRAIN_emits_observable_events(self) -> None:
        brain = MacBrain(camera=FakeCamera())
        brain.start()
        brain.step()
        brain.stop()
        event_types = [event["event_type"] for event in brain.events]
        self.assertIn("MAC_BRAIN.started", event_types)
        self.assertIn("sensor.camera.frame", event_types)
        self.assertIn("perception.completed", event_types)
        self.assertIn("cognition.completed", event_types)
        self.assertIn("reasoning.completed", event_types)
        self.assertIn("action.completed", event_types)
        self.assertIn("MAC_BRAIN.stopped", event_types)

    def test_virtual_body_rejects_unknown_actions(self) -> None:
        body = VirtualBody()
        with self.assertRaises(ValueError):
            body.execute("run_shell_command")

    def test_virtual_body_is_deterministic(self) -> None:
        body = VirtualBody()
        first = body.execute("turn_left", degrees=30)
        second = body.execute("move_forward", distance_m=1.0)
        self.assertEqual(first["heading_deg"], 30.0)
        self.assertAlmostEqual(second["x_m"], 0.8660254, places=5)
        self.assertAlmostEqual(second["y_m"], 0.5, places=5)

    def test_camera_is_required_for_live_step(self) -> None:
        brain = MacBrain()
        brain.start()
        with self.assertRaises(RuntimeError):
            brain.step()
        brain.stop()


if __name__ == "__main__":
    unittest.main()
