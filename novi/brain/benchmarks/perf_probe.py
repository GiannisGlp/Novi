#!/usr/bin/env python3
"""PERF-PROBE: wall-clock per-step cost profile of the Novi Mac Brain.

Measures, with real execution (no synthetic numbers):

  1. Whole-brain ``MacBrain.step()`` latency for two perception stacks:
       - deterministic ``SpecialistPerception()`` (fixture backend),
       - neural ``SpecialistPerception(NeuralPerceptionBackend(...))``
         (torchvision SSDLite320-MobileNetV3, MPS when available).
  2. Sub-phase cost, timed OUTSIDE the brain loop:
       - fake camera ``read()`` (wrapper overhead only), and
       - ``SpecialistPerception.process(...)`` on the same BGR frame.
  3. Memory embedding-recall cost: ``DurableMemoryStore(':memory:')``
     with 200 admitted memories; 50 ``retrieve_semantic`` queries using
     the 'hash' embedder, plus a MiniLM attempt guarded by a 60 s model
     load budget (skipped honestly if exceeded).

stdlib-only harness (time.perf_counter / statistics / json / argparse).
Heavy dependencies (cv2, torch, sentence-transformers) are imported
lazily and every absence degrades to an explicit SKIP reason instead of
a crash. Always exits 0 unless argument parsing fails.

Usage:
    PYTHONPATH=. .venv/bin/python -m novi.brain.benchmarks.perf_probe \
        --json-out /tmp/perf.json
"""

from __future__ import annotations

import argparse
import contextlib
import json
import platform
import statistics
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

BENCH_ID = "PERF-PROBE"
REVISION = "1.0.0"

WARMUP_STEPS = 3
TIMED_STEPS = 20
PERCEPTION_WARMUP_REPS = 2
PERCEPTION_REPS = 30
CAMERA_READ_REPS = 30

MEMORIES_ADMIT = 200
RECALL_QUERIES = 50
MINILM_LOAD_TIMEOUT_S = 60.0     # spec: skip MiniLM timing if load exceeds 60 s
MINILM_JOIN_TIMEOUT_S = 180.0    # outer leash so the harness can never hang

SCENE_W, SCENE_H = 640, 480


def log(msg: str) -> None:
    """Progress goes to stderr; stdout stays reserved for the JSON summary."""
    print(msg, file=sys.stderr, flush=True)


# --------------------------------------------------------------------------- #
# statistics helpers (same linear-interpolation percentile style as
# novi/brain/benchmarks/arch_close_003_gate.py)
# --------------------------------------------------------------------------- #

def _pctl(samples: list[float], q: float) -> float:
    s = sorted(samples)
    n = len(s)
    if n == 1:
        return s[0]
    k = (n - 1) * q
    lo = int(k)
    hi = min(lo + 1, n - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def ms_summary(samples_ms: list[float]) -> dict[str, Any]:
    return {
        "count": len(samples_ms),
        "mean_ms": round(statistics.fmean(samples_ms), 3),
        "p50": round(_pctl(samples_ms, 0.50), 3),
        "p95": round(_pctl(samples_ms, 0.95), 3),
    }


def timed_calls(fn: Callable[[], Any], reps: int, warmup: int = 0) -> list[float]:
    """Run fn() reps times after warmup runs; return per-call milliseconds."""
    for _ in range(warmup):
        fn()
    out: list[float] = []
    for _ in range(reps):
        t0 = time.perf_counter()
        fn()
        out.append((time.perf_counter() - t0) * 1000.0)
    return out


# --------------------------------------------------------------------------- #
# synthetic scene + fake camera (stand-ins for MacCamera)
# --------------------------------------------------------------------------- #

def build_scene() -> tuple[Any, str]:
    """BGR uint8 640x480x3 synthetic living-room-ish scene for SSDLite."""
    try:
        import cv2
        import numpy as np

        img = np.full((SCENE_H, SCENE_W, 3), (60, 45, 35), dtype=np.uint8)
        # floor band
        cv2.rectangle(img, (0, 330), (SCENE_W, SCENE_H), (70, 90, 60), thickness=-1)
        # window
        cv2.rectangle(img, (430, 40), (600, 190), (235, 220, 170), thickness=-1)
        cv2.rectangle(img, (430, 40), (600, 190), (90, 70, 50), thickness=3)
        # table (rectangles)
        cv2.rectangle(img, (80, 250), (300, 270), (0, 110, 160), thickness=-1)
        cv2.rectangle(img, (100, 270), (120, 340), (0, 80, 120), thickness=-1)
        cv2.rectangle(img, (260, 270), (280, 340), (0, 80, 120), thickness=-1)
        # objects on/near the table (circles)
        cv2.circle(img, (140, 235), 22, (60, 60, 230), thickness=-1)   # red ball
        cv2.circle(img, (210, 232), 16, (230, 200, 60), thickness=-1)  # cyan ball
        cv2.circle(img, (500, 260), 30, (80, 170, 90), thickness=-1)   # green ball
        # person-like figure (rectangles + circle)
        cv2.circle(img, (380, 210), 26, (140, 150, 200), thickness=-1)
        cv2.rectangle(img, (360, 236), (400, 320), (150, 160, 210), thickness=-1)
        # book
        cv2.rectangle(img, (170, 240), (240, 252), (200, 200, 200), thickness=-1)
        return img, "cv2"
    except Exception as exc:  # pragma: no cover - degraded-honesty path
        try:
            import numpy as np
        except Exception:
            raise RuntimeError(f"SKIP scene: neither cv2 nor numpy usable ({exc})") from None
        img = np.zeros((SCENE_H, SCENE_W, 3), dtype=np.uint8)
        img[:240, :, 0] = 120          # crude blocks so detectors see *something*
        img[240:, :, 1] = 90
        img[100:200, 100:260, 2] = 200
        log(f"WARN: cv2 unavailable ({exc}); numpy fallback scene")
        return img, "numpy-fallback"


def make_fake_camera(payload: Any):
    """Camera double satisfying MacBrain: .read() -> CameraFrame, .close()."""
    from novi.brain.io import CameraFrame

    class ProbeCamera:
        def __init__(self) -> None:
            self._n = 0
            self.closed = False

        def read(self) -> CameraFrame:
            self._n += 1
            return CameraFrame(
                frame_id=f"probe-{self._n}",
                captured_at="t",
                width=SCENE_W,
                height=SCENE_H,
                payload=payload,
                metadata={},
            )

        def close(self) -> None:
            self.closed = True

    return ProbeCamera()


# --------------------------------------------------------------------------- #
# brain profiles
# --------------------------------------------------------------------------- #

def build_deterministic_perception():
    from novi.brain.b2_perception import SpecialistPerception

    return SpecialistPerception()  # fixture backend, no hardware/models


def build_neural_perception():
    from novi.brain.b2_perception import SpecialistPerception
    from novi.brain.models.neural_backend import NeuralPerceptionBackend

    backend = NeuralPerceptionBackend(confidence_threshold=0.45)
    device = getattr(getattr(backend, "detector", None), "device", None)
    return SpecialistPerception(backend), device


def brain_profile(perception, payload: Any, label: str) -> dict[str, Any]:
    """start -> warmup -> 20 timed steps -> sub-phase timings -> stop."""
    from novi.brain.engine import MacBrain, MacBrainConfig

    camera = make_fake_camera(payload)
    scratch = Path(tempfile.mkdtemp(prefix="novi-perf-probe-"))  # keep repo clean
    brain = MacBrain(
        camera=camera,
        perception=perception,
        stt=None,
        config=MacBrainConfig(curiosity_enabled=False, memory_dir=scratch),
    )
    try:
        brain.start()
        for _ in range(WARMUP_STEPS):
            brain.step()

        step_ms = timed_calls(brain.step, TIMED_STEPS)

        # Sub-phases, deliberately OUTSIDE the brain loop.
        camera_read_ms = timed_calls(camera.read, CAMERA_READ_REPS)

        def _process(n: int) -> None:
            perception.process(
                sensor_id="probe", frame_id=f"p{n}", timestamp="t", frame=payload
            )

        perception_ms = timed_calls(
            lambda: _process(perception_ms_counter()), PERCEPTION_REPS,
            warmup=PERCEPTION_WARMUP_REPS,
        )
    finally:
        brain.stop()

    return {
        "label": label,
        "step": ms_summary(step_ms),
        "camera_read_fake": ms_summary(camera_read_ms),
        "perception_process": ms_summary(perception_ms),
    }


def perception_ms_counter():  # unique frame ids without polluting timing scope
    global _FRAME_N
    _FRAME_N += 1
    return _FRAME_N


_FRAME_N = 0


# --------------------------------------------------------------------------- #
# embedding recall profile
# --------------------------------------------------------------------------- #

_OBJECTS = ("mug", "book", "ball", "key", "phone", "plant", "clock", "box")
_COLORS = ("red", "blue", "green", "yellow", "black", "white")
_PLACES = ("table", "shelf", "floor", "desk", "window")


def _admit_memories(store, n: int) -> float:
    t0 = time.perf_counter()
    for i in range(n):
        obj = _OBJECTS[i % len(_OBJECTS)]
        color = _COLORS[(i // len(_OBJECTS)) % len(_COLORS)]
        place = _PLACES[i % len(_PLACES)]
        store.admit(
            memory_type="perception",
            content=f"the {color} {obj} was seen near the {place} (slot {i})",
            confidence=0.9,
            verification_status="verified",
            privacy_class="public",
            provenance={"source": "perf-probe", "event_id": f"evt-{i}"},
        )
    return time.perf_counter() - t0


def _recall_queries(store, n: int) -> list[float]:
    samples: list[float] = []
    for i in range(n):
        obj = _OBJECTS[i % len(_OBJECTS)]
        place = _PLACES[(i * 3) % len(_PLACES)]
        query = f"where is the {obj} near the {place}?"
        t0 = time.perf_counter()
        store.retrieve_semantic(query, limit=5)
        samples.append((time.perf_counter() - t0) * 1000.0)
    return samples


def embed_hash_profile() -> dict[str, Any]:
    from novi.brain.storage import DurableMemoryStore

    store = DurableMemoryStore(":memory:", embedder="hash")
    try:
        admit_s = _admit_memories(store, MEMORIES_ADMIT)
        recall_ms = _recall_queries(store, RECALL_QUERIES)
    finally:
        store.close()
    return {"admit_total_s": round(admit_s, 4), "recall": ms_summary(recall_ms)}


def embed_minilm_profile() -> dict[str, Any]:
    """MiniLM variant, bounded: skip if the model load alone exceeds 60 s.

    Runs in a daemon thread so a hanging download can never wedge the probe;
    the outer join is a safety leash, the 60 s budget is measured precisely
    around store construction (which builds the embedding provider).
    """
    from novi.brain.storage import DurableMemoryStore

    result: dict[str, Any] = {}

    def worker() -> None:
        try:
            t0 = time.perf_counter()
            store = DurableMemoryStore(":memory:", embedder="minilm")
            load_s = time.perf_counter() - t0
            if load_s > MINILM_LOAD_TIMEOUT_S:
                result["status"] = "skipped"
                result["reason"] = (
                    f"MiniLM load took {load_s:.1f}s (> {MINILM_LOAD_TIMEOUT_S:.0f}s budget)"
                )
                with contextlib.suppress(Exception):
                    store.close()
                return
            admit_s = _admit_memories(store, MEMORIES_ADMIT)
            recall_ms = _recall_queries(store, RECALL_QUERIES)
            store.close()
            result["status"] = "ok"
            result["load_s"] = round(load_s, 2)
            result["admit_total_s"] = round(admit_s, 4)
            result["recall"] = ms_summary(recall_ms)
        except Exception as exc:
            result["status"] = "skipped"
            result["reason"] = f"{type(exc).__name__}: {exc}"

    th = threading.Thread(target=worker, name="minilm-profile", daemon=True)
    th.start()
    th.join(MINILM_JOIN_TIMEOUT_S)
    if not result:
        return {
            "status": "skipped",
            "reason": (
                f"no result within {MINILM_JOIN_TIMEOUT_S:.0f}s join leash "
                "(model load/download presumed stalled)"
            ),
        }
    return result


# --------------------------------------------------------------------------- #
# environment manifest
# --------------------------------------------------------------------------- #

def env_manifest(neural_device: str | None) -> dict[str, Any]:
    u = platform.uname()
    meta: dict[str, Any] = {
        "host": u.node,
        "os": f"{platform.system()} {platform.release()}",
        "machine": u.machine,
        "python": platform.python_version(),
        "mps_available": None,
        "torch": None,
        "torchvision": None,
        "neural_device": neural_device,
    }
    try:
        import torch
        import torchvision

        meta["torch"] = torch.__version__
        meta["torchvision"] = torchvision.__version__
        meta["mps_available"] = bool(getattr(torch.backends, "mps", None) and torch.backends.mps.is_available())
    except Exception:
        pass
    return meta


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #

def run_probe() -> dict[str, Any]:
    summary: dict[str, Any] = {
        "bench_id": BENCH_ID,
        "revision": REVISION,
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "params": {
            "warmup_steps": WARMUP_STEPS,
            "timed_steps": TIMED_STEPS,
            "perception_reps": PERCEPTION_REPS,
            "memories_admitted": MEMORIES_ADMIT,
            "recall_queries": RECALL_QUERIES,
            "scene_wh": [SCENE_W, SCENE_H],
        },
        "meta": {},
        "deterministic": None,
        "neural": None,
        "embed_hash_recall_ms_p50": None,
        "skips": [],
    }
    skips = summary["skips"]

    payload, scene_backend = build_scene()
    summary["meta"]["scene_backend"] = scene_backend

    # --- whole-brain + sub-phase profiles --------------------------------- #
    neural_device: str | None = None
    try:
        det_perc = build_deterministic_perception()
        log("[probe] deterministic brain: start/warmup/step ...")
        det_res = brain_profile(det_perc, payload, "deterministic")
        summary["deterministic"] = {
            "step_ms_p50": det_res["step"]["p50"],
            "step_ms_p95": det_res["step"]["p95"],
            "step_detail": det_res["step"],
            "perception_process_ms_p50": det_res["perception_process"]["p50"],
            "perception_process_ms_p95": det_res["perception_process"]["p95"],
            "camera_read_fake_ms_p50": det_res["camera_read_fake"]["p50"],
        }
        log(f"[probe] deterministic steps: {det_res['step']}")
    except Exception as exc:
        skips.append(f"deterministic brain: {type(exc).__name__}: {exc}")
        log(f"SKIP deterministic brain: {exc}")

    try:
        neu_perc, neural_device = build_neural_perception()
        log("[probe] neural brain: constructing SSDLite backend (may load weights) ...")
        neu_res = brain_profile(neu_perc, payload, "neural")
        summary["neural"] = {
            "step_ms_p50": neu_res["step"]["p50"],
            "step_ms_p95": neu_res["step"]["p95"],
            "step_detail": neu_res["step"],
            "perception_ms_p50": neu_res["perception_process"]["p50"],
            "perception_ms_p95": neu_res["perception_process"]["p95"],
            "perception_detail": neu_res["perception_process"],
            "camera_read_fake_ms_p50": neu_res["camera_read_fake"]["p50"],
        }
        log(f"[probe] neural steps: {neu_res['step']}")
        log(f"[probe] neural perception.process: {neu_res['perception_process']}")
    except Exception as exc:
        skips.append(f"neural brain: {type(exc).__name__}: {exc}")
        log(f"SKIP neural brain: {exc}")

    summary["meta"].update(env_manifest(neural_device))

    # --- embedding recall ---------------------------------------------------#
    try:
        log("[probe] hash-embedding recall ...")
        hash_res = embed_hash_profile()
        summary["embed_hash_recall_ms_p50"] = hash_res["recall"]["p50"]
        summary["embed_hash"] = hash_res
        log(f"[probe] hash recall: {hash_res}")
    except Exception as exc:
        skips.append(f"hash embed recall: {type(exc).__name__}: {exc}")
        log(f"SKIP hash embed recall: {exc}")

    log("[probe] MiniLM recall attempt (60s load budget) ...")
    mini_res = embed_minilm_profile()
    summary["embed_minilm"] = mini_res
    if mini_res.get("status") == "ok":
        summary["embed_minilm_recall_ms_p50"] = mini_res["recall"]["p50"]
        log(f"[probe] minilm recall: {mini_res}")
    else:
        skips.append(f"minilm recall: {mini_res.get('reason', 'unknown')}")
        log(f"SKIP minilm recall: {mini_res.get('reason')}")

    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="PERF-PROBE: wall-clock per-step cost profile of the Novi Mac Brain"
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="write the JSON summary to this path (still printed to stdout)",
    )
    args = parser.parse_args(argv)

    summary = run_probe()
    text = json.dumps(summary, indent=2, sort_keys=False)
    print(text)  # stdout: pure JSON summary, exit 0
    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text + "\n", encoding="utf-8")
        log(f"[probe] JSON written to {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
