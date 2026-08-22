"""Tests for NoviEpisode dataset recording from the Mac Brain runtime."""

import unittest

from brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
from MAC_BRAIN.nvidia_experiments import (
    OBSERVED,
    SIMULATED,
    EpisodeRecorder,
    LeRobotAdapter,
    NoviEpisode,
    NoviNativeAdapter,
)
from MAC_BRAIN.runtime import MacBrain, MacBrainConfig
from MAC_BRAIN.tests.test_mac_brain import FakeCamera


class CupBackend(DeterministicPerceptionBackend):
    def detect(self, frame):
        return (Detection("cup", 0.85, (0.1, 0.1, 0.5, 0.5)),)


class EpisodeRecorderTests(unittest.TestCase):
    def test_record_step(self):
        recorder = EpisodeRecorder(task_name="test_task")
        step = recorder.record_step(
            observation={"entities": ["cup"]},
            action={"skill": "pick", "parameters": {"object_id": "cup"}},
            outcome={"status": "SUCCESS"},
        )
        self.assertEqual(recorder.step_count, 1)
        self.assertEqual(step.step_index, 0)
        self.assertEqual(step.evidence_class, OBSERVED)

    def test_build_episode(self):
        recorder = EpisodeRecorder(task_name="pick_cup", description="Pick up the cup")
        recorder.record_step(
            observation={"entities": ["cup"]},
            action={"skill": "pick"},
            outcome={"status": "SUCCESS"},
        )
        recorder.record_step(
            observation={"entities": ["cup", "table"]},
            action={"skill": "place"},
            outcome={"status": "SUCCESS"},
        )
        episode = recorder.build_episode()
        self.assertIsInstance(episode, NoviEpisode)
        self.assertEqual(episode.task_name, "pick_cup")
        self.assertEqual(len(episode.steps), 2)
        self.assertEqual(episode.evidence_class, OBSERVED)

    def test_reset(self):
        recorder = EpisodeRecorder(task_name="test")
        recorder.record_step(observation={}, action={}, outcome={})
        self.assertEqual(recorder.step_count, 1)
        recorder.reset()
        self.assertEqual(recorder.step_count, 0)

    def test_episode_has_provenance(self):
        recorder = EpisodeRecorder(task_name="test", source="mac_brain")
        recorder.record_step(observation={}, action={}, outcome={})
        episode = recorder.build_episode()
        self.assertIn("source", episode.provenance)
        self.assertEqual(episode.provenance["source"], "mac_brain")

    def test_simulated_evidence_class(self):
        recorder = EpisodeRecorder(task_name="sim_test", evidence_class=SIMULATED, source="isaac_sim")
        recorder.record_step(observation={}, action={}, outcome={})
        episode = recorder.build_episode()
        self.assertEqual(episode.evidence_class, SIMULATED)

    def test_record_runtime_step(self):
        """Record an episode from a real MacBrain step."""
        brain = MacBrain(
            camera=FakeCamera(),
            perception=SpecialistPerception(CupBackend()),
            config=MacBrainConfig(curiosity_enabled=False),
        )
        brain.start()
        brain.step()
        recorder = EpisodeRecorder(task_name="observe_cup")
        recorder.record_runtime_step(brain, cycle=1)
        brain.step()
        recorder.record_runtime_step(brain, cycle=2)
        brain.stop()
        self.assertEqual(recorder.step_count, 2)
        episode = recorder.build_episode()
        self.assertEqual(len(episode.steps), 2)
        # Each step has observation, action, and outcome data from the runtime.
        for step in episode.steps:
            self.assertIn("cycle", step.observation)
            self.assertIn("action", step.action)
            self.assertIn("loop_outcome", step.outcome)

    def test_recorded_episode_exports_through_adapters(self):
        """A recorded episode round-trips through all adapters."""
        brain = MacBrain(
            camera=FakeCamera(),
            perception=SpecialistPerception(CupBackend()),
            config=MacBrainConfig(curiosity_enabled=False),
        )
        brain.start()
        brain.step()
        recorder = EpisodeRecorder(task_name="observe_cup")
        recorder.record_runtime_step(brain, cycle=1)
        brain.stop()
        episode = recorder.build_episode()
        for adapter_name, adapter in [("novi_native", NoviNativeAdapter()), ("lerobot", LeRobotAdapter())]:
            formatted = adapter.to_format(episode)
            restored = adapter.from_format(formatted)
            self.assertEqual(len(restored.steps), len(episode.steps))
            self.assertEqual(restored.evidence_class, episode.evidence_class)

    def test_multi_step_episode_from_runtime(self):
        """Record a multi-step episode from several runtime steps."""
        brain = MacBrain(
            camera=FakeCamera(),
            perception=SpecialistPerception(CupBackend()),
            config=MacBrainConfig(curiosity_enabled=False),
        )
        brain.start()
        recorder = EpisodeRecorder(task_name="multi_step_observation", description="Multi-step cup observation")
        for i in range(5):
            brain.step()
            recorder.record_runtime_step(brain, cycle=i + 1)
        brain.stop()
        episode = recorder.build_episode()
        self.assertEqual(len(episode.steps), 5)
        self.assertEqual(episode.description, "Multi-step cup observation")
        # Verify the episode can be serialized.
        snap = episode.snapshot()
        self.assertEqual(snap["step_count"], 5)
        # Verify all steps have runtime data.
        for step in episode.steps:
            self.assertIn("detection_count", step.observation)
            self.assertIn("governance_decision", step.action)
            self.assertIn("loop_outcome", step.outcome)


if __name__ == "__main__":
    unittest.main()
