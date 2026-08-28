"""ObservationRecorder: durable spatial/sighting memory (recognition plan §4).

The recognition pipeline identifies WHAT (face/object instance) — this store
remembers WHERE and WHEN it was seen, and keeps the perceptual vector saved
at-sight. One canonical SQLite file (``novi/data/novi.db``, WAL) shared with
RecognitionStore / DurableMemoryStore — never a second database.

Coalescing rule (plan §4.2): repeated sightings of the same entity in the
same place collapse into ONE row whose last-seen advances, so continuous
camera observation cannot grow the table unboundedly; a move to a new place
opens a second row (which then answers "where did I last see X").

Privacy (plan §4.5): face sightings are biometric — refused while the privacy
switch is off (audited); object sightings are non-biometric, always allowed.
Provenance is mandatory on every write, mirroring ``RecognitionStore``.
"""

from __future__ import annotations

import json
import math
import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .recognition_store import RecognitionKind

_BIOMETRIC = {RecognitionKind.FACE.value, RecognitionKind.VOICE.value}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS observation_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    obs_kind TEXT NOT NULL,
    entity_ref TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT '',
    label TEXT NOT NULL DEFAULT '',
    place TEXT NOT NULL DEFAULT '',
    bbox_json TEXT NOT NULL DEFAULT '[]',
    temporal_at TEXT NOT NULL DEFAULT '',
    frame_ref TEXT NOT NULL DEFAULT '',
    vector_json TEXT NOT NULL DEFAULT '[]',
    provenance_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE(obs_kind, entity_ref, place)
);
CREATE INDEX IF NOT EXISTS idx_obs_entity ON observation_records(entity_ref, temporal_at);
CREATE INDEX IF NOT EXISTS idx_obs_place  ON observation_records(place, temporal_at);
CREATE TABLE IF NOT EXISTS observation_audit (
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
class Observation:
    """One durable sighting: what/where/when + the saved vector."""

    obs_kind: str
    entity_ref: str
    label: str
    place: str
    temporal_at: str
    category: str = ""
    bbox: tuple[int, ...] | None = None
    frame_ref: str = ""
    vector: list[float] | None = None
    provenance: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "obs_kind": self.obs_kind,
            "entity_ref": self.entity_ref,
            "category": self.category,
            "label": self.label,
            "place": self.place,
            "bbox": list(self.bbox) if self.bbox else [],
            "temporal_at": self.temporal_at,
            "frame_ref": self.frame_ref,
            "vector": self.vector or [],
            "provenance": self.provenance or {},
        }


class ObservationRecorder:
    """Persistent, coalescing observation journal with spatial retrieval."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self._path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()
        self._privacy = True
        self.audit_log: list[dict] = []

    # -- privacy -------------------------------------------------------------

    @property
    def privacy_enabled(self) -> bool:
        return self._privacy

    def set_privacy(self, enabled: bool, *, reason: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO observation_audit (kind, reason, created_at) VALUES (?, ?, ?)",
                ("privacy-enabled" if enabled else "privacy-disabled", reason, _now()),
            )
            self._conn.commit()
            self._privacy = enabled
            self.audit_log.append({"kind": "privacy-enabled" if enabled else "privacy-disabled", "reason": reason})

    # -- writing -------------------------------------------------------------

    def record(
        self,
        *,
        kind: RecognitionKind,
        entity_ref: str,
        place: str = "",
        label: str = "",
        category: str = "",
        bbox: tuple[int, int, int, int] | None = None,
        vector: list[float] | None = None,
        frame_id: str = "",
        provenance: dict[str, Any] | None = None,
    ) -> Observation:
        """Persist a sighting; coalesces with any open row for the same
        (kind, entity, place) by advancing last-seen.

        Requires provenance (frame_id or provenance dict), like every
        RecognitionStore write.
        """
        prov = provenance or {}
        if not prov and not frame_id:
            raise ValueError("observation record requires provenance (frame_id or provenance dict)")
        if kind.value in _BIOMETRIC and not self.privacy_enabled:
            raise PermissionError(f"{kind.value} observation refused: biometric processing disabled")
        now = _now()
        with self._lock:
            self._conn.execute(
                "INSERT INTO observation_records (obs_kind, entity_ref, category, label, place,"
                " bbox_json, temporal_at, frame_ref, vector_json, provenance_json)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                " ON CONFLICT(obs_kind, entity_ref, place) DO UPDATE SET"
                " category=excluded.category, label=excluded.label, bbox_json=excluded.bbox_json,"
                " temporal_at=excluded.temporal_at, frame_ref=excluded.frame_ref,"
                " vector_json=excluded.vector_json, provenance_json=excluded.provenance_json",
                (
                    kind.value,
                    entity_ref,
                    category,
                    label,
                    place,
                    json.dumps(list(bbox) if bbox else []),
                    now,
                    frame_id,
                    json.dumps(vector or []),
                    json.dumps({**prov, "frame_id": frame_id} if frame_id else prov),
                ),
            )
            self._conn.commit()
        return Observation(
            obs_kind=kind.value, entity_ref=entity_ref, label=label, place=place,
            temporal_at=now, category=category, bbox=bbox, frame_ref=frame_id,
            vector=vector, provenance=prov,
        )

    # -- retrieval -----------------------------------------------------------

    def last_sighting(self, kind: RecognitionKind, entity_ref: str) -> Observation | None:
        """The single most recent observation of an entity (any place)."""
        rows = self._rows("WHERE obs_kind = ? AND entity_ref = ? ORDER BY temporal_at DESC LIMIT 1",
                          (kind.value, entity_ref))
        return rows[0] if rows else None

    def in_place(self, place: str, kind: RecognitionKind | None = None) -> list[Observation]:
        """What Novi currently knows to have been seen at this place."""
        if kind is None:
            rows = self._rows("WHERE place = ? ORDER BY temporal_at DESC", (place,))
        else:
            rows = self._rows("WHERE place = ? AND obs_kind = ? ORDER BY temporal_at DESC", (place, kind.value))
        return rows

    def search(
        self,
        query_vector: list[float],
        *,
        kind: RecognitionKind | None = None,
        place: str | None = None,
        limit: int = 5,
    ) -> list[tuple[str, float]]:
        """Top-k (entity_ref, cosine) over saved vectors — instance search."""
        if kind is None and place is None:
            rows = self._rows("ORDER BY temporal_at DESC")
        elif kind is None:
            rows = self._rows("WHERE place = ?", (place,))
        elif place is None:
            rows = self._rows("WHERE obs_kind = ?", (kind.value,))
        else:
            rows = self._rows("WHERE obs_kind = ? AND place = ?", (kind.value, place))
        scored = [(o.entity_ref, _cosine(query_vector, o.vector or [])) for o in rows]
        scored.sort(key=lambda pair: -pair[1])
        return scored[:limit]

    def all(self, kind: RecognitionKind | None = None) -> list[Observation]:
        if kind is None:
            return self._rows("ORDER BY temporal_at DESC")
        return self._rows("WHERE obs_kind = ? ORDER BY temporal_at DESC", (kind.value,))

    def count(self, kind: RecognitionKind | None = None) -> int:
        return len(self.all(kind))

    # -- internals -----------------------------------------------------------

    def _rows(self, where_sql: str, params: tuple = ()) -> list[Observation]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT obs_kind, entity_ref, category, label, place, bbox_json,"
                " temporal_at, frame_ref, vector_json, provenance_json"
                f" FROM observation_records {where_sql}",
                params,
            ).fetchall()
        out: list[Observation] = []
        for (obs_kind, entity_ref, category, label, place, bbox_json,
             temporal_at, frame_ref, vector_json, provenance_json) in rows:
            bbox_raw = json.loads(bbox_json or "[]")
            out.append(
                Observation(
                    obs_kind=obs_kind,
                    entity_ref=entity_ref,
                    category=category,
                    label=label,
                    place=place,
                    bbox=tuple(int(v) for v in bbox_raw) if bbox_raw else None,
                    temporal_at=temporal_at,
                    frame_ref=frame_ref,
                    vector=[float(v) for v in json.loads(vector_json or "[]")],
                    provenance=json.loads(provenance_json or "{}"),
                )
            )
        return out

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def rename_entity(self, kind: RecognitionKind, old_ref: str, new_ref: str) -> int:
        """Re-bind sighting rows from one entity_ref to another (naming loop).

        When the human names an unresolved proposal, its previously-recorded
        observations move from the unresolved ref to the canonical object/person
        id so history ("where did I last see it") is preserved under the name.
        Same-kind only; returns the number of rows re-bound.
        """
        if not old_ref or not new_ref or old_ref == new_ref:
            return 0
        with self._lock:
            cur = self._conn.execute(
                "UPDATE observation_records SET entity_ref = ?"
                " WHERE obs_kind = ? AND entity_ref = ?",
                (new_ref, kind.value, old_ref),
            )
            self._conn.commit()
            return cur.rowcount
