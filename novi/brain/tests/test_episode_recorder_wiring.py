"""Tests for EpisodeRecorder wiring into the runtime.

Verifies:
  - start_recording / stop_recording / is_recording / recording_step_count.
  - Steps are automatically recorded when recording is enabled.
  - build_episode produces a NoviEpisode with correct data.
  - export_episode works through all adapters.
  - The episode.recording_started / recording_stopped events are emitted.
  - Recording can be stopped and the episode exported in one call.
"""

import unittest

from novi.brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
from novi.brain.nvidia_experiments import OBSERVED, NoviEpisode
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.tests.test_mac_brain import FakeCamera


class CupBackend(DeterministicPerceptionBackend):
    def detect(self, frame):
        return (Detection("cup", 0.85, (0.1, 0.1, 0.5, 0.5)),)


class EpisodeRecorderWiringTests(unittest.TestCase):
    def _brain(self):
        brain = MacBrain(
            camera=FakeCamera(),
            perception=SpecialistPerception(CupBackend()),
            config=MacBrainConfig(curiosity_enabled=False),
        )
        brain.start()
        return brain

    def test_not_recording_by_default(self):
        brain = self._brain()
        try:
            self.assertFalse(brain.is_recording)
            self.assertEqual(brain.recording_step_count, 0)
        finally:
            brain.stop()

    def test_start_recording(self):
        brain = self._brain()
        try:
            brain.start_recording(task_name="test_task", description="testing")
            self.assertTrue(brain.is_recording)
        finally:
            brain.stop()

    def test_steps_recorded_automatically(self):
        """Steps are automatically recorded when recording is enabled."""
        brain = self._brain()
        try:
            brain.start_recording(task_name="auto_record")
            brain.step()
            brain.step()
            brain.step()
            self.assertEqual(brain.recording_step_count, 3)
        finally:
            brain.stop()

    def test_stop_recording_returns_episode(self):
        """stop_recording returns a NoviEpisode with recorded steps."""
        brain = self._brain()
        try:
            brain.start_recording(task_name="test_episode")
            brain.step()
            brain.step()
            episode = brain.stop_recording()
            self.assertIsInstance(episode, NoviEpisode)
            self.assertEqual(len(episode.steps), 2)
            self.assertEqual(episode.task_name, "test_episode")
        finally:
            brain.stop()

    def test_recording_stopped_after_stop(self):
        """is_recording is False after stop_recording."""
        brain = self._brain()
        try:
            brain.start_recording()
            brain.step()
            brain.stop_recording()
            self.assertFalse(brain.is_recording)
            self.assertEqual(brain.recording_step_count, 0)
        finally:
            brain.stop()

    def test_recording_started_event_emitted(self):
        brain = self._brain()
        try:
            brain.start_recording(task_name="event_test")
            events = [e for e in brain.events if e["event_type"] == "episode.recording_started"]
            self.assertGreater(len(events), 0)
            self.assertEqual(events[-1]["payload"]["task_name"], "event_test")
        finally:
            brain.stop()

    def test_recording_stopped_event_emitted(self):
        brain = self._brain()
        try:
            brain.start_recording(task_name="stop_test")
            brain.step()
            episode = brain.stop_recording()
            events = [e for e in brain.events if e["event_type"] == "episode.recording_stopped"]
            self.assertGreater(len(events), 0)
            self.assertEqual(events[-1]["payload"]["step_count"], 1)
        finally:
            brain.stop()

    def test_export_episode_novi_native(self):
        brain = self._brain()
        try:
            brain.start_recording(task_name="export_test")
            brain.step()
            episode = brain.stop_recording()
            exported = brain.export_episode(episode, format="novi_native")
            self.assertIn("episode_id", exported)
            self.assertIn("steps", exported)
            self.assertEqual(len(exported["steps"]), 1)
        finally:
            brain.stop()

    def test_export_episode_lerobot(self):
        brain = self._brain()
        try:
            brain.start_recording(task_name="lerobot_test")
            brain.step()
            brain.step()
            episode = brain.stop_recording()
            exported = brain.export_episode(episode, format="lerobot")
            self.assertIn("frames", exported)
            self.assertEqual(len(exported["frames"]), 2)
        finally:
            brain.stop()

    def test_export_episode_all_formats(self):
        """Episode can be exported through all 4 adapter formats."""
        brain = self._brain()
        try:
            brain.start_recording(task_name="multi_format")
            brain.step()
            episode = brain.stop_recording()
            for fmt in ("novi_native", "lerobot", "isaac_lab", "rosbag"):
                exported = brain.export_episode(episode, format=fmt)
                self.assertIsInstance(exported, dict)
        finally:
            brain.stop()

    def test_export_unknown_format_raises(self):
        brain = self._brain()
        try:
            brain.start_recording()
            brain.step()
            episode = brain.stop_recording()
            with self.assertRaises(ValueError):
                brain.export_episode(episode, format="unknown_format")
        finally:
            brain.stop()

    def test_recorded_steps_have_runtime_data(self):
        """Recorded steps contain detection, governance, and loop verify data."""
        brain = self._brain()
        try:
            brain.start_recording(task_name="data_check")
            brain.step()
            episode = brain.stop_recording()
            step = episode.steps[0]
            self.assertIn("detection_count", step.observation)
            self.assertIn("world_entities", step.observation)
            self.assertIn("action", step.action)
            self.assertIn("governance_decision", step.action)
            self.assertIn("loop_outcome", step.outcome)
            self.assertEqual(step.evidence_class, OBSERVED)
        finally:
            brain.stop()

    def test_stop_recording_when_not_recording_returns_none(self):
        """stop_recording returns None when not recording."""
        brain = self._brain()
        try:
            result = brain.stop_recording()
            self.assertIsNone(result)
        finally:
            brain.stop()

    def test_multi_step_episode(self):
        """A multi-step episode records all steps correctly."""
        brain = self._brain()
        try:
            brain.start_recording(task_name="multi_step", description="5-step test")
            for _ in range(5):
                brain.step()
            episode = brain.stop_recording()
            self.assertEqual(len(episode.steps), 5)
            self.assertEqual(episode.description, "5-step test")
            # Verify step indices are sequential.
            for i, step in enumerate(episode.steps):
                self.assertEqual(step.step_index, i)
        finally:
            brain.stop()

    def test_recording_does_not_break_normal_step(self):
        """Recording doesn't interfere with normal step execution."""
        brain = self._brain()
        try:
            brain.start_recording()
            result = brain.step()
            self.assertIn("cycle", result)
            self.assertIn("detections", result)
            brain.stop_recording()
        finally:
            brain.stop()


if __name__ == "__main__":
    unittest.main()
