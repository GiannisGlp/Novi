"""Tests for LeRobot dataset export + GR00T embodiment config template."""

import json
import tempfile
import unittest
from pathlib import Path

from novi.brain.lerobot_export import (
    build_gr00t_embodiment_config,
    export_lerobot_dataset,
    validate_lerobot_export,
    write_gr00t_embodiment_config,
)
from novi.brain.nvidia_experiments import build_navigate_episode, build_pick_cup_episode


class LeRobotExportTests(unittest.TestCase):
    def test_export_layout_and_metadata(self):
        episodes = [build_navigate_episode(simulated=False), build_pick_cup_episode(simulated=True)]
        with tempfile.TemporaryDirectory() as tmp:
            manifest = export_lerobot_dataset(episodes, tmp, robot_type="novi_mac_brain")
            self.assertEqual(manifest.episode_count, 2)
            self.assertEqual(manifest.frame_count, 5)  # 3 + 2 steps
            out = Path(tmp)
            info = json.loads((out / "meta" / "info.json").read_text(encoding="utf-8"))
            self.assertEqual(info["total_episodes"], 2)
            self.assertEqual(info["total_frames"], 5)
            self.assertTrue(info["novi"]["evidence_classes_preserved"])
            self.assertTrue((out / "data" / "README.md").exists())

    def test_episode_meta_files(self):
        episodes = [build_navigate_episode(simulated=False), build_pick_cup_episode(simulated=False)]
        with tempfile.TemporaryDirectory() as tmp:
            export_lerobot_dataset(episodes, tmp)
            meta_files = sorted((Path(tmp) / "meta" / "episodes").glob("*.json"))
            self.assertEqual(len(meta_files), 2)
            meta0 = json.loads(meta_files[0].read_text(encoding="utf-8"))
            self.assertEqual(meta0["episode_index"], 0)
            self.assertEqual(meta0["length"], 3)
            self.assertEqual(meta0["tasks"], ["navigate_to_kitchen"])

    def test_validation_passes_for_valid_export(self):
        episodes = [build_navigate_episode(simulated=False), build_pick_cup_episode(simulated=True)]
        with tempfile.TemporaryDirectory() as tmp:
            export_lerobot_dataset(episodes, tmp)
            report = validate_lerobot_export(tmp)
            self.assertTrue(report["valid"], msg=report["issues"])
            self.assertEqual(report["episode_count"], 2)
            self.assertEqual(report["frame_count"], 5)

    def test_validation_detects_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            export_lerobot_dataset([build_navigate_episode()], tmp)
            (Path(tmp) / "data" / "chunk-0000" / "00000.json").unlink()
            report = validate_lerobot_export(tmp)
            self.assertFalse(report["valid"])
            self.assertTrue(any("missing" in issue for issue in report["issues"]))

    def test_validation_detects_missing_info(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = validate_lerobot_export(tmp)
            self.assertFalse(report["valid"])
            self.assertTrue(any("info.json missing" in issue for issue in report["issues"]))

    def test_validation_detects_missing_frame_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            export_lerobot_dataset([build_navigate_episode()], tmp)
            data_file = Path(tmp) / "data" / "chunk-0000" / "00000.json"
            payload = json.loads(data_file.read_text(encoding="utf-8"))
            del payload["frames"][0]["action"]
            data_file.write_text(json.dumps(payload), encoding="utf-8")
            report = validate_lerobot_export(tmp)
            self.assertFalse(report["valid"])
            self.assertTrue(any("missing field action" in issue for issue in report["issues"]))

    def test_validation_detects_length_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            export_lerobot_dataset([build_navigate_episode()], tmp)
            meta_file = Path(tmp) / "meta" / "episodes" / "00000.json"
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
            meta["length"] = 99
            meta_file.write_text(json.dumps(meta), encoding="utf-8")
            report = validate_lerobot_export(tmp)
            self.assertFalse(report["valid"])
            self.assertTrue(any("frames 3 != length 99" in issue for issue in report["issues"]))

    def test_validation_detects_frame_count_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            export_lerobot_dataset([build_navigate_episode()], tmp)
            info_file = Path(tmp) / "meta" / "info.json"
            info = json.loads(info_file.read_text(encoding="utf-8"))
            info["total_frames"] = 7
            info_file.write_text(json.dumps(info), encoding="utf-8")
            report = validate_lerobot_export(tmp)
            self.assertFalse(report["valid"])
            self.assertTrue(any("counted frames 3 != total_frames 7" in issue for issue in report["issues"]))

    def test_exported_frames_preserve_evidence_and_provenance(self):
        episode = build_navigate_episode(simulated=False)
        with tempfile.TemporaryDirectory() as tmp:
            export_lerobot_dataset([episode], tmp)
            data_file = Path(tmp) / "data" / "chunk-0000" / "00000.json"
            payload = json.loads(data_file.read_text(encoding="utf-8"))
            first = payload["frames"][0]
            self.assertEqual(first["_novi_evidence_class"], episode.evidence_class)
            self.assertIn("source", first["_novi_provenance"])
            self.assertIn("_novi_provenance", payload["frames"][-1])


class Gr00tEmbodimentConfigTests(unittest.TestCase):
    def test_config_has_robot_sensors_and_action_space(self):
        config = build_gr00t_embodiment_config()
        self.assertEqual(config["robot"]["name"], "novi")
        modalities = {s["modality"] for s in config["sensors"]}
        self.assertEqual(modalities, {"rgb", "depth", "proprioception"})
        self.assertIn("navigate", config["action_space"])
        self.assertIn("pick", config["action_space"])
        self.assertIn("speak", config["action_space"])
        self.assertEqual(config["action_space"]["navigate"]["risk_class"], "R3")

    def test_config_customizable(self):
        config = build_gr00t_embodiment_config(
            robot_name="novi-2",
            control_frequency_hz=20,
            sensors=[{"modality": "rgb", "rate_hz": 20}],
        )
        self.assertEqual(config["robot"]["name"], "novi-2")
        self.assertEqual(config["control_frequency_hz"], 20)
        self.assertEqual(len(config["sensors"]), 1)

    def test_write_config_roundtrip(self):
        config = build_gr00t_embodiment_config()
        with tempfile.TemporaryDirectory() as tmp:
            path = write_gr00t_embodiment_config(config, tmp)
            self.assertTrue(Path(path).exists())
            loaded = json.loads(Path(path).read_text(encoding="utf-8"))
            self.assertEqual(loaded["robot"]["name"], "novi")
            self.assertEqual(loaded["config_version"], "1.0.0")


if __name__ == "__main__":
    unittest.main()
