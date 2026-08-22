"""Autonomy event bus (canonical authority: docs/02-autonomy/10_AUTONOMY_EVENT_BUS.md).

Implements the canonical event envelope with:

- typed events (``event_type``) + ``version``;
- timestamps (``occurred_at`` / ``published_at``);
- ``correlation_id`` / ``causation_id`` (causal threading);
- ``priority`` (critical > high > normal > low);
- ``privacy_class`` + access control on consumers;
- replay (ordered, filterable, access-scoped);
- deduplication (same type + correlation + causation collapses);
- bounded-queue backpressure (drop-oldest with observable counters);
- health monitoring (published/deduped/dropped counts, per-type).

The bus stays independent of the transport implementation (in-memory here;
an NVIDIA-accelerated transport on Jetson must preserve this contract).

The flattened ``snapshot()`` keeps both ``event_type`` and ``type`` keys so
legacy ``MacBrain.events`` consumers keep working while new consumers use the
canonical envelope.
"""

from __future__ import annotations

import json
from collections import Counter, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable
from uuid import uuid4

# ---------------------------------------------------------------------------
# Envelope constants
# ---------------------------------------------------------------------------

PRIORITY_ORDER = {"low": 0, "normal": 1, "high": 2, "critical": 3}
PRIORITIES = frozenset(PRIORITY_ORDER)

# Privacy classes rank low→high; a consumer with access level X sees events
# whose privacy_class rank is <= X.
PRIVACY_RANK = {"public": 0, "unclassified": 1, "restricted": 2, "private": 3}
PRIVACY_CLASSES = frozenset(PRIVACY_RANK)

DEFAULT_PRIORITY = "normal"
DEFAULT_PRIVACY = "unclassified"
DEFAULT_VERSION = 1

# Maximum number of events retained when no explicit cap is given.
DEFAULT_MAX_EVENTS = 4096


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _payload_signature(payload: dict[str, Any]) -> str:
    """Deterministic payload fingerprint for dedup (stable across dict order)."""
    return json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))


@dataclass(frozen=True)
class EventEnvelope:
    """One event on the bus, matching the canonical envelope in doc 10."""

    event_id: str
    event_type: str
    version: int
    occurred_at: str
    published_at: str
    source: str
    correlation_id: str
    causation_id: str
    priority: str
    privacy_class: str
    payload: dict[str, Any]
    sequence: int = 0

    def snapshot(self) -> dict[str, Any]:
        """Canonical envelope dict; ``event_type`` is kept for legacy readers."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "type": self.event_type,
            "version": self.version,
            "occurred_at": self.occurred_at,
            "published_at": self.published_at,
            "source": self.source,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "priority": self.priority,
            "privacy_class": self.privacy_class,
            "payload": dict(self.payload),
            "sequence": self.sequence,
        }


class EventBus:
    """In-memory autonomy event bus with the doc-10 contract.

    ``publish`` normalizes the envelope, deduplicates, applies bounded-queue
    backpressure, and appends to the ordered ring. ``replay`` / ``events``
    provide ordered, access-controlled reads.
    """

    def __init__(self, *, max_events: int = DEFAULT_MAX_EVENTS) -> None:
        self._max_events = max(1, int(max_events))
        self._events: deque[EventEnvelope] = deque(maxlen=self._max_events)
        self._sequence = 0
        self._published = 0
        self._deduped = 0
        self._dropped = 0
        self._by_type: Counter[str] = Counter()
        self._last_event_id: str = ""

    # ---- publishing ----

    def publish(
        self,
        event_type: str,
        payload: dict[str, Any],
        *,
        source: str = "runtime",
        correlation_id: str | None = None,
        causation_id: str | None = None,
        priority: str = DEFAULT_PRIORITY,
        privacy_class: str = DEFAULT_PRIVACY,
        version: int = DEFAULT_VERSION,
        occurred_at: str = "",
    ) -> EventEnvelope:
        """Publish one event and return its envelope.

        When correlation_id is omitted a fresh correlation domain is opened;
        when causation_id is omitted the previous event on the bus is the
        causal parent (natural chain). Duplicate (type, correlation, causation)
        publications collapse to the existing envelope (dedup).
        """
        if priority not in PRIORITY_ORDER:
            priority = DEFAULT_PRIORITY
        if privacy_class not in PRIVACY_RANK:
            privacy_class = DEFAULT_PRIVACY
        if not occurred_at:
            occurred_at = utc_now()
        corr = correlation_id or str(uuid4())
        # Causation is the causally-preceding event; the first event of a
        # correlation domain is caused by the domain root (its correlation_id).
        cause = causation_id or self._last_event_id or corr

        # Dedup: same event caused by the same prior event within the same
        # correlation domain is a re-delivery, not a new event.
        for existing in self._events:
            if (
                existing.event_type == event_type
                and existing.correlation_id == corr
                and existing.causation_id == cause
                and existing.source == source
                and _payload_signature(existing.payload) == _payload_signature(payload)
            ):
                self._deduped += 1
                return existing

        self._sequence += 1
        envelope = EventEnvelope(
            event_id=str(uuid4()),
            event_type=event_type,
            version=version,
            occurred_at=occurred_at,
            published_at=utc_now(),
            source=source,
            correlation_id=corr,
            causation_id=cause,
            priority=priority,
            privacy_class=privacy_class,
            payload=dict(payload),
            sequence=self._sequence,
        )

        # Bounded queue: drop the oldest event to keep safety/interactive
        # events from being starved by bursts of low-value events.
        if len(self._events) >= self._max_events:
            self._events.popleft()
            self._dropped += 1

        self._events.append(envelope)
        self._published += 1
        self._by_type[event_type] += 1
        self._last_event_id = envelope.event_id
        return envelope

    # ---- reads / replay ----

    def events(
        self,
        *,
        access_level: str = DEFAULT_PRIVACY,
        priority_min: str = "low",
        limit: int | None = None,
    ) -> tuple[EventEnvelope, ...]:
        """Ordered events visible to a consumer at ``access_level``.

        Access control: events whose privacy_class outranks the consumer's
        access level are withheld (no untrusted consumer sees them).
        Priority filtering honors ``priority_min`` (e.g. "high" → only
        high/critical events).
        """
        return self._filtered(access_level=access_level, priority_min=priority_min, limit=limit)

    def replay(
        self,
        *,
        event_type: str | None = None,
        correlation_id: str | None = None,
        access_level: str = DEFAULT_PRIVACY,
        priority_min: str = "low",
        limit: int | None = None,
    ) -> tuple[dict[str, Any], ...]:
        """Replay events as canonical snapshots (audit / simulation harness)."""
        out: list[EventEnvelope] = []
        for e in self._events:
            if event_type is not None and e.event_type != event_type:
                continue
            if correlation_id is not None and e.correlation_id != correlation_id:
                continue
            out.append(e)
        visible = self._filter(access_level=access_level, priority_min=priority_min, items=out)
        if limit is not None and limit > 0:
            visible = visible[-limit:]
        return tuple(e.snapshot() for e in visible)

    def events_by_type(self, event_type: str, *, limit: int | None = None) -> tuple[dict[str, Any], ...]:
        return self.replay(event_type=event_type, limit=limit)

    def since(self, sequence: int, *, access_level: str = DEFAULT_PRIVACY) -> tuple[dict[str, Any], ...]:
        """Events with sequence strictly greater than ``sequence`` (incremental)."""
        return tuple(
            e.snapshot()
            for e in self._events
            if e.sequence > sequence and PRIVACY_RANK[e.privacy_class] <= PRIVACY_RANK[access_level]
        )

    def latest_sequence(self) -> int:
        return self._sequence

    # ---- health ----

    def health(self) -> dict[str, Any]:
        return {
            "published": self._published,
            "deduped": self._deduped,
            "dropped": self._dropped,
            "retained": len(self._events),
            "max_events": self._max_events,
            "per_type": dict(self._by_type),
        }

    # ---- helpers ----

    def _filter(
        self,
        *,
        access_level: str,
        priority_min: str,
        items: Iterable[EventEnvelope],
    ) -> list[EventEnvelope]:
        access_rank = PRIVACY_RANK.get(access_level, PRIVACY_RANK[DEFAULT_PRIVACY])
        priority_rank = PRIORITY_ORDER.get(priority_min, 0)
        return [
            e for e in items
            if PRIVACY_RANK[e.privacy_class] <= access_rank
            and PRIORITY_ORDER[e.priority] >= priority_rank
        ]

    def _filtered(
        self,
        *,
        access_level: str,
        priority_min: str,
        limit: int | None,
    ) -> tuple[EventEnvelope, ...]:
        visible = self._filter(access_level=access_level, priority_min=priority_min, items=self._events)
        if limit is not None and limit > 0:
            visible = visible[-limit:]
        return tuple(visible)
