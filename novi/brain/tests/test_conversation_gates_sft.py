"""Plan 03 Gap 7: quality gates and failure-driven training builders.

Deterministic, socket-free. Gates use synthetic baselines; SFT tests
use synthetic FAIL evidence and graded sessions. One compatibility
test proves gold rows satisfy the training backend's prompt contract.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from novi.brain.conversation_gates import evaluate_gates
from novi.brain.conversation_sft import build_candidates, build_gold, packet_to_situation


def _baseline(*, dimensions: dict[str, float], labels: dict[str, int],
              clarification: float | None = 0.0,
              overall: float = 1.0) -> dict[str, Any]:
    return {
        "git_sha": "x", "timestamp": "t", "model": "deterministic",
        "by_dimension": {dim: {"scenarios": 4, "passed": round(rate * 4),
                               "pass_rate": rate}
                         for dim, rate in dimensions.items()},
        "label_counts": dict(labels),
        "metrics": {} if clarification is None else {"clarification_rate": clarification},
        "totals": {"scenarios": 4, "passed": round(overall * 4), "pass_rate": overall},
    }


from typing import Any

_FULL_DIMS = {
    "Context continuity": 1.0, "Referent resolution": 1.0,
    "Memory retrieval": 1.0, "Perception grounding": 1.0,
    "Capability honesty": 1.0, "Correction handling": 1.0,
}


class GatesTests(unittest.TestCase):
    def test_clean_baseline_passes(self) -> None:
        verdict = evaluate_gates(_baseline(dimensions=dict(_FULL_DIMS), labels={}))
        self.assertEqual(verdict["status"], "PASS")
        self.assertTrue(all(g["status"] == "PASS" for g in verdict["gates"]))

    def test_critical_label_blocks(self) -> None:
        verdict = evaluate_gates(_baseline(
            dimensions=dict(_FULL_DIMS), labels={"MEMORY_HALLUCINATED": 1}))
        self.assertEqual(verdict["status"], "FAIL")
        critical = [g for g in verdict["gates"]
                    if "critical" in g["gate"]][0]
        self.assertEqual(critical["status"], "FAIL")

    def test_missing_dimension_unmeasured_not_failed(self) -> None:
        dims = dict(_FULL_DIMS)
        del dims["Perception grounding"]
        verdict = evaluate_gates(_baseline(dimensions=dims, labels={}))
        statuses = {g["gate"]: g["status"] for g in verdict["gates"]}
        self.assertEqual(statuses["perception grounding >= 0.95"], "UNMEASURED")
        self.assertEqual(verdict["status"], "PASS")

    def test_weak_dimension_fails(self) -> None:
        dims = dict(_FULL_DIMS)
        dims["Referent resolution"] = 0.5
        verdict = evaluate_gates(_baseline(dimensions=dims, labels={}, overall=0.75))
        self.assertEqual(verdict["status"], "FAIL")


class SftBuilderTests(unittest.TestCase):
    def _fail_evidence(self, tmp: str) -> Path:
        root = Path(tmp)
        (root / "scenarios").mkdir()
        envelope = {
            "scenario": "C-X", "title": "X", "dimension": "Memory retrieval",
            "result": "FAIL", "failure_labels": ["MEMORY_MISSED"],
            "conversation": [{
                "turn_index": 0, "user_text": "What do I like?",
                "response_text": "Not sure.", "result": "FAIL",
                "failure_labels": ["MEMORY_MISSED"],
                "retrieved_context": {
                    "trace": {"conversation": {
                        "intent": {"intent": "MEMORY_QUERY"},
                        "response_goal": {"goal": "ADMIT_UNCERTAINTY",
                                         "reason": "no evidence"},
                    }},
                    "grounding": {"packet": {
                        "current_turn": "What do I like?",
                        "anchor": {"topic": ""},
                        "resolved_entities": {},
                        "relevant_memories": [
                            {"content": "jazz it is", "confidence": 0.9,
                             "source": "store"}],
                        "world_context": [],
                        "uncertainty": ["no reliable memory found"],
                        "social_context": {},
                        "identity_context": {},
                    }},
                },
            }],
        }
        (root / "scenarios" / "C-X.json").write_text(json.dumps(envelope))
        return root

    def test_candidates_flagged_not_trainable(self) -> None:
        with TemporaryDirectory() as tmp:
            rows = build_candidates(self._fail_evidence(tmp))
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertTrue(row["needs_review"])
        self.assertTrue(row["synthetic"])
        self.assertEqual(row["bad_response"], "Not sure.")
        self.assertIn("situation", row)
        self.assertIn("decision", row)

    def test_gold_requires_human_ideal(self) -> None:
        session = {"graded_turns": [
            {"conversation_id": "s", "turn_id": 0, "user_text": "Range?",
             "response": "Dunno.", "grade": "FAIL",
             "what_instead": "The Model Y gets 330 miles.",
             "intent": {"intent": "INFORMATION_REQUEST"}},
            {"conversation_id": "s", "turn_id": 1, "user_text": "Hi.",
             "response": "Hey.", "grade": "PASS", "what_instead": ""},
            {"conversation_id": "s", "turn_id": 2, "user_text": "Range?",
             "response": "Dunno.", "grade": "MAJOR ISSUE", "what_instead": ""},
        ]}
        sft, dpo = build_gold(session)
        self.assertEqual(len(sft), 1)
        self.assertEqual(len(dpo), 1)
        self.assertEqual(sft[0]["preferred_response"], "The Model Y gets 330 miles.")
        self.assertEqual(dpo[0]["preferred"], "b")
        self.assertEqual(dpo[0]["response_a"], "Dunno.")
        self.assertTrue(sft[0]["reviewed"])
        self.assertFalse(sft[0]["synthetic"])

    def test_gold_rows_satisfy_backend_prompt_contract(self) -> None:
        from training.training.common import prompt_for

        session = {"graded_turns": [
            {"conversation_id": "s", "turn_id": 0, "user_text": "Range?",
             "response": "Dunno.", "grade": "FAIL",
             "what_instead": "The Model Y gets 330 miles.",
             "intent": {"intent": "INFORMATION_REQUEST"}},
        ]}
        sft, dpo = build_gold(session)
        prompt = prompt_for(sft[0])
        self.assertIn("Range?", prompt)
        self.assertIn("ANSWER_DIRECTLY", prompt)

    def test_packet_to_situation_shape(self) -> None:
        situation = packet_to_situation({
            "current_turn": "What is on the table?",
            "anchor": {"topic": "lunch"},
            "resolved_entities": {"the table": "table"},
            "relevant_memories": [{"content": "m", "confidence": 0.5, "source": "s"}],
            "world_context": [{"text": "cup"}],
            "uncertainty": ["u"],
            "social_context": {"e": 1},
            "identity_context": {"addressee": "vano"},
        })
        for key in ("person", "world", "conversation", "memory", "social"):
            self.assertIn(key, situation)
        self.assertEqual(situation["person"]["id"], "vano")
        self.assertEqual(situation["memory"][0]["summary"], "m")


if __name__ == "__main__":
    unittest.main()
