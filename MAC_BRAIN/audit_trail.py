"""Persistent decision audit trail (canonical authority: docs/02-autonomy/13_AUTONOMY_OBSERVABILITY_AND_AUDIT.md).

Structured records of consequential decisions and actions with retention
controls — distinct from short-lived operational logs.

Each audit record captures the decision-trace metadata required by doc 13:

    correlation ID, goal ID, plan ID, action ID, model/runtime version,
    timestamps, confidence, policy result, safety result, outcome.

The trail:

- is append-only (audit records are never mutated in place);
- enforces retention (max records / max age) with a retention report;
- supports the user-audit view (high-level fields + no raw media);
- exposes a correlation-grouped trace for reproducibility and simulation replay;
- keeps raw media out (audio/video frames are never stored — referential
  hashes or counts only).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# Media-like payload keys that must never be stored verbatim (doc 13 §Privacy).
_FORBIDDEN_RAW_KEYS = frozenset({"audio", "video", "frame", "image", "raw_audio", "raw_video", "pcm", "wav"})


@dataclass(frozen=True)
class AuditEntry:
    """One immutable audit record for a consequential decision/action."""

    entry_id: str
    correlation_id: str
    timestamp: str
    action: str
    decision_reason: str
    policy_result: str
    safety_result: str
    outcome: str
    goal_id: str = ""
    plan_id: str = ""
    action_id: str = ""
    actor: str = ""
    version: str = ""
    confidence: float | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def snapshot(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
            "action": self.action,
            "decision_reason": self.decision_reason,
            "policy_result": self.policy_result,
            "safety_result": self.safety_result,
            "outcome": self.outcome,
            "goal_id": self.goal_id,
            "plan_id": self.plan_id,
            "action_id": self.action_id,
            "actor": self.actor,
            "version": self.version,
            "confidence": self.confidence,
            "details": dict(self.details),
        }

    def user_view(self) -> dict[str, Any]:
        """User audit view (doc 13 §User Audit): structured, privacy-safe.

        Shows what was observed at a high level, what action occurred, why it
        was requested, which capability ran, and the result — without raw
        media or full chain-of-thought.
        """
        return {
            "timestamp": self.timestamp,
            "action": self.action,
            "why": self.decision_reason,
            "policy": self.policy_result,
            "safety": self.safety_result,
            "result": self.outcome,
            "goal": self.goal_id or None,
            "actor": self.actor or None,
            "details": {k: v for k, v in self.details.items() if k not in _FORBIDDEN_MEDIA_KEYS},
        }


# Public alias so user_view's comprehension can reference it.
_FORBIDDEN_MEDIA_KEYS = _FORBIDDEN_RAW_KEYS


def _redact(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a copy with audio/video-like payloads replaced by a size hash.

    doc 13 §Privacy: do not store raw audio/video; prefer references/hashes.
    """
    out: dict[str, Any] = {}
    for k, v in payload.items():
        if k.lower() in _FORBIDDEN_RAW_KEYS:
            digest = ""
            try:
                digest = str(hash(json.dumps(v, sort_keys=True, default=str)))
            except Exception:  # pragma: no cover - defensive
                digest = "unhashable"
            out[k] = f"<redacted:{digest}>"
        elif isinstance(v, dict):
            out[k] = _redact(v)
        elif isinstance(v, list):
            out[k] = [_redact(x) if isinstance(x, dict) else x for x in v]
        else:
            out[k] = v
    return out


class AuditTrail:
    """Append-only, retention-controlled audit trail for consequential decisions."""

    def __init__(self, *, retention_max_entries: int = 10000, retention_seconds: float | None = None) -> None:
        self._entries: list[AuditEntry] = []
        self._max_entries = max(1, int(retention_max_entries))
        self._retention_seconds = retention_seconds
        self._seq = 0
        self._by_correlation: dict[str, list[str]] = {}

    # ---- write ----

    def record(
        self,
        *,
        correlation_id: str,
        action: str,
        decision_reason: str,
        policy_result: str,
        safety_result: str,
        outcome: str = "not_executed",
        risk_class: str = "",
        goal_id: str = "",
        plan_id: str = "",
        action_id: str = "",
        actor: str = "",
        version: str = "",
        confidence: float | None = None,
        details: dict[str, Any] | None = None,
        timestamp: str = "",
    ) -> AuditEntry:
        """Append one audit entry for a consequential decision/action."""
        entry = AuditEntry(
            entry_id=f"audit-{uuid4().hex[:16]}",
            correlation_id=correlation_id or str(uuid4()),
            timestamp=timestamp or utc_now(),
            action=action,
            decision_reason=decision_reason,
            policy_result=policy_result or risk_class,
            safety_result=safety_result,
            outcome=outcome,
            goal_id=goal_id,
            plan_id=plan_id,
            action_id=action_id,
            actor=actor,
            version=version,
            confidence=confidence,
            details=_redact(details or {}),
        )
        self._entries.append(entry)
        self._by_correlation.setdefault(entry.correlation_id, []).append(entry.entry_id)
        self._seq += 1
        self._enforce_retention()
        return entry

    def _enforce_retention(self) -> None:
        """Apply retention: cap count and drop entries older than the window."""
        if self._retention_seconds is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(seconds=self._retention_seconds)
            before = len(self._entries)
            self._entries = [
                e for e in self._entries
                if _parse_dt(e.timestamp) >= cutoff
            ]
            if len(self._entries) != before:
                self._rebuild_index()
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]
            self._rebuild_index()

    def _rebuild_index(self) -> None:
        self._by_correlation = {}
        for e in self._entries:
            self._by_correlation.setdefault(e.correlation_id, []).append(e.entry_id)

    # ---- queries ----

    def entries(self, *, limit: int | None = None) -> tuple[AuditEntry, ...]:
        items = tuple(self._entries)
        if limit is not None and limit > 0:
            items = items[-limit:]
        return items

    def snapshots(self, *, limit: int | None = None) -> tuple[dict[str, Any], ...]:
        return tuple(e.snapshot() for e in self.entries(limit=limit))

    def user_audit_view(self, *, limit: int | None = None) -> tuple[dict[str, Any], ...]:
        """Authorized user-facing audit view (doc 13 §User Audit)."""
        return tuple(e.user_view() for e in self.entries(limit=limit))

    def by_correlation(self, correlation_id: str) -> tuple[AuditEntry, ...]:
        """All entries sharing a correlation id (reproducible decision trace)."""
        return tuple(e for e in self._entries if e.correlation_id == correlation_id)

    def trace_for_action(self, action_id: str) -> tuple[AuditEntry, ...]:
        return tuple(e for e in self._entries if e.action_id == action_id)

    def by_goal(self, goal_id: str) -> tuple[AuditEntry, ...]:
        return tuple(e for e in self._entries if e.goal_id == goal_id)

    # ---- health / stats ----

    def stats(self) -> dict[str, Any]:
        return {
            "records": len(self._entries),
            "correlation_domains": len(self._by_correlation),
            "retention_max_entries": self._max_entries,
            "retention_seconds": self._retention_seconds,
            "actions": _count(self._entries, key=lambda e: e.action),
            "outcomes": _count(self._entries, key=lambda e: e.outcome),
        }


def _count(items: Iterable[AuditEntry], *, key) -> dict[str, int]:
    out: dict[str, int] = {}
    for e in items:
        k = key(e)
        out[k] = out.get(k, 0) + 1
    return out


def _parse_dt(iso: str) -> datetime:
    try:
        return datetime.fromisoformat(iso)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
