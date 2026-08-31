"""Privacy and data governance for training data (plan 23 §7–§8, step 04).

Implements the §7 obligations for training corpora:

- consent state: traces of non-consenting persons never enter a dataset;
- retention policy: examples older than the window are dropped at export;
- redaction: PII (email, phone, SSN, card numbers, credentials) is replaced
  deterministically; raw names never leave the workspace unabstracted;
- biometric separation: content referencing face embeddings / voiceprints is
  *dropped* from language-training corpora (it is never language evidence);
- abstract person ids (`person:owner_001`, `person:anon_001`) replace raw ids;
- dataset deletion: `purge_dataset` physically removes training files.

The brain's `novi/brain/privacy.py` governs the *runtime* memory store; this
module governs the *training* corpus. Same obligations, different surface.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

REDACTED = "[REDACTED]"

# --- PII patterns (deterministic, conservative) ------------------------------
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"\+?\d[\d\s().-]{6,}\d")
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_CARD_RE = re.compile(r"\b(?:\d[ -]?){13,19}\b")
_APIKEY_RE = re.compile(r"\b(?:sk|pk|ak|ghp|gho|ghu|AIza|ya29)[-_A-Za-z0-9]{12,}\b")
_TOKEN_RE = re.compile(r"\b(?:password|passphrase|secret|pin|api[ -]?key|token)\s+[=:]?\s*([A-Za-z0-9_\-!@#$%^&*]{4,})", re.IGNORECASE)
_IP_RE = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")

_REDACTORS: tuple[re.Pattern, ...] = (_EMAIL_RE, _PHONE_RE, _SSN_RE, _CARD_RE, _APIKEY_RE, _IP_RE)

# Biometric markers: language evidence must never contain biometric content.
BIOMETRIC_MARKERS: tuple[str, ...] = (
    "face embedding", "faceembedding", "voiceprint", "fingerprint", "retina scan",
    "biometric", "embedding matched", "embedding similarity", "gallery match",
)
_BIOMETRIC_KEYS = ("voiceprint", "face_embedding", "face_embedding_ref", "embedding", "biometric_ref")

_OWNER_ALIASES = frozenset({"vano", "owner", "master", "user"})

# Deterministic within-process abstract-id mapping (plan §7: person:owner_001).
_ANON_BY_RAW: dict[str, str] = {}
_ANON_COUNTER = 0


def _abstract_person_id(raw: str) -> str:
    global _ANON_COUNTER
    key = (raw or "").strip().lower()
    if not key:
        return "person:unknown_001"
    if key in _OWNER_ALIASES:
        return "person:owner_001"
    if key.startswith("person:"):
        return raw
    if key in _ANON_BY_RAW:
        return _ANON_BY_RAW[key]
    _ANON_COUNTER += 1
    abstract = f"person:anon_{_ANON_COUNTER:03d}"
    _ANON_BY_RAW[key] = abstract
    return abstract


def redact_text(text: str) -> str:
    """Replace PII with REDACTED, deterministically."""
    out = text
    for pattern in _REDACTORS:
        out = pattern.sub(REDACTED, out)
    out = _TOKEN_RE.sub(lambda m: m.group(0).replace(m.group(1), REDACTED), out)
    return out


def contains_biometric(text: str) -> bool:
    low = text.lower()
    return any(marker in low for marker in BIOMETRIC_MARKERS)


@dataclass(frozen=True)
class ConsentState:
    consenting: frozenset[str] | None = None  # None = no restriction

    def allows(self, person_id: str) -> bool:
        if self.consenting is None:
            return True
        return person_id in self.consenting


@dataclass(frozen=True)
class RetentionPolicy:
    max_age_days: float = 180.0

    def expired(self, exported_at: str | None, now: datetime | None = None) -> bool:
        if not exported_at:
            return False  # no timestamp -> treated as fresh
        try:
            ts = datetime.fromisoformat(exported_at)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        except ValueError:
            return True  # malformed timestamp -> drop (fail closed)
        now = now or datetime.now(timezone.utc)
        return now - ts > timedelta(days=self.max_age_days)


@dataclass
class SanitizationReport:
    kept: int = 0
    redacted: int = 0
    dropped_biometric: int = 0
    dropped_no_consent: int = 0
    dropped_expired: int = 0
    dropped_malformed: int = 0
    abstracted_persons: int = 0

    def add(self, other: "SanitizationReport") -> None:
        for f in self.__dataclass_fields__:
            setattr(self, f, getattr(self, f) + getattr(other, f))


class Sanitizer:
    """One-pass privacy pipeline for training examples (plan §7)."""

    def __init__(
        self,
        consent: ConsentState | None = None,
        retention: RetentionPolicy | None = None,
    ) -> None:
        self.consent = consent or ConsentState()
        self.retention = retention or RetentionPolicy()

    def sanitize(self, example: dict[str, Any]) -> tuple[dict[str, Any] | None, SanitizationReport]:
        report = SanitizationReport()
        if not isinstance(example, dict) or not example.get("example_id"):
            report.dropped_malformed = 1
            return None, report

        raw_person_id = ((example.get("situation") or {}).get("person") or {}).get("id", "")
        if not self.consent.allows(raw_person_id):
            report.dropped_no_consent = 1
            return None, report

        exported_at = example.pop("_exported_at", None)
        if self.retention.expired(exported_at):
            report.dropped_expired = 1
            return None, report

        # Biometric separation: references to biometric artifacts are stripped
        # from structured fields FIRST (they are never language evidence);
        # any remaining biometric *content* drops the whole example.
        out = _deep_copy(example)
        _strip_biometric_keys(out)

        texts = [out.get("response", ""), raw_person_id] + _all_strings(out)
        if any(contains_biometric(t) for t in texts):
            report.dropped_biometric = 1
            return None, report

        # Redact free text.
        redacted_response = redact_text(out.get("response", ""))
        if redacted_response != out.get("response", ""):
            report.redacted += 1
        out["response"] = redacted_response
        # Emotional fields (plan 24 §29-§30): preferred_response, evidence,
        # and DPO preference pairs carry the same PII obligations.
        for key in ("preferred_response", "evidence", "response_a", "response_b"):
            if key in out and isinstance(out[key], str):
                redacted = redact_text(out[key])
                if redacted != out[key]:
                    report.redacted += 1
                out[key] = redacted
        sit = out.get("situation") or {}
        for mem in sit.get("memory") or []:
            mem["summary"] = redact_text(mem.get("summary", ""))
        for key in ("topic", "input_event"):
            conv = sit.get("conversation") or {}
            if key in conv:
                conv[key] = redact_text(conv[key])
        for key in ("changes", "perception"):
            world = sit.get("world") or {}
            if key in world:
                world[key] = [redact_text(str(v)) for v in world[key]]
        social = sit.get("social") or {}
        for k, v in list(social.items()):
            if isinstance(v, str):
                social[k] = redact_text(v)
        # Emotional situation strings (relationship, user_goal, ...); the
        # person dict is handled separately below.
        for key, value in list(sit.items()):
            if key == "person" or not isinstance(value, str):
                continue
            sit[key] = redact_text(value)

        # Strip biometric refs from structured fields (already done above for
        # the whole tree; keep the world-level pass for clarity).
        world = sit.get("world") or {}
        for key in list(world.keys()):
            if any(m in key.lower() for m in _BIOMETRIC_KEYS):
                del world[key]

        # Abstract the person id; never carry the raw name into training data.
        person = sit.get("person") or {}
        if person.get("id"):
            person["id"] = _abstract_person_id(person["id"])
            report.abstracted_persons += 1
        person["name"] = "" if person.get("name") and person.get("name") not in _OWNER_ALIASES else person.get("name", "")

        report.kept = 1
        return out, report

    def sanitize_all(self, examples: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], SanitizationReport]:
        kept: list[dict[str, Any]] = []
        total = SanitizationReport()
        for ex in examples:
            out, report = self.sanitize(ex)
            total.add(report)
            if out is not None:
                kept.append(out)
        return kept, total

    def purge_dataset(self, dataset_dir: str | Path) -> int:
        """Physically delete dataset files (plan §7 'training-dataset deletion')."""
        path = Path(dataset_dir)
        if not path.is_dir():
            return 0
        removed = 0
        for pattern in ("*.jsonl", "*.json"):
            for f in path.glob(pattern):
                if f.is_file():
                    f.unlink()
                    removed += 1
        return removed


def _all_strings(node: Any) -> list[str]:
    """All string leaves under a dict/list tree (for biometric scanning)."""
    out: list[str] = []
    if isinstance(node, str):
        out.append(node)
    elif isinstance(node, dict):
        for v in node.values():
            out.extend(_all_strings(v))
    elif isinstance(node, list):
        for v in node:
            out.extend(_all_strings(v))
    return out


def _deep_copy(node: Any) -> Any:
    if isinstance(node, dict):
        return {k: _deep_copy(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_deep_copy(v) for v in node]
    return node


def _strip_biometric_keys(node: Any) -> None:
    """Recursively remove keys that reference biometric artifacts (in place)."""
    if isinstance(node, dict):
        for key in list(node.keys()):
            if any(m in key.lower() for m in _BIOMETRIC_KEYS):
                del node[key]
            else:
                _strip_biometric_keys(node[key])
    elif isinstance(node, list):
        for v in node:
            _strip_biometric_keys(v)
