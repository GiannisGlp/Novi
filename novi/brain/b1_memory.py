from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import Any, Iterable

from .contracts import utc_now, validate_contract


@dataclass(frozen=True)
class MemoryRecord:
    memory_id: str
    memory_type: str
    created_at: str
    content: Any
    confidence: float
    verification_status: str
    privacy_class: str
    revision: int
    provenance: Any
    event_refs: tuple[str, ...] = ()
    entity_refs: tuple[str, ...] = ()
    semantic_index_ref: str | None = None
    temporal_context: Any = None
    spatial_context: Any = None
    retention_policy_ref: str | None = None
    dependency_refs: tuple[str, ...] = ()

    def as_contract(self) -> dict[str, Any]:
        payload = asdict(self)
        for field in ("event_refs", "entity_refs", "dependency_refs"):
            payload[field] = list(payload[field])
        return {key: value for key, value in payload.items() if value is not None}


@dataclass(frozen=True)
class MemoryAdmission:
    accepted: bool
    memory_id: str | None
    decision: str
    reason: str


class DeterministicMemoryManager:
    """Bounded B1 memory manager using the canonical MemoryRecord contract.

    This is intentionally an in-process semantic baseline. It does not select or
    adopt a durable database; Stage-1 storage remains governed by ADR-DATA-001.
    """

    def __init__(self) -> None:
        self._records: dict[str, MemoryRecord] = {}
        self._deleted: set[str] = set()

    @staticmethod
    def _identity(payload: dict[str, Any]) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return "mem-" + sha256(canonical.encode("utf-8")).hexdigest()[:24]

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
        memory_id = self._identity({k: v for k, v in asdict(record).items() if k != "created_at" and k != "memory_id"})
        record = MemoryRecord(memory_id=memory_id, **{k: v for k, v in asdict(record).items() if k != "memory_id"})
        validate_contract("novi.memory-record", record.as_contract())

        existing = self._records.get(memory_id)
        if existing is not None and memory_id not in self._deleted:
            return MemoryAdmission(True, memory_id, "KEEP_EXISTING", "duplicate_admission")
        # A tombstoned (forgotten) record is not a live duplicate; re-store so
        # the memory becomes retrievable again.
        self._records[memory_id] = record
        self._deleted.discard(memory_id)
        return MemoryAdmission(True, memory_id, "STORE_EPISODE", "admitted")

    def retrieve(self, query: str, *, entity: str | None = None, memory_type: str | None = None, limit: int = 5) -> tuple[MemoryRecord, ...]:
        if limit <= 0:
            return ()
        terms = {term.lower() for term in query.split() if term}
        candidates: list[tuple[int, str, MemoryRecord]] = []
        for memory_id, record in self._records.items():
            if memory_id in self._deleted:
                continue
            if entity is not None and entity not in record.entity_refs:
                continue
            if memory_type is not None and memory_type != record.memory_type:
                continue
            haystack = json.dumps(record.content, sort_keys=True, default=str).lower()
            haystack += " " + " ".join(record.entity_refs)
            score = sum(1 for term in terms if term in haystack)
            if terms and score == 0:
                continue
            candidates.append((score, memory_id, record))
        candidates.sort(key=lambda item: (-item[0], item[1]))
        return tuple(item[2] for item in candidates[:limit])

    def forget(self, memory_id: str) -> bool:
        if memory_id not in self._records or memory_id in self._deleted:
            return False
        self._deleted.add(memory_id)
        return True

    def get(self, memory_id: str) -> MemoryRecord | None:
        if memory_id in self._deleted:
            return None
        return self._records.get(memory_id)

    @property
    def active_count(self) -> int:
        return sum(1 for memory_id in self._records if memory_id not in self._deleted)

    @property
    def deleted_count(self) -> int:
        return len(self._deleted)
