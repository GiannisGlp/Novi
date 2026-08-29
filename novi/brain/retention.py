"""Memory retention + capacity enforcement (Phase 4b, north-star gap doc).

Retention is now a store-side responsibility, not a hope:

- ``RetentionPolicy`` — per-memory-type TTLs, a default TTL, a global
  capacity cap, per-type caps, and protected sets (types/classes that are
  never auto-expired: safety invariants, protected privacy classes).
- ``RetentionEnforcer`` — the deterministic sweep: (a) tombstones records
  past their explicit ``expires_at``; (b) expires records older than their
  type TTL; (c) evicts the LOWEST-VALUE records when the store exceeds its
  capacity — never touching protected types/classes.

Value for eviction = confidence × recency × verification factor: the
weakest evidence loses first. Everything is a soft delete (deleted=1
tombstone) so privacy/audit semantics stay recoverable; hard deletes remain
an explicit erasure act. Records past ``expires_at`` are additionally
excluded from retrieval at query time, so expiry is honored WITHOUT waiting
for a sweep (the store's "honor expires_at automatically" duty).

Fail-closed: unparseable stamps, unknown ages, and protected classes are
never destroyed by this layer.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from .b1_memory import MemoryRecord as MemoryRecordLike
from .storage import DurableMemoryStore


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse(stamp: str) -> datetime | None:
    if not stamp:
        return None
    try:
        parsed = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except (ValueError, TypeError):
        return None


@dataclass(frozen=True)
class RetentionPolicy:
    """Deterministic retention rules for one store."""

    default_ttl_days: float = 365.0
    type_ttls: dict[str, float] = field(default_factory=dict)  # seconds, per type
    type_caps: dict[str, int] = field(default_factory=dict)
    max_records: int = 10000
    protected_types: tuple[str, ...] = ("invariant",)
    protected_classes: tuple[str, ...] = ("protected",)

    def ttl_seconds_for(self, memory_type: str) -> float | None:
        """Type TTL in seconds; the default TTL otherwise (None = never)."""
        if memory_type in self.type_ttls:
            return float(self.type_ttls[memory_type])
        if self.default_ttl_days <= 0:
            return None
        return self.default_ttl_days * 86400.0


@dataclass
class RetentionReport:
    """What one sweep did — fully auditable."""

    expired_expired: list[str] = field(default_factory=list)  # reason: EXPIRED (explicit)
    expired_ttl: list[str] = field(default_factory=list)  # reason: TTL
    evicted: list[str] = field(default_factory=list)  # reason: CAPACITY

    def snapshot(self) -> dict[str, object]:
        return {
            "expired": len(self.expired_expired),
            "ttl_expired": len(self.expired_ttl),
            "evicted": len(self.evicted),
            "expired_ids": list(self.expired_expired),
            "ttl_expired_ids": list(self.expired_ttl),
            "evicted_ids": list(self.evicted),
        }


class RetentionEnforcer:
    """Runs the policy over a DurableMemoryStore; soft deletes only, fail-closed."""

    def __init__(self, store: DurableMemoryStore, policy: RetentionPolicy | None = None) -> None:
        self.store = store
        self.policy = policy or RetentionPolicy()

    # ------------------------------------------------------------------ sweep

    def sweep(self, *, now: str | None = None) -> RetentionReport:
        """Apply expiry + TTL + capacity rules. Deterministic and auditable."""
        report = RetentionReport()
        stamp_now = _parse(now) if now else datetime.now(timezone.utc)

        # (a) explicit expiry (expires_at in the past): the store surfaces
        # these rows specifically so they can be tombstoned (its own active
        # view hides them from consumers).
        for entry in self.store.over_due_rows():
            record = entry["record"]
            self._tombstone(record.memory_id, "EXPIRED")
            report.expired_expired.append(record.memory_id)

        # (b) per-type TTL.
        for entry in self.store.active_rows():
            record = entry["record"]
            if self._protected(record):
                continue
            limit = self.policy.ttl_seconds_for(record.memory_type)
            if limit is None:
                continue
            created = _parse(record.created_at)
            if created is None:
                continue  # unknown age: fail closed, keep
            if created + timedelta(seconds=limit) <= stamp_now:
                self._tombstone(record.memory_id, "TTL")
                report.expired_ttl.append(record.memory_id)

        # (c) capacity.
        self._enforce_capacity(stamp_now, report)
        return report

    # ---------------------------------------------------------------- capacity

    def _value_score(self, record: Any, stamp_now: datetime) -> float:
        """Retention value: confidence × recency-weight; weaker evidence first out."""
        created = _parse(record.created_at)
        age_days = 365.0 if created is None else max(0.0, (stamp_now - created).total_seconds() / 86400.0)
        recency = math.exp(-age_days / 14.0)
        verified = 1.0 if str(getattr(record, "verification_status", "")).lower() == "verified" else 0.6
        return float(record.confidence) * recency * verified

    def _protected(self, record: Any) -> bool:
        if record.memory_type in self.policy.protected_types:
            return True
        privacy = str(getattr(record, "privacy_class", "") or "").lower()
        return privacy in self.policy.protected_classes

    def _evictable(self, record: Any) -> bool:
        return not (
            self._protected(record)
            or str(record.verification_status or "").lower() == "consolidated"
        )

    def _enforce_capacity(self, stamp_now: datetime, report: RetentionReport) -> None:
        rows = self.store.active_rows()
        evictable = [
            (entry["record"], self._value_score(entry["record"], stamp_now))
            for entry in rows
            if self._evictable(entry["record"])
        ]
        # Global cap: evict lowest value first.
        overflow = len(rows) - self.policy.max_records
        if overflow > 0:
            overflow_set = {record.memory_id for record, _ in sorted(evictable, key=lambda pair: (pair[1], pair[0].memory_id))[:overflow]}
            for memory_id in sorted(overflow_set):
                self._tombstone(memory_id, "CAPACITY")
                report.evicted.append(memory_id)

        # Per-type caps (evictable records of that type only).
        by_type: dict[str, list[tuple[MemoryRecordLike, float]]] = {}
        for record, score in evictable:
            by_type.setdefault(record.memory_type, []).append((record, score))
        for memory_type, cap in self.policy.type_caps.items():
            typed = by_type.get(memory_type, ())
            excess = len(typed) - int(cap)
            if excess <= 0:
                continue
            losers = {record.memory_id for record, _ in sorted(typed, key=lambda pair: (pair[1], pair[0].memory_id))[:excess]}
            for memory_id in sorted(losers):
                self._tombstone(memory_id, "CAPACITY")
                report.evicted.append(memory_id)

    # ----------------------------------------------------------------- helpers

    def _tombstone(self, memory_id: str, reason: str) -> bool:
        """Soft delete (auditable tombstone) — never a physical erase."""
        return self.store.forget(memory_id)
