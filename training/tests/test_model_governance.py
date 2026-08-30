"""Tests for the model registry + rollback (plan 23 §22-§23, §29)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from training.models.registry import (
    ModelRegistry,
    build_manifest,
    compatible_schemas,
)
from training.models.rollback import (
    ROLLBACK_TRIGGERS,
    DeploymentSlots,
    detect_rollback,
    trigger_from_metrics,
)
from training.schemas import SCHEMA_VERSIONS


def _manifest(model_id: str = "novi-qwen3-8b-dialogue-v1", **overrides) -> dict:
    m = {
        "model_id": model_id,
        "base_model": "qwen3:8b",
        "adapter_type": "lora",
        "training_dataset": "dialogue-v1",
        "training_commit": "abc123",
        "training_config": "sft-v3",
        "created_at": "2026-08-30T12:00:00+00:00",
        "evaluation_suite": "social-v1",
        "metrics": {"naturalness": 0.91, "grounding": 0.97, "memory": 0.92, "initiative": 0.88, "safety": 0.995},
        "status": "candidate",
        "context_schema": SCHEMA_VERSIONS["context"],
        "memory_schema": SCHEMA_VERSIONS["memory"],
        "world_schema": SCHEMA_VERSIONS["world"],
        "dialogue_schema": SCHEMA_VERSIONS["dialogue"],
    }
    m.update(overrides)
    return m


class TestManifest:
    def test_build_manifest_fills_plan_fields(self):
        m = build_manifest(base_model="qwen3:8b", training_dataset="dialogue-v1", training_config="sft-v3")
        assert m["model_id"].startswith("novi-")
        assert m["adapter_type"] == "lora"
        assert m["status"] == "candidate"
        assert m["training_commit"]

    def test_plan_section22_manifest_fields(self):
        m = _manifest()
        for key in ("model_id", "base_model", "adapter_type", "training_dataset",
                    "training_commit", "training_config", "created_at", "evaluation_suite",
                    "metrics", "status"):
            assert key in m


class TestRegistry:
    def test_register_writes_manifest(self, tmp_path: Path):
        reg = ModelRegistry(tmp_path)
        reg.register(_manifest())
        f = tmp_path / "novi-qwen3-8b-dialogue-v1.json"
        assert f.exists()
        assert json.loads(f.read_text())["model_id"] == "novi-qwen3-8b-dialogue-v1"

    def test_register_requires_model_id(self, tmp_path: Path):
        reg = ModelRegistry(tmp_path)
        with pytest.raises(ValueError):
            reg.register(_manifest(model_id=""))

    def test_duplicate_id_rejected(self, tmp_path: Path):
        reg = ModelRegistry(tmp_path)
        reg.register(_manifest())
        with pytest.raises(ValueError):
            reg.register(_manifest())

    def test_list_and_get(self, tmp_path: Path):
        reg = ModelRegistry(tmp_path)
        reg.register(_manifest("novi-a-v1"))
        reg.register(_manifest("novi-b-v1"))
        assert {m["model_id"] for m in reg.list()} == {"novi-a-v1", "novi-b-v1"}
        assert reg.get("novi-a-v1")["model_id"] == "novi-a-v1"

    def test_status_transitions(self, tmp_path: Path):
        reg = ModelRegistry(tmp_path)
        reg.register(_manifest())
        reg.set_status("novi-qwen3-8b-dialogue-v1", "staged")
        reg.set_status("novi-qwen3-8b-dialogue-v1", "active")
        assert reg.get("novi-qwen3-8b-dialogue-v1")["status"] == "active"

    def test_invalid_transition_rejected(self, tmp_path: Path):
        reg = ModelRegistry(tmp_path)
        reg.register(_manifest())
        with pytest.raises(ValueError):
            reg.set_status("novi-qwen3-8b-dialogue-v1", "active")  # candidate -> active is not direct

    def test_never_deploy_unnamed_checkpoint(self, tmp_path: Path):
        reg = ModelRegistry(tmp_path)
        with pytest.raises(ValueError):
            reg.register(_manifest(model_id="checkpoint-42-epoch-3"))  # unnamed per plan §22

    def test_unknown_id_get_raises(self, tmp_path: Path):
        reg = ModelRegistry(tmp_path)
        with pytest.raises(KeyError):
            reg.get("nope")


class TestSchemaCompatibility:
    def test_matching_schemas_compatible(self):
        assert compatible_schemas(_manifest()) == []

    def test_mismatched_dialogue_schema_rejected(self):
        m = _manifest(dialogue_schema=SCHEMA_VERSIONS["dialogue"] + 1)
        errs = compatible_schemas(m)
        assert any("dialogue" in e for e in errs)

    def test_all_schema_versions_checked(self):
        m = _manifest(context_schema=1, memory_schema=1, world_schema=1, dialogue_schema=1)
        errs = compatible_schemas(m)
        assert len(errs) == 4


class TestRollback:
    def test_promote_and_rollback_swap_slots(self):
        slots = DeploymentSlots()
        slots.promote("novi-v2")
        slots.promote("novi-v3")
        assert slots.current == "novi-v3"
        assert slots.previous == "novi-v2"
        slots.rollback()
        assert slots.current == "novi-v2"
        assert slots.previous == "novi-v3"

    def test_rollback_without_retraining(self):
        slots = DeploymentSlots()
        slots.promote("a")
        slots.promote("b")
        slots.rollback()
        assert slots.current == "a"  # instant switch, no training involved

    def test_restore_known_good(self):
        slots = DeploymentSlots()
        slots.promote("kg")  # known good
        slots.promote("v2")
        slots.promote("v3")
        assert slots.known_good == "kg"
        slots.restore_known_good()
        assert slots.current == "kg"

    def test_rollback_trigger_list_matches_plan(self):
        assert frozenset({
            "safety_regression", "identity_hallucination", "memory_hallucination",
            "naturalness_regression", "latency_regression", "initiative_spam",
        }) == ROLLBACK_TRIGGERS

    def test_trigger_from_metrics_safety(self):
        metrics = {"safety": {"unsupported_claim_rate": 0.3}}
        triggers = trigger_from_metrics(metrics, safety_floor=0.995)
        assert "safety_regression" in triggers

    def test_trigger_from_metrics_initiative_spam(self):
        metrics = {"initiative": {"appropriate_initiative_rate": 0.1}}
        assert "initiative_spam" in trigger_from_metrics(metrics)

    def test_detect_rollback_combines(self):
        triggers = detect_rollback(metrics={"safety": {"unsupported_claim_rate": 0.9}}, safety_floor=0.995)
        assert triggers == ["safety_regression"]

    def test_no_triggers_when_clean(self):
        metrics = {"safety": {"unsupported_claim_rate": 0.0},
                   "initiative": {"appropriate_initiative_rate": 0.95}}
        assert detect_rollback(metrics, safety_floor=0.995) == []
