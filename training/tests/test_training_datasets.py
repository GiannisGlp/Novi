"""Tests for the experiment datasets (plan 23 §32/§33/§16/§19/§22)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from training.schemas import PREFERENCE_CATEGORIES, validate_example

DATASETS = Path(__file__).resolve().parents[1] / "datasets"

SFT = DATASETS / "sft" / "sft_v1.jsonl"
SFT_INDEX = DATASETS / "sft" / "memory_index_v2.json"
DPO = DATASETS / "dpo" / "preference_pairs_v1.jsonl"
RETRIEVAL = DATASETS / "retrieval" / "retrieval_v1.jsonl"
POLICY = DATASETS / "policy" / "policy_v1.jsonl"
GROUNDING = DATASETS / "grounding" / "grounding_v1.jsonl"


def _load(path: Path) -> list[dict]:
    assert path.exists(), f"missing: {path}"
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


class TestSftDataset:
    def test_size_meets_experiment_gate(self):
        assert len(_load(SFT)) >= 200  # sft.yaml min_examples
        assert len(_load(SFT)) <= 2000  # plan §32 band

    def test_all_rows_schema_valid(self):
        for ex in _load(SFT):
            assert validate_example(ex) == [], ex["example_id"]

    def test_all_rows_context_valid_with_index(self):
        from training.collection.validator import validate_example_ctx

        index = set(json.loads(SFT_INDEX.read_text()))
        for ex in _load(SFT):
            errors = validate_example_ctx(ex, memory_index=index)
            assert errors == [], (ex["example_id"], errors)

    def test_provenance_marked(self):
        rows = _load(SFT)
        assert any(r["source"] == "curated" and r["synthetic"] is False for r in rows)
        assert any(r["source"] == "template-derived" and r["synthetic"] is True
                   and r.get("derived_from") for r in rows)

    def test_unique_ids_and_all_tasks(self):
        from training.schemas import SFT_TASKS

        rows = _load(SFT)
        ids = [r["example_id"] for r in rows]
        assert len(ids) == len(set(ids))
        assert {r["task"] for r in rows} == SFT_TASKS

    def test_reproducible(self):
        script = DATASETS / "build_sft_dataset.py"
        out = subprocess.run([sys.executable, str(script), "--check"], capture_output=True,
                             text=True, cwd=Path(__file__).resolve().parents[2])
        assert out.returncode == 0, out.stderr
        assert "OK" in out.stdout


class TestPreferencePairs:
    def test_more_than_1000_pairs(self):
        pairs = _load(DPO)
        assert len(pairs) >= 1000  # plan §33

    def test_all_valid(self):
        for p in _load(DPO):
            assert validate_example(p, kind="preference") == [], p["example_id"]

    def test_categories_cover_plan_list(self):
        cats = {p["category"] for p in _load(DPO)}
        assert cats == PREFERENCE_CATEGORIES


class TestRetrieval:
    def test_valid_and_featured(self):
        for r in _load(RETRIEVAL):
            assert validate_example(r, kind="retrieval") == [], r["example_id"]
            assert r["preferred"] == [0]
            assert len(r["candidate_features"]) == len(r["candidates"])
            assert "semantic" in r["candidate_features"][0]


class TestPolicy:
    def test_valid_and_preferred_in_candidates(self):
        for r in _load(POLICY):
            assert validate_example(r, kind="policy") == [], r["example_id"]
            assert r["preferred"] in r["candidates"]


class TestGrounding:
    def test_valid(self):
        for r in _load(GROUNDING):
            assert validate_example(r, kind="grounding") == [], r["example_id"]


class TestAuxReproducible:
    def test_aux_builders_reproducible(self):
        script = DATASETS / "build_aux_datasets.py"
        out = subprocess.run([sys.executable, str(script), "--check"], capture_output=True,
                             text=True, cwd=Path(__file__).resolve().parents[2])
        assert out.returncode == 0, out.stderr
        assert "OK" in out.stdout


class TestPolicyConfig:
    def test_policy_config_exists(self):
        cfg = Path(__file__).resolve().parents[1] / "configs" / "policy.yaml"
        assert cfg.exists()
