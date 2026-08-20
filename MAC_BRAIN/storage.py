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
    state                TEXT NOT NULL DEFAULT 'active',
    last_accessed_at     TEXT,
    expires_at           TEXT,
    purpose              TEXT,
    consent              INTEGER NOT NULL DEFAULT 1,
    deleted              INTEGER NOT NULL DEFAULT 0
);
"""

SCHEMA_MEMORY_FTS = """
CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
    memory_id UNINDEXED,
    content,
    entity_refs,
    memory_type,
    tokenize = 'unicode61'
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

SCHEMA_SOUL = """
CREATE TABLE IF NOT EXISTS soul (
    key         TEXT PRIMARY KEY,
    value       TEXT
);
"""

SCHEMA_RELATIONSHIPS = """
CREATE TABLE IF NOT EXISTS relationships (
    person     TEXT PRIMARY KEY,
    value      TEXT
);
"""

SCHEMA_LEXICON = """
CREATE TABLE IF NOT EXISTS lexicon (
    key         TEXT PRIMARY KEY,
    value       TEXT
);
"""

SCHEMA_PREFERENCES = """
CREATE TABLE IF NOT EXISTS preferences (
    key         TEXT PRIMARY KEY,
    value       TEXT
);
"""

SCHEMA_BELIEFS = """
CREATE TABLE IF NOT EXISTS beliefs (
    key         TEXT PRIMARY KEY,
    value       TEXT
);
"""

SCHEMA_EXPECTATIONS = """
CREATE TABLE IF NOT EXISTS expectations (
    key         TEXT PRIMARY KEY,
    value       TEXT
);
"""

SCHEMA_TEMPORAL = """
CREATE TABLE IF NOT EXISTS temporal (
    key         TEXT PRIMARY KEY,
    value       TEXT
);
"""

SCHEMA_FUSION = """
CREATE TABLE IF NOT EXISTS fusion (
    key         TEXT PRIMARY KEY,
    value       TEXT
);
"""

SCHEMA_VECTORS = """
CREATE TABLE IF NOT EXISTS vectors (
    memory_id   TEXT PRIMARY KEY,
    text        TEXT NOT NULL
);
"""

SCHEMA_BODY = """
CREATE TABLE IF NOT EXISTS body (
    key         TEXT PRIMARY KEY,
    value       TEXT
);
"""

SCHEMA_IDENTITY = """
CREATE TABLE IF NOT EXISTS identity (
    key         TEXT PRIMARY KEY,
    value       TEXT
);
"""

SCHEMA_KNOWLEDGE = """
CREATE TABLE IF NOT EXISTS knowledge (
    key         TEXT PRIMARY KEY,
    value       TEXT
);
"""

SCHEMA_PLANS = """
CREATE TABLE IF NOT EXISTS plans (
    key         TEXT PRIMARY KEY,
    value       TEXT
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

    def __init__(self, path: str | Path, embedder: Any | None = None) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        from .vector import EmbeddingIndex, HashingEmbedding

        self._embedder = embedder if embedder is not None else HashingEmbedding()
        self._embed_index = EmbeddingIndex(self._embedder)
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.executescript(SCHEMA_MEMORY)
        self._conn.executescript(SCHEMA_MEMORY_FTS)
        self._conn.executescript(SCHEMA_GOALS)
        self._conn.executescript(SCHEMA_SOUL)
        self._conn.executescript(SCHEMA_RELATIONSHIPS)
        self._conn.executescript(SCHEMA_LEXICON)
        self._conn.executescript(SCHEMA_PREFERENCES)
        self._conn.executescript(SCHEMA_BELIEFS)
        self._conn.executescript(SCHEMA_EXPECTATIONS)
        self._conn.executescript(SCHEMA_TEMPORAL)
        self._conn.executescript(SCHEMA_FUSION)
        self._conn.executescript(SCHEMA_VECTORS)
        self._conn.executescript(SCHEMA_BODY)
        self._conn.executescript(SCHEMA_IDENTITY)
        self._conn.executescript(SCHEMA_KNOWLEDGE)
        self._conn.executescript(SCHEMA_PLANS)
        self._migrate()
        # load persisted embeddings into the in-memory index
        for row in self._conn.execute("SELECT memory_id, text FROM vectors").fetchall():
            self._embed_index.add(row["memory_id"], row["text"])
        self._conn.commit()

    # ---- lifecycle ----
    def close(self) -> None:
        self._conn.commit()
        self._conn.close()

    def _migrate(self) -> None:
        """Add lifecycle columns to databases created before consolidation existed."""
        cols = {row[1] for row in self._conn.execute("PRAGMA table_info(memory_records)").fetchall()}
        if "state" not in cols:
            self._conn.execute("ALTER TABLE memory_records ADD COLUMN state TEXT NOT NULL DEFAULT 'active'")
        if "last_accessed_at" not in cols:
            self._conn.execute("ALTER TABLE memory_records ADD COLUMN last_accessed_at TEXT")
        if "expires_at" not in cols:
            self._conn.execute("ALTER TABLE memory_records ADD COLUMN expires_at TEXT")
        if "purpose" not in cols:
            self._conn.execute("ALTER TABLE memory_records ADD COLUMN purpose TEXT")
        if "consent" not in cols:
            self._conn.execute("ALTER TABLE memory_records ADD COLUMN consent INTEGER NOT NULL DEFAULT 1")

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
        cur = self._conn.execute(
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
        if cur.rowcount == 1:
            self._fts_insert(record)
            self._vector_insert(record)
        self._conn.commit()

    def _vector_text(self, record: MemoryRecord) -> str:
        text = json.dumps(record.content, sort_keys=True, default=str).lower()
        return text + " " + " ".join(record.entity_refs)

    def _vector_insert(self, record: MemoryRecord) -> None:
        text = self._vector_text(record)
        self._embed_index.add(record.memory_id, text)
        self._conn.execute("INSERT OR IGNORE INTO vectors (memory_id, text) VALUES (?, ?)", (record.memory_id, text))

    def _fts_document(self, record: MemoryRecord) -> str:
        text = json.dumps(record.content, sort_keys=True, default=str).lower()
        return text + " " + " ".join(record.entity_refs)

    def _fts_insert(self, record: MemoryRecord) -> None:
        self._conn.execute(
            "INSERT INTO memory_fts (memory_id, content, entity_refs, memory_type) VALUES (?,?,?,?)",
            (record.memory_id, self._fts_document(record), " ".join(record.entity_refs), record.memory_type),
        )

    def _row_to_record(self, row: sqlite3.Row) -> MemoryRecord:
        return self._to_record(row)

    def get(self, memory_id: str) -> MemoryRecord | None:
        row = self._conn.execute("SELECT * FROM memory_records WHERE memory_id=? AND deleted=0", (memory_id,)).fetchone()
        return self._to_record(row) if row else None

    def retrieve(self, query: str, *, entity: str | None = None, memory_type: str | None = None, limit: int = 5) -> tuple[MemoryRecord, ...]:
        if limit <= 0:
            return ()
        rows = self._conn.execute("SELECT * FROM memory_records WHERE deleted=0 AND state='active'").fetchall()
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

    def retrieve_indexed(self, query: str, *, entity: str | None = None, memory_type: str | None = None, limit: int = 5) -> tuple[MemoryRecord, ...]:
        """FTS5-backed retrieval: candidate memory_ids are found via MATCH, so only
        the (small) matched subset is fetched and JSON-parsed instead of a full scan.

        Falls back to the full-scan `retrieve` when there are no terms or the FTS
        engine rejects a query, so it is always safe to call.
        """
        if limit <= 0:
            return ()
        terms = [t.lower() for t in query.split() if t]
        if not terms:
            return self.retrieve(query, entity=entity, memory_type=memory_type, limit=limit)
        matcher = " OR ".join(f'"{t}"' for t in terms)
        try:
            wide = max(limit * 20, 50)
            candidates = self._conn.execute(
                "SELECT memory_id FROM memory_fts WHERE memory_fts MATCH ? ORDER BY rank LIMIT ?", (matcher, wide)
            ).fetchall()
        except Exception:
            return self.retrieve(query, entity=entity, memory_type=memory_type, limit=limit)
        scored: list[tuple[int, str, MemoryRecord]] = []
        for (memory_id,) in candidates:
            row = self._conn.execute("SELECT * FROM memory_records WHERE memory_id=? AND deleted=0 AND state='active'", (memory_id,)).fetchone()
            if row is None:
                continue
            record = self._to_record(row)
            if entity is not None and entity not in record.entity_refs:
                continue
            if memory_type is not None and memory_type != record.memory_type:
                continue
            haystack = self._fts_document(record)
            score = sum(1 for term in terms if term in haystack)
            if score == 0:
                continue
            scored.append((score, record.memory_id, record))
        scored.sort(key=lambda item: (-item[0], item[1]))
        return tuple(item[2] for item in scored[:limit])

    def retrieve_semantic(self, query: str, *, entity: str | None = None, memory_type: str | None = None, limit: int = 5) -> tuple[MemoryRecord, ...]:
        """Vector-similarity retrieval over the embedding index."""
        if limit <= 0:
            return ()
        candidates = self._embed_index.search(query, limit=max(limit * 20, 50))
        scored: list[tuple[float, MemoryRecord]] = []
        for (memory_id, score) in candidates:
            row = self._conn.execute("SELECT * FROM memory_records WHERE memory_id=? AND deleted=0 AND state='active'", (memory_id,)).fetchone()
            if row is None:
                continue
            record = self._to_record(row)
            if entity is not None and entity not in record.entity_refs:
                continue
            if memory_type is not None and memory_type != record.memory_type:
                continue
            scored.append((score, record))
        scored.sort(key=lambda item: -item[0])
        return tuple(item[1] for item in scored[:limit])

    def forget(self, memory_id: str) -> bool:
        cur = self._conn.execute("UPDATE memory_records SET deleted=1 WHERE memory_id=? AND deleted=0", (memory_id,))
        if cur.rowcount > 0:
            self._conn.execute("DELETE FROM memory_fts WHERE memory_id=?", (memory_id,))
            self._conn.execute("DELETE FROM vectors WHERE memory_id=?", (memory_id,))
            self._embed_index.remove(memory_id)
        self._conn.commit()
        return cur.rowcount > 0

    # ---- privacy / governance primitives ----
    def hard_delete(self, memory_id: str) -> bool:
        """Physically remove a record so deletion cannot be undone by recovery."""
        cur = self._conn.execute("DELETE FROM memory_records WHERE memory_id=?", (memory_id,))
        self._conn.execute("DELETE FROM memory_fts WHERE memory_id=?", (memory_id,))
        self._conn.execute("DELETE FROM vectors WHERE memory_id=?", (memory_id,))
        self._embed_index.remove(memory_id)
        self._conn.commit()
        return cur.rowcount > 0

    def update_memory(
        self,
        memory_id: str,
        *,
        content: Any = None,
        privacy_class: str | None = None,
        purpose: str | None = None,
        consent: bool | None = None,
        expires_at: str | None = None,
        revision_bump: bool = True,
    ) -> bool:
        row = self._conn.execute("SELECT revision FROM memory_records WHERE memory_id=? AND deleted=0", (memory_id,)).fetchone()
        if row is None:
            return False
        sets: list[str] = []
        params: list[Any] = []
        if content is not None:
            sets.append("content=?")
            params.append(_json(content))
        if privacy_class is not None:
            sets.append("privacy_class=?")
            params.append(privacy_class)
        if purpose is not None:
            sets.append("purpose=?")
            params.append(purpose)
        if consent is not None:
            sets.append("consent=?")
            params.append(int(bool(consent)))
        if expires_at is not None:
            sets.append("expires_at=?")
            params.append(expires_at)
        if revision_bump:
            sets.append("revision=revision+1")
        if not sets:
            return False
        params.append(memory_id)
        cur = self._conn.execute(f"UPDATE memory_records SET {', '.join(sets)} WHERE memory_id=? AND deleted=0", params)
        self._conn.commit()
        return cur.rowcount > 0

    def set_expiry(self, memory_id: str, expires_at: str) -> bool:
        return self.update_memory(memory_id, expires_at=expires_at)

    def records_by_entity(self, entity: str) -> list[dict[str, Any]]:
        rows = self._conn.execute("SELECT * FROM memory_records WHERE deleted=0 AND entity_refs LIKE ?", (f"%{entity}%",)).fetchall()
        return [self._row_to_state(row) for row in rows]

    def get_state_row(self, memory_id: str) -> dict[str, Any] | None:
        row = self._conn.execute("SELECT * FROM memory_records WHERE memory_id=? AND deleted=0", (memory_id,)).fetchone()
        return self._row_to_state(row) if row else None

    def dependent_ids(self, memory_id: str) -> tuple[str, ...]:
        rows = self._conn.execute("SELECT memory_id FROM memory_records WHERE deleted=0 AND dependency_refs LIKE ?", (f"%{memory_id}%",)).fetchall()
        return tuple(row["memory_id"] for row in rows)

    def count_by_class(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for row in self._conn.execute("SELECT privacy_class, COUNT(*) AS n FROM memory_records WHERE deleted=0 GROUP BY privacy_class").fetchall():
            counts[row["privacy_class"]] = int(row["n"])
        return counts

    def expired_ids(self, now: str) -> tuple[str, ...]:
        rows = self._conn.execute("SELECT memory_id FROM memory_records WHERE deleted=0 AND state='active' AND expires_at IS NOT NULL AND expires_at <= ?", (now,)).fetchall()
        return tuple(row["memory_id"] for row in rows)

    def _row_to_state(self, row: sqlite3.Row) -> dict[str, Any]:
        return {"memory_id": row["memory_id"], "memory_type": row["memory_type"], "content": _unjson(row["content"], ""), "privacy_class": row["privacy_class"], "purpose": row["purpose"], "consent": bool(row["consent"]), "expires_at": row["expires_at"], "state": row["state"], "dependency_refs": _unjson(row["dependency_refs"], ())}

    def gate_governance(self, memory_ids: Iterable[str]) -> dict[str, dict[str, Any]]:
        """Resolve privacy/purpose/consent for a set of ids in one query (retrieval gate)."""
        ids = tuple(memory_ids)
        if not ids:
            return {}
        marks = ",".join("?" for _ in ids)
        rows = self._conn.execute(f"SELECT memory_id, privacy_class, purpose, consent FROM memory_records WHERE deleted=0 AND memory_id IN ({marks})", ids).fetchall()
        return {r["memory_id"]: {"privacy_class": r["privacy_class"], "purpose": r["purpose"], "consent": bool(r["consent"])} for r in rows}

    @property
    def active_count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM memory_records WHERE deleted=0 AND state='active'").fetchone()
        return int(row[0])

    def get_state(self, memory_id: str) -> str | None:
        row = self._conn.execute("SELECT state FROM memory_records WHERE memory_id=? AND deleted=0", (memory_id,)).fetchone()
        return row["state"] if row else None

    @property
    def deleted_count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM memory_records WHERE deleted=1").fetchone()
        return int(row[0])

    # ---- lifecycle (consolidation) ----
    def active_rows(self) -> list[dict[str, Any]]:
        rows = self._conn.execute("SELECT * FROM memory_records WHERE deleted=0 AND state='active'").fetchall()
        return [
            {
                "record": self._to_record(row),
                "state": row["state"],
                "expires_at": row["expires_at"],
                "last_accessed_at": row["last_accessed_at"],
            }
            for row in rows
        ]

    def set_state(self, memory_id: str, state: str) -> bool:
        value = state.value if hasattr(state, "value") else state
        cur = self._conn.execute("UPDATE memory_records SET state=? WHERE memory_id=? AND deleted=0", (str(value), memory_id))
        self._conn.commit()
        return cur.rowcount > 0

    def set_confidence(self, memory_id: str, confidence: float) -> bool:
        cur = self._conn.execute("UPDATE memory_records SET confidence=? WHERE memory_id=? AND deleted=0", (float(confidence), memory_id))
        self._conn.commit()
        return cur.rowcount > 0

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

    # ---- soul ----
    def save_soul(self, snapshot: dict[str, Any]) -> None:
        self._conn.execute("INSERT OR REPLACE INTO soul (key, value) VALUES ('state', ?)", (_json(snapshot),))
        self._conn.commit()

    def load_soul(self) -> dict[str, Any] | None:
        row = self._conn.execute("SELECT value FROM soul WHERE key='state'").fetchone()
        if row is None:
            return None
        return _unjson(row["value"], None)

    # ---- relationships ----
    def save_relationships(self, rows: list[dict[str, Any]]) -> None:
        for row in rows:
            self._conn.execute(
                "INSERT OR REPLACE INTO relationships (person, value) VALUES (?, ?)",
                (row.get("person", ""), _json(row)),
            )
        self._conn.commit()

    def load_relationships(self) -> list[dict[str, Any]]:
        rows = self._conn.execute("SELECT value FROM relationships").fetchall()
        return [_unjson(row["value"], {}) for row in rows if row["value"]]

    # ---- lexicon ----
    def save_lexicon(self, rows: list[dict[str, Any]]) -> None:
        self._conn.execute("INSERT OR REPLACE INTO lexicon (key, value) VALUES ('state', ?)", (_json(rows),))
        self._conn.commit()

    def load_lexicon(self) -> list[dict[str, Any]]:
        row = self._conn.execute("SELECT value FROM lexicon WHERE key='state'").fetchone()
        if row is None:
            return []
        return _unjson(row["value"], [])

    # ---- preferences ----
    def save_preferences(self, rows: list[dict[str, Any]]) -> None:
        self._conn.execute("INSERT OR REPLACE INTO preferences (key, value) VALUES ('state', ?)", (_json(rows),))
        self._conn.commit()

    def load_preferences(self) -> list[dict[str, Any]]:
        row = self._conn.execute("SELECT value FROM preferences WHERE key='state'").fetchone()
        if row is None:
            return []
        return _unjson(row["value"], [])

    # ---- beliefs ----
    def save_beliefs(self, rows: list[dict[str, Any]]) -> None:
        self._conn.execute("INSERT OR REPLACE INTO beliefs (key, value) VALUES ('state', ?)", (_json(rows),))
        self._conn.commit()

    def load_beliefs(self) -> list[dict[str, Any]]:
        row = self._conn.execute("SELECT value FROM beliefs WHERE key='state'").fetchone()
        if row is None:
            return []
        return _unjson(row["value"], [])

    # ---- expectations ----
    def save_expectations(self, data: dict[str, Any]) -> None:
        self._conn.execute("INSERT OR REPLACE INTO expectations (key, value) VALUES ('state', ?)", (_json(data),))
        self._conn.commit()

    def load_expectations(self) -> dict[str, Any]:
        row = self._conn.execute("SELECT value FROM expectations WHERE key='state'").fetchone()
        if row is None:
            return {}
        return _unjson(row["value"], {})

    # ---- temporal ----
    def save_temporal(self, data: dict[str, Any]) -> None:
        self._conn.execute("INSERT OR REPLACE INTO temporal (key, value) VALUES ('state', ?)", (_json(data),))
        self._conn.commit()

    def load_temporal(self) -> dict[str, Any]:
        row = self._conn.execute("SELECT value FROM temporal WHERE key='state'").fetchone()
        if row is None:
            return {}
        return _unjson(row["value"], {})

    # ---- fusion ----
    def save_fusion(self, data: dict[str, Any]) -> None:
        self._conn.execute("INSERT OR REPLACE INTO fusion (key, value) VALUES ('state', ?)", (_json(data),))
        self._conn.commit()

    def load_fusion(self) -> dict[str, Any]:
        row = self._conn.execute("SELECT value FROM fusion WHERE key='state'").fetchone()
        if row is None:
            return {}
        return _unjson(row["value"], {})

    # ---- body pose ----
    def save_body(self, snapshot: dict[str, Any]) -> None:
        self._conn.execute("INSERT OR REPLACE INTO body (key, value) VALUES ('state', ?)", (_json(snapshot),))
        self._conn.commit()

    def load_body(self) -> dict[str, Any] | None:
        row = self._conn.execute("SELECT value FROM body WHERE key='state'").fetchone()
        if row is None:
            return None
        return _unjson(row["value"], None)

    # ---- identity ----
    def save_identity(self, snapshot: dict[str, Any]) -> None:
        self._conn.execute("INSERT OR REPLACE INTO identity (key, value) VALUES ('state', ?)", (_json(snapshot),))
        self._conn.commit()

    def load_identity(self) -> dict[str, Any] | None:
        row = self._conn.execute("SELECT value FROM identity WHERE key='state'").fetchone()
        if row is None:
            return None
        return _unjson(row["value"], None)

    # ---- knowledge graph ----
    def save_knowledge(self, snapshot: dict[str, Any]) -> None:
        self._conn.execute("INSERT OR REPLACE INTO knowledge (key, value) VALUES ('state', ?)", (_json(snapshot),))
        self._conn.commit()

    def load_knowledge(self) -> dict[str, Any] | None:
        row = self._conn.execute("SELECT value FROM knowledge WHERE key='state'").fetchone()
        if row is None:
            return None
        return _unjson(row["value"], None)

    # ---- plans ----
    def save_plans(self, data: list[dict[str, Any]]) -> None:
        self._conn.execute("INSERT OR REPLACE INTO plans (key, value) VALUES ('all', ?)", (_json(data),))
        self._conn.commit()

    def load_plans(self) -> list[dict[str, Any]]:
        row = self._conn.execute("SELECT value FROM plans WHERE key='all'").fetchone()
        if row is None:
            return []
        return _unjson(row["value"], [])

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
