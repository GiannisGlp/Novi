"""Grounding ranking training (plan 23 §36/§14, steps 22-23).

Trains a small linear ranker over grounding features (language similarity +
gaze/pointing/gesture cue matches). It ranks candidate (object, destination)
groundings; the final physical action still passes deterministic validation
and governance (plan §14/§36) — ranking, never direct control.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.config import capture_provenance, load_config  # noqa: E402
from training.training.common import add_common_args, emit_report, load_jsonl  # noqa: E402


def _tokens(text: str) -> set[str]:
    return set("".join(ch for ch in text.lower() if ch.isalnum() or ch == " ").split())


def _smoke_report(cfg) -> dict:
    records = load_jsonl(ROOT / cfg.dataset)
    from training.schemas import validate_example  # noqa: PLC0415

    bad = [r["example_id"] for r in records if validate_example(r, kind="grounding")]
    if bad:
        raise ValueError(f"grounding: {len(bad)} records fail validation, e.g. {bad[:3]}")
    prov = capture_provenance(cfg.base_model, cfg.dataset_version, cfg.seed, cfg.hyperparams, ROOT)
    prov.pop("captured_at", None)
    return {
        "dry_run": True,
        "task": "grounding",
        "config": cfg.to_dict(),
        "records_loaded": len(records),
        "features": cfg.hyperparams.get("features", []),
        "framework": prov.pop("framework"),
        "provenance": prov,
        "next_step": "run without --dry-run to train the linear grounding ranker",
    }


def _feature_row(record: dict, idx: int, features: list[str]) -> list[float]:
    """One candidate's feature vector (deterministic extraction from cues)."""
    candidate = record["candidates"][idx]
    cues = record.get("cues") or {}
    language = record.get("language", "")
    out: list[float] = []
    for f in features:
        if f == "language_similarity":
            overlap = _tokens(language) & _tokens(candidate)
            union = _tokens(language) | _tokens(candidate)
            out.append(len(overlap) / len(union) if union else 0.0)
        elif f == "gaze_match":
            out.append(1.0 if cues.get("gaze") == candidate else 0.0)
        elif f == "pointing_match":
            out.append(1.0 if cues.get("pointing") == candidate else 0.0)
        elif f == "gesture_match":
            out.append(1.0 if record.get("gesture") == candidate else 0.0)
        elif f == "recency":
            out.append(0.5)
        elif f == "confidence":
            out.append(0.9)
        else:
            out.append(0.0)
    return out


def _preferred_object(record: dict) -> str:
    preferred = record.get("preferred", "")
    if "(" in preferred and ")" in preferred:
        return preferred[preferred.index("(") + 1:preferred.index(")")].split(",")[0].strip()
    return preferred


def _real_report(cfg) -> dict:
    from training.training.backends.torch_linear import train_linear_ranker  # noqa: PLC0415

    records = load_jsonl(ROOT / cfg.dataset)
    features = cfg.hyperparams.get("features", [])
    rows: list[list[float]] = []
    labels: list[float] = []
    for rec in records:
        target = _preferred_object(rec)
        for i, candidate in enumerate(rec["candidates"]):
            rows.append(_feature_row(rec, i, features))
            labels.append(1.0 if candidate == target else 0.0)
    weights, preds = train_linear_ranker(
        rows, labels,
        epochs=int(cfg.hyperparams.get("epochs", 10)),
        lr=float(cfg.hyperparams.get("learning_rate", 1e-2)),
        seed=cfg.seed,
    )
    out_dir = Path(cfg.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    artifact = out_dir / "grounding_ranker_v1.json"
    artifact.write_text(json.dumps({
        "model": "linear",
        "features": features,
        "weights": {k: v for k, v in weights.items() if k != "bias"},
        "bias": float(weights.get("bias", 0.0)),
        "provenance": capture_provenance(cfg.base_model, cfg.dataset_version, cfg.seed, cfg.hyperparams),
    }, indent=2))
    return {
        "task": "grounding",
        "framework": "torch-linear",
        "artifact": str(artifact),
        "candidates_trained": len(rows),
        "weights": weights,
        "sample_predictions": preds[:5],
        "note": "ranking only; physical action still passes deterministic governance (plan §36)",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args(argv)
    cfg = load_config(args.config)
    report = _smoke_report(cfg) if args.dry_run else _real_report(cfg)
    return emit_report(report, args.out_json)


if __name__ == "__main__":
    raise SystemExit(main())
