"""Tests for the seed curated dialogue dataset (plan 23 step 08, §32)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from training.collection.validator import validate_example_ctx
from training.schemas import SFT_TASKS, validate_example

DATASETS = Path(__file__).resolve().parents[1] / "datasets"
SEED = DATASETS / "curated" / "seed_dialogue_v1.jsonl"
MEMORY_INDEX = DATASETS / "curated" / "memory_index_v1.json"


def _load_seed() -> list[dict]:
    assert SEED.exists(), f"seed dataset missing: {SEED}"
    return [json.loads(line) for line in SEED.read_text().splitlines() if line.strip()]


class TestSeedDataset:
    def test_seed_exists_and_nonempty(self):
        examples = _load_seed()
        assert len(examples) >= 40

    def test_every_example_passes_schema_validation(self):
        for ex in _load_seed():
            assert validate_example(ex) == [], ex["example_id"]

    def test_every_example_passes_dataset_validation(self):
        index = set(json.loads(MEMORY_INDEX.read_text()))
        for ex in _load_seed():
            errors = validate_example_ctx(ex, memory_index=index)
            assert errors == [], (ex["example_id"], errors)

    def test_covers_all_sft_task_types(self):
        tasks = {ex["task"] for ex in _load_seed()}
        assert tasks == SFT_TASKS

    def test_abstract_person_ids_only(self):
        for ex in _load_seed():
            pid = (ex["situation"]["person"] or {}).get("id", "")
            assert pid.startswith("person:"), ex["example_id"]

    def test_unique_example_ids(self):
        ids = [ex["example_id"] for ex in _load_seed()]
        assert len(ids) == len(set(ids))

    def test_plan_section5_example_present(self):
        examples = _load_seed()
        assert any(
            ex["example_id"] == "dlg-0001821" and ex["response"] == "There's one part of the camera side we haven't closed yet."
            for ex in examples
        )

    def test_memory_ids_all_in_index(self):
        index = set(json.loads(MEMORY_INDEX.read_text()))
        for ex in _load_seed():
            for m in ex["situation"]["memory"]:
                assert m["id"] in index, (ex["example_id"], m["id"])

    def test_no_assistant_style_phrases_in_responses(self):
        bad = ("i acknowledge", "i have detected", "i can confirm that", "as an ai")
        for ex in _load_seed():
            low = ex["response"].lower()
            assert not any(b in low for b in bad), ex["example_id"]


class TestDeterminism:
    def test_build_is_reproducible(self):
        import subprocess
        import sys

        script = Path(__file__).resolve().parents[1] / "datasets" / "build_seed.py"
        out = subprocess.run(
            [sys.executable, str(script), "--check"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parents[2],
        )
        assert out.returncode == 0, out.stderr
        assert "OK" in out.stdout

    def test_seed_hash_stable(self):
        # Guards against accidental nondeterminism (ordering, RNG) in the seed.
        h = hashlib.sha256(SEED.read_bytes()).hexdigest()
        assert h == "374c1e27146e9c6664730a5806e797975e2845eb943805342f06ab1d244009d7"
