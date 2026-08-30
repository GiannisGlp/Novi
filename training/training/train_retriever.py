"""Retrieval reranker training — third experiment (plan 23 §34, steps 16-18).

A small independent reranker over the composite retrieval features, trained
on `datasets/retrieval/` records (query + candidate memories + preferred
ranking). Candidate generation stays vector/FTS (novi/brain/retrieval_policy
composite score as the deterministic fallback); the learned scorer re-ranks
top-k. Cheaper, interpretable, replaceable — not an LLM fine-tune.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.config import capture_provenance, load_config  # noqa: E402
from training.training.common import add_common_args, emit_report, load_jsonl  # noqa: E402


def _smoke_report(cfg) -> dict:
    records = load_jsonl(ROOT / cfg.dataset)
    from training.schemas import validate_example  # noqa: PLC0415

    bad = [r["example_id"] for r in records if validate_example(r, kind="retrieval")]
    if bad:
        raise ValueError(f"retrieval: {len(bad)} records fail validation, e.g. {bad[:3]}")
    prov = capture_provenance(cfg.base_model, cfg.dataset_version, cfg.seed, cfg.hyperparams, ROOT)
    prov.pop("captured_at", None)
    return {
        "dry_run": True,
        "task": "retrieval",
        "config": cfg.to_dict(),
        "records_loaded": len(records),
        "features": cfg.hyperparams.get("features", []),
        "framework": prov.pop("framework"),
        "provenance": prov,
        "next_step": "grow retrieval dataset -> run without --dry-run (torch linear ranker)",
    }


def _real_report(cfg) -> dict:
    from training.training.backends.torch_linear import train_linear_ranker  # noqa: PLC0415

    records = load_jsonl(ROOT / cfg.dataset)
    features = _feature_rows(records, cfg.hyperparams.get("features", []))
    labels = _labels(records)
    weights, preds = train_linear_ranker(
        features, labels,
        epochs=int(cfg.hyperparams.get("epochs", 10)),
        lr=float(cfg.hyperparams.get("learning_rate", 1e-2)),
        seed=cfg.seed,
    )
    out_dir = Path(cfg.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    artifact = out_dir / "retrieval_reranker_v1.json"
    import json  # noqa: PLC0415

    artifact.write_text(json.dumps({
        "model": "linear",
        "features": cfg.hyperparams.get("features", []),
        "weights": weights,
        "provenance": capture_provenance(cfg.base_model, cfg.dataset_version, cfg.seed, cfg.hyperparams),
    }, indent=2))
    return {
        "task": "retrieval",
        "framework": "torch-linear",
        "artifact": str(artifact),
        "records_trained": len(records),
        "weights": weights,
        "sample_predictions": preds[:5],
        "note": "integrate via training/integration/reranker.py behind deterministic guardrails (plan §34)",
    }


def _feature_rows(records: list[dict], feature_names: list[str]) -> list[list[float]]:
    rows = []
    for rec in records:
        for i, _cand in enumerate(rec["candidates"]):
            rows.append(_candidate_features(rec, i, feature_names))
    return rows


def _candidate_features(rec: dict, idx: int, feature_names: list[str]) -> list[float]:
    """Features per candidate come from the record's 'candidate_features' list.

    Each candidate may carry its own composite-signal vector (semantic,
    temporal, person, … — the same signals novi/brain/retrieval_policy uses).
    Absent explicit features, fall back to the position prior (rank-0 signal).
    """
    feats = (rec.get("candidate_features") or [])
    if len(feats) > idx and isinstance(feats[idx], dict):
        return [float(feats[idx].get(f, 0.0)) for f in feature_names]
    if len(feats) > idx and isinstance(feats[idx], list):
        return [float(v) for v in feats[idx][: len(feature_names)]] or [1.0 if idx == 0 else 0.0]
    return [1.0 if idx == 0 else 0.0] * len(feature_names)


def _labels(records: list[dict]) -> list[float]:
    labels = []
    for rec in records:
        preferred = set(rec.get("preferred") or [])
        for i in range(len(rec["candidates"])):
            labels.append(1.0 if i in preferred else 0.0)
    return labels


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args(argv)
    cfg = load_config(args.config)
    report = _smoke_report(cfg) if args.dry_run else _real_report(cfg)
    return emit_report(report, args.out_json)


if __name__ == "__main__":
    raise SystemExit(main())
