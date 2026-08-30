"""Tests for training configs + pipeline smoke runs (plan 23 §31, steps 10-15)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from training.config import TrainConfig, capture_provenance, load_config

CONFIGS = Path(__file__).resolve().parents[1] / "configs"
DATASETS = Path(__file__).resolve().parents[1] / "datasets"


class TestConfigLoading:
    @pytest.mark.parametrize("name", ["sft", "dpo", "retrieval", "grounding", "evaluation"])
    def test_committed_configs_load(self, name: str):
        cfg = load_config(CONFIGS / f"{name}.yaml")
        assert isinstance(cfg, TrainConfig)
        assert cfg.kind == name

    def test_sft_config_values(self):
        cfg = load_config(CONFIGS / "sft.yaml")
        assert cfg.base_model == "qwen3:8b"
        assert cfg.seed == 20260830
        assert cfg.hyperparams["lora_r"] == 16

    def test_config_rejects_unknown_kind(self, tmp_path: Path):
        f = tmp_path / "bad.yaml"
        f.write_text("kind: telepathy\nbase_model: x\ndataset: d\n")
        with pytest.raises(ValueError):
            load_config(f)

    def test_config_requires_seed(self, tmp_path: Path):
        f = tmp_path / "noseed.yaml"
        f.write_text("kind: sft\nbase_model: x\ndataset: d\n")
        with pytest.raises(ValueError):
            load_config(f)

    def test_evaluation_config_defines_gates(self):
        cfg = load_config(CONFIGS / "evaluation.yaml")
        gates = cfg.hyperparams.get("gates", {})
        assert gates["safety"] == pytest.approx(0.995)
        assert set(gates) >= {"naturalness", "grounding", "memory", "initiative", "silence", "safety", "latency", "regression"}


class TestProvenance:
    def test_provenance_records_expected_fields(self):
        prov = capture_provenance(base_model="qwen3:8b", dataset_version="v1")
        for key in ("base_model", "training_commit", "dataset_version", "random_seed",
                    "hardware", "framework", "captured_at"):
            assert key in prov, key

    def test_provenance_commit_matches_git(self):
        import subprocess

        git_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=Path(__file__).resolve().parents[2]
        ).stdout.strip()
        prov = capture_provenance(base_model="qwen3:8b", dataset_version="v1")
        assert prov["training_commit"] == git_sha


class TestSftSmoke:
    def _run(self, extra: list[str] | None = None) -> dict:
        import subprocess
        import sys

        script = Path(__file__).resolve().parents[1] / "training" / "train_sft.py"
        cmd = [sys.executable, str(script), "--config", str(CONFIGS / "sft.yaml"), "--dry-run", "--out-json", "-"]
        if extra:
            cmd += extra
        out = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).resolve().parents[2])
        assert out.returncode == 0, out.stderr
        return json.loads(out.stdout.strip().splitlines()[-1])

    def test_smoke_run_reports_dry_run(self):
        report = self._run()
        assert report["dry_run"] is True
        assert report["examples_loaded"] >= 40
        assert report["config"]["kind"] == "sft"
        assert report["framework"] in ("dry-run", "mlx", "torch-peft", "transformers-only", "none")

    def test_smoke_run_is_deterministic(self):
        assert self._run() == self._run()

    def test_smoke_run_covers_all_tasks(self):
        report = self._run()
        tasks = report["task_counts"]
        assert len(tasks) >= 8


class TestEvaluateSmoke:
    def _run(self) -> dict:
        import subprocess
        import sys

        script = Path(__file__).resolve().parents[1] / "training" / "evaluate.py"
        out = subprocess.run(
            [sys.executable, str(script), "--config", str(CONFIGS / "evaluation.yaml"), "--out-json", "-"],
            capture_output=True, text=True, cwd=Path(__file__).resolve().parents[2],
        )
        assert out.returncode == 0, out.stderr
        return json.loads(out.stdout.strip().splitlines()[-1])

    def test_evaluate_runs_30_scenarios(self):
        report = self._run()
        assert report["scenarios_run"] == 30
        assert "metrics" in report
        assert "safety" in report["metrics"]

    def test_baseline_passes_safety_gate(self):
        report = self._run()
        assert report["gates"]["safety"]["passed"] is True


class TestScenarioPrompt:
    def test_prompt_includes_situation_and_act(self):
        from training.evaluation.scenarios import ALL_SCENARIOS  # noqa: PLC0415
        from training.training.evaluate import _scenario_prompt  # noqa: PLC0415

        prompt = _scenario_prompt(ALL_SCENARIOS[0], "GREETING")
        assert "person:owner_001" in prompt
        assert "Communicative act: GREETING" in prompt

    def test_prompt_deterministic(self):
        from training.evaluation.scenarios import ALL_SCENARIOS  # noqa: PLC0415
        from training.training.evaluate import _scenario_prompt  # noqa: PLC0415

        a = _scenario_prompt(ALL_SCENARIOS[1], "RESPOND")
        b = _scenario_prompt(ALL_SCENARIOS[1], "RESPOND")
        assert a == b
