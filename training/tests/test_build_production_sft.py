"""Tests for the evidence-based production SFT builder (plan 03 parity).

Runs the real builder over a tiny synthetic acceptance fixture (minimal
envelopes constructed in a tmp dir) and asserts schema-valid rows with
deterministic provenance fields.
"""

from __future__ import annotations

import json
from pathlib import Path

from training.datasets.build_production_sft import build_rows
from training.schemas import validate_example


def _turn(
    user,
    response,
    *,
    reply_source="dialogue",
    goal="ANSWER_DIRECTLY",
    intent="INFORMATION_REQUEST",
    referents=None,
    memories=None,
    must_include=None,
    must_not_include=None,
):
    return {
        "turn_index": 0,
        "user_text": user,
        "response_text": response,
        "reply_source": reply_source,
        "intent": {
            "intent": intent,
            "dialogue_act": "QUESTION",
            "confidence": 0.9,
            "needs_clarification": False,
        },
        "referents": referents or {},
        "response_goal": {
            "goal": goal,
            "must_include": must_include or [],
            "may_include": [],
            "must_not_include": must_not_include or [],
            "required_evidence": [],
        },
        "retrieved_context": {
            "grounding": {
                "packet": {
                    "relevant_memories": [{"content": m} for m in (memories or [])],
                    "anchor": {"topic": ""},
                    "response_requirements": [],
                }
            }
        },
    }


def _envelope(scenario, result, git_sha, turns):
    return {
        "schema": "conversation-acceptance/v1",
        "scenario": scenario,
        "title": "t",
        "result": result,
        "git_sha": git_sha,
        "conversation": turns,
    }


def _write_envelope(base: Path, scenario: str, envelope: dict) -> None:
    d = base / "scenarios"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{scenario}.json").write_text(json.dumps(envelope))


def test_builder_collects_schema_valid_rows(tmp_path):
    env = _envelope("C-001", "PASS", "abc123", [
        _turn(
            "Recommend an interior for my car.",
            "Got it — dark interiors suit you.",
            goal="RECOMMEND",
            intent="RECOMMENDATION",
            memories=["You prefer dark interiors."],
        ),
        _turn("Hi Novi.", "Hi there!", goal="ACKNOWLEDGE", intent="GREETING"),
    ])
    _write_envelope(tmp_path, "C-001", env)

    rows = build_rows([tmp_path])
    assert len(rows) == 2
    for ex in rows:
        assert validate_example(ex, kind="canonical") == []
    tasks = {ex["task"] for ex in rows}
    assert "memory_grounded_response" in tasks
    assert "social_greeting" in tasks


def test_builder_skips_fail_and_non_dialogue_turns(tmp_path):
    env = _envelope("C-002", "PASS", "abc123", [
        _turn("Good.", "Thanks!", reply_source="fallback"),
        _turn("", "empty user"),
        _turn("hello", ""),
        _turn("Valid q.", "Valid a."),
    ])
    _write_envelope(tmp_path, "C-002", env)
    rows = build_rows([tmp_path])
    assert [ex["situation"]["conversation"]["input"] for ex in rows] == ["Valid q."]


def test_builder_skips_failed_envelope(tmp_path):
    _write_envelope(tmp_path, "C-003", _envelope("C-003", "FAIL", "abc123", [_turn("q", "a")]))
    assert build_rows([tmp_path]) == []


def test_provenance_fields(tmp_path):
    env = _envelope("C-004", "PASS", "deadbeef", [
        _turn(
            "Do you remember I like jazz?",
            "Yeah — you like jazz.",
            goal="REMEMBER",
            intent="MEMORY_UPDATE",
            memories=["I like jazz."],
        ),
    ])
    _write_envelope(tmp_path, "C-004", env)
    ex = build_rows([tmp_path])[0]
    assert ex["example_id"] == "acc-1"
    assert ex["synthetic"] is False
    assert ex["evidence_git_sha"] == "deadbeef"
    assert ex["source"].startswith("acceptance:")
    assert ":C-004:turn0" in ex["source"]
    assert ex["preferred_response"] == "Yeah — you like jazz."
    assert ex["response"] == "Yeah — you like jazz."
    assert ex["situation"]["memory"][0]["source"] == "acceptance"
    assert ex["situation"]["memory"][0]["summary"] == "I like jazz."


def test_dedup_and_cap(tmp_path):
    turns = [_turn(f"q{i}", "a") for i in range(8)]
    # make turn[1] an exact duplicate of turn[0]
    turns[1]["user_text"] = turns[0]["user_text"]
    turns[1]["response_text"] = turns[0]["response_text"]
    _write_envelope(tmp_path, "C-005", _envelope("C-005", "PASS", "abc", turns))
    rows = build_rows([tmp_path])
    assert len(rows) == 5
