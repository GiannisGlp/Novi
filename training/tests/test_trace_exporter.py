"""Tests for trace export + eligibility (plan 23 §6)."""

from __future__ import annotations

from novi.brain.decision_trace import DecisionTrace, utc_now_iso
from training.collection.trace_exporter import (
    TraceExporter,
    default_task_for_act,
    eligibility_reasons,
    is_eligible,
)


def _trace(**overrides) -> dict:
    t = DecisionTrace(
        trace_id="trace-1",
        cycle_id=7,
        time=utc_now_iso(),
        input_event="Vano: what did we decide about the camera?",
        perception_evidence=["camera detected on desk"],
        world_changes=[],
        identity_resolution={"person_id": "person:vano", "confidence": 0.98, "name": "Vano"},
        retrieved_memories=["mem-1821"],
        social_context={"engaged": True, "interruptibility": 0.15, "topic": "camera integration"},
        dialogue_act="RESPOND",
        dialogue_reason="question_answered",
        initiative_score=0.0,
        llm_model="qwen3:8b",
        response="We discussed camera recognition yesterday.",
        outcome="acknowledged",
    )
    for k, v in overrides.items():
        setattr(t, k, v)
    return t.snapshot()


class TestTaskInference:
    def test_act_to_task_mapping(self):
        assert default_task_for_act("GREETING") == "social_greeting"
        assert default_task_for_act("CLARIFY") == "clarification"
        assert default_task_for_act("REPAIR") == "repair"
        assert default_task_for_act("CONTINUE") == "context_continuation"
        assert default_task_for_act("SILENCE") == "silence_abstention"
        assert default_task_for_act("COMMENT") == "proactive_comment"
        assert default_task_for_act("RESPOND") == "natural_dialogue"
        assert default_task_for_act("ASK") == "clarification"
        assert default_task_for_act("TELEPORT") == "natural_dialogue"  # unknown -> default


class TestEligibility:
    def test_full_trace_eligible(self):
        assert is_eligible(_trace()) is True
        assert eligibility_reasons(_trace()) != []

    def test_missing_dialogue_act_not_eligible(self):
        t = _trace(dialogue_act="", response="")
        assert is_eligible(t) is False
        assert "clear_decision" not in eligibility_reasons(t)

    def test_empty_trace_not_eligible(self):
        t = _trace(input_event="", response="", dialogue_act="SILENCE",
                   perception_evidence=[], retrieved_memories=[], identity_resolution={})
        # silence without any context is not a meaningful example
        assert is_eligible(t) is False

    def test_correction_outcome_eligible(self):
        t = _trace(outcome="corrected", correction="no, the blue one")
        assert is_eligible(t) is True
        assert "explicit_correction" in eligibility_reasons(t)

    def test_unknown_outcome_still_eligible_when_decision_clear(self):
        t = _trace(outcome="")
        assert is_eligible(t) is True

    def test_interesting_failure_eligible(self):
        t = _trace(outcome="ignored", dialogue_act="COMMENT")
        assert is_eligible(t) is True
        assert "interesting_failure" in eligibility_reasons(t)

    def test_initiative_decision_eligible(self):
        t = _trace(dialogue_act="COMMENT", initiative_score=0.7, input_event="chair moved")
        assert is_eligible(t) is True
        assert "initiative_decision" in eligibility_reasons(t)


class TestExport:
    def test_exports_canonical_example(self):
        exporter = TraceExporter()
        examples = exporter.export(_trace())
        assert len(examples) == 1
        ex = examples[0]
        assert ex["task"] == "natural_dialogue"
        assert ex["response"] == "We discussed camera recognition yesterday."
        assert ex["decision"]["dialogue_act"] == "RESPOND"
        assert ex["decision"]["reason"] == "question_answered"
        sit = ex["situation"]
        assert sit["memory"] == [{"id": "mem-1821", "summary": "mem-1821", "confidence": 1.0}]
        assert sit["social"] == {"engaged": True, "interruptibility": 0.15, "topic": "camera integration"}

    def test_silence_exports_empty_response(self):
        exporter = TraceExporter()
        t = _trace(dialogue_act="SILENCE", response="", input_event="chair moved")
        examples = exporter.export(t)
        assert examples[0]["task"] == "silence_abstention"
        assert examples[0]["response"] == ""

    def test_example_id_stable_and_prefixed(self):
        exporter = TraceExporter()
        ex = exporter.export(_trace())[0]
        assert ex["example_id"].startswith("trace-1-")

    def test_person_id_copied_from_identity(self):
        exporter = TraceExporter()
        ex = exporter.export(_trace())[0]
        assert ex["situation"]["person"]["id"] == "person:vano"

    def test_export_skips_ineligible_traces(self):
        exporter = TraceExporter()
        bad = _trace(dialogue_act="", response="")
        assert exporter.export(bad) == []

    def test_export_all_filters_and_counts(self):
        exporter = TraceExporter()
        traces = [_trace(), _trace(dialogue_act="", response=""), _trace(trace_id="trace-2", dialogue_act="SILENCE")]
        examples = exporter.export_all(traces)
        assert len(examples) == 2

    def test_deterministic_example_ids(self):
        exporter = TraceExporter()
        a = exporter.export(_trace())[0]["example_id"]
        b = exporter.export(_trace())[0]["example_id"]
        assert a == b

    def test_trace_with_memories_uses_their_summaries(self):
        exporter = TraceExporter()
        t = _trace()
        # simulate richer memory records: retrieved_memories entries carry summaries
        t["retrieved_memories"] = [
            {"id": "mem-9", "summary": "Vano and Novi discussed camera recognition yesterday.", "confidence": 0.97},
        ]
        ex = exporter.export(t)[0]
        assert ex["situation"]["memory"][0]["summary"].startswith("Vano and Novi")
