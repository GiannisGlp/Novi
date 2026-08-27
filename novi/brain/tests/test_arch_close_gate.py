import json
import tempfile
import unittest
from pathlib import Path

from novi.brain.benchmarks.arch_close_003_gate import run


class ArchClose003GateTests(unittest.TestCase):
    def test_gate_passes_correctness_and_produces_adopt(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "gate.json"
            run(out)
            self.assertTrue(out.exists())
            data = json.loads(out.read_text())
            self.assertEqual(data["decision"], "ADOPT")
            self.assertTrue(data["correctness_gate"]["passed"])
            checks = {c["check"]: c["result"] for c in data["correctness_gate"]["checks"]}
            self.assertTrue(all(v == "PASS" for v in checks.values()))
            # mandatory recovery checks all present
            for name in (
                "commit_reopen_persistence",
                "uncommitted_rollback",
                "duplicate_idempotent",
                "checkpoint_reopen_integrity",
                "backup_restore",
                "malformed_migration_no_corruption",
            ):
                self.assertIn(name, checks)
            self.assertEqual(data["benchmark"]["journal_mode"], "wal")
            self.assertGreater(data["benchmark"]["writes"], 0)


if __name__ == "__main__":
    unittest.main()
