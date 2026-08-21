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


@dataclass
class SummaryReport:
    created: int = 0
    groups: int = 0


class SummaryConsolidator:
    """Episodic → semantic consolidation (Memory 3.0).

    Groups active episodic memories (utterances/perceptions) by shared entity and
    distills each group into a single higher-level ``summary`` memory. This gives
    Novi a gist-level understanding instead of a pile of raw episodes, and the
    summaries are retrievable by entity like any other memory.

    Deterministic and CI-safe: no LLM dependency. Idempotent across restarts: an
    entity is only summarized once (a summary already exists for it).
    """

    def __init__(
        self,
        store: Any,
        *,
        min_group_size: int = 2,
        summary_types: tuple[str, ...] = ("utterance", "perception"),
        summary_memory_type: str = "summary",
    ) -> None:
        self.store = store
        self.min_group_size = min_group_size
        self.summary_types = summary_types
        self.summary_memory_type = summary_memory_type

    def consolidate(self) -> SummaryReport:
        rows = self.store.active_rows()
        episodic = [item["record"] for item in rows if item["record"].memory_type in self.summary_types]
        groups: dict[str, list[Any]] = {}
        for record in episodic:
            for entity in record.entity_refs:
                groups.setdefault(entity, []).append(record)
        report = SummaryReport()
        for entity, records in groups.items():
            if len(records) < self.min_group_size:
                continue
            if self._summary_exists(entity):
                continue
            summary = self._summarize(entity, records)
            admission = self.store.admit(
                memory_type=self.summary_memory_type,
                content=summary,
                confidence=min(0.9, max(float(r.confidence) for r in records)),
                verification_status="consolidated",
                privacy_class="public",
                provenance={"source": "consolidation", "kind": "episodic_summary", "entity": entity, "folded": [r.memory_id for r in records]},
                entity_refs=(entity,),
                dependency_refs=tuple(r.memory_id for r in records),
            )
            report.groups += 1
            if admission.accepted:
                report.created += 1
        return report

    def _summary_exists(self, entity: str) -> bool:
        for item in self.store.active_rows():
            record = item["record"]
            if record.memory_type == self.summary_memory_type and entity in record.entity_refs:
                return True
        return False

    @staticmethod
    def _summarize(entity: str, records: list[Any]) -> str:
        seen: set[str] = set()
        parts: list[str] = []
        for record in sorted(records, key=lambda r: r.created_at):
            content = record.content if isinstance(record.content, str) else str(record.content)
            if content in seen:
                continue
            seen.add(content)
            parts.append(content)
        return f"{entity}: " + "; ".join(parts)


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
