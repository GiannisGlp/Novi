"""Central web-runtime resource budgets (plan 02, Phase 6).

Every long-lived collection, queue, and endpoint in the web runtime derives
its hard limit from here. Values are explicit, documented, and overridable
via environment variables so desktop and future Jetson deployments can set
different envelopes without code changes.

Ownership summary:
  recent events        -> bounded EventBus (brain) + bounded server _log
  compatibility events -> bounded compat window (brain config)
  current preview      -> latest frame only (integration_api)
  browser event window -> bounded UI window (frontend MAX_EVENTS)
  event dedup          -> cursor + bounded rolling window (frontend)
  chat threads         -> LRU-bound dict, "" pinned (server _threads/_seqs)
  object embeddings    -> FIFO-bound cache (camera loop)
  background workers   -> lifecycle owner (server start/stop)
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_int(name: str, default: int) -> int:
    try:
        return max(1, int(os.environ.get(name, default)))
    except (TypeError, ValueError):
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class WebRuntimeBudgets:
    """Hard limits for the web runtime. All values are maximums, not targets."""

    # Event pipeline
    max_events: int = 500  # server _log window (matches legacy 500-entry cap)
    event_batch_size: int = 200  # max entries per poll_events/SSE response
    max_event_payload_bytes: int = 65536  # per-entry guard at the web boundary
    # Chat
    max_chat_turns: int = 200  # per-thread conversation window (legacy cap)
    max_chat_threads: int = 16  # distinct per-person threads retained ("" pinned, LRU-evicted)
    # Object-embedding cache (camera loop, GAP-3 naming)
    max_object_embeddings: int = 64  # label -> vector entries retained (FIFO-evicted)
    # Preview (latest-frame semantics; never a history)
    preview_max_bytes: int = 200000  # max base64 payload served per frame
    preview_fps: int = 3  # ~300ms poll; budgets network/encode rate
    # Concurrency
    max_sse_clients: int = 16  # simultaneous /api/events/stream connections
    max_concurrent_requests: int = 32  # in-flight HTTP requests
    # Transport deadline per connection (seconds): socket I/O fails instead of
    # stalling forever behind a slow client. It does not preempt long handler
    # compute; pair with max_concurrent_requests for full slow-client cover.
    request_timeout_s: float = 30.0
    # SSE transport
    sse_heartbeat_s: float = 12.0
    sse_poll_interval_s: float = 0.25

    @classmethod
    def from_env(cls) -> "WebRuntimeBudgets":
        """Build budgets honoring NOVI_WEB_* overrides."""
        return cls(
            max_events=_env_int("NOVI_WEB_MAX_EVENTS", 500),
            event_batch_size=_env_int("NOVI_WEB_EVENT_BATCH_SIZE", 200),
            max_event_payload_bytes=_env_int("NOVI_WEB_MAX_EVENT_PAYLOAD_BYTES", 65536),
            max_chat_turns=_env_int("NOVI_WEB_MAX_CHAT_TURNS", 200),
            max_chat_threads=_env_int("NOVI_WEB_MAX_CHAT_THREADS", 16),
            max_object_embeddings=_env_int("NOVI_WEB_MAX_OBJECT_EMBEDDINGS", 64),
            preview_max_bytes=_env_int("NOVI_WEB_PREVIEW_MAX_BYTES", 200000),
            preview_fps=_env_int("NOVI_WEB_PREVIEW_FPS", 3),
            max_sse_clients=_env_int("NOVI_WEB_MAX_SSE_CLIENTS", 16),
            max_concurrent_requests=_env_int("NOVI_WEB_MAX_CONCURRENT_REQUESTS", 32),
            request_timeout_s=_env_float("NOVI_WEB_REQUEST_TIMEOUT", 30.0),
        )


# Process-wide default; tests construct small instances directly.
DEFAULT_BUDGETS: WebRuntimeBudgets = WebRuntimeBudgets()
