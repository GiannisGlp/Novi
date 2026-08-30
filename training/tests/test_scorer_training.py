"""Tests for the small-scorer training runs (plan 23 steps 17/20/23)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

CONFIGS = Path(__file__).resolve().parents[1] / "configs"
ROOT = Path(__file__).resolve().parents[2]


def _run(script: str, config: str) -> dict:
    out = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parents[1] / "training" / script),
         "--config", str(CONFIGS / config), "--out-json", "-"],
        capture_output=True, text=True, cwd=ROOT,
    )
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout.strip().splitlines()[-1])


class TestScorerTraining:
    @pytest.mark.parametrize("script,config,kind", [
        ("train_retriever.py", "retrieval.yaml", "retrieval"),
        ("train_policy.py", "policy.yaml", "policy"),
        ("train_grounding.py", "grounding.yaml", "grounding"),
    ])
    def test_real_training_runs_and_writes_artifact(self, tmp_path, script, config, kind):
        import importlib.util

        if not importlib.util.find_spec("torch"):
            pytest.skip("torch not installed")
        report = _run(script, config)
        assert report["task"] == kind
        assert report["framework"] == "torch-linear"
        artifact = Path(report["artifact"])
        assert artifact.exists(), report
        data = json.loads(artifact.read_text())
        assert data.get("weights") or data.get("act_weights")
        assert "provenance" in data

    def test_retriever_artifact_orders_relevant_first(self, tmp_path):
        # End-to-end criterion: applying the learned weights to a record's
        # candidate features must rank the preferred candidate first.
        from training.training.common import load_jsonl  # noqa: PLC0415

        report = _run("train_retriever.py", "retrieval.yaml")
        artifact = json.loads(Path(report["artifact"]).read_text())
        weights = [artifact["weights"][f"w_{i}"] for i in range(len(artifact["weights"]))]
        records = load_jsonl(ROOT / "training/datasets/retrieval/retrieval_v1.jsonl")
        rec = records[0]
        scores = []
        for feats in rec["candidate_features"]:
            vec = [float(feats[k]) for k in artifact.get("features", artifact.get("feature_names", list(feats)))]
            scores.append(sum(w * v for w, v in zip(weights, vec, strict=True)))
        best = max(range(len(scores)), key=lambda i: scores[i])
        assert best == rec["preferred"][0]

    def test_policy_scorer_discriminates(self, tmp_path):
        report = _run("train_policy.py", "policy.yaml")
        artifact = json.loads(Path(report["artifact"]).read_text())
        assert artifact["model"] == "linear-ovr"
        assert artifact["act_weights"]
        assert len(artifact["act_weights"]) >= 5

    def test_grounding_ranker_cue_weights(self, tmp_path):
        report = _run("train_grounding.py", "grounding.yaml")
        weights = json.loads(Path(report["artifact"]).read_text())["weights"]
        # gaze/pointing matches are the discriminative features
        assert weights.get("w_1", 0.0) + weights.get("w_2", 0.0) > 0.0
