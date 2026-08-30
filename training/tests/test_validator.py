"""Tests for dataset validation (plan 23 §8)."""

from __future__ import annotations

from training.collection.validator import DatasetValidator, ValidationReport, validate_example_ctx


def _ex(example_id: str = "e1", response: str = "The mug is on the desk.") -> dict:
    return {
        "example_id": example_id,
        "task": "memory_grounded_response",
        "situation": {
            "person": {"id": "person:owner_001", "name": "Vano", "relationship": "owner", "confidence": 0.98},
            "world": {"location": "office", "perception": ["mug on desk"]},
            "conversation": {"topic": "mug", "input_event": "where is the mug?"},
            "memory": [{"id": "mem-1", "summary": "mug was placed on desk", "confidence": 0.95}],
            "social": {},
        },
        "decision": {"dialogue_act": "RESPOND", "reason": "question_answered", "verbosity": "short"},
        "response": response,
    }


class TestContextCompleteness:
    def test_memory_must_exist_in_store(self):
        errors = validate_example_ctx(_ex(), memory_index={"mem-1"})
        assert errors == []

    def test_missing_memory_rejected(self):
        errors = validate_example_ctx(_ex(), memory_index=set())
        assert any("memory" in e for e in errors)

    def test_memory_summary_required_for_grounded_response(self):
        ex = _ex()
        ex["situation"]["memory"][0]["summary"] = ""
        errors = validate_example_ctx(ex, memory_index={"mem-1"})
        assert any("summary" in e for e in errors)


class TestVisualEvidence:
    def test_grounding_claims_need_perception_evidence(self):
        ex = _ex()
        ex["situation"]["world"]["perception"] = []
        errors = validate_example_ctx(ex, memory_index={"mem-1"})
        assert any("perception" in e or "visual" in e for e in errors)

    def test_unsupported_claim_rejected(self):
        # claims to have seen the mug, but no perception evidence
        ex = _ex(response="I saw the mug on the desk.")
        ex["situation"]["world"]["perception"] = []
        errors = validate_example_ctx(ex, memory_index={"mem-1"})
        assert any("claim" in e for e in errors)

    def test_claim_supported_by_evidence_ok(self):
        ex = _ex(response="I saw the mug on the desk.")
        errors = validate_example_ctx(ex, memory_index={"mem-1"})
        assert errors == []


class TestIdentity:
    def test_low_identity_confidence_rejected(self):
        ex = _ex()
        ex["situation"]["person"]["confidence"] = 0.4
        errors = validate_example_ctx(ex, memory_index={"mem-1"})
        assert any("confidence" in e for e in errors)

    def test_threshold_configurable(self):
        ex = _ex()
        ex["situation"]["person"]["confidence"] = 0.7
        assert validate_example_ctx(ex, memory_index={"mem-1"}, identity_threshold=0.9)
        assert validate_example_ctx(ex, memory_index={"mem-1"}, identity_threshold=0.5) == []


class TestOutcome:
    def test_outcome_required_when_task_requires_it(self):
        ex = _ex()
        ex["outcome"] = ""
        errors = validate_example_ctx(ex, memory_index={"mem-1"}, require_outcome=True)
        assert any("outcome" in e for e in errors)

    def test_known_outcome_accepted(self):
        ex = _ex()
        ex["outcome"] = "acknowledged"
        errors = validate_example_ctx(ex, memory_index={"mem-1"}, require_outcome=True)
        assert errors == []

    def test_unknown_outcome_value_rejected(self):
        ex = _ex()
        ex["outcome"] = "maybe??"
        errors = validate_example_ctx(ex, memory_index={"mem-1"}, require_outcome=True)
        assert any("outcome" in e for e in errors)


class TestPipeline:
    def test_validator_runs_stages_and_reports(self):
        v = DatasetValidator(memory_index={"mem-1"})
        good = _ex()
        bad_memory = _ex(example_id="e2")
        bad_memory["situation"]["memory"][0]["id"] = "ghost-mem"
        report = v.validate([good, bad_memory])
        assert isinstance(report, ValidationReport)
        assert len(report.accepted) == 1
        assert len(report.rejected) == 1
        assert report.rejected[0][0]["example_id"] == "e2"
        assert report.rejected[0][1]

    def test_malformed_non_dict_dropped(self):
        v = DatasetValidator()
        report = v.validate([_ex(), "garbage", None, 42])
        assert len(report.accepted) == 1
        assert report.rejected_count == 3

    def test_quality_scores_attached(self):
        v = DatasetValidator(memory_index={"mem-1"})
        report = v.validate([_ex()])
        assert "quality" in report.accepted[0]
        assert 0.0 <= report.accepted[0]["quality"] <= 1.0

    def test_empty_input(self):
        v = DatasetValidator()
        report = v.validate([])
        assert report.accepted == []
        assert report.rejected == []
