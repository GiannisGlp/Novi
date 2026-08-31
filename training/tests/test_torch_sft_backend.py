"""Tests for the torch-peft SFT backend (plan 24 §25, §51 item 24/27).

The backend must render the emotional prompt (social context + selected
strategy) and read the emotional `preferred_response` key so the emotional
SFT/DPO runs train on the right target, not a near-empty plan-23 prompt.
"""

from __future__ import annotations

import torch

from training.training.backends.torch_sft import _build_chat_dataset, _prompt_text


class _FakeTokenizer:
    """Deterministic tiny tokenizer so the test needs no real model."""

    def __call__(self, text, truncation=True, max_length=None, return_tensors=None):
        ids = [ord(c) % 100 + 1 for c in text]
        return {
            "input_ids": torch.tensor([ids]),
            "attention_mask": torch.ones(1, len(ids), dtype=torch.long),
        }


def _emotional() -> dict:
    return {
        "example_id": "emo-00182",
        "task": "appropriate_acknowledgement",
        "situation": {
            "relationship": "owner",
            "conversation_phase": "repair",
            "user_goal": "solve_problem",
            "affective_hypotheses": [{"label": "frustration", "probability": 0.76}],
            "novi_caused_problem": True,
            "interruptibility": 0.3,
        },
        "desired_behavior": {"act": ["ACKNOWLEDGE", "APOLOGIZE", "SOLVE"]},
        "preferred_response": "Yeah, I took that the wrong way. Let me reset.",
    }


class TestPromptText:
    def test_emotional_example_uses_emotional_prompt(self):
        prompt = _prompt_text(_emotional())
        assert "Relationship: owner" in prompt
        assert "Conversation phase: repair" in prompt
        assert "Communicative act: ACKNOWLEDGE" in prompt

    def test_plan23_example_uses_situation_prompt(self):
        ex = {"situation": {"person": {"id": "p1", "relationship": "owner"}},
              "decision": {"dialogue_act": "RESPOND"}}
        prompt = _prompt_text(ex)
        assert "Person: p1 (owner)" in prompt
        assert "Communicative act: RESPOND" in prompt


class TestBuildChatDataset:
    def test_reads_preferred_response_for_emotional(self):
        rows = _build_chat_dataset([_emotional()], _FakeTokenizer(), 2048)
        assert len(rows) == 1
        assert rows[0]["labels"].shape[0] > 0

    def test_reads_response_for_plan23(self):
        ex = {"example_id": "x", "situation": {}, "response": "hello"}
        rows = _build_chat_dataset([ex], _FakeTokenizer(), 2048)
        assert len(rows) == 1

    def test_masks_prompt_labels(self):
        rows = _build_chat_dataset([_emotional()], _FakeTokenizer(), 2048)
        labels = rows[0]["labels"]
        # the prompt portion is masked (-100), the response portion is not
        assert (labels == -100).any()
        assert (labels != -100).any()
