"""Memory consolidation, decay and contradiction resolution for the Mac Brain.

Implements the consolidation operations from
04_MEMORY_CONSOLIDATION_RETRIEVAL_AND_CONTEXT.md as a bounded pass over the
durable store: expiry, confidence decay, archival, and contradiction resolution
(supersede). It mutates store row state only -- it never rewrites the canonical
MemoryRecord semantics, and it never deletes historical evidence for
consequential knowledge (archival preserves the row; deletion is a separate
privacy/lifecycle operation).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class MemoryState(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"


@dataclass(frozen=True)
class ConsolidationConfig:
    enabled: bool = True
    default_ttl_seconds: float = 0.0  # 0 = no expiry by default
    ttl_by_type: dict[str, float] = field(default_factory=dict)
    decay_start_seconds: float = 60.0
    decay_period_seconds: float = 60.0
    decay_factor: float = 0.9
    min_confidence: float = 0.3
    contradiction_types: tuple[str, ...] = ("fact",)


@dataclass
class ConsolidationReport:
    expired: int = 0
    archived: int = 0
    decayed: int = 0
    superseded: int = 0


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


class MemoryConsolidator:
    """Bounded consolidation pass over a durable store (or any store exposing the row API)."""

    def __init__(self, store: Any, config: ConsolidationConfig | None = None) -> None:
        self.store = store
        self.config = config or ConsolidationConfig()

    def consolidate(self, now: str | None = None) -> ConsolidationReport:
        if not self.config.enabled:
            return ConsolidationReport()
        now_dt = _parse_utc(now) if now else datetime.now(timezone.utc)
        rows = self.store.active_rows()
        report = ConsolidationReport()

        if self.config.contradiction_types:
            report.superseded = self._resolve_contradictions(rows)

        for item in rows:
            record = item["record"]
            # contradiction/expiry may already have moved this row; skip if it is no longer active.
            if self.store.get_state(record.memory_id) != MemoryState.ACTIVE.value:
                continue
            created_at = _parse_utc(record.created_at)
            age_s = (now_dt - created_at).total_seconds()
            ttl = self.config.ttl_by_type.get(record.memory_type, self.config.default_ttl_seconds)
            if ttl and age_s > ttl:
                self.store.set_state(record.memory_id, MemoryState.EXPIRED)
                report.expired += 1
                continue
            new_conf = self._decayed(record.confidence, age_s)
            if new_conf < record.confidence:
                if new_conf < self.config.min_confidence:
                    self.store.set_state(record.memory_id, MemoryState.ARCHIVED)
                    report.archived += 1
                else:
                    self.store.set_confidence(record.memory_id, new_conf)
                    report.decayed += 1
        return report

    def _decayed(self, confidence: float, age_s: float) -> float:
        start = self.config.decay_start_seconds
        if age_s <= start:
            return confidence
        steps = (age_s - start) / self.config.decay_period_seconds
        return max(0.0, confidence * (self.config.decay_factor ** steps))

    def _resolve_contradictions(self, rows: list[dict[str, Any]]) -> int:
        superseded = 0
        contradiction_types = set(self.config.contradiction_types)
        groups: dict[str, list[dict[str, Any]]] = {}
        for item in rows:
            record = item["record"]
            if record.memory_type not in contradiction_types:
                continue
            for entity in record.entity_refs:
                groups.setdefault(entity, []).append(item)
        for group in groups.values():
            if len(group) < 2:
                continue
            ordered = sorted(group, key=lambda item: (item["record"].created_at, item["record"].confidence))
            keeper = ordered[-1]
            keeper_text = str(keeper["record"].content)
            for item in ordered[:-1]:
                if str(item["record"].content) != keeper_text:
                    self.store.set_state(item["record"].memory_id, MemoryState.SUPERSEDED)
                    superseded += 1
        return superseded
