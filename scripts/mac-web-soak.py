"""Short-horizon web-runtime soak harness (plan 02, Phase 11).

Runs a NoviWebServer in-process on a realistic workload — auto-stepping
brain, chat turns, event polling with a moving cursor (page navigation),
preview frames — and samples /api/runtime/metrics. Fails when any bounded
counter exceeds its limit or RSS shows a persistent runaway slope.

This is the quick gate. The full 30-60 minute acceptance soak is the same
workload with --seconds 1800/3600 plus a real camera, LLM, and browser.

Usage:
    .venv/bin/python scripts/mac-web-soak.py [--seconds 300] [--tick 0.05]
"""

from __future__ import annotations

import argparse
import contextlib
import statistics
import sys
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def rss_slope_bps(samples: list[tuple[float, float]]) -> float:
    """Least-squares slope of RSS over time (bytes/sec)."""
    n = len(samples)
    if n < 3:
        return 0.0
    mx = statistics.fmean(t for t, _ in samples)
    my = statistics.fmean(v for _, v in samples)
    denom = sum((t - mx) ** 2 for t, _ in samples)
    if denom == 0:
        return 0.0
    return sum((t - mx) * (v - my) for t, v in samples) / denom


def main() -> int:
    ap = argparse.ArgumentParser(description="Novi web-runtime soak gate")
    ap.add_argument("--seconds", type=float, default=300.0)
    ap.add_argument("--tick", type=float, default=0.05)
    ap.add_argument("--sample-every", type=float, default=10.0)
    ap.add_argument(
        "--max-slope-bps", type=float, default=65536.0, help="fail if RSS slope over the second half exceeds this"
    )
    args = ap.parse_args()

    from novi.web.server import NoviWebServer

    server = NoviWebServer(port=0, store_path=None, auto_step=True, tick=args.tick, chat_llm=False)
    server.start()
    # Python-heap series always works (even where /bin/ps is sandboxed) and
    # directly reflects the fixed leak class (event-list object retention).
    tracemalloc.start()
    rss: list[tuple[float, float]] = []
    pyheap: list[tuple[float, float]] = []
    failures: list[str] = []
    after = 0
    pages = ("/overview", "/camera", "/events", "/chat", "/memory")
    t0 = time.time()
    try:
        i = 0
        while time.time() - t0 < args.seconds:
            page = pages[i % len(pages)]
            # Simulate the active page's demand pattern.
            if page in ("/events", "/overview"):
                chunk = server.poll_events(after)
                after = chunk["after"]
                if chunk.get("has_more"):
                    chunk = server.poll_events(after)
                    after = chunk["after"]
            if page == "/camera":
                server.preview_frame()
            if page == "/chat" and i % 2 == 0:
                with contextlib.suppress(Exception):
                    server.chat_send(f"soak message {i}")
            if page == "/overview":
                server.state()
            m = server.runtime_metrics()
            now = time.time() - t0
            if m["rss_bytes"] is not None:
                rss.append((now, float(m["rss_bytes"])))
            pyheap.append((now, float(tracemalloc.get_traced_memory()[0])))
            for count_key, limit_key in (
                ("compat_event_count", "compat_event_limit"),
                ("server_log_size", "server_log_limit"),
                ("active_sse_clients", "sse_limit"),
                ("preview_frame_bytes", "preview_max_bytes"),
            ):
                if m[count_key] > m[limit_key]:
                    failures.append(f"{count_key}={m[count_key]} over {limit_key}={m[limit_key]}")
            if m["eventbus_size"] > m["eventbus_limit"]:
                failures.append(f"eventbus_size={m['eventbus_size']} over limit")
            i += 1
            time.sleep(min(args.sample_every, max(0.0, args.seconds - (time.time() - t0))))
        # Slopes over the second half only: warmup allocation is not a leak.
        # RSS when the platform allows it, Python heap always.
        second_rss = [s for s in rss if s[0] >= args.seconds / 2]
        second_py = [s for s in pyheap if s[0] >= args.seconds / 2]
        slope = rss_slope_bps(second_rss if len(second_rss) >= 3 else rss)
        pyslope = rss_slope_bps(second_py if len(second_py) >= 3 else pyheap)
        rss_txt = f"{rss[-1][1] / 1e6:.1f}MB slope={slope:.1f}B/s" if rss else "unavailable (sandboxed ps)"
        print(
            f"samples={len(pyheap)} rss={rss_txt} pyheap_end={pyheap[-1][1] / 1e6:.1f}MB "
            f"pyheap_slope={pyslope:.1f}B/s "
            f"compat={m['compat_event_count']}/{m['compat_event_limit']} "
            f"log={m['server_log_size']}/{m['server_log_limit']}"
        )
        if rss and slope > args.max_slope_bps:
            failures.append(f"rss slope {slope:.1f} B/s over {args.max_slope_bps:.1f} B/s")
        if pyslope > args.max_slope_bps:
            failures.append(f"python-heap slope {pyslope:.1f} B/s over {args.max_slope_bps:.1f} B/s")
    finally:
        server.stop()

    if failures:
        print("SOAK FAIL:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("SOAK PASS: counters bounded, RSS slope within budget")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
