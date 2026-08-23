"""Privacy and memory data governance for the Mac Brain.

Implements the semantic privacy obligations of docs/04-memory-and-knowledge/14:

    COLLECT MINIMALLY -> CLASSIFY -> PURPOSE-BIND -> USE -> DERIVE
    -> RETAIN/REVIEW -> RESTRICT / DELETE / GENERALIZE -> VERIFY

- Deterministic privacy classification (public / operational / personal /
  sensitive / credential / biometric / location / communication / derived).
- Per-class retention and expiry, enforced by `sweep`.
- Purpose limitation + consent: a record bound to a purpose is not silently
  usable for unrelated high-impact purposes.
- Governed operations: RESTRICT, GENERALIZE, ERASE — where erasure physically
  removes the record (cannot be undone by recovery) and **propagates to
  dependent derived representations** (dependency_refs).
- Authorization filter so retrieval never exposes records above a sensitivity
  limit or outside an allowed purpose.

The store is the physical mechanism; this module is the policy/decision layer.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

# Privacy classes ordered from least to most sensitive.
PRIVACY_CLASSES = ("public", "operational", "personal", "sensitive", "credential", "biometric", "location", "communication", "derived")
SENSITIVITY_RANK = {name: i for i, name in enumerate(PRIVACY_CLASSES)}

_PERSON_LABELS = {"alice", "bob", "vano", "charlie", "dana", "eve"}

# Common object/place labels every brain recognizes even before they are
# observed (single source of truth for chat entity extraction, discourse
# topic grounding and privacy classification).
COMMON_ENTITY_LABELS = frozenset({
    "alice", "bob", "door", "person", "table", "room", "kitchen",
    "object", "window", "lamp", "chair", "plant",
})

# Deterministic classification lexicon (class -> keywords). Matched on normalized text.
_KEYWORDS: dict[str, tuple[str, ...]] = {
    "credential": ("password", "token", "secret", "apikey", "api_key", "pin", "credential", "passphrase"),
    "biometric": ("face", "voiceprint", "fingerprint", "retina", "biometric"),
    "sensitive": ("health", "medical", "diagnosis", "finance", "account", "card", "confidential"),
    "location": ("location", "coordinates", "latitude", "longitude", "address", "gps"),
    "communication": ("direct message", "dm ", "voicemail", "call ", "texted", "email", "letter"),
}
# Iterate classes from most to least sensitive so the most-sensitive match wins.
_KEYWORD_CLASS_ORDER = ("credential", "biometric", "sensitive", "location", "communication")

_DERIVED_TYPES = {"summary", "relationship", "prediction", "belief", "causal", "embedding", "knowledge_graph", "skill", "lexicon"}
_PERSON_TYPES = {"utterance", "dialogue", "conversation", "identity", "goal"}

# Retention defaults (seconds) per privacy class; None == keep until reviewed.
_DEFAULT_RETENTION_SECONDS: dict[str, int | None] = {
    "public": None,
    "operational": 30 * 86400,
    "personal": 90 * 86400,
    "sensitive": 14 * 86400,
    "credential": 7 * 86400,
    "biometric": 14 * 86400,
    "location": 7 * 86400,
    "communication": 30 * 86400,
    "derived": 90 * 86400,
}


def _as_text(content: Any) -> str:
    if isinstance(content, str):
        return content.lower()
    if isinstance(content, (dict, list)):
        return json.dumps(content).lower()
    return str(content).lower()


@dataclass
class Classification:
    privacy_class: str
    reason: str
    sensitivity: int


@dataclass
class ErasureReport:
    erased_ids: list[str] = field(default_factory=list)
    propagated: list[str] = field(default_factory=list)


class PrivacyGovernance:
    """Policy + decision layer for memory privacy and erasure."""

    def __init__(
        self,
        store: Any = None,
        *,
        default_purpose: str = "general",
        retention_seconds: dict[str, int | None] | None = None,
        allowed_purposes: dict[str, set[str]] | None = None,
        max_sensitivity_default: str = "sensitive",
    ) -> None:
        self.store = store
        self.default_purpose = default_purpose
        self.retention_seconds = dict(retention_seconds or _DEFAULT_RETENTION_SECONDS)
        self.allowed_purposes = allowed_purposes or {
            "general": {"public", "operational", "personal", "sensitive"},
            "social": {"public", "operational", "personal"},
            "safety": set(PRIVACY_CLASSES),
            "research": {"public", "operational", "derived"},
        }
        self.max_sensitivity_default = max_sensitivity_default

    # ---- classification ----
    def classify(self, *, memory_type: str = "perception", content: Any = None, entity_refs: Iterable[str] = (), modality: str = "") -> Classification:
        text = _as_text(content)
        entities = {str(e).lower() for e in entity_refs}
        mtype = (memory_type or "").lower()
        if mtype in _DERIVED_TYPES:
            return Classification("derived", f"memory_type={mtype}", SENSITIVITY_RANK["derived"])
        for cls in _KEYWORD_CLASS_ORDER:
            for kw in _KEYWORDS[cls]:
                if kw in text:
                    return Classification(cls, f"keyword={kw!r}", SENSITIVITY_RANK[cls])
        if mtype in _PERSON_TYPES or entities & _PERSON_LABELS:
            return Classification("personal", "person-typed or person entity", SENSITIVITY_RANK["personal"])
        if modality in ("speech", "audio"):
            return Classification("personal", f"modality={modality}", SENSITIVITY_RANK["personal"])
        if modality == "vision" and entities & _PERSON_LABELS:
            return Classification("personal", "vision+person", SENSITIVITY_RANK["personal"])
        return Classification("operational", "default", SENSITIVITY_RANK["operational"])

    def retention_seconds_for(self, privacy_class: str) -> int | None:
        return self.retention_seconds.get(privacy_class)

    def expiry_for(self, privacy_class: str, now: datetime | None = None) -> str | None:
        ttl = self.retention_seconds_for(privacy_class)
        if ttl is None:
            return None
        now = now or datetime.now(timezone.utc)
        return (now + timedelta(seconds=ttl)).isoformat()

    # ---- purpose limitation + authorization ----
    def purpose_allowed(self, record_purpose: str | None, requested_purpose: str) -> bool:
        """A record bound to one purpose is not used for an unrelated purpose unless that
        purpose is in the record's allowed set (purpose expansion requires governance)."""
        rec = record_purpose or self.default_purpose
        allowed = self.allowed_purposes.get(requested_purpose, set())
        if "all" in allowed:
            return True
        return rec in allowed or rec == requested_purpose

    def authorize(self, records: Iterable[dict[str, Any]], *, requested_purpose: str = "general", max_sensitivity: str | None = None) -> tuple[dict[str, Any], ...]:
        """Filter records for retrieval by sensitivity limit + purpose + consent."""
        cap = SENSITIVITY_RANK[max_sensitivity or self.max_sensitivity_default]
        out = []
        for r in records:
            if not r.get("consent", True):
                continue
            if SENSITIVITY_RANK.get(r.get("privacy_class", "operational"), cap) > cap:
                continue
            if not self.purpose_allowed(r.get("purpose"), requested_purpose):
                continue
            out.append(r)
        return tuple(out)

    def authorize_ids(self, memory_ids: Iterable[str], *, requested_purpose: str = "general", max_sensitivity: str | None = None) -> tuple[str, ...]:
        """Resolve governance state for ids via the store and return the allowed subset."""
        ids = tuple(memory_ids)
        if self.store is None or not ids:
            return ids
        gate = self.store.gate_governance(ids)
        allowed = []
        for mid in ids:
            g = gate.get(mid)
            if g is None:  # not resolvable -> do not expose
                continue
            if not g.get("consent", True):
                continue
            if SENSITIVITY_RANK.get(g.get("privacy_class", "operational"), SENSITIVITY_RANK[self.max_sensitivity_default]) > SENSITIVITY_RANK[max_sensitivity or self.max_sensitivity_default]:
                continue
            if not self.purpose_allowed(g.get("purpose"), requested_purpose):
                continue
            allowed.append(mid)
        return tuple(allowed)

    # ---- governed operations (operate on the store) ----
    def sweep(self, now: datetime | None = None) -> ErasureReport:
        """Erase records past retention, propagating to dependent representations."""
        now = now or datetime.now(timezone.utc)
        report = ErasureReport()
        if self.store is None:
            return report
        for memory_id in self.store.expired_ids(now.isoformat()):
            self._erase(memory_id, reason="retention_expiry", report=report)
        return report

    def erase_memory(self, memory_id: str, *, reason: str = "user_request") -> ErasureReport:
        report = ErasureReport()
        if self.store is not None:
            self._erase(memory_id, reason=reason, report=report)
        return report

    def forget_entity(self, entity: str, *, reason: str = "right_to_be_forgotten") -> ErasureReport:
        """Right-to-be-forgotten: erase every active record referencing the entity and propagate."""
        report = ErasureReport()
        if self.store is None:
            return report
        for row in self.store.records_by_entity(entity):
            self._erase(row["memory_id"], reason=reason, report=report)
        return report

    def _erase(self, memory_id: str, report: ErasureReport, reason: str) -> None:
        if memory_id in report.erased_ids:
            return
        report.erased_ids.append(memory_id)
        for dep in self.store.dependent_ids(memory_id):
            if dep not in report.erased_ids:
                report.propagated.append(dep)
                self._erase(dep, report, reason="propagated_from=" + memory_id)
        self.store.hard_delete(memory_id)

    def restrict(self, memory_id: str, *, purpose: str) -> bool:
        st = self.store
        if st is None:
            return False
        ok = st.update_memory(memory_id, purpose=purpose)
        if ok:
            st.set_state(memory_id, "restricted")
        return ok

    def govern(self, memory_id: str, *, privacy_class: str, purpose: str | None = None, now: datetime | None = None) -> None:
        """Bind purpose and retention expiry to a newly admitted record (post-admission)."""
        if self.store is None:
            return
        self.store.update_memory(memory_id, purpose=purpose or self.default_purpose, expires_at=self.expiry_for(privacy_class, now))

    def generalize(self, memory_id: str) -> bool:
        """Coarsen a record's content (prefer coarse over exact identity/location/content),
        preserving provenance and marking the result as derived."""
        st = self.store
        if st is None:
            return False
        row = st.get_state_row(memory_id)
        if row is None:
            return False
        coarse = {"summary": "coarsened_by_policy", "original_type": row["memory_type"]}
        return st.update_memory(memory_id, content=coarse, privacy_class="derived", revision_bump=True)

    def snapshot(self) -> dict[str, Any]:
        if self.store is None:
            return {"enabled": False}
        by_class = self.store.count_by_class()
        return {
            "enabled": True,
            "default_purpose": self.default_purpose,
            "max_sensitivity_default": self.max_sensitivity_default,
            "counts_by_privacy_class": by_class,
            "total_active": sum(by_class.values()),
            "purposes": {k: sorted(v) for k, v in self.allowed_purposes.items()},
        }
