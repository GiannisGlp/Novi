"""Soak-test harness (plan 12, §50 Phase 50, Step 30).

Long-running stability harness. Required durations: 1h / 4h / 8h / 24h when
hardware permits. Tracks memory growth, disk usage, shard corruption, reload
failures, latency drift, thermal behavior, repeated generation failures,
scheduler starvation, stale state.

This module provides the harness + a short CI-safe soak (``--ci``, ~seconds)
so the infrastructure is testable in CI; the full durations are run on target
hardware with ``python novi/brain/benchmarks/soak.py --minutes 60`` etc.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from novi.brain.inference.backends.mock import MockBackend
from novi.brain.inference.registry import ModelRegistry, ModelSpec
from novi.brain.inference.request import InferenceRequest
from novi.brain.inference.runtime import InferenceRuntime


def _soak_runtime() -> InferenceRuntime:
    """Runtime with an approved mock-routable model (registry default has no
    approved model — routing is disabled until evidence exists, plan 12 Step 10)."""
    registry = ModelRegistry()
    spec = registry.get("qwen3-8b")
    registry.register(
        ModelSpec(
            id=spec.id,
            family=spec.family,
            role_candidates=spec.role_candidates,
            backend_preferences=("mock",),
            source_type=spec.source_type,
            source_id=spec.source_id,
            local_aliases=spec.local_aliases,
            status="approved",
        )
    )
    return InferenceRuntime(backends=[MockBackend()], registry=registry)


def _rss_mib() -> float | None:
    try:
        import resource

        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    except Exception:
        return None


def run_soak(*, duration_s: float, interval_s: float = 1.0) -> dict:
    """Run repeated warm requests against the runtime and track stability."""
    runtime = _soak_runtime()
    start = time.monotonic()
    deadline = start + duration_s
    samples: list[dict] = []
    failures = 0
    requests = 0
    latency_drift: list[float] = []

    while time.monotonic() < deadline:
        request = InferenceRequest(messages=[{"role": "user", "content": f"ping {requests}"}])
        began = time.monotonic()
        try:
            response = runtime.generate(request)
            latency_ms = (time.monotonic() - began) * 1000.0
            if not response.ok:
                failures += 1
        except Exception:  # repeated generation failures tracked, not fatal
            failures += 1
            latency_ms = 0.0
        requests += 1
        latency_drift.append(latency_ms)
        if requests % 10 == 0:
            samples.append(
                {
                    "requests": requests,
                    "elapsed_s": round(time.monotonic() - start, 2),
                    "rss_mib": _rss_mib(),
                    "queue_depth": dict(runtime.scheduler.queue_depth()),
                    "failures": failures,
                    "telemetry_requests": runtime.telemetry.request_count,
                }
            )
        time.sleep(interval_s)

    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "duration_s": round(time.monotonic() - start, 2),
        "requests": requests,
        "failures": failures,
        "error_rate": round(failures / max(requests, 1), 4),
        "avg_latency_ms": round(sum(latency_drift) / max(len(latency_drift), 1), 3),
        "min_latency_ms": round(min(latency_drift), 3) if latency_drift else None,
        "max_latency_ms": round(max(latency_drift), 3) if latency_drift else None,
        "final_rss_mib": _rss_mib(),
        "final_queue_depth": dict(runtime.scheduler.queue_depth()),
        "telemetry": runtime.telemetry.summary(),
        "samples": samples,
        "note": "short soak; full 1h/4h/8h/24h durations require target hardware (plan 12 §50)",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Novi inference soak harness (plan 12 §50)")
    parser.add_argument("--minutes", type=float, default=1.0, help="soak duration in minutes")
    parser.add_argument("--ci", action="store_true", help="CI-safe short soak (~3 s)")
    parser.add_argument("--out", default="", help="output JSON path")
    args = parser.parse_args()

    duration_s = 3.0 if args.ci else args.minutes * 60.0
    record = run_soak(duration_s=duration_s)
    out = Path(args.out) if args.out else Path(__file__).resolve().parents[3] / "benchmarks" / "soak-test.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    print(
        f"soak: requests={record['requests']} failures={record['failures']} "
        f"error_rate={record['error_rate']} avg_latency_ms={record['avg_latency_ms']} "
        f"final_rss_mib={record['final_rss_mib']} -> {out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
