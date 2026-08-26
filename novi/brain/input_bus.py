"""Prioritized input bus — the front door of the unified input architecture.

Every source (web chat, web voice, CLI, camera presence, audio events)
enqueues here WITHOUT touching the brain lock: ``put`` never blocks, so a
slow producer (mic recording, remote HTTP) can never stall cognition.
The engine drains the bus once per cycle inside its cognition loop and
processes inputs in priority order:

    PRI_INTERRUPT 0 — direct address ("Novi, …"), overrides anything
    PRI_SPEECH    1 — voice/text conversational turns
    PRI_EVENT     2 — presence transitions / scene changes
    PRI_AMBIENT   3 — low-value ambient signals

Coalescing: bursts of the same logical signal (e.g. repeated presence
frames) collapse to the newest envelope; a higher-priority replacement
always wins. Bounded queue: on overflow the lowest-priority oldest item
is dropped first (never an interrupt). All public methods are thread-safe
via a single Condition — no busy waiting anywhere.
"""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any

# Priority bands (lower number = processed first).
PRI_INTERRUPT = 0
PRI_SPEECH = 1
PRI_EVENT = 2
PRI_AMBIENT = 3

_PRIORITIES = (PRI_INTERRUPT, PRI_SPEECH, PRI_EVENT, PRI_AMBIENT)


def classify_priority(source: str, kind: str) -> int:
    """Map (source, kind) onto a priority band.

    Direct address always interrupts regardless of origin; speech turns come
    next; discrete world events after that; everything else is ambient.
    """
    kind_l = (kind or "").strip().lower()
    if kind_l in ("interrupt", "address", "direct"):
        return PRI_INTERRUPT
    if kind_l in ("chat", "voice", "text", "message", "command", "speech"):
        # A command addressed at Novi by name interrupts; other speech doesn't.
        return PRI_INTERRUPT if kind_l == "command" else PRI_SPEECH
    if kind_l in (
        "presence.entered", "presence.left", "scene.changed",
        "person_entered", "person_left", "vision", "audio_event",
    ):
        return PRI_EVENT
    return PRI_AMBIENT


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class InputEnvelope:
    """One unit of work for the brain, stamped with provenance and priority."""

    seq: int
    source: str
    kind: str
    priority: int
    payload: Any
    submitted_at: str
    coalesce_key: str | None = None
    drop_count: int = 0


@dataclass
class _BusStats:
    total_submitted: int = 0
    total_dropped: int = 0
    per_source: dict[str, int] = field(default_factory=dict)


class InputBus:
    """Bounded, coalescing, prioritized MPSC queue feeding one cognition loop."""

    def __init__(self, maxsize: int = 512) -> None:
        self._cond = threading.Condition()
        self._queues: dict[int, deque[InputEnvelope]] = {p: deque() for p in _PRIORITIES}
        self._coalesce: dict[str, tuple[int, int]] = {}  # key -> (priority, seq)
        self._seq = 0
        self._closed = False
        self._maxsize = max(1, int(maxsize))
        self._stats = _BusStats()

    # -- producers (never block) ---------------------------------------------

    def put(
        self,
        *,
        source: str,
        kind: str,
        payload: Any = None,
        priority: int | None = None,
        coalesce_key: str | None = None,
    ) -> InputEnvelope:
        """Enqueue one input. Never blocks; assigns the monotonic seq."""
        with self._cond:
            if self._closed:
                raise RuntimeError("input bus is closed")
            self._seq += 1
            pri = int(priority) if priority is not None else classify_priority(source, kind)
            if pri not in self._queues:
                pri = PRI_AMBIENT
            env = InputEnvelope(
                seq=self._seq,
                source=source,
                kind=kind,
                priority=pri,
                payload=payload,
                submitted_at=_utc_now_iso(),
                coalesce_key=(coalesce_key or None),
            )
            # Coalescing: replace an older envelope under the same key.
            replaced = False
            if env.coalesce_key:
                old = self._coalesce.get(env.coalesce_key)
                if old is not None:
                    old_pri, old_seq = old
                    q = self._queues[old_pri]
                    for idx, candidate in enumerate(q):
                        if candidate.seq == old_seq:
                            if env.priority <= old_pri:
                                # newest wins within same/higher band; keep count
                                env = replace(env, drop_count=candidate.drop_count + 1)
                                q[idx] = env
                                replaced = True
                            break
                    else:
                        old_entry = self._coalesce.pop(env.coalesce_key, None)
                        del old_entry  # stale bookkeeping only
                    if replaced:
                        self._coalesce[env.coalesce_key] = (env.priority, env.seq)

            if not replaced:
                self._queues[env.priority].append(env)
                if env.coalesce_key:
                    self._coalesce[env.coalesce_key] = (env.priority, env.seq)
                self._evict_overflow_locked()

            self._stats.total_submitted += 1
            self._stats.per_source[source] = self._stats.per_source.get(source, 0) + 1
            self._cond.notify_all()
            return env

    def _evict_overflow_locked(self) -> None:
        depth = sum(len(q) for q in self._queues.values())
        while depth > self._maxsize:
            victim_pri = next((p for p in sorted(_PRIORITIES, reverse=True) if self._queues[p]), None)
            if victim_pri is None:
                return
            victim = self._queues[victim_pri].popleft()
            if victim.coalesce_key:
                self._coalesce.pop(victim.coalesce_key, None)
            self._stats.total_dropped += 1
            depth -= 1

    # -- consumer (the cognition loop) ---------------------------------------

    def drain(self, max_items: int = 16, timeout_s: float = 0.0) -> list[InputEnvelope]:
        """Return up to ``max_items`` envelopes ordered by (priority, seq).

        Blocks up to ``timeout_s`` when empty; returns [] when closed or when
        nothing arrives within the window.
        """
        with self._cond:
            if not self._closed and self._depth_locked() == 0 and timeout_s > 0:
                self._cond.wait(timeout_s)
            out: list[InputEnvelope] = []
            for pri in _PRIORITIES:
                q = self._queues[pri]
                while q and len(out) < max_items:
                    env = q.popleft()
                    if env.coalesce_key:
                        cur = self._coalesce.get(env.coalesce_key)
                        if cur and cur[1] == env.seq:
                            self._coalesce.pop(env.coalesce_key, None)
                    out.append(env)
                if len(out) >= max_items:
                    break
            return out

    def close(self) -> None:
        """Close the bus; waiters wake and later drains return []."""
        with self._cond:
            self._closed = True
            self._cond.notify_all()

    # -- introspection ---------------------------------------------------------

    @property
    def closed(self) -> bool:
        with self._cond:
            return self._closed

    def stats(self) -> dict[str, Any]:
        with self._cond:
            return {
                "total_submitted": self._stats.total_submitted,
                "total_dropped": self._stats.total_dropped,
                "per_source": dict(self._stats.per_source),
                "depth": self._depth_locked(),
                "maxsize": self._maxsize,
                "closed": self._closed,
            }

    def _depth_locked(self) -> int:
        return sum(len(q) for q in self._queues.values())
