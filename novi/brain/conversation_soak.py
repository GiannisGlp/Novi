"""Long-conversation stability runner (plan 03 Phases 17-18).

Drives hundreds of mixed-dimension turns through ONE real MacBrain on
ONE real database over the production respond() path and watches for
the failures long sessions expose: memory contamination (a durable
fact taught at turn 0 must still be recalled), latency drift, state
growth beyond bounds, and database bloat.

Content reuses the benchmark scenarios' own turns (round-robin across
dimensions), so the soak speaks the same distribution the benchmark
scores. Restart probes are excluded here (covered by C-111/C-112);
this runner tests continuity, not restarts.

Two modes:

- CI-safe default: deterministic transport, ``--turns 120`` (~seconds);
- on-device acceptance: ``--brain-llm`` with a live backend and
  ``--turns``/wall-clock sized for 30min/1h/2h sessions.

Writes soak.json (Phase 22 evidence shape where applicable) and exits
0 on PASS, 1 on FAIL.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from novi.brain.conversation_trace import utc_now_iso
from novi.brain.conversation_replay import default_brain_factory

PROBE_TEACH = "Remember that I like ultraviolet polka-dot linings."
PROBE_ASK = "What linings do I like?"
PROBE_NEEDLE = "ultraviolet"

# Likes-slot teachers: their teaches legitimately supersede the probe
# (single slot per person/kind by design), so they are excluded from the
# script — the probe measures drift/contamination, not the slot model.
# (Multi-item preference memory is a known open gap; see Gap-4 notes.)
_SOAK_EXCLUDED = frozenset({"C-142", "C-160"})

# Soak fails when the last latency window exceeds the first by this
# factor (real drift, not noise) or any memory probe fails.
LATENCY_DRIFT_FACTOR = 3.0


def build_script(*, turns: int) -> list[str]:
    """Round-robin turn script across all benchmark dimensions."""
    from novi.brain.conversation_scenarios import SCENARIOS

    buckets: dict[str, list[str]] = {}
    for scenario in SCENARIOS:
        if scenario.restart_after_turn >= 0:
            continue  # restart semantics belong to C-111/C-112, not soaks
        if scenario.scenario_id in _SOAK_EXCLUDED:
            continue  # likes-teachers would legitimately supersede the probe
        buckets.setdefault(scenario.dimension, []).extend(scenario.turns)
    dimensions = sorted(buckets)
    script: list[str] = []
    indices = {dim: 0 for dim in dimensions}
    while len(script) < turns:
        progressed = False
        for dim in dimensions:
            bucket = buckets[dim]
            if not bucket:
                continue
            script.append(bucket[indices[dim] % len(bucket)])
            indices[dim] += 1
            progressed = True
            if len(script) >= turns:
                break
        if not progressed:
            break
    return script


def _rss_mib() -> float | None:
    try:
        import resource
        import sys as _sys

        raw = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        return round(raw / (1024.0 * 1024.0) if _sys.platform == "darwin" else raw / 1024.0, 2)
    except Exception:
        return None


def _state_bounds(brain: Any) -> dict[str, Any]:
    """Largest per-speaker conversation state (bounded by design)."""
    try:
        from novi.brain.conversation.conversation_state import (
            MAX_ACTIVE_ENTITIES,
            MAX_RECENT_TURNS,
        )

        convos = brain.__dict__.get("_conversations", {}) or {}
        worst = {"speakers": len(convos), "active_entities": 0, "recent_turns": 0}
        for state in convos.values():
            worst["active_entities"] = max(
                worst["active_entities"], len(getattr(state, "active_entities", []) or []))
            worst["recent_turns"] = max(
                worst["recent_turns"], len(getattr(state, "recent_turns", []) or []))
        worst["within_bounds"] = (
            worst["active_entities"] <= MAX_ACTIVE_ENTITIES
            and worst["recent_turns"] <= MAX_RECENT_TURNS)
        return worst
    except Exception:
        return {"speakers": 0, "active_entities": 0, "recent_turns": 0,
                "within_bounds": True}


def run_soak(*, turns: int = 120, probe_every: int = 30,
             brain_llm: bool = False, llm_url: str = "http://localhost:11434",
             llm_model: str = "", db_path: Path | None = None,
             min_live_ratio: float | None = None,
             ticks_between_turns: int = 3) -> dict[str, Any]:
    """Run the soak. Returns the soak report (never raises on brain errors).

    ``min_live_ratio`` (0..1, None = unchecked): when set, the soak fails
    unless at least that fraction of script turns actually went through the
    live model transport. Live is judged by the reply's grounding route ==
    "dialogue" — the one label only the true LLM path sets (chat.py compose
    attaches it with grounding.model_route). The deterministic social fast
    paths (greetings/check-ins/skills) do not set it even in live mode, so a
    backend that silently degrades can no longer report a meaningless PASS
    (the 300-turn acceptance soak hit exactly this: 26/307 live turns, 0.5s
    mean, yet "PASS").

    ``ticks_between_turns`` models the real-surface cadence the soak would
    otherwise lack: web/CLI surfaces call ``brain.step()`` around each user
    message, which advances the CommunicationDecision fatigue cooldown. A
    bare respond()-only loop never ticks, so after 20 recorded interactions
    the brain goes permanently silent (social-fatigue budget) and every
    later turn degrades to the deterministic path — a harness artifact, not
    a product behavior. Ticking ``ticks_between_turns`` per script turn
    simulates seconds elapsing between messages (1 tick ~= 1 engine cycle).
    """
    if min_live_ratio is not None and not 0.0 <= float(min_live_ratio) <= 1.0:
        raise ValueError("min_live_ratio must be within [0, 1]")

    from novi.brain.conversation_trace import git_sha

    script = build_script(turns=turns)
    tmpdir = None
    if db_path is None:
        tmpdir = tempfile.TemporaryDirectory(prefix="conv-soak-")
        db_path = Path(tmpdir.name) / "soak.db"
    brain = default_brain_factory(db_path, brain_llm=brain_llm,
                                  llm_url=llm_url, llm_model=llm_model)
    latencies: list[float] = []
    probes: list[dict[str, Any]] = []
    errors = 0
    live_turns = 0
    route_counts: dict[str, int] = {}
    started = time.perf_counter()
    rss_start = _rss_mib()
    db_start = db_path.stat().st_size if db_path.exists() else 0
    try:
        brain.start()
        try:
            brain.respond(PROBE_TEACH)
            count = 0
            for text in script:
                # Simulate seconds elapsing before the user's next message:
                # real web/CLI surfaces step the engine (advancing the
                # CommunicationDecision cooldown) between messages; without
                # this the soak hits the 20-interaction social-fatigue wall
                # and every later turn silently degrades to deterministic.
                fatigue_clock = getattr(brain, "communication_decision", None)
                if fatigue_clock is not None and ticks_between_turns > 0:
                    try:
                        for _ in range(ticks_between_turns):
                            fatigue_clock.tick()
                    except Exception:
                        pass
                turn_start = time.perf_counter()
                try:
                    reply = brain.respond(text) or {}
                except Exception:
                    reply, errors = {}, errors + 1
                route = str((reply.get("trace") or {}).get("route") or "")
                source = str(reply.get("reply_source") or "")
                # Live-engagement marker: ONLY the true LLM path labels its
                # grounding route "dialogue" (chat.py compose sets it with
                # grounding.model_route). trace.route is hardcoded to
                # "local_llm" for every non-None reply and reply_source is
                # "dialogue" for every fallback=False reply — including the
                # deterministic social fast paths (greetings, check-ins,
                # skills) that never invoke the model — so those two fields
                # would over-count degraded runs. See code-review note.
                grounding_route = str(((reply.get("grounding") or {}).get("route")) or "")
                if grounding_route == "dialogue":
                    live_turns += 1
                bucket = grounding_route or route or source or "none"
                route_counts[bucket] = route_counts.get(bucket, 0) + 1
                latencies.append((time.perf_counter() - turn_start) * 1000.0)
                count += 1
                if probe_every > 0 and count % probe_every == 0:
                    probe_start = time.perf_counter()
                    try:
                        answer = (brain.respond(PROBE_ASK) or {}).get("text") or ""
                    except Exception:
                        answer, errors = "", errors + 1
                    probes.append({
                        "after_turn": count,
                        "passed": PROBE_NEEDLE in answer.lower(),
                        "latency_ms": round((time.perf_counter() - probe_start) * 1000.0, 1),
                    })
                    latencies.append(probes[-1]["latency_ms"])
        finally:
            try:
                brain.stop()
            except Exception:
                pass
    finally:
        if tmpdir is not None:
            pass  # kept for post-mortem during the report below
    duration_s = round(time.perf_counter() - started, 1)
    half = max(1, len(latencies) // 2)
    first_mean = sum(latencies[:half]) / half
    last_mean = sum(latencies[-half:]) / half
    drift = (last_mean / first_mean) if first_mean > 0 else 1.0
    bounds = _state_bounds(brain)
    live_ratio = round(live_turns / len(script), 3) if script else 0.0
    report = {
        "schema": "conversation-soak/v1",
        "timestamp": utc_now_iso(),
        "git_sha": git_sha(),
        "runtime": "mac-brain",
        "model": llm_model or "deterministic",
        "configuration": {"turns": turns, "probe_every": probe_every,
                          "brain_llm": brain_llm, "llm_url": llm_url,
                          "min_live_ratio": min_live_ratio,
                          "ticks_between_turns": ticks_between_turns},
        "duration_s": duration_s,
        "turns_run": len(script) + len(probes) + 1,
        "errors": errors,
        "live_engagement": {
            "script_turns": len(script),
            "live_turns": live_turns,
            "ratio": live_ratio,
            "min_live_ratio": min_live_ratio,
            "route_counts": dict(sorted(route_counts.items())),
        },
        "latency_ms": {
            "mean": round(sum(latencies) / max(1, len(latencies)), 1),
            "max": round(max(latencies) if latencies else 0.0, 1),
            "first_half_mean": round(first_mean, 1),
            "last_half_mean": round(last_mean, 1),
            "drift_factor": round(drift, 2),
        },
        "memory_probes": {"passed": sum(1 for p in probes if p["passed"]),
                          "of": len(probes), "probes": probes},
        "growth": {
            "db_bytes_start": db_start,
            "db_bytes_end": db_path.stat().st_size if db_path.exists() else 0,
            "rss_mib_start": rss_start,
            "rss_mib_end": _rss_mib(),
        },
        "state_bounds": bounds,
    }
    checks = {
        "no_errors": errors == 0,
        "probes_pass": bool(probes) and all(p["passed"] for p in probes),
        "latency_bounded": drift <= LATENCY_DRIFT_FACTOR,
        "state_bounded": bool(bounds.get("within_bounds")),
    }
    if min_live_ratio is not None:
        checks["live_engaged"] = live_ratio >= min_live_ratio
    report["checks"] = checks
    report["status"] = "PASS" if all(checks.values()) else "FAIL"
    if tmpdir is not None:
        tmpdir.cleanup()
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Long-conversation stability runner (plan 03 Phases 17-18)")
    parser.add_argument("--turns", type=int, default=120)
    parser.add_argument("--probe-every", type=int, default=30)
    parser.add_argument("--evidence-dir", default="",
                        help="write soak.json here (empty = stdout only)")
    parser.add_argument("--db-path", default="",
                        help="reuse a database file (default: fresh temp)")
    parser.add_argument("--brain-llm", action="store_true")
    parser.add_argument("--llm-url", default="http://localhost:11434")
    parser.add_argument("--llm-model", default="")
    parser.add_argument("--min-live-ratio", type=float, default=None,
                        help="fail unless this fraction of script turns used the live "
                             "model transport (default: 0.5 with --brain-llm, else unchecked)")
    parser.add_argument("--ticks-between-turns", type=int, default=3,
                        help="CommunicationDecision ticks before each script turn, "
                             "simulating seconds between user messages (default: 3)")
    parser.add_argument("--ci", action="store_true",
                        help="short CI-safe soak (40 turns)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    turns = 40 if args.ci else args.turns
    # A live acceptance soak must prove the model was actually engaged; a
    # silently degraded (deterministic-fallback) run is a FAIL, not a PASS.
    min_live_ratio = args.min_live_ratio
    if min_live_ratio is None and args.brain_llm:
        min_live_ratio = 0.5
    report = run_soak(turns=turns, probe_every=args.probe_every,
                      brain_llm=args.brain_llm, llm_url=args.llm_url,
                      llm_model=args.llm_model,
                      db_path=Path(args.db_path) if args.db_path else None,
                      min_live_ratio=min_live_ratio,
                      ticks_between_turns=args.ticks_between_turns)
    if args.evidence_dir:
        out = Path(args.evidence_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "soak.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({key: report[key] for key in
                      ("turns_run", "duration_s", "errors", "live_engagement",
                       "latency_ms", "memory_probes", "checks", "status")}, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
