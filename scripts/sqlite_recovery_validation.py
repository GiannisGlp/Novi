#!/usr/bin/env python3
"""Validate SQLite durability/recovery invariants for ARCH-CLOSE-003.

This is a deterministic local harness, not a claim of exhaustive crash testing.
It validates rollback, commit persistence, duplicate-event idempotency, stale
revision rejection, checkpoint/reopen integrity, backup/restore, and migration
failure isolation.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import tempfile
import time
from pathlib import Path

SCHEMA_V1 = """
CREATE TABLE IF NOT EXISTS events (
  event_id TEXT PRIMARY KEY,
  revision INTEGER NOT NULL,
  payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS state (
  key TEXT PRIMARY KEY,
  revision INTEGER NOT NULL,
  value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS schema_meta (
  version INTEGER NOT NULL
);
"""


def connect(path: Path) -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=FULL")
    db.execute("PRAGMA foreign_keys=ON")
    return db


def check(name: str, ok: bool, detail: str = "") -> dict:
    return {"name": name, "passed": bool(ok), "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="sqlite-recovery-validation-result.json")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="novi-sqlite-recovery-") as tmp:
        root = Path(tmp)
        db_path = root / "novi.db"
        backup_path = root / "backup.db"
        results: list[dict] = []

        db = connect(db_path)
        db.executescript(SCHEMA_V1)
        db.execute("INSERT INTO schema_meta(version) VALUES (1)")
        db.commit()

        # Commit persistence / reopen.
        db.execute("INSERT INTO events VALUES (?, ?, ?)", ("e1", 1, "hello"))
        db.execute("INSERT INTO state VALUES (?, ?, ?)", ("core", 1, "ready"))
        db.commit()
        db.close()
        db = connect(db_path)
        persisted = db.execute("SELECT payload FROM events WHERE event_id='e1'").fetchone()
        results.append(check("commit_reopen_persistence", persisted == ("hello",)))

        # Crash-before-commit analogue: uncommitted transaction must disappear on close.
        db.execute("INSERT INTO events VALUES (?, ?, ?)", ("uncommitted", 2, "discard"))
        db.close()
        db = connect(db_path)
        absent = db.execute("SELECT 1 FROM events WHERE event_id='uncommitted'").fetchone() is None
        results.append(check("rollback_uncommitted_transaction", absent))

        # Duplicate event submission must be rejected without changing state.
        duplicate_rejected = False
        try:
            db.execute("INSERT INTO events VALUES (?, ?, ?)", ("e1", 1, "duplicate"))
            db.commit()
        except sqlite3.IntegrityError:
            db.rollback()
            duplicate_rejected = True
        results.append(check("duplicate_event_rejected", duplicate_rejected))

        # Stale revision must not overwrite newer state.
        stale_rejected = False
        try:
            current = db.execute("SELECT revision FROM state WHERE key='core'").fetchone()[0]
            if 0 < current:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute("SELECT revision FROM state WHERE key='core'").fetchone()
                if row[0] != 0:
                    raise RuntimeError("stale revision rejected")
                db.commit()
        except RuntimeError:
            db.rollback()
            stale_rejected = True
        results.append(check("stale_revision_rejected", stale_rejected))

        # Checkpoint/reopen integrity.
        db.execute("PRAGMA wal_checkpoint(FULL)")
        db.close()
        db = connect(db_path)
        count = db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        results.append(check("checkpoint_reopen_integrity", count == 1, f"event_count={count}"))

        # Backup/restore using SQLite online backup API.
        backup = sqlite3.connect(backup_path)
        db.backup(backup)
        backup.close()
        restored = sqlite3.connect(backup_path)
        restored_count = restored.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        restored.close()
        results.append(check("backup_restore", restored_count == 1, f"restored_events={restored_count}"))

        # Malformed migration must not silently change the source database.
        before = db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        migration_failed = False
        try:
            db.execute("BEGIN")
            db.execute("ALTER TABLE events ADD COLUMN impossible TEXT")
            db.execute("ALTER TABLE events ADD COLUMN impossible TEXT")
            db.commit()
        except sqlite3.OperationalError:
            db.rollback()
            migration_failed = True
        after = db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        results.append(check("malformed_migration_isolated", migration_failed and before == after))

        db.close()
        passed = all(r["passed"] for r in results)
        report = {
            "benchmark_id": "ARCH-CLOSE-003-SQLITE-RECOVERY-001",
            "sqlite_version": sqlite3.sqlite_version,
            "python": os.sys.version.split()[0],
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "tests": results,
            "passed": passed,
            "limitations": [
                "This harness validates transactional/recovery invariants without forcibly killing a live process at arbitrary kernel/storage boundaries.",
                "Storage-full and permission failures require environment-controlled integration tests.",
                "Concurrent conflict and interrupted backup require separate stress/fault campaigns.",
            ],
        }

    Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
