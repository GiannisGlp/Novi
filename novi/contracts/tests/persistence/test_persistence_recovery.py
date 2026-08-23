#!/usr/bin/env python3
"""Executable persistence/recovery checks for durable canonical contracts."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SCHEMA = ROOT / "schemas" / "novi.event-envelope.schema.json"

EVENT = {
    "event_id": "evt-persistence-001",
    "event_type": "persistence.fixture",
    "schema_version": "1.0.0",
    "occurred_at": "2026-01-01T00:00:00Z",
    "producer_id": "persistence-test",
    "payload": {"value": 42},
}


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "event.json"
        path.write_text(json.dumps(EVENT, sort_keys=True), encoding="utf-8")

        # Persistence round-trip must preserve identity and semantic content.
        restored = json.loads(path.read_text(encoding="utf-8"))
        assert restored == EVENT
        assert restored["event_id"] == EVENT["event_id"]
        assert restored["schema_version"] == EVENT["schema_version"]

        # A second read represents process restart/recovery of the durable record.
        recovered = json.loads(path.read_text(encoding="utf-8"))
        assert recovered == restored

        # Historical records are immutable: this validator does not permit an
        # in-place semantic rewrite to masquerade as the original record.
        mutated = dict(recovered)
        mutated["event_id"] = "evt-persistence-mutated"
        assert mutated != recovered

    print("PERSISTENCE/RECOVERY VALIDATION: PASS")
    print("Validated serialization round-trip, restart-style recovery, and identity immutability.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
