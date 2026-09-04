"""Dataset exporter tests. Socket-free, deterministic, tmp fixtures."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from novi.brain.conversation_dataset import SCHEMA, export_failure_dataset


def _envelope(scenario: str, result: str, turns: list[dict]) -> dict:
    return {"scenario": scenario, "result": result, "git_sha": "abc",
            "model": "deterministic", "configuration": {},
            "conversation": turns}


def _turn(idx: int, labels: list[str]) -> dict:
    return {"turn_index": idx, "user_text": f"q{idx}",
            "response_text": f"bad{idx}", "failure_labels": labels,
            "retrieved_context": {
                "trace": {"conversation": {"intent": {"intent": "MEMORY_QUERY"}}},
                "grounding": {"packet": {
                    "relevant_memories": [{"content": "You prefer dark."}],
                    "resolved_entities": {"it": "Tesla"}}}}}


class ExporterTests(unittest.TestCase):
    def _write(self, root: Path, name: str, envelope: dict) -> None:
        dest = root / "scenarios"
        dest.mkdir(parents=True, exist_ok=True)
        (dest / name).write_text(json.dumps(envelope), encoding="utf-8")

    def test_exports_fail_turns_only(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "A.json", _envelope(
                "A", "FAIL", [_turn(0, ["MEMORY_MISSED"]),
                              _turn(1, [])]))
            self._write(root, "B.json", _envelope(
                "B", "PASS", [_turn(0, [])]))
            summary = export_failure_dataset(root, root / "sft.jsonl")
            self.assertEqual(summary["scenarios_seen"], 2)
            self.assertEqual(summary["pairs"], 1)
            pair = json.loads((root / "sft.jsonl").read_text(
                encoding="utf-8").strip())
            self.assertEqual(pair["schema"], SCHEMA)
            self.assertEqual(pair["scenario"], "A")
            self.assertEqual(pair["failure_labels"], ["MEMORY_MISSED"])
            self.assertIn("dark", json.dumps(pair["ideal_skeleton"]))
            self.assertEqual(pair["ideal_skeleton"]["source"], "heuristic-v1")

    def test_referent_skeleton(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "C.json", _envelope(
                "C", "FAIL", [_turn(0, ["WRONG_REFERENT"])]))
            summary = export_failure_dataset(root, root / "sft.jsonl")
        self.assertEqual(summary["by_label"], {"WRONG_REFERENT": 1})

    def test_empty_dir(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            summary = export_failure_dataset(Path(tmp),
                                             Path(tmp) / "sft.jsonl")
        self.assertEqual(summary, {"scenarios_seen": 0, "pairs": 0,
                                   "by_label": {},
                                   "out": str(Path(tmp) / "sft.jsonl")})


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
