"""Tests for the production-parity ChatML SFT template (plan 03 parity).

``render_chatml`` must produce a SYSTEM role carrying the persona + the
situation context, and a USER role carrying the real utterance verbatim. The
torch backend must emit qwen ChatML with roles when a user utterance exists and
keep the legacy flat prompt when it does not.
"""

from __future__ import annotations

import torch

from training.training.backends.torch_sft import (
    _build_chat_dataset,
    _prompt_text,
    _training_text,
)
from training.training.common import NOVI_PERSONA, render_chatml


class _FakeTokenizer:
    """Deterministic tiny tokenizer so the test needs no real model."""

    def __call__(self, text, truncation=True, max_length=None, return_tensors=None):
        ids = [ord(c) % 100 + 1 for c in text]
        return {
            "input_ids": torch.tensor([ids]),
            "attention_mask": torch.ones(1, len(ids), dtype=torch.long),
        }


def _production_example() -> dict:
    return {
        "example_id": "acc-1",
        "task": "natural_dialogue",
        "situation": {
            "person": {"id": "person:unknown", "relationship": ""},
            "conversation": {
                "topic": "car interior",
                "input": "Recommend an interior for my car.",
                "entities": ["dark"],
            },
            "memory": [
                {
                    "id": "acc-mem-1-0",
                    "summary": "You prefer dark interiors.",
                    "confidence": 0.9,
                    "source": "acceptance",
                }
            ],
            "intent": "RECOMMENDATION",
            "referents": {},
            "response_goal": "RECOMMEND",
        },
        "decision": {"dialogue_act": "RESPOND", "verbosity": "short"},
        "response": "Got it — dark interiors suit you.",
        "preferred_response": "Got it — dark interiors suit you.",
    }


class TestRenderChatml:
    def test_system_contains_persona_and_user_verbatim(self):
        system, user = render_chatml(_production_example())
        assert NOVI_PERSONA in system
        assert user == "Recommend an interior for my car."
        assert "- Intent: RECOMMENDATION" in system
        assert "- Communicative act: RESPOND" in system
        assert "- Memory: You prefer dark interiors." in system

    def test_user_falls_back_to_top_level_user_key(self):
        ex = {
            "situation": {"conversation": {"topic": "", "input": ""}},
            "user": "Hello there",
            "decision": {"dialogue_act": "RESPOND"},
        }
        _system, user = render_chatml(ex)
        assert user == "Hello there"

    def test_empty_user_for_legacy_row(self):
        ex = {"situation": {"person": {"id": "p1"}}, "decision": {"dialogue_act": "RESPOND"}}
        system, user = render_chatml(ex)
        assert user == ""
        assert NOVI_PERSONA in system


class TestTorchTextBuilder:
    def test_chatml_text_starts_with_system_ends_with_response(self):
        ex = _production_example()
        text = _training_text(ex)
        assert text.startswith("<|im_start|>system\n")
        assert text.endswith("Got it — dark interiors suit you.<|im_end|>")
        assert "<|im_start|>user\nRecommend an interior for my car.<|im_end|>" in text
        assert "<|im_start|>assistant\n" in text

    def test_prompt_text_is_chatml_for_user_utterance(self):
        prompt = _prompt_text(_production_example())
        assert prompt.startswith("<|im_start|>system\n")
        assert prompt.endswith("<|im_start|>assistant\n")

    def test_legacy_example_still_flat(self):
        ex = {
            "situation": {"person": {"id": "p1", "relationship": "owner"}},
            "decision": {"dialogue_act": "RESPOND"},
            "response": "hello",
        }
        prompt = _prompt_text(ex)
        assert not prompt.startswith("<|im_start|>system")
        assert "Person: p1 (owner)" in prompt
        text = _training_text(ex)
        assert text.endswith("\n<|im_start|>assistant\nhello<|im_end|>")


class TestBuildChatDataset:
    def test_chatml_row_masks_prompt_labels(self):
        rows = _build_chat_dataset([_production_example()], _FakeTokenizer(), 2048)
        assert len(rows) == 1
        labels = rows[0]["labels"]
        assert (labels == -100).any()
        assert (labels != -100).any()

    def test_legacy_row_still_builds(self):
        ex = {"example_id": "x", "situation": {}, "response": "hello"}
        rows = _build_chat_dataset([ex], _FakeTokenizer(), 2048)
        assert len(rows) == 1
