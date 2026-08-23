"""RecognitionStore: durable memory for faces, voices, noises, places.

Doc 16 §3 — "Novi should save voices, noises, places, people and
recognize all these". SQLite-backed (stdlib sqlite3, WAL), same storage
philosophy as the brain's DurableMemoryStore but scoped to perception
enrollment records:

- FACE / VOICE embeddings  -> cosine nearest-match (biometric kinds,
  gated by the privacy switch);
- NOISE / PLACE descriptors -> JSON key/value overlap lookup
  (non-biometric; always allowed).

Every write carries mandatory provenance. Privacy transitions are
audited in-store.
"""

from __future__ import annotations

import enum
import json
import math
import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class RecognitionKind(str, enum.Enum):
    FACE = "face"
    VOICE = "voice"
    NOISE = "noise"
    PLACE = "place"


_BIOMETRIC = {RecognitionKind.FACE, RecognitionKind.VOICE}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS recognition_enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    label TEXT NOT NULL,
    person_id TEXT NOT NULL,
    embedding_json TEXT NOT NULL DEFAULT '[]',
    descriptor_json TEXT NOT NULL DEFAULT '{}',
    frame_ref TEXT NOT NULL DEFAULT '',
    provenance_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS recognition_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT ''
);
"""


def _now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


@dataclass(frozen=True)
class Match:
    kind: RecognitionKind
    label: str
    person_id: str
    similarity: float
    enrollment_id: int


class RecognitionStore:
    """Persistent recognition enrollments + matching, privacy-gated."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self._path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()
        self.audit_log: list[dict] = []
        self._privacy = True

    # -- privacy -------------------------------------------------------------

    @property
    def privacy_enabled(self) -> bool:
        return self._privacy

    def set_privacy(self, enabled: bool, *, reason: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO recognition_audit (kind, reason, created_at) VALUES (?, ?, ?)",
                ("privacy-enabled" if enabled else "privacy-disabled", reason, _now()),
            )
            self._conn.commit()
            self._privacy = enabled
            self.audit_log.append({"kind": "privacy-enabled" if enabled else "privacy-disabled", "reason": reason})

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # -- enrollment -----------------------------------------------------------

    def enroll(
        self,
        *,
        kind: RecognitionKind,
        label: str,
        embedding: list[float] | None = None,
        descriptor: dict[str, Any] | None = None,
        person_id: str | None = None,
        frame_id: str = "",
        provenance: dict[str, Any] | None = None,
    ) -> str:
        prov = provenance or {}
        if not prov and not frame_id:
            raise ValueError("recognition enrollment requires provenance (frame_id or provenance dict)")
        if kind in _BIOMETRIC and not self.privacy_enabled:
            raise PermissionError(f"{kind.value} enrollment refused: biometric processing disabled")
        pid = person_id or f"{kind.value}-{label.lower().replace(' ', '-')}"
        with self._lock:
            self._conn.execute(
                "INSERT INTO recognition_enrollments (kind, label, person_id, embedding_json, descriptor_json, frame_ref, provenance_json, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    kind.value,
                    label,
                    pid,
                    json.dumps(embedding or []),
                    json.dumps(descriptor or {}),
                    frame_id,
                    json.dumps({**prov, "frame_id": frame_id} if frame_id else prov),
                    _now(),
                ),
            )
            self._conn.commit()
        return pid

    # -- matching ---------------------------------------------------------------

    def match(self, kind: RecognitionKind, embedding: list[float], *, min_similarity: float = 0.90) -> Match | None:
        """Nearest enrolled neighbor above min_similarity (None otherwise)."""
        if kind in _BIOMETRIC and not self.privacy_enabled:
            raise PermissionError(f"{kind.value} matching refused: biometric processing disabled")
        best: Match | None = None
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, label, person_id, embedding_json FROM recognition_enrollments WHERE kind = ?",
                (kind.value,),
            ).fetchall()
        for rid, label, pid, emb_json in rows:
            sim = _cosine(embedding, json.loads(emb_json))
            if sim >= min_similarity and (best is None or sim > best.similarity):
                best = Match(kind=kind, label=label, person_id=pid, similarity=sim, enrollment_id=rid)
        return best

    def lookup_by_descriptor(self, kind: RecognitionKind, query: dict[str, Any]) -> list[dict]:
        """Descriptor overlap search: any stored key whose value matches."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, label, person_id, descriptor_json FROM recognition_enrollments WHERE kind = ?",
                (kind.value,),
            ).fetchall()
        hits: list[dict] = []
        for rid, label, pid, desc_json in rows:
            desc = json.loads(desc_json)
            overlap: dict[str, Any] = {}
            for k, v in query.items():
                if k not in desc:
                    continue
                dv = desc[k]
                if isinstance(dv, list) and isinstance(v, (list, tuple)):
                    missing = [x for x in v if x not in dv]
                    if not missing:  # query subset of stored
                        overlap[k] = v
                elif dv == v:
                    overlap[k] = v
            if overlap:
                hits.append({"id": rid, "label": label, "person_id": pid, "matched_on": overlap})
        return hits

    def all(self, kind: RecognitionKind | None = None) -> list[dict]:
        sql = "SELECT id, kind, label, person_id, created_at FROM recognition_enrollments"
        params: tuple = ()
        if kind is not None:
            sql += " WHERE kind = ?"
            params = (kind.value,)
        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
        return [{"id": r[0], "kind": r[1], "label": r[2], "person_id": r[3], "created_at": r[4]} for r in rows]
