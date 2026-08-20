"""Stage-1 durable storage for the Mac Brain.

Implements the ADR-DATA-001 candidate baseline (SQLite, WAL, local, single-node)
as a persistence layer *below* the memory/autonomy semantics. It persists
``MemoryRecord`` objects and bounded goal history so state survives process
restarts. The store is a durable mechanism only — it does not own cognition,
memory semantics, or authorization.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable

from brain.b1_memory import MemoryAdmission, MemoryRecord, DeterministicMemoryManager, validate_contract, utc_now

SCHEMA_MEMORY = """
CREATE TABLE IF NOT EXISTS memory_records (
    memory_id            TEXT PRIMARY KEY,
    memory_type          TEXT NOT NULL,
    created_at           TEXT NOT NULL,
    content              TEXT NOT NULL,
    confidence           REAL NOT NULL,
    verification_status  TEXT NOT NULL,
    privacy_class        TEXT NOT NULL,
    revision             INTEGER NOT NULL,
    provenance           TEXT,
    event_refs           TEXT,
    entity_refs          TEXT,
    semantic_index_ref   TEXT,
    temporal_context     TEXT,
    spatial_context      TEXT,
    retention_policy_ref TEXT,
    dependency_refs      TEXT,
    deleted              INTEGER NOT NULL DEFAULT 0
);
"""

SCHEMA_GOALS = """
CREATE TABLE IF NOT EXISTS goals (
    goal_id         TEXT PRIMARY KEY,
    kind            TEXT NOT NULL,
    target          TEXT,
    priority        REAL,
    max_steps       INTEGER,
    created_cycle   INTEGER,
    status          TEXT,
    steps_taken     INTEGER
);
"""


def _json(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _unjson(value: str | None, default: Any) -> Any:
    if value is None:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


class DurableMemoryStore:
    """SQLite-backed store exposing the same memory surface as ``DeterministicMemoryManager``."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.executescript(SCHEMA_MEMORY)
        self._conn.executescript(SCHEMA_GOALS)
        self._conn.commit()

    # ---- lifecycle ----
    def close(self) -> None:
        self._conn.commit()
        self._conn.close()

    # ---- memory ----
    def admit(
        self,
        *,
        memory_type: str,
        content: Any,
        confidence: float,
        verification_status: str,
        privacy_class: str,
        provenance: Any,
        event_refs: Iterable[str] = (),
        entity_refs: Iterable[str] = (),
        dependency_refs: Iterable[str] = (),
        temporal_context: Any = None,
        spatial_context: Any = None,
        retention_policy_ref: str | None = None,
    ) -> MemoryAdmission:
        if not 0.0 <= confidence <= 1.0:
            return MemoryAdmission(False, None, "DISCARD", "confidence_out_of_range")
        if provenance in (None, {}, ""):
            return MemoryAdmission(False, None, "DISCARD", "missing_provenance")
        if content in (None, ""):
            return MemoryAdmission(False, None, "DISCARD", "empty_content")

        record = MemoryRecord(
            memory_id="",
            memory_type=memory_type,
            created_at=utc_now(),
            content=content,
            confidence=confidence,
            verification_status=verification_status,
            privacy_class=privacy_class,
            revision=0,
            provenance=provenance,
            event_refs=tuple(event_refs),
            entity_refs=tuple(entity_refs),
            temporal_context=temporal_context,
            spatial_context=spatial_context,
            retention_policy_ref=retention_policy_ref,
            dependency_refs=tuple(dependency_refs),
        )
        memory_id = DeterministicMemoryManager._identity({k: v for k, v in record.as_contract().items() if k != "created_at" and k != "memory_id"})
        record = MemoryRecord(memory_id=memory_id, **{k: v for k, v in record.as_contract().items() if k != "memory_id"})
        validate_contract("novi.memory-record", record.as_contract())

        exists = self.get(memory_id)
        if exists is not None:
            return MemoryAdmission(True, memory_id, "KEEP_EXISTING", "duplicate_admission")
        self._insert(record)
        return MemoryAdmission(True, memory_id, "STORE_EPISODE", "admitted")

    def _insert(self, record: MemoryRecord) -> None:
        self._conn.execute(
            """INSERT OR IGNORE INTO memory_records
               (memory_id, memory_type, created_at, content, confidence, verification_status,
                privacy_class, revision, provenance, event_refs, entity_refs,
                semantic_index_ref, temporal_context, spatial_context, retention_policy_ref,
                dependency_refs, deleted)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)""",
            (
                record.memory_id,
                record.memory_type,
                record.created_at,
                _json(record.content),
                record.confidence,
                record.verification_status,
                record.privacy_class,
                record.revision,
                _json(record.provenance),
                _json(list(record.event_refs)),
                _json(list(record.entity_refs)),
                record.semantic_index_ref,
                _json(record.temporal_context),
                _json(record.spatial_context),
                record.retention_policy_ref,
                _json(list(record.dependency_refs)),
            ),
        )
        self._conn.commit()

    def _row_to_record(self, row: sqlite3.Row) -> MemoryRecord:
        return self._to_record(row)

    def get(self, memory_id: str) -> MemoryRecord | None:
        row = self._conn.execute("SELECT * FROM memory_records WHERE memory_id=? AND deleted=0", (memory_id,)).fetchone()
        return self._to_record(row) if row else None

    def retrieve(self, query: str, *, entity: str | None = None, memory_type: str | None = None, limit: int = 5) -> tuple[MemoryRecord, ...]:
        if limit <= 0:
            return ()
        rows = self._conn.execute("SELECT * FROM memory_records WHERE deleted=0").fetchall()
        terms = {term.lower() for term in query.split() if term}
        scored: list[tuple[int, str, MemoryRecord]] = []
        for row in rows:
            record = self._to_record(row)
            if entity is not None and entity not in record.entity_refs:
                continue
            if memory_type is not None and memory_type != record.memory_type:
                continue
            haystack = json.dumps(record.content, sort_keys=True, default=str).lower()
            haystack += " " + " ".join(record.entity_refs)
            score = sum(1 for term in terms if term in haystack)
            if terms and score == 0:
                continue
            scored.append((score, record.memory_id, record))
        scored.sort(key=lambda item: (-item[0], item[1]))
        return tuple(item[2] for item in scored[:limit])

    def forget(self, memory_id: str) -> bool:
        cur = self._conn.execute("UPDATE memory_records SET deleted=1 WHERE memory_id=? AND deleted=0", (memory_id,))
        self._conn.commit()
        return cur.rowcount > 0

    @property
    def active_count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM memory_records WHERE deleted=0").fetchone()
        return int(row[0])

    @property
    def deleted_count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM memory_records WHERE deleted=1").fetchone()
        return int(row[0])

    # ---- goals ----
    def save_goal(self, *, goal_id: str, kind: str, target: Any, priority: float, max_steps: int, created_cycle: int, status: str, steps_taken: int) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO goals (goal_id, kind, target, priority, max_steps, created_cycle, status, steps_taken) VALUES (?,?,?,?,?,?,?,?)",
            (goal_id, kind, _json(target), priority, max_steps, created_cycle, status, steps_taken),
        )
        self._conn.commit()

    def goals(self) -> tuple[dict[str, Any], ...]:
        rows = self._conn.execute("SELECT * FROM goals").fetchall()
        return tuple(
            {
                "goal_id": row[0],
                "kind": row[1],
                "target": _unjson(row[2], row[2]),
                "priority": row[3],
                "max_steps": row[4],
                "created_cycle": row[5],
                "status": row[6],
                "steps_taken": row[7],
            }
            for row in rows
        )

    def _to_record(self, row: sqlite3.Row) -> MemoryRecord:
        return MemoryRecord(
            memory_id=row["memory_id"],
            memory_type=row["memory_type"],
            created_at=row["created_at"],
            content=_unjson(row["content"], ""),
            confidence=row["confidence"],
            verification_status=row["verification_status"],
            privacy_class=row["privacy_class"],
            revision=row["revision"],
            provenance=_unjson(row["provenance"], {}),
            event_refs=tuple(_unjson(row["event_refs"], [])),
            entity_refs=tuple(_unjson(row["entity_refs"], [])),
            semantic_index_ref=row["semantic_index_ref"],
            temporal_context=_unjson(row["temporal_context"], None),
            spatial_context=_unjson(row["spatial_context"], None),
            retention_policy_ref=row["retention_policy_ref"],
            dependency_refs=tuple(_unjson(row["dependency_refs"], [])),
        )
