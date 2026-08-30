"""Data-contract tests for the training workspace (plan 23, step 02)."""

from __future__ import annotations

import pytest

from training.schemas import (
    SCHEMA_VERSIONS,
    TRAINABLE_DIALOGUE_ACTS,
    Annotation,
    CanonicalExample,
    PolicyExample,
    RetrievalExample,
    validate_annotation,
    validate_example,
)


def _canonical(**overrides) -> dict:
    ex = {
        "example_id": "dlg-0001821",
        "task": "dialogue_realization",
        "situation": {
            "person": {"id": "person:owner_001", "name": "Vano", "relationship": "owner", "confidence": 0.98},
            "world": {"location": "office", "person_facing_novi": True},
            "conversation": {"topic": "camera integration", "open_threads": ["perception-to-world-model integration"]},
            "memory": [{"id": "mem-1821", "summary": "Previous discussion about camera integration", "confidence": 0.97}],
            "social": {"engaged": True, "interruptibility": 0.15},
        },
        "decision": {"dialogue_act": "CONTINUE", "reason": "unfinished_thread", "verbosity": "short"},
        "response": "There's one part of the camera side we haven't closed yet.",
    }
    ex.update(overrides)
    return ex


# ---------------------------------------------------------------------------
# CanonicalExample
# ---------------------------------------------------------------------------


class TestCanonicalExample:
    def test_plan_section5_example_roundtrips(self):
        ex = CanonicalExample.from_dict(_canonical())
        assert ex.example_id == "dlg-0001821"
        assert ex.decision.dialogue_act == "CONTINUE"
        assert ex.situation.person.id == "person:owner_001"
        assert validate_example(ex.to_dict()) == []

    def test_to_dict_matches_input(self):
        data = _canonical()
        assert CanonicalExample.from_dict(data).to_dict() == data

    def test_accepts_all_training_tasks(self):
        for task in ("natural_dialogue", "context_continuation", "clarification", "repair",
                     "memory_grounded_response", "proactive_comment", "social_greeting",
                     "silence_abstention", "dialogue_realization"):
            data = _canonical(task=task)
            assert validate_example(data) == [], task

    def test_rejects_unknown_task(self):
        errors = validate_example(_canonical(task="not_a_task"))
        assert any("task" in e for e in errors)

    def test_rejects_missing_example_id(self):
        errors = validate_example(_canonical(example_id=""))
        assert errors

    def test_identity_confidence_floor_not_schema_level(self):
        # Identity threshold is dataset-level policy (collection/validator.py);
        # the schema only rejects out-of-range probabilities.
        data = _canonical()
        data["situation"]["person"]["confidence"] = 0.5
        assert validate_example(data) == []

    def test_rejects_identity_confidence_out_of_range(self):
        data = _canonical()
        data["situation"]["person"]["confidence"] = 1.7
        errors = validate_example(data)
        assert any("confidence" in e for e in errors)

    def test_rejects_memory_without_existence_guarantee(self):
        data = _canonical()
        data["situation"]["memory"][0]["id"] = ""
        assert validate_example(data)

    def test_rejects_unknown_dialogue_act(self):
        data = _canonical()
        data["decision"]["dialogue_act"] = "TELEPORT"
        errors = validate_example(data)
        assert any("dialogue_act" in e for e in errors)

    def test_rejects_out_of_range_probabilities(self):
        data = _canonical()
        data["situation"]["social"]["interruptibility"] = 1.7
        assert validate_example(data)

    def test_rejects_missing_response_for_spoken_acts(self):
        data = _canonical()
        data["response"] = ""
        errors = validate_example(data)
        assert any("response" in e for e in errors)

    def test_silence_abstention_allows_empty_response(self):
        data = _canonical(task="silence_abstention", response="")
        data["decision"]["dialogue_act"] = "SILENCE"
        assert validate_example(data) == []

    def test_abstract_person_ids_required(self):
        data = _canonical()
        data["situation"]["person"]["id"] = "vano"  # raw name, not abstract
        errors = validate_example(data)
        assert any("abstract" in e or "person" in e for e in errors)


class TestActSets:
    def test_trainable_acts_match_plan_section12(self):
        assert frozenset({
            "SILENCE", "RESPOND", "ASK", "CLARIFY", "COMMENT", "CONTINUE",
            "FOLLOW_UP", "GREETING", "FAREWELL", "WARN", "SUGGEST",
        }) == TRAINABLE_DIALOGUE_ACTS

    def test_act_set_mirrors_brain_policy(self):
        # One source of truth: the deterministic brain's act vocabulary.
        from novi.brain.dialogue_policy import DialogueAct  # noqa: PLC0415

        brain_acts = {a.value for a in DialogueAct}
        assert brain_acts >= TRAINABLE_DIALOGUE_ACTS


class TestSchemaVersions:
    def test_plan_section29_versions(self):
        assert SCHEMA_VERSIONS["context"] == 3
        assert SCHEMA_VERSIONS["memory"] == 5
        assert SCHEMA_VERSIONS["world"] == 4
        assert SCHEMA_VERSIONS["dialogue"] == 3


# ---------------------------------------------------------------------------
# Annotation (§9)
# ---------------------------------------------------------------------------


class TestAnnotation:
    def test_plan_section9_example_roundtrips(self):
        ann = {
            "annotation_id": "ann-1",
            "example_id": "dlg-0001821",
            "reviewer_id": "reviewer:alice",
            "dialogue_act": "CLARIFY",
            "memory_relevance": 0.91,
            "initiative_appropriate": True,
            "grounding_correct": True,
            "naturalness": 5,
            "verbosity": 5,
            "certainty": 5,
        }
        a = Annotation.from_dict(ann)
        assert a.dialogue_act == "CLARIFY"
        assert a.memory_relevance == pytest.approx(0.91)
        assert validate_annotation(a.to_dict()) == []

    def test_rejects_review_scores_out_of_range(self):
        ann = {
            "annotation_id": "ann-1", "example_id": "e1", "reviewer_id": "r1",
            "dialogue_act": "CLARIFY", "naturalness": 9,
        }
        assert validate_annotation(ann)

    def test_rejects_probability_out_of_range(self):
        ann = {
            "annotation_id": "ann-1", "example_id": "e1", "reviewer_id": "r1",
            "dialogue_act": "CLARIFY", "memory_relevance": -0.2,
        }
        assert validate_annotation(ann)


# ---------------------------------------------------------------------------
# Policy / retrieval / grounding / preference records (§12–§14, §11)
# ---------------------------------------------------------------------------


class TestPolicyExample:
    def test_plan_section12_example(self):
        rec = {
            "example_id": "pol-1",
            "state": {
                "user_speaking": False, "known_person": True, "new_event": True,
                "event_salience": 0.86, "open_thread": True, "interruption_cost": 0.08,
            },
            "candidates": ["SILENCE", "GREETING", "CONTINUE"],
            "preferred": "CONTINUE",
        }
        assert validate_example(rec, kind="policy") == []
        p = PolicyExample.from_dict(rec)
        assert p.preferred == "CONTINUE"

    def test_preferred_must_be_in_candidates(self):
        rec = {
            "example_id": "pol-2", "state": {"known_person": True},
            "candidates": ["SILENCE"], "preferred": "GREETING",
        }
        assert validate_example(rec, kind="policy")

    def test_candidates_must_be_trainable_acts(self):
        rec = {
            "example_id": "pol-3", "state": {}, "candidates": ["SILENCE", "INITIATE"],
            "preferred": "SILENCE",
        }
        assert validate_example(rec, kind="policy")


class TestRetrievalExample:
    def test_plan_section13_example(self):
        rec = {
            "example_id": "ret-1",
            "query": "What did we decide about the camera?",
            "candidates": [
                "Vano bought a camera in March.",
                "Vano and Novi discussed camera recognition yesterday.",
                "Novi saw a camera in the kitchen.",
            ],
            "preferred": [1],
        }
        assert validate_example(rec, kind="retrieval") == []
        r = RetrievalExample.from_dict(rec)
        assert r.preferred == [1]

    def test_preferred_indices_within_bounds(self):
        rec = {
            "example_id": "ret-2", "query": "q",
            "candidates": ["a", "b"], "preferred": [0, 2],
        }
        assert validate_example(rec, kind="retrieval")

    def test_empty_candidates_rejected(self):
        rec = {"example_id": "ret-3", "query": "q", "candidates": [], "preferred": []}
        assert validate_example(rec, kind="retrieval")


class TestGroundingExample:
    def test_plan_section14_example(self):
        rec = {
            "example_id": "gr-1",
            "language": "Move that there.",
            "candidates": ["blue mug", "red book", "laptop"],
            "cues": {"gaze": "blue mug", "pointing": "blue mug"},
            "destination_candidates": ["shelf", "table"],
            "gesture": "shelf",
            "preferred": "move(blue_mug, shelf)",
        }
        assert validate_example(rec, kind="grounding") == []

    def test_preferred_candidate_must_exist(self):
        rec = {
            "example_id": "gr-2", "language": "that",
            "candidates": ["blue mug"], "cues": {},
            "preferred": "move(teapot, shelf)",
        }
        assert validate_example(rec, kind="grounding")


class TestPreferencePair:
    def test_plan_section11_example(self):
        pair = {
            "example_id": "pref-1",
            "category": "naturalness",
            "situation": {"person_present": True, "known_person": True},
            "response_a": "Hello Vano. It is nice to see you again.",
            "response_b": "Hey.",
            "preferred": "B",
        }
        assert validate_example(pair, kind="preference") == []

    def test_preferred_must_be_a_or_b(self):
        pair = {
            "example_id": "pref-2", "category": "brevity",
            "situation": {}, "response_a": "a", "response_b": "b", "preferred": "C",
        }
        assert validate_example(pair, kind="preference")


class TestKindDispatch:
    def test_unknown_kind_rejected(self):
        with pytest.raises(ValueError):
            validate_example({}, kind="telepathy")

    def test_canonical_default(self):
        assert validate_example(_canonical()) == []
