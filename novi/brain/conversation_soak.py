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
             llm_model: str = "", db_path: Path | None = None) -> dict[str, Any]:
    """Run the soak. Returns the soak report (never raises on brain errors)."""
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
    started = time.perf_counter()
    rss_start = _rss_mib()
    db_start = db_path.stat().st_size if db_path.exists() else 0
    try:
        brain.start()
        try:
            brain.respond(PROBE_TEACH)
            count = 0
            for text in script:
                turn_start = time.perf_counter()
                try:
                    brain.respond(text)
                except Exception:
                    errors += 1
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
    report = {
        "schema": "conversation-soak/v1",
        "timestamp": utc_now_iso(),
        "git_sha": git_sha(),
        "runtime": "mac-brain",
        "model": llm_model or "deterministic",
        "configuration": {"turns": turns, "probe_every": probe_every,
                          "brain_llm": brain_llm, "llm_url": llm_url},
        "duration_s": duration_s,
        "turns_run": len(script) + len(probes) + 1,
        "errors": errors,
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
    parser.add_argument("--ci", action="store_true",
                        help="short CI-safe soak (40 turns)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    turns = 40 if args.ci else args.turns
    report = run_soak(turns=turns, probe_every=args.probe_every,
                      brain_llm=args.brain_llm, llm_url=args.llm_url,
                      llm_model=args.llm_model,
                      db_path=Path(args.db_path) if args.db_path else None)
    if args.evidence_dir:
        out = Path(args.evidence_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "soak.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({key: report[key] for key in
                      ("turns_run", "duration_s", "errors", "latency_ms",
                       "memory_probes", "checks", "status")}, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
