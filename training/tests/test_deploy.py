"""Tests for the deployment workflow (plan 23 steps 12/24-26, §18 loop)."""

from __future__ import annotations

from pathlib import Path

import pytest

from training.models.deploy import (
    DeploymentReport,
    plan_deployment,
    run_deployment,
)


def _eval_report(passed: bool = True) -> dict:
    gates = {
        "naturalness": {"passed": True, "value": {}},
        "grounding": {"passed": True, "value": {}},
        "memory": {"passed": True, "value": {}},
        "initiative": {"passed": True, "value": {}},
        "silence": {"passed": passed, "value": {}},
        "safety": {"passed": passed, "value": {"safety_score": 1.0 if passed else 0.9}},
        "latency": {"passed": None, "value": {"note": "measured on-device"}},
        "regression": {"passed": None, "value": {"note": "external"}},
    }
    return {
        "subject": "candidate:test",
        "metrics": {"safety": {"unsupported_claim_rate": 0.0 if passed else 0.1}},
        "gates": gates,
    }


class TestPlanDeployment:
    def test_all_gates_pass_plans_promotion(self, tmp_path):
        plan = plan_deployment(_eval_report(True), adapter_dir="training/models/adapters/novi-qwen3-8b-dialogue-v1")
        assert plan["deploy"] is True
        assert plan["gates_passed"] == ["naturalness", "grounding", "memory", "initiative", "silence", "safety"]
        assert plan["steps"] == ["register_candidate", "stage", "shadow_compare", "promote_active"]

    def test_safety_gate_failure_blocks(self, tmp_path):
        plan = plan_deployment(_eval_report(False), adapter_dir="x")
        assert plan["deploy"] is False
        assert "safety" in plan["gates_failed"]
        assert "shadow_compare" not in plan["steps"]

    def test_external_gates_not_treated_as_failures(self):
        plan = plan_deployment(_eval_report(True), adapter_dir="x")
        assert "latency" not in plan["gates_failed"]
        assert "regression" not in plan["gates_failed"]


class TestRunDeployment:
    def test_register_stage_and_slots(self, tmp_path: Path):
        report = run_deployment(
            eval_report=_eval_report(True),
            adapter_dir="training/models/adapters/novi-qwen3-8b-dialogue-v1",
            registry_root=tmp_path,
            base_model="qwen3:8b",
            training_dataset="sft_v1",
            training_config="sft-v1",
            commit="abc123",
        )
        assert isinstance(report, DeploymentReport)
        assert report.deployed is True
        assert report.model_id == "novi-qwen3-8b-dialogue-v1"
        # manifest registered and promoted to active
        manifests = list((tmp_path / "novi-qwen3-8b-dialogue-v1.json").exists() for _ in [0])
        assert manifests == [True]
        import json  # noqa: PLC0415

        manifest = json.loads((tmp_path / "novi-qwen3-8b-dialogue-v1.json").read_text())
        assert manifest["status"] == "active"
        assert manifest["metrics"]["safety"] == pytest.approx(1.0)

    def test_failed_gates_never_register(self, tmp_path: Path):
        report = run_deployment(
            eval_report=_eval_report(False),
            adapter_dir="x",
            registry_root=tmp_path,
            base_model="qwen3:8b",
            training_dataset="sft_v1",
            training_config="sft-v1",
            commit="abc123",
        )
        assert report.deployed is False
        assert not (tmp_path / "x.json").exists()