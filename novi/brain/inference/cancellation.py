"""Cooperative request cancellation (plan 12, §20 Phase 15, §26 item 16).

Preemption is NOT implemented (plan 12, §20: "Do not implement preemption until
the backend lifecycle is proven safe"). Cancellation is cooperative: a request
checks its ``CancellationToken`` at safe boundaries (between layers, before
decode, between stream chunks) and aborts with ``InferenceCancelledError``.

Scheduler-level cancellation at request boundaries is allowed: a background
deep-reasoning request may be cancelled when a high-priority request arrives,
per the configured policy (wait | queue | cancel_background | switch_model |
smaller_fallback).
"""

from __future__ import annotations

import threading
from typing import Any


class CancellationToken:
    """Thread-safe cooperative cancellation token."""

    def __init__(self) -> None:
        self._cancelled = threading.Event()
        self._reason: str | None = None

    def cancel(self, reason: str = "cancelled") -> None:
        self._reason = reason
        self._cancelled.set()

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled.is_set()

    @property
    def reason(self) -> str | None:
        return self._reason

    def check(self) -> None:
        """Raise ``InferenceCancelledError`` if cancelled (call at boundaries)."""
        if self._cancelled.is_set():
            from .errors import InferenceCancelledError

            raise InferenceCancelledError(
                self._reason or "request cancelled",
                context={"cancelled": True},
            )

    def snapshot(self) -> dict[str, Any]:
        return {"cancelled": self.is_cancelled, "reason": self._reason}
