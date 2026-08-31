"""Tests for the emotional SFT pipeline (plan 24 §25, §51 item 24).

Phase 21 (§25) SFT emotional behavior: the training target is
`social context + selected strategy -> natural response`, never
`emotion label -> canned phrase`. These tests cover the emotional prompt
builder, the combined SFT-ready dataset, and the committed config.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from training.schemas import EMOTIONAL_SFT_TASKS, validate_example
from training.training.common import (
    emotional_situation_to_prompt,
    prompt_for,
    situation_to_prompt,
)

DATASETS = Path(__file__).resolve().parents[1] / "datasets"
EMOTIONAL_SFT = DATASETS / "sft" / "emotional_sft_v1.jsonl"


def _load(path: Path) -> list[dict]:
    assert path.exists(), f"missing: {path}"
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _emotional(**overrides) -> dict:
    ex = {
        "example_id": "emo-00182",
        "task": "appropriate_acknowledgement",
        "situation": {
            "relationship": "owner",
            "conversation_phase": "repair",
            "user_goal": "solve_problem",
            "affective_hypotheses": [
                {"label": "frustration", "probability": 0.76},
                {"label": "fatigue", "probability": 0.14},
            ],
            "novi_caused_problem": True,
            "interruptibility": 0.30,
        },
        "desired_behavior": {
            "act": ["ACKNOWLEDGE", "APOLOGIZE", "SOLVE"],
            "verbosity": "short",
            "defensiveness": "none",
            "certainty": "moderate",
        },
        "preferred_response": "Yeah, I took that the wrong way. Let me reset.",
    }
    ex.update(overrides)
    return ex


class TestEmotionalPrompt:
    def test_renders_social_context(self):
        prompt = emotional_situation_to_prompt(_emotional())
        assert "Relationship: owner" in prompt
        assert "Conversation phase: repair" in prompt
        assert "User goal: solve_problem" in prompt
        assert "Affective hypotheses:" in prompt
        assert "frustration" in prompt
        assert "Novi caused problem: true" in prompt
        assert "Interruptibility: 0.3" in prompt

    def test_renders_selected_strategy(self):
        prompt = emotional_situation_to_prompt(_emotional())
        assert "Communicative act: ACKNOWLEDGE" in prompt

    def test_uses_first_acceptable_act_as_strategy(self):
        prompt = emotional_situation_to_prompt(_emotional())
        act_line = prompt.split("Communicative act:")[1]
        assert "ACKNOWLEDGE" in act_line
        assert "APOLOGIZE" not in act_line

    def test_not_emotion_label_to_canned_phrase(self):
        # Plan §25: the prompt is social context + selected strategy, not
        # "emotion: frustration -> say X". No canned instruction may appear.
        prompt = emotional_situation_to_prompt(_emotional())
        assert "Communicative act:" in prompt
        assert "say" not in prompt.lower()

    def test_silence_act_rendered(self):
        ex = _emotional(task="appropriate_silence")
        ex["desired_behavior"]["act"] = ["SILENCE"]
        ex["preferred_response"] = ""
        prompt = emotional_situation_to_prompt(ex)
        assert "Communicative act: SILENCE" in prompt

    def test_prompt_for_dispatches_emotional(self):
        assert prompt_for(_emotional()) == emotional_situation_to_prompt(_emotional())

    def test_prompt_for_dispatches_plan23(self):
        ex = {
            "example_id": "dlg-0001",
            "situation": {"person": {"id": "person:owner_001", "relationship": "owner"},
                          "world": {"location": "office"}},
            "decision": {"dialogue_act": "RESPOND"},
            "response": "Sure.",
        }
        assert prompt_for(ex) == situation_to_prompt(ex)


class TestEmotionalSftDataset:
    def test_file_exists_and_meets_gate(self):
        rows = _load(EMOTIONAL_SFT)
        assert len(rows) >= 200  # sft_emotional.yaml min_examples

    def test_all_rows_schema_valid(self):
        for ex in _load(EMOTIONAL_SFT):
            assert validate_example(ex, kind="emotional") == [], ex["example_id"]

    def test_all_rows_have_response_or_silence(self):
        for ex in _load(EMOTIONAL_SFT):
            acts = ex["desired_behavior"]["act"]
            if "SILENCE" not in acts:
                assert ex["preferred_response"], ex["example_id"]

    def test_unique_ids(self):
        rows = _load(EMOTIONAL_SFT)
        ids = [r["example_id"] for r in rows]
        assert len(ids) == len(set(ids))

    def test_covers_all_sft_tasks(self):
        tasks = {r["task"] for r in _load(EMOTIONAL_SFT)}
        assert tasks >= EMOTIONAL_SFT_TASKS

    def test_excludes_preference_and_perspective(self):
        tasks = {r["task"] for r in _load(EMOTIONAL_SFT)}
        assert "preference" not in tasks
        assert "perspective" not in tasks

    def test_reproducible(self):
        script = DATASETS / "build_emotional_datasets.py"
        out = subprocess.run([sys.executable, str(script), "--check"], capture_output=True,
                             text=True, cwd=Path(__file__).resolve().parents[2])
        assert out.returncode == 0, out.stderr
        assert "OK" in out.stdout


class TestEmotionalSftConfig:
    def test_config_exists_and_loads(self):
        from training.config import load_config

        cfg_path = Path(__file__).resolve().parents[1] / "configs" / "sft_emotional.yaml"
        assert cfg_path.exists()
        cfg = load_config(cfg_path)
        assert cfg.kind == "sft"
        assert cfg.base_model == "qwen3:8b"
        assert cfg.dataset == "training/datasets/sft/emotional_sft_v1.jsonl"
        assert cfg.min_examples <= len(_load(EMOTIONAL_SFT))
