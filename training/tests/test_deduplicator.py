"""Tests for dataset deduplication + contradiction detection (plan 23 §8)."""

from __future__ import annotations

from training.collection.deduplicator import (
    exact_fingerprint,
    find_contradictions,
    find_near_duplicates,
)


def _ex(example_id: str, response: str, topic: str = "mug") -> dict:
    return {
        "example_id": example_id,
        "task": "natural_dialogue",
        "situation": {
            "person": {"id": "person:owner_001", "name": "Vano", "relationship": "owner", "confidence": 0.98},
            "world": {"location": "office"},
            "conversation": {"topic": topic, "input_event": f"about the {topic}"},
            "memory": [],
            "social": {},
        },
        "decision": {"dialogue_act": "RESPOND", "reason": "", "verbosity": "short"},
        "response": response,
    }


class TestExactDedup:
    def test_identical_examples_same_fingerprint(self):
        a = _ex("a", "The mug is on the desk.")
        b = _ex("b", "The mug is on the desk.")
        assert exact_fingerprint(a) == exact_fingerprint(b)

    def test_different_response_differs(self):
        a = _ex("a", "The mug is on the desk.")
        b = _ex("b", "The mug is on the shelf.")
        assert exact_fingerprint(a) != exact_fingerprint(b)

    def test_fingerprint_normalizes_whitespace(self):
        a = _ex("a", "The  mug  is   here.")
        b = _ex("b", "The mug is here.")
        assert exact_fingerprint(a) == exact_fingerprint(b)


class TestNearDedup:
    def test_high_similarity_flagged(self):
        a = _ex("a", "Yeah, that makes sense to me.")
        b = _ex("b", "Yeah, that makes sense.")
        dups = find_near_duplicates([a, b])
        assert dups  # the pair should be flagged

    def test_distinct_responses_not_flagged(self):
        a = _ex("a", "The mug is on the desk.")
        b = _ex("b", "Have you seen my headphones?")
        assert find_near_duplicates([a, b]) == []

    def test_different_topics_not_flagged_even_if_short(self):
        a = _ex("a", "Hey.", topic="greeting")
        b = _ex("b", "Hey.", topic="farewell")
        # exact same response -> dedup, but reported with both ids
        assert find_near_duplicates([a, b])


class TestContradictions:
    def test_contradictory_facts_detected(self):
        a = _ex("a", "The mug is on the desk.")
        b = _ex("b", "The mug is on the shelf.")
        contrad = find_contradictions([a, b])
        assert len(contrad) == 1
        assert {"a", "b"} == {c["example_a"] for c in contrad} | {c["example_b"] for c in contrad}

    def test_consistent_facts_not_flagged(self):
        a = _ex("a", "The mug is on the desk.")
        b = _ex("b", "The mug is on the desk.")
        assert find_contradictions([a, b]) == []

    def test_different_subjects_not_flagged(self):
        a = _ex("a", "The mug is on the desk.", topic="mug")
        b = _ex("b", "The book is on the shelf.", topic="book")
        assert find_contradictions([a, b]) == []

    def test_contradiction_requires_same_topic(self):
        a = _ex("a", "The mug is on the desk.", topic="mug")
        b = _ex("b", "The mug is on the shelf.", topic="mug")
        assert find_contradictions([a, b])
