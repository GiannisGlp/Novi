"""Plan 03 Gap 5: pairwise comparison and human session grading.

Deterministic, socket-free. Pairwise tests use small synthetic evidence
dirs; grading tests use synthetic interaction JSONL.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from novi.brain.conversation_grade import (
    GRADES,
    ROOT_LAYERS,
    apply_grades,
    grade_template,
    load_log_records,
)
from novi.brain.conversation_pairwise import (
    RATING_QUESTIONS,
    collect_ratings,
    compare_runs,
    ratings_template,
)


def _envelope(scenario: str, *, result: str, responses: list[str],
              labels: list[list[str]] | None = None,
              git_sha: str = "abc") -> dict[str, Any]:
    turns = []
    for index, text in enumerate(responses):
        turns.append({
            "scenario_id": scenario,
            "turn_index": index,
            "user_text": f"q{index}",
            "response_text": text,
            "result": "FAIL" if (labels or [[]])[index] else "PASS",
            "failure_labels": (labels or [[]])[index]
            if labels and index < len(labels) else [],
        })
    return {"schema": "conversation-acceptance/v1", "scenario": scenario,
            "title": scenario, "dimension": "Context continuity",
            "git_sha": git_sha, "conversation": turns, "result": result,
            "failure_labels": []}


class PairwiseTests(unittest.TestCase):
    def _dirs(self, tmp: str) -> tuple[Path, Path]:
        old = Path(tmp) / "old"
        new = Path(tmp) / "new"
        (old / "scenarios").mkdir(parents=True)
        (new / "scenarios").mkdir(parents=True)
        (old / "baseline.json").write_text(json.dumps(
            {"git_sha": "old-sha", "timestamp": "t0", "model": "deterministic",
             "totals": {"scenarios": 2, "passed": 1}}))
        (new / "baseline.json").write_text(json.dumps(
            {"git_sha": "new-sha", "timestamp": "t1", "model": "deterministic",
             "totals": {"scenarios": 2, "passed": 2}}))
        (old / "scenarios" / "C-A.json").write_text(json.dumps(
            _envelope("C-A", result="FAIL", responses=["dunno"],
                      labels=[["MEMORY_MISSED"]])))
        (new / "scenarios" / "C-A.json").write_text(json.dumps(
            _envelope("C-A", result="PASS", responses=["jazz it is"])))
        (old / "scenarios" / "C-B.json").write_text(json.dumps(
            _envelope("C-B", result="PASS", responses=["same here"])))
        (new / "scenarios" / "C-B.json").write_text(json.dumps(
            _envelope("C-B", result="PASS", responses=["same here"])))
        return old, new

    def test_fixed_and_stable_detected(self) -> None:
        with TemporaryDirectory() as tmp:
            old, new = self._dirs(tmp)
            report = compare_runs(old, new)
        self.assertEqual(report["totals"]["fixed"], 1)
        self.assertEqual(report["totals"]["stable"], 1)
        self.assertEqual(report["old"]["git_sha"], "old-sha")
        self.assertEqual(report["new"]["git_sha"], "new-sha")

    def test_unpaired_flagged(self) -> None:
        with TemporaryDirectory() as tmp:
            old, new = self._dirs(tmp)
            (new / "scenarios" / "C-NEW.json").write_text(json.dumps(
                _envelope("C-NEW", result="PASS", responses=["hi"])))
            report = compare_runs(old, new)
        self.assertEqual(report["totals"]["unpaired"], 1)

    def test_template_has_phase36_questions(self) -> None:
        with TemporaryDirectory() as tmp:
            old, new = self._dirs(tmp)
            rows = ratings_template(compare_runs(old, new))
        self.assertEqual(len(rows), 2)
        for key in ("understood", "trust", "preference", "what_instead"):
            self.assertIn(key, rows[0]["ratings"])
        self.assertIn("preference", RATING_QUESTIONS)

    def test_collect_counts_preferences(self) -> None:
        with TemporaryDirectory() as tmp:
            old, new = self._dirs(tmp)
            rows = ratings_template(compare_runs(old, new))
        rows[0]["ratings"].update({"preference": "new", "trust": 5, "natural": 4})
        rows[1]["ratings"].update({"preference": "tie", "trust": 3})
        summary = collect_ratings(rows)
        self.assertEqual(summary["answered"], 2)
        self.assertEqual(summary["preferences"], {"new": 1, "tie": 1})
        self.assertEqual(summary["mean_scores"]["trust"], 4.0)
        self.assertNotIn("made_repeat", summary["mean_scores"])


class GradeTests(unittest.TestCase):
    def _log(self, tmp: str) -> Path:
        path = Path(tmp) / "session.jsonl"
        records = [
            {"conversation_id": "s1", "turn_id": 0, "raw_input": "Hi.",
             "response": "Hey.", "reply_source": "fallback",
             "intent": {"intent": "GREETING"}},
            {"conversation_id": "s1", "turn_id": 1, "raw_input": "Range?",
             "response": "330 miles.", "reply_source": "fallback",
             "intent": {"intent": "INFORMATION_REQUEST"}},
        ]
        path.write_text("\n".join(json.dumps(r) for r in records) + "\n")
        return path

    def test_template_and_apply_roundtrip(self) -> None:
        with TemporaryDirectory() as tmp:
            log = self._log(tmp)
            records = load_log_records(log)
            self.assertEqual(len(records), 2)
            rows = grade_template(records)
            self.assertIsNone(rows[0]["grade"])
            rows[0].update({"grade": "PASS"})
            rows[1].update({"grade": "MAJOR ISSUE",
                            "failure_labels": ["WRONG_REFERENT"],
                            "root_cause": "referent resolution",
                            "what_instead": "Answer about the Model Y."})
            evidence = apply_grades(records, rows)
        self.assertEqual(evidence["turns"], 2)
        self.assertEqual(evidence["graded"], 2)
        self.assertEqual(evidence["grade_counts"]["MAJOR ISSUE"], 1)
        self.assertEqual(evidence["root_cause_counts"]["referent resolution"], 1)
        self.assertEqual(evidence["unknown_root_causes"], [])

    def test_duplicate_keys_match_in_order(self) -> None:
        # An appended log repeats keys; the first grade hits the first
        # occurrence instead of the last row silently winning.
        with TemporaryDirectory() as tmp:
            log = self._log(tmp)
            records = load_log_records(log)
            doubled = records + records
            rows = grade_template(doubled)
            rows[0].update({"grade": "FAIL", "root_cause": "intent"})
            rows[2].update({"grade": "PASS"})
            evidence = apply_grades(doubled, rows)
        first = [t for t in evidence["graded_turns"]
                 if (t["conversation_id"], t["turn_id"]) == ("s1", 0)]
        self.assertEqual([t["grade"] for t in first], ["FAIL", "PASS"])

    def test_unknown_root_flagged_not_dropped(self) -> None:
        with TemporaryDirectory() as tmp:
            log = self._log(tmp)
            records = load_log_records(log)
            rows = grade_template(records)
            rows[0].update({"grade": "FAIL", "root_cause": "vibes"})
            evidence = apply_grades(records, rows)
        self.assertEqual(evidence["unknown_root_causes"], ["vibes"])
        self.assertIn("FAIL", evidence["grade_counts"])

    def test_grades_constrained_to_scale(self) -> None:
        self.assertIn("PASS", GRADES)
        self.assertIn("FAIL", GRADES)
        self.assertIn("referent resolution", ROOT_LAYERS)
        self.assertIn("LLM generation", ROOT_LAYERS)


if __name__ == "__main__":
    unittest.main()
