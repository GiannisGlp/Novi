#!/usr/bin/env python3
"""Mac feasibility experiment for nvidia/LocateAnything-3B (plan Phase 4, §19 steps 10-14).

Runs with the isolated venv:  .venv-locateanything/bin/python scripts/mac-locateanything-experiment.py

Covers plan steps:
  4.2 load-only test (versions, device, memory before/after, load time, revision)
  4.3 single inference on novi/assets/test-image.png ("locate all objects visible in the image")
  4.4 grounding queries: person / largest object / nearest center / absent object
  4.5 stress: 1 / 5 / 10 repeated queries, multiple boxes, large / small / cluttered image,
      p50/p95/p99 latency + memory

Dogfoods the real Novi path: LocateAnythingRuntime -> LocateAnythingBackend ->
strict parser -> typed GroundingObservation. Raw output, parse outcome and
adapter result are all recorded; failures are recorded, never papered over.

Writes evidence to docs/07-locate-anything/evidence/mac-feasibility-<timestamp>.json
"""

from __future__ import annotations

import io
import json
import os
import resource
import statistics
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault(
    "HF_HOME", os.path.expanduser("~/.cache/novi/models/locateanything-hf")
)

from PIL import Image  # noqa: E402

from novi.brain.io import CameraFrame  # noqa: E402
from novi.perception.grounding import SpatialInferenceMode, SpatialInferencePolicy, SpatialQuery  # noqa: E402
from novi.perception.locate_anything import LocateAnythingBackend  # noqa: E402
from novi.perception.locate_anything_runtime import LocateAnythingRuntime, probe_capabilities  # noqa: E402


def _rss_gb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024**3)


def _frame_from_pil(image: Image.Image, fid: str) -> CameraFrame:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return CameraFrame(frame_id=fid, captured_at=time.strftime("%H:%M:%S"), width=image.width, height=image.height, payload=buf.getvalue())


def _make_test_images() -> dict[str, Image.Image]:
    base = Image.open(REPO_ROOT / "novi" / "assets" / "test-image.png").convert("RGB")

    large = Image.new("RGB", (1920, 1080))
    px = large.load()
    for y in range(0, 1080, 16):
        for x in range(0, 1920, 16):
            px[x, y] = ((x * 255) // 1920, (y * 255) // 1080, 120)
    from PIL import ImageDraw as _ID  # noqa: PLC0415

    d_large = _ID.Draw(large)
    for i in range(6):
        color = ((i * 40) % 255, (i * 90) % 255, (i * 30) % 255)
        d_large.rectangle((100 + i * 300, 80 + i * 150, 400 + i * 300, 380 + i * 150), fill=color)

    small = base.resize((64, 64))

    cluttered = Image.new("RGB", (640, 480), (30, 30, 30))
    d_clutter = _ID.Draw(cluttered)
    import random  # noqa: PLC0415

    rng = random.Random(7)
    for _ in range(40):
        x0, y0 = rng.randint(0, 600), rng.randint(0, 440)
        w, h = rng.randint(10, 90), rng.randint(10, 90)
        d_clutter.rectangle((x0, y0, x0 + w, y0 + h), fill=(rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255)))

    return {"base": base, "large": large, "small": small, "cluttered": cluttered}


def main() -> int:
    evidence: dict = {
        "model_id": "nvidia/LocateAnything-3B",
        "revision": "c32291ca5e996f5a7a485845b4f57a233936bba0",
        "python": sys.version.split()[0],
        "runtime": {},
        "load": {},
        "inferences": [],
        "stress": {},
        "decision_gate": {},
    }

    # ---- Step 4.2 load-only test -----------------------------------------
    import torch  # noqa: PLC0415
    import transformers  # noqa: PLC0415

    evidence["runtime"]["torch"] = torch.__version__
    evidence["runtime"]["transformers"] = transformers.__version__
    evidence["runtime"]["mps_available"] = bool(torch.backends.mps.is_available())
    evidence["runtime"]["device"] = "mps" if torch.backends.mps.is_available() else "cpu"

    caps = probe_capabilities()
    evidence["capability_state"] = caps.state.value
    evidence["capability_details"] = list(caps.details)
    print(f"[probe] state={caps.state.value} device={caps.device} mem_gb={caps.details}")

    mem_before = _rss_gb()
    load_attempts: list[dict] = []
    runtime = None
    for dtype_name, dtype in (("bfloat16", torch.bfloat16), ("float32", torch.float32)):
        attempt: dict = {"dtype": dtype_name}
        started = time.perf_counter()
        try:
            from functools import partial  # noqa: PLC0415

            loader = partial(_load_with_dtype, dtype)
            runtime = LocateAnythingRuntime(loader=loader)
            runtime.load()
            attempt["load_seconds"] = round(time.perf_counter() - started, 2)
            attempt["ok"] = True
        except Exception as exc:  # noqa: BLE001 — recording, not masking
            attempt["ok"] = False
            attempt["error"] = f"{type(exc).__name__}: {exc}"
        load_attempts.append(attempt)
        print(f"[load {dtype_name}] ok={attempt['ok']} {attempt.get('load_seconds')}s {attempt.get('error', '')}")
        if runtime is not None and attempt["ok"]:
            break

    mem_after_load = _rss_gb()
    evidence["load"]["attempts"] = load_attempts
    evidence["load"]["mem_before_gb"] = round(mem_before, 2)
    evidence["load"]["mem_after_gb"] = round(mem_after_load, 2)
    evidence["load"]["mem_delta_gb"] = round(mem_after_load - mem_before, 2)
    if not any(a["ok"] for a in load_attempts):
        evidence["decision_gate"] = {"outcome": "C", "reason": "model could not load on this Mac at all"}
        _write_evidence(evidence)
        print("FAILED: no dtype loaded the model")
        return 1

    # ---- adapter wiring (dogfood the real path) --------------------------
    class RecordingRuntime:
        """Wraps the real runtime; records the last raw text for evidence."""

        def __init__(self, inner):
            self._inner = inner
            self.last_raw: str | None = None

        def probe(self):
            return self._inner.probe()

        def infer(self, image, prompt, mode):
            raw, latency = self._inner.infer(image, prompt, mode)
            self.last_raw = raw
            return raw, latency

    recording = RecordingRuntime(runtime)  # type: ignore[arg-type]
    backend = LocateAnythingBackend()
    backend.attach_runtime(recording)  # type: ignore[arg-type]
    images = _make_test_images()
    frame = _frame_from_pil(images["base"], "test-image")

    def run_query(text: str, *, frame_id: str = "test-image", image: Image.Image | None = None, mode: SpatialInferenceMode = SpatialInferenceMode.HYBRID, tag: str = "") -> dict:
        f = _frame_from_pil(image or images["base"], frame_id)
        q = SpatialQuery(text=text, frame_id=frame_id, timestamp="t0")
        policy = SpatialInferencePolicy(mode=mode)
        t0 = time.perf_counter()
        result = backend.ground(f, q, policy)
        wall = round((time.perf_counter() - t0) * 1000.0, 1)
        rec = {
            "tag": tag or text,
            "query": text,
            "mode": mode.value,
            "latency_ms": result.latency_ms,
            "wall_ms": wall,
            "rss_gb": round(_rss_gb(), 2),
            "success": result.success,
            "no_object": result.no_object,
            "backend_status": result.backend_status,
            "n_observations": len(result.observations),
            "observations": [
                {
                    "label": o.label,
                    "pixel_box": getattr(o, "pixel_box", None),
                    "source_box": getattr(o, "source_box", None),
                    "pixel_point": getattr(o, "pixel_point", None),
                }
                for o in result.observations
            ],
            "validation_errors": list(result.validation_errors),
            "raw_hash": result.raw_hash,
            "raw_text": (recording.last_raw or "")[:800],  # evidence-only debug capture
        }
        print(f"[infer] {text[:45]:47s} ok={result.success} obs={len(result.observations)} lat={result.latency_ms}ms")
        return rec

    # ---- Step 4.3 single inference ---------------------------------------
    evidence["inferences"].append(run_query("locate all objects visible in the image", tag="4.3 all objects"))
    _write_evidence(evidence, live=True)

    # ---- Step 4.4 grounding queries --------------------------------------
    for q in (
        "locate the person",
        "locate the largest object",
        "locate the object nearest the center",
        "locate a unicorn",
    ):
        evidence["inferences"].append(run_query(q, tag=f"4.4 {q}"))
        _write_evidence(evidence, live=True)

    # ---- Step 4.5 stress test --------------------------------------------
    stress: dict = {"runs": []}
    latencies: list[float] = []
    for n in (1, 5, 10):
        run_lats: list[float] = []
        for i in range(n):
            rec = run_query("locate the person", frame_id=f"stress-{n}-{i}", tag=f"4.5 stress {n}x #{i}")
            run_lats.append(rec["latency_ms"] or rec["wall_ms"])
            _write_evidence(evidence, live=True)
        stress["runs"].append({"n": n, "latencies_ms": [round(x, 1) for x in run_lats]})
        latencies.extend(run_lats)
    for tag, img in (("multiple boxes", None), ("large image", images["large"]), ("small image", images["small"]), ("cluttered image", images["cluttered"])):
        rec = run_query("locate all objects visible in the image", frame_id=f"stress-{tag.replace(' ', '-')}", image=img, tag=f"4.5 {tag}")
        stress["runs"].append({"n": 1, "tag": tag, "latencies_ms": [rec["latency_ms"] or rec["wall_ms"]]})
        latencies.append(rec["latency_ms"] or rec["wall_ms"])
        _write_evidence(evidence, live=True)

    stress["p50_ms"] = round(statistics.median(latencies), 1)
    stress["p95_ms"] = round(sorted(latencies)[int(0.95 * (len(latencies) - 1))], 1)
    stress["p99_ms"] = round(sorted(latencies)[int(0.99 * (len(latencies) - 1))], 1)
    stress["peak_mem_gb"] = round(_rss_gb(), 2)
    evidence["stress"] = stress

    # ---- Step 4.6 decision gate ------------------------------------------
    ok = [a["ok"] for a in load_attempts]
    usable = any(ok)
    median = statistics.median(latencies) if latencies else float("inf")
    if not usable:
        outcome = "C"
        reason = "MPS cannot run the model reliably (no dtype loaded)"
    elif median > 120_000:
        outcome = "B"
        reason = f"MPS works but is too slow/heavy (median {median:.0f} ms); keep adapter, run on local NVIDIA"
    elif median > 30_000:
        outcome = "B"
        reason = (
            f"MPS works but is heavy (median {median:.0f} ms): usable for occasional "
            "cognition-driven grounding on the dev Mac, not per-frame; realtime path is NVIDIA"
        )
    else:
        outcome = "A"
        reason = f"MPS usable (median {median:.0f} ms)"
    evidence["decision_gate"] = {"outcome": outcome, "reason": reason}
    print(f"[decision gate] {outcome}: {reason}")

    _write_evidence(evidence)
    return 0


def _load_with_dtype(dtype):
    from functools import partial  # noqa: PLC0415
    from novi.perception.locate_anything_runtime import _RealLocateAnythingBundle  # noqa: PLC0415

    return _RealLocateAnythingBundle(dtype=dtype)


def _write_evidence(evidence: dict, *, live: bool = False) -> Path:
    out_dir = REPO_ROOT / "docs" / "07-locate-anything" / "evidence"
    out_dir.mkdir(parents=True, exist_ok=True)
    name = "mac-feasibility-live.json" if live else f"mac-feasibility-{time.strftime('%Y%m%d-%H%M%S')}.json"
    path = out_dir / name
    path.write_text(json.dumps(evidence, indent=2))
    print(f"[evidence] {path}")
    return path


if __name__ == "__main__":
    raise SystemExit(main())
