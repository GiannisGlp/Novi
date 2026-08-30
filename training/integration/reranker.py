"""Learned memory-retrieval reranker integration (plan 23 §34, step 18).

Candidate generation stays vector/FTS (the brain's composite retrieval —
novi/brain/retrieval_policy.py — remains the deterministic authority). The
learned reranker re-ranks top-k candidates when a trained artifact exists;
otherwise `composite_rank` (deterministic, explainable) is used. The brain
always sees an ordered, explainable candidate list — never a black box.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Composite weights mirroring novi/brain/retrieval_policy.DEFAULT_WEIGHTS
# (plan 22 Phase 5). Imported lazily so this module works even if the brain
# package changes; local copy keeps the fallback deterministic.
_COMPOSITE_WEIGHTS: dict[str, float] = {
    "semantic": 0.22, "temporal": 0.10, "person": 0.10, "situation": 0.10,
    "goal": 0.08, "causal": 0.05, "importance": 0.12, "confidence": 0.06,
    "provenance": 0.07, "spatial": 0.05, "novelty": 0.05,
}
_LEXICAL_BOOST = 0.15  # per query token matched in the candidate summary
_LEXICAL_CAP = 0.4


def _norm_tokens(text: str) -> set[str]:
    return set("".join(ch for ch in text.lower() if ch.isalnum() or ch == " ").split())


def _feature(candidate: dict[str, Any], key: str) -> float:
    for alias in (key, {"temporal": "recency"}.get(key, key)):
        if alias in candidate:
            return float(candidate[alias])
    return 0.0


def _score_candidate(query: str, candidate: dict[str, Any]) -> tuple[float, list[str]]:
    why: list[str] = []
    total = 0.0
    for key, weight in _COMPOSITE_WEIGHTS.items():
        value = _feature(candidate, key)
        if value:
            total += weight * value
            why.append(f"{key}+{value:.2f}*{weight:.2f}")
    summary = candidate.get("summary", "")
    if query and summary:
        overlap = _norm_tokens(query) & _norm_tokens(summary)
        boost = min(len(overlap) * _LEXICAL_BOOST, _LEXICAL_CAP)
        if boost:
            total += boost
            why.append(f"lexical+{boost:.2f}")
    return total, why


def composite_rank(query: str, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deterministic, explainable ranking (the safe default)."""
    scored = [
        {
            "id": c.get("id", f"cand-{i}"),
            "summary": c.get("summary", ""),
            "score": round(s, 4),
            "why": why,
        }
        for i, c in enumerate(candidates)
        for s, why in [_score_candidate(query, c)]
    ]
    scored.sort(key=lambda s: s["score"], reverse=True)
    return scored


class LearnedReranker:
    """Trained linear reranker with deterministic composite fallback."""

    def __init__(self, artifact_path: str | Path) -> None:
        self._weights: list[float] | None = None
        self._bias: float = 0.0
        artifact = Path(artifact_path)
        if artifact.exists():
            try:
                data = json.loads(artifact.read_text())
                w = {k: v for k, v in (data.get("weights", {}) or {}).items() if k.startswith("w_")}
                sorted_keys = sorted(w, key=lambda k: int(k.split("_")[1]))
                # Feature order comes from the artifact's `features` list
                # (names); the w_* keys are only a fallback for old artifacts.
                feature_order = list(data.get("features") or sorted_keys)
                if w and feature_order and len(w) == len(feature_order):
                    self._weights = [float(w[k]) for k in sorted_keys]
                    self._feature_order = feature_order
                    self._bias = float(data.get("bias", 0.0))
            except (json.JSONDecodeError, ValueError, TypeError):
                self._weights = None

    def rerank(self, query: str, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if self._weights is None or not self._feature_order:
            return composite_rank(query, candidates)
        scored = []
        for i, c in enumerate(candidates):
            vec = [float(c.get(f, 0.0)) for f in self._feature_order]
            learned = self._bias + sum(w * v for w, v in zip(self._weights, vec, strict=True))
            lexical = min(len(_norm_tokens(query) & _norm_tokens(c.get("summary", ""))) * _LEXICAL_BOOST, _LEXICAL_CAP)
            scored.append({
                "id": c.get("id", f"cand-{i}"),
                "summary": c.get("summary", ""),
                "score": round(learned + lexical, 4),
                "why": [f"learned+{learned:.3f}", f"lexical+{lexical:.3f}"],
            })
        scored.sort(key=lambda s: s["score"], reverse=True)
        return scored
