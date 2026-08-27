"""Sleep cycle & memory maturation (Phase P1).

A bounded background "sleep" phase that runs every N brain cycles and
matures the durable memory store:

1. **Consolidation** — ``SummaryConsolidator`` distills unconsolidated
   episodic groups into ``summary`` memories (idempotent per entity).
2. **Decay** — active memories whose ``expires_at`` passed are marked
   ``state='decayed'`` (row preserved; retrieval filters on state).
3. **Strengthening** — replay signal: memories recalled recently
   (``last_accessed_at`` within the phase window) get a confidence bump
   (+0.02, capped at 0.99) and stay ``active``.
4. **Summary refresh** — when a narrator callable is provided and returns
   non-None text, the oldest stale summary is re-written through
   ``update_memory``. Without a narrator the phase is fully deterministic.

Every phase uses existing store APIs only. Any exception is reported via
the optional ``emit`` callback as ``sleep.error`` and never propagates to
the engine loop. Deterministic and CI-safe: no network, no LLM required.
"""

from __future__ import annotations

import contextlib
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from .b1_memory import utc_now
from .consolidation import SummaryConsolidator

DECAYED_STATE = "decayed"
SUMMARY_MEMORY_TYPE = "summary"
STRENGTH_BUMP = 0.02
CONFIDENCE_CAP = 0.99


def _parse_utc(value: Any) -> datetime | None:
    """Parse an ISO timestamp ('Z' or '+00:00' suffix); None when unparseable."""
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class SleepCycle:
    """Scheduled memory-maturation pass over a durable memory store.

    Args:
        store: ``DurableMemoryStore`` (or anything exposing ``active_rows``,
            ``expired_ids``, ``set_state``, ``set_confidence``).
        consolidator: a ``SummaryConsolidator`` (constructed by the caller so
            an existing instance is reused, matching engine wiring).
        narrator: optional callable(list[dict]) -> str | None, same calling
            convention as ``chat.py`` (episodes list in, narrative out).
        every_n_cycles: run the phase when ``cycle % every_n_cycles == 0``.
        max_minutes_per_phase: recency window for replay-driven strengthening.
        emit: optional callable(event_type, payload) for audit events
            (``sleep.started``, ``sleep.consolidated``, ``sleep.decayed``,
            ``sleep.strengthened``, ``sleep.error``).
    """

    def __init__(
        self,
        store: Any,
        consolidator: SummaryConsolidator | None = None,
        narrator: Any | None = None,
        *,
        every_n_cycles: int = 500,
        max_minutes_per_phase: float = 1.0,
        emit: Any = None,
    ) -> None:
        self.store = store
        self.consolidator = consolidator
        self.narrator = narrator
        self.every_n_cycles = max(1, int(every_n_cycles))
        self.max_minutes_per_phase = float(max_minutes_per_phase)
        self._emit = emit
        # Observability: last phase report + run count (surfaced in /api/state).
        self.last_report: dict[str, Any] | None = None
        self.phases_run: int = 0

    # ---- scheduling -------------------------------------------------------

    def maybe_sleep(self, cycle: int) -> dict[str, Any] | None:
        """Run the sleep phase on cadence multiples; None otherwise.

        Returns ``{cycle, consolidated_groups, new_summaries, decayed,
        strengthened, duration_ms}``. Never raises.
        """
        cycle = int(cycle)
        if cycle <= 0 or cycle % self.every_n_cycles != 0:
            return None
        started = time.perf_counter()
        report: dict[str, Any] = {
            "cycle": cycle,
            "consolidated_groups": 0,
            "new_summaries": 0,
            "decayed": 0,
            "strengthened": 0,
            "duration_ms": 0.0,
        }
        self._emit_event("sleep.started", {"cycle": cycle})
        try:
            self._phase_consolidate(report)
            self._phase_decay(report)
            self._phase_strengthen(report)
            self._phase_refresh_summary(report)
        except Exception as exc:  # noqa: BLE001 - sleep must never kill the loop
            self._emit_event("sleep.error", {"cycle": cycle, "error": str(exc)})
        report["duration_ms"] = round((time.perf_counter() - started) * 1000.0, 2)
        self.last_report = report
        self.phases_run += 1
        return report

    # ---- phases -----------------------------------------------------------

    def _phase_consolidate(self, report: dict[str, Any]) -> None:
        if self.consolidator is None:
            return
        summary = self.consolidator.consolidate()
        report["consolidated_groups"] = int(getattr(summary, "groups", 0) or 0)
        report["new_summaries"] = int(getattr(summary, "created", 0) or 0)
        self._emit_event(
            "sleep.consolidated",
            {"cycle": report["cycle"], "groups": report["consolidated_groups"], "summaries": report["new_summaries"]},
        )

    def _phase_decay(self, report: dict[str, Any]) -> None:
        if self.store is None:
            return
        expired = self.store.expired_ids(utc_now())
        decayed = 0
        for memory_id in expired:
            if self.store.set_state(memory_id, DECAYED_STATE):
                decayed += 1
        report["decayed"] = decayed
        self._emit_event("sleep.decayed", {"cycle": report["cycle"], "count": decayed})

    def _phase_strengthen(self, report: dict[str, Any]) -> None:
        if self.store is None:
            return
        window_s = max(0.0, self.max_minutes_per_phase) * 60.0
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=window_s)
        strengthened = 0
        for item in self.store.active_rows():  # state='active' rows only
            last_accessed = item.get("last_accessed_at")
            if not last_accessed:
                continue
            accessed_at = _parse_utc(last_accessed)
            if accessed_at is None or accessed_at < cutoff:
                continue
            record = item["record"]
            new_conf = min(CONFIDENCE_CAP, float(record.confidence) + STRENGTH_BUMP)
            if new_conf > record.confidence:
                self.store.set_confidence(record.memory_id, new_conf)
                strengthened += 1
        report["strengthened"] = strengthened
        self._emit_event("sleep.strengthened", {"cycle": report["cycle"], "count": strengthened})

    def _phase_refresh_summary(self, report: dict[str, Any]) -> None:
        """Re-narrate the single oldest summary through the narrator (best-effort)."""
        if self.narrator is None or self.store is None:
            return
        summaries = [
            item
            for item in self.store.active_rows()
            if item["record"].memory_type == SUMMARY_MEMORY_TYPE
        ]
        if not summaries:
            return
        oldest = min(summaries, key=lambda item: item["record"].created_at)
        record = oldest["record"]
        content = record.content if isinstance(record.content, str) else str(record.content)
        episodes = [{"memory_type": record.memory_type, "content": content}]
        # No local guard here BY DESIGN: this phase runs last, so a failing
        # narrator escapes to maybe_sleep's outer wrapper, which logs
        # sleep.error — every exception stays auditable and non-propagating.
        refreshed = self.narrator(episodes)
        if not refreshed or not str(refreshed).strip():
            return
        self.store.update_memory(record.memory_id, content=str(refreshed).strip())

    # ---- helpers ----------------------------------------------------------

    def _emit_event(self, event_type: str, payload: dict[str, Any]) -> None:
        if self._emit is None:
            return
        with contextlib.suppress(Exception):  # auditing must never crash sleep
            self._emit(event_type, payload)
