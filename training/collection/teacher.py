"""Teacher/evaluator model (plan 23 §18, phase 13).

Uses `qwen3.8:27b` (local ollama) as an optional teacher for difficult
examples: ranking candidate responses, scoring naturalness/grounding/
context/verbosity, identifying unsupported claims and repetition.

The teacher is **never ground truth** (plan §18): human review remains
required for important training data. A deterministic scorer backs the same
interface so CI and offline runs never depend on the teacher being up.

Teacher output format (plan §18):

    {"grounding": 0.98, "naturalness": 0.91, "context_use": 0.94,
     "verbosity": 0.89, "unsupported_claim": 0.01, "overall": 0.93}
"""

from __future__ import annotations

import json
import re
import urllib.request
from typing import Any

from training.collection.deduplicator import extract_claims
from training.collection.validator import ASSISTANT_PHRASES, _claims_perception

DEFAULT_TEACHER_MODEL = "qwen3.8:27b"

_VERBOSE_THRESHOLD_CHARS = 200
_MEMORY_PHRASES = re.compile(
    r"\b(we decided|we agreed|you said|you told me|you mentioned|remember|as we discussed)\b",
    re.IGNORECASE,
)


def _has_assistant_phrasing(text: str) -> bool:
    low = text.lower()
    return any(p in low for p in ASSISTANT_PHRASES)


def _repetition_penalty(text: str, seen: set[str]) -> float:
    norm = " ".join(text.lower().split())
    if norm in seen:
        return 0.4
    seen.add(norm)
    return 0.0


def deterministic_scores(example: dict[str, Any], _seen: set[str] | None = None) -> dict[str, float]:
    """Deterministic teacher scores (offline fallback; plan §18 output shape)."""
    seen = _seen if _seen is not None else set()
    response = example.get("response", "")
    sit = example.get("situation") or {}
    evidence = list(((sit.get("world") or {}).get("perception") or []))
    topic = (sit.get("conversation") or {}).get("topic", "")

    # grounding: position claims must be backed by evidence.
    claims = extract_claims(response)
    if claims:
        evidence_text = " ".join(evidence).lower()
        grounded = sum(1 for _s, _rel, obj in claims if obj.lower() in evidence_text)
        grounding = grounded / len(claims)
    else:
        grounding = 0.9 if not _claims_perception(response) or evidence else 0.3

    # naturalness: assistant-style phrasing + repetition.
    naturalness = 1.0
    if _has_assistant_phrasing(response):
        naturalness -= 0.55
    naturalness -= _repetition_penalty(response, seen)
    naturalness = max(0.05, min(1.0, naturalness))

    # context use: response should touch the conversation topic.
    context_use = 0.5
    if topic:
        low = response.lower()
        topic_tokens = set(re.findall(r"[a-z']+", topic.lower()))
        context_use = 0.9 if topic_tokens & set(re.findall(r"[a-z']+", low)) else 0.6

    # verbosity: brief, conversational responses score high.
    verbosity = 1.0 if len(response) <= 60 else (0.9 if len(response) <= _VERBOSE_THRESHOLD_CHARS else 0.3)

    # unsupported claims: perceptual claims or memory references without backing.
    unsupported = 0.0
    if _claims_perception(response) and not evidence:
        unsupported = max(unsupported, 0.8)
    if _MEMORY_PHRASES.search(response) and not sit.get("memory"):
        unsupported = max(unsupported, 0.6)
    if claims and not evidence:
        unsupported = max(unsupported, 0.7)

    overall = 0.25 * grounding + 0.25 * naturalness + 0.2 * context_use + 0.15 * verbosity + 0.15 * (1.0 - unsupported)
    return {
        "grounding": round(grounding, 3),
        "naturalness": round(naturalness, 3),
        "context_use": round(context_use, 3),
        "verbosity": round(verbosity, 3),
        "unsupported_claim": round(unsupported, 3),
        "overall": round(max(0.0, min(1.0, overall)), 3),
    }


def rank_responses(situation: dict[str, Any], responses: list[str]) -> list[tuple[str, float]]:
    """Rank candidate responses by deterministic teacher criteria."""
    seen: set[str] = set()
    scored = []
    for r in responses:
        ex = {"response": r, "situation": situation}
        scored.append((r, deterministic_scores(ex, seen)["overall"]))
    return sorted(scored, key=lambda kv: kv[1], reverse=True)


class TeacherEvaluator:
    """Optional local teacher (ollama qwen3.8:27b) with deterministic fallback."""

    def __init__(self, backend: str = "deterministic", model: str = DEFAULT_TEACHER_MODEL,
                 timeout_s: float = 30.0, ollama_url: str = "http://localhost:11434") -> None:
        self.backend = backend
        self.model = model
        self.timeout_s = timeout_s
        self.ollama_url = ollama_url

    # -- ollama ---------------------------------------------------------------
    def _ollama_generate(self, prompt: str) -> str | None:
        # think=false: Qwen3's CoT thinking would consume the whole budget and
        # return an empty `response`; the teacher must answer directly.
        payload = json.dumps({"model": self.model, "prompt": prompt, "stream": False,
                              "think": False,
                              "options": {"temperature": 0.0, "num_predict": 256}}).encode()
        req = urllib.request.Request(
            f"{self.ollama_url}/api/generate", data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:  # noqa: S310
                data = json.loads(resp.read().decode())
            return data.get("response", "")
        except Exception:  # noqa: BLE001 - any network error -> fall back
            return None

    def _ollama_evaluate(self, example: dict[str, Any]) -> dict[str, float] | None:
        prompt = (
            "You are the evaluation teacher for Novi, a home robot. Score this "
            "dialogue example on a 0-1 scale for each criterion. Reply with ONLY "
            "JSON: {\"grounding\":..,\"naturalness\":..,\"context_use\":..,"
            "\"verbosity\":..,\"unsupported_claim\":..,\"overall\":..}\n"
            f"Situation: {json.dumps(example.get('situation', {}), ensure_ascii=False)[:1200]}\n"
            f"Dialogue act: {example.get('decision', {}).get('dialogue_act', '')}\n"
            f"Response: {example.get('response', '')}"
        )
        raw = self._ollama_generate(prompt)
        if raw is None:
            return None
        try:
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if not m:
                return None
            parsed = json.loads(m.group(0))
            return {k: max(0.0, min(1.0, float(parsed[k]))) for k in
                    ("grounding", "naturalness", "context_use", "verbosity", "unsupported_claim", "overall")}
        except (ValueError, TypeError, KeyError):
            return None

    # -- public ---------------------------------------------------------------
    def evaluate(self, example: dict[str, Any]) -> dict[str, Any]:
        """Teacher scores for one example; deterministic fallback on any failure."""
        if self.backend == "ollama":
            scores = self._ollama_evaluate(example)
            if scores is not None:
                scores["teacher"] = self.model
                return scores
        scores = deterministic_scores(example)
        scores["teacher"] = "deterministic"
        return scores


def filter_dataset(examples: list[dict[str, Any]], min_overall: float = 0.7,
                   teacher: TeacherEvaluator | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Quality gate: keep examples whose teacher overall score >= threshold."""
    teacher = teacher or TeacherEvaluator(backend="deterministic")
    kept: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    for ex in examples:
        scores = teacher.evaluate(ex)
        ex = dict(ex)
        ex["teacher_scores"] = scores
        if scores["overall"] >= min_overall:
            kept.append(ex)
        else:
            dropped.append(ex)
    return kept, dropped
