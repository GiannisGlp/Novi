"""Prospective memory and commitments (plan 22, Phase 6).

``ProspectiveMemory`` represents future intentions ("remind me to test the
camera after this") with triggers; when trigger conditions occur, the
intention flows through salience → dialogue policy → INITIATE/ASK/REMIND
(Task 6.2). Necessary for continuity and natural follow-up.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

PENDING = "pending"
DUE = "due"
FULFILLED = "fulfilled"
CANCELLED = "cancelled"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class TriggerKind(str, Enum):
    CONVERSATION_END = "conversation_end"
    EXPLICIT_REQUEST = "explicit_request"
    TIME = "time"
    EVENT = "event"


@dataclass
class ProspectiveMemory:
    trigger: str
    intended_action: str
    owner: str = ""
    created_at: str = field(default_factory=utc_now_iso)
    due_at: str = ""
    status: str = PENDING
    priority: float = 0.5
    confidence: float = 0.8
    source: str = "conversation"
    trigger_kind: TriggerKind = TriggerKind.CONVERSATION_END
    memory_id: str = field(default_factory=lambda: f"prosp-{uuid.uuid4().hex[:8]}")

    def snapshot(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "trigger": self.trigger,
            "intended_action": self.intended_action,
            "owner": self.owner,
            "created_at": self.created_at,
            "due_at": self.due_at,
            "status": self.status,
            "priority": round(self.priority, 3),
            "confidence": round(self.confidence, 3),
            "source": self.source,
            "trigger_kind": self.trigger_kind.value,
        }


class ProspectiveMemoryStore:
    """Bounded store of future intentions with trigger checking."""

    def __init__(self, *, max_entries: int = 32) -> None:
        self._entries: dict[str, ProspectiveMemory] = {}
        self.max_entries = max_entries

    def register(
        self,
        *,
        trigger: str,
        intended_action: str,
        owner: str = "",
        priority: float = 0.5,
        confidence: float = 0.8,
        source: str = "conversation",
        trigger_kind: TriggerKind = TriggerKind.CONVERSATION_END,
        due_at: str = "",
    ) -> ProspectiveMemory:
        mem = ProspectiveMemory(
            trigger=trigger, intended_action=intended_action, owner=owner,
            priority=priority, confidence=confidence, source=source,
            trigger_kind=trigger_kind, due_at=due_at,
        )
        self._entries[mem.memory_id] = mem
        if len(self._entries) > self.max_entries:
            oldest = min(self._entries.values(), key=lambda m: m.created_at)
            self._entries.pop(oldest.memory_id, None)
        return mem

    def check_due(self, *, conversation_ended: bool = False, now: str | None = None) -> list[ProspectiveMemory]:
        """Return (and mark) entries whose trigger conditions occurred."""
        now = now or utc_now_iso()
        due: list[ProspectiveMemory] = []
        for mem in self._entries.values():
            if mem.status != PENDING:
                continue
            fired = False
            if mem.trigger_kind == TriggerKind.CONVERSATION_END and conversation_ended:
                fired = True
            elif mem.trigger_kind == TriggerKind.TIME and mem.due_at and mem.due_at <= now:
                fired = True
            elif mem.trigger_kind == TriggerKind.EVENT and mem.trigger in (now, ""):
                fired = True  # explicit event trigger supplied by caller
            if fired:
                mem.status = DUE
                due.append(mem)
        return due

    def fulfill(self, memory_id: str) -> bool:
        mem = self._entries.get(memory_id)
        if mem is None:
            return False
        mem.status = FULFILLED
        return True

    def cancel(self, memory_id: str) -> bool:
        mem = self._entries.get(memory_id)
        if mem is None:
            return False
        mem.status = CANCELLED
        return True

    def due_entries(self) -> list[ProspectiveMemory]:
        return [m for m in self._entries.values() if m.status == DUE]

    def pending_entries(self) -> list[ProspectiveMemory]:
        return [m for m in self._entries.values() if m.status == PENDING]

    def snapshot(self) -> dict[str, Any]:
        return {"entries": [m.snapshot() for m in self._entries.values()]}

    @classmethod
    def from_snapshot(cls, data: dict[str, Any] | None) -> "ProspectiveMemoryStore":
        store = cls()
        if not data:
            return store
        for raw in data.get("entries", []):
            mem = ProspectiveMemory(
                trigger=str(raw.get("trigger", "")),
                intended_action=str(raw.get("intended_action", "")),
                owner=str(raw.get("owner", "")),
                created_at=str(raw.get("created_at", "") or utc_now_iso()),
                due_at=str(raw.get("due_at", "")),
                status=str(raw.get("status", PENDING)),
                priority=float(raw.get("priority", 0.5)),
                confidence=float(raw.get("confidence", 0.8)),
                source=str(raw.get("source", "conversation")),
                trigger_kind=TriggerKind(raw.get("trigger_kind", TriggerKind.CONVERSATION_END.value)),
                memory_id=str(raw.get("memory_id", "") or f"prosp-{uuid.uuid4().hex[:8]}"),
            )
            store._entries[mem.memory_id] = mem
        return store
