"""PersonObjectAssociationStore: durable person↔object co-occurrence memory.

The recognition pipeline knows WHAT (object instance) and WHO (person) — this
store remembers WHO was seen WITH WHICH OBJECT, WHERE, and HOW OFTEN, so Novi
can ground conversations in its history of the room ("the blue mug you were
holding in the kitchen"). One canonical SQLite file (``novi/data/novi.db``,
WAL) shared with RecognitionStore / ObservationRecorder / DurableMemoryStore —
never a second database.

Coalescing rule: repeated co-occurrences of the same (person, object, place)
collapse into ONE row whose count increments and whose last-seen advances, so
continuous camera observation cannot grow the table unboundedly; a move to a
different place opens a second row.

Privacy (mirrors the other stores): every row is person-keyed co-occurrence
metadata, so writes are refused while the privacy switch is off (fail-closed,
audited); reads stay available because the memory is non-biometric. Provenance
is mandatory on every write.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_SCHEMA = """
CREATE TABLE IF NOT EXISTS person_object_associations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_ref TEXT NOT NULL,
    object_ref TEXT NOT NULL,
    object_label TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT '',
    place TEXT NOT NULL DEFAULT '',
    saw_count INTEGER NOT NULL DEFAULT 1,
    first_seen TEXT NOT NULL DEFAULT '',
    last_seen TEXT NOT NULL DEFAULT '',
    provenance_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE(person_ref, object_ref, place)
);
CREATE INDEX IF NOT EXISTS idx_assoc_person ON person_object_associations(person_ref, last_seen);
CREATE INDEX IF NOT EXISTS idx_assoc_object ON person_object_associations(object_ref, last_seen);
CREATE TABLE IF NOT EXISTS person_object_association_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT ''
);
"""


def _now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


@dataclass(frozen=True)
class Association:
    """One durable person-object co-occurrence fact.

    ``places`` carries the aggregated place list returned by
    :meth:`objects_with`; raw per-place rows leave it empty and set ``place``.
    """

    person_ref: str
    object_ref: str
    label: str
    category: str
    place: str
    saw_count: int
    first_seen_at: str
    last_seen_at: str
    places: tuple[str, ...] = ()
    provenance: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "person_ref": self.person_ref,
            "object_ref": self.object_ref,
            "label": self.label,
            "category": self.category,
            "place": self.place,
            "saw_count": self.saw_count,
            "first_seen_at": self.first_seen_at,
            "last_seen_at": self.last_seen_at,
            "places": list(self.places),
            "provenance": self.provenance or {},
        }


class PersonObjectAssociationStore:
    """Persistent, coalescing person-object co-occurrence journal."""

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
                "INSERT INTO person_object_association_audit (kind, reason, created_at)"
                " VALUES (?, ?, ?)",
                ("privacy-enabled" if enabled else "privacy-disabled", reason, _now()),
            )
            self._conn.commit()
            self._privacy = enabled
            self.audit_log.append(
                {"kind": "privacy-enabled" if enabled else "privacy-disabled", "reason": reason}
            )

    # -- writing -------------------------------------------------------------

    def note(
        self,
        person_ref: str,
        object_ref: str,
        *,
        label: str = "",
        category: str = "",
        place: str = "",
        count_incr: int = 1,
        first_seen_at: str | None = None,
        last_seen_at: str | None = None,
        frame_id: str = "",
        provenance: dict[str, Any] | None = None,
    ) -> Association:
        """Record a person-object co-occurrence; coalesces on repeat.

        Mandatory provenance (frame_id or provenance dict), like every
        recognition-store write. Refused while the privacy switch is off —
        person-keyed rows never grow the store during a private session.
        """
        prov = provenance or {}
        if not prov and not frame_id:
            raise ValueError(
                "association write requires provenance (frame_id or provenance dict)"
            )
        if not self.privacy_enabled:
            raise PermissionError("person-object association refused: privacy disabled")
        last = last_seen_at or _now()
        first = first_seen_at or last
        with self._lock:
            self._upsert(
                person_ref, object_ref,
                label=label, category=category, place=place,
                count_incr=max(0, int(count_incr)), first_seen_at=first,
                last_seen_at=last,
                provenance={**prov, "frame_id": frame_id} if frame_id else prov,
            )
        return Association(
            person_ref=person_ref, object_ref=object_ref, label=label,
            category=category, place=place, saw_count=max(0, int(count_incr)),
            first_seen_at=first, last_seen_at=last, provenance=prov,
        )

    def rename_person(self, old_ref: str, new_ref: str) -> int:
        """Merge all co-occurrence rows from ``old_ref`` into ``new_ref``.

        Used by the identity naming loop: when a placeholder person gets a real
        name, its accumulated memory moves under the canonical id, with counts
        summed and first/last seen bounds preserved (min-first, max-last).
        Returns the number of distinct (person, object, place) rows moved.
        """
        if not old_ref or not new_ref or old_ref == new_ref:
            return 0
        with self._lock:
            rows = self._conn.execute(
                "SELECT object_ref, object_label, category, place, saw_count,"
                " first_seen, last_seen, provenance_json"
                " FROM person_object_associations WHERE person_ref = ?",
                (old_ref,),
            ).fetchall()
            for (object_ref, label, category, place, count,
                 first_seen, last_seen, prov_json) in rows:
                self._upsert(
                    new_ref, object_ref,
                    label=label, category=category, place=place,
                    count_incr=count, first_seen_at=first_seen,
                    last_seen_at=last_seen,
                    provenance=json.loads(prov_json or "{}"),
                )
            self._conn.execute(
                "DELETE FROM person_object_associations WHERE person_ref = ?",
                (old_ref,),
            )
            self._conn.commit()
            return len(rows)

    # -- retrieval -----------------------------------------------------------

    def objects_with(self, person_ref: str, *, limit: int = 8) -> list[Association]:
        """Top objects this person has been seen with, aggregated across places.

        One row per object_ref (deduped), ranked by total co-occurrence count
        then most-recent sighting. Ordered newest-first for ties.
        """
        with self._lock:
            rows = self._conn.execute(
                "SELECT object_ref, MAX(object_label) AS label, MAX(category) AS category,"
                " SUM(saw_count) AS total, MIN(first_seen) AS first_seen,"
                " MAX(last_seen) AS last_seen,"
                " GROUP_CONCAT(DISTINCT place) AS places"
                " FROM person_object_associations WHERE person_ref = ?"
                " GROUP BY object_ref"
                " ORDER BY total DESC, last_seen DESC LIMIT ?",
                (person_ref, max(1, int(limit))),
            ).fetchall()
        out: list[Association] = []
        for (object_ref, label, category, total, first_seen, last_seen, places) in rows:
            pks = tuple(p for p in (places or "").split(",") if p)
            out.append(
                Association(
                    person_ref=person_ref, object_ref=object_ref, label=label or "",
                    category=category or "", place="", saw_count=int(total or 0),
                    first_seen_at=first_seen or "", last_seen_at=last_seen or "",
                    places=pks,
                )
            )
        return out

    def seen_with(self, person_ref: str, object_ref: str) -> dict[str, Any] | None:
        """Aggregate verdict: has this person ever been seen with this object?

        Returns None when never; otherwise ``{seen, count, last_seen_at, places}``.
        """
        with self._lock:
            row = self._conn.execute(
                "SELECT SUM(saw_count) AS total, MAX(last_seen) AS last_seen,"
                " GROUP_CONCAT(DISTINCT place) AS places"
                " FROM person_object_associations"
                " WHERE person_ref = ? AND object_ref = ?",
                (person_ref, object_ref),
            ).fetchone()
        if row is None or (row[0] or 0) == 0:
            return None
        total, last_seen, places = row
        return {
            "seen": True,
            "count": int(total or 0),
            "last_seen_at": last_seen or "",
            "places": [p for p in (places or "").split(",") if p],
        }

    def recent_summary(self, person_ref: str, *, limit: int = 3) -> list[str]:
        """Bounded human lines for dialogue: ``"mug in kitchen (3x)"``."""
        out: list[str] = []
        for a in self.objects_with(person_ref, limit=limit):
            where = a.places[0] if a.places else ""
            if where:
                out.append(f"{a.label or a.object_ref} in {where} ({a.saw_count}x)")
            else:
                out.append(f"{a.label or a.object_ref} ({a.saw_count}x)")
        return out

    def all(self, person_ref: str | None = None) -> list[Association]:
        """Every raw per-place co-occurrence row (no aggregation)."""
        if person_ref is None:
            where_sql, params = "", ()
        else:
            where_sql, params = "WHERE person_ref = ?", (person_ref,)
        with self._lock:
            rows = self._conn.execute(
                "SELECT person_ref, object_ref, object_label, category, place,"
                " saw_count, first_seen, last_seen, provenance_json"
                f" FROM person_object_associations {where_sql} ORDER BY last_seen DESC",
                params,
            ).fetchall()
        out: list[Association] = []
        for (person_ref_r, object_ref, label, category, place,
             count, first_seen, last_seen, prov_json) in rows:
            out.append(
                Association(
                    person_ref=person_ref_r, object_ref=object_ref, label=label,
                    category=category, place=place, saw_count=int(count or 0),
                    first_seen_at=first_seen or "", last_seen_at=last_seen or "",
                    provenance=json.loads(prov_json or "{}"),
                )
            )
        return out

    def count(self) -> int:
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM person_object_associations"
            ).fetchone()
        return int(row[0] or 0)

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # -- internals -----------------------------------------------------------

    def _upsert(
        self,
        person_ref: str,
        object_ref: str,
        *,
        label: str,
        category: str,
        place: str,
        count_incr: int,
        first_seen_at: str,
        last_seen_at: str,
        provenance: dict[str, Any],
    ) -> None:
        """Shared coalescing upsert: sum counts, min first-seen, max last-seen."""
        self._conn.execute(
            "INSERT INTO person_object_associations"
            " (person_ref, object_ref, object_label, category, place, saw_count,"
            "  first_seen, last_seen, provenance_json)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
            " ON CONFLICT(person_ref, object_ref, place) DO UPDATE SET"
            " object_label = excluded.object_label,"
            " category = excluded.category,"
            " saw_count = person_object_associations.saw_count + excluded.saw_count,"
            " first_seen = MIN(person_object_associations.first_seen, excluded.first_seen),"
            " last_seen = MAX(person_object_associations.last_seen, excluded.last_seen),"
            " provenance_json = excluded.provenance_json",
            (
                person_ref, object_ref, label, category, place, count_incr,
                first_seen_at, last_seen_at, json.dumps(provenance),
            ),
        )
        self._conn.commit()
