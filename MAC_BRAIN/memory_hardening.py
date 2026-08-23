"""Memory & Knowledge hardening for the Mac Brain (PERFECTING_PLAN Step 2).

Hardens storage/admission/retrieval to the canonical MemoryRecord contract:
  - Full MemoryRecord field set + typed epistemic/verification state at admission.
  - Write gate (identity -> integrity -> privacy -> instruction/data separation ->
    poisoning -> retention -> policy).
  - Retrieval failure states (NO_RESULT/AMBIGUOUS/CONFLICTED/STALE/ABSTAIN).
  - Contextual trust + independence groups (common source != corroboration).
  - Governance/oversight interfaces behind contracts.
  - Ties: world-state labels carry evidence class so simulations never become facts.

Canonical authority:
  - docs/04-memory-and-knowledge/02_MEMORY_LIFECYCLE_AND_ADMISSION.md
  - docs/04-memory-and-knowledge/03_PROVENANCE_EVIDENCE_TRUST_AND_UNCERTAINTY.md
  - docs/04-memory-and-knowledge/04_MEMORY_CONSOLIDATION_RETRIEVAL_AND_CONTEXT.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Iterable, Sequence

# ---------------------------------------------------------------------------
# Epistemic status (same vocabulary as world_model.py, but standalone for
# the memory contract boundary)
# ---------------------------------------------------------------------------

OBSERVED = "OBSERVED"
INFERRED = "INFERRED"
FUSED = "FUSED"
REMEMBERED = "REMEMBERED"
PREDICTED = "PREDICTED"
SIMULATED = "SIMULATED"
COUNTERFACTUAL = "COUNTERFACTUAL"
VERIFIED = "VERIFIED"
UNKNOWN = "UNKNOWN"

ALL_EPISTEMIC_STATUSES = frozenset({
    OBSERVED, INFERRED, FUSED, REMEMBERED, PREDICTED, SIMULATED,
    COUNTERFACTUAL, VERIFIED, UNKNOWN,
})

# Evidence classes (same as docs/03-cognition + NVIDIA integration)
EVIDENCE_CLASSES = frozenset({OBSERVED, INFERRED, PREDICTED, SIMULATED})

# ---------------------------------------------------------------------------
# Verification states (docs/04-memory-and-knowledge/03 §Confidence and verification)
# ---------------------------------------------------------------------------

UNVERIFIED = "UNVERIFIED"
MODEL_SUPPORTED = "MODEL_SUPPORTED"
MULTI_SOURCE_SUPPORTED = "MULTI_SOURCE_SUPPORTED"
USER_CONFIRMED = "USER_CONFIRMED"
SYSTEM_VERIFIED = "SYSTEM_VERIFIED"
EXTERNALLY_VERIFIED = "EXTERNALLY_VERIFIED"
CONTRADICTED = "CONTRADICTED"
EXPIRED = "EXPIRED"

ALL_VERIFICATION_STATES = frozenset({
    UNVERIFIED, MODEL_SUPPORTED, MULTI_SOURCE_SUPPORTED, USER_CONFIRMED,
    SYSTEM_VERIFIED, EXTERNALLY_VERIFIED, CONTRADICTED, EXPIRED,
})

# ---------------------------------------------------------------------------
# Retrieval failure states (docs/04-memory-and-knowledge/04)
# ---------------------------------------------------------------------------

NO_RESULT = "NO_RESULT"
LOW_CONFIDENCE = "LOW_CONFIDENCE"
AMBIGUOUS = "AMBIGUOUS"
CONFLICTED = "CONFLICTED"
STALE = "STALE"
UNAUTHORIZED = "UNAUTHORIZED"
DEGRADED = "DEGRADED"
ABSTAIN = "ABSTAIN"

ALL_RETRIEVAL_STATES = frozenset({
    NO_RESULT, LOW_CONFIDENCE, AMBIGUOUS, CONFLICTED, STALE,
    UNAUTHORIZED, DEGRADED, ABSTAIN,
})

# ---------------------------------------------------------------------------
# Admission decisions (docs/04-memory-and-knowledge/02 §Admission decision)
# ---------------------------------------------------------------------------

DISCARD = "DISCARD"
KEEP_TRANSIENT = "KEEP_TRANSIENT"
STORE_EPISODE = "STORE_EPISODE"
STORE_CANDIDATE = "STORE_CANDIDATE"
MERGE = "MERGE"
UPDATE = "UPDATE"
VERIFY_FIRST = "VERIFY_FIRST"
DEFER_TO_CONSOLIDATION = "DEFER_TO_CONSOLIDATION"
CREATE_SCHEMA_PROPOSAL = "CREATE_SCHEMA_PROPOSAL"
KEEP_EXISTING = "KEEP_EXISTING"

# ---------------------------------------------------------------------------
# Lifecycle states (docs/04-memory-and-knowledge/02 §Lifecycle states)
# ---------------------------------------------------------------------------

CAPTURED = "CAPTURED"
CLASSIFIED = "CLASSIFIED"
ADMISSION_PENDING = "ADMISSION_PENDING"
ADMITTED = "ADMITTED"
TRANSIENT = "TRANSIENT"
INDEXED = "INDEXED"
ACTIVE = "ACTIVE"
CONSOLIDATING = "CONSOLIDATING"
SUPERSEDED = "SUPERSEDED"
ARCHIVED = "ARCHIVED"
DELETED = "DELETED"

ALL_LIFECYCLE_STATES = frozenset({
    CAPTURED, CLASSIFIED, ADMISSION_PENDING, ADMITTED, TRANSIENT,
    INDEXED, ACTIVE, CONSOLIDATING, SUPERSEDED, ARCHIVED, DELETED,
})

# ---------------------------------------------------------------------------
# Source classes (docs/04-memory-and-knowledge/03 §Source classes)
# ---------------------------------------------------------------------------

DIRECT_SENSOR = "DIRECT_SENSOR"
USER_STATEMENT = "USER_STATEMENT"
TRUSTED_PERSON_STATEMENT = "TRUSTED_PERSON_STATEMENT"
OTHER_PERSON_STATEMENT = "OTHER_PERSON_STATEMENT"
SYSTEM_STATE = "SYSTEM_STATE"
TOOL_OUTPUT = "TOOL_OUTPUT"
LOCAL_FILE = "LOCAL_FILE"
DOCUMENT = "DOCUMENT"
DATABASE = "DATABASE"
WEB_RESOURCE = "WEB_RESOURCE"
MODEL_INFERENCE = "MODEL_INFERENCE"
MODEL_GENERATED = "MODEL_GENERATED"
IMPORTED_DATA = "IMPORTED_DATA"
SIMULATION = "SIMULATION"
HUMAN_VALIDATION = "HUMAN_VALIDATION"
DERIVED_MEMORY = "DERIVED_MEMORY"

ALL_SOURCE_CLASSES = frozenset({
    DIRECT_SENSOR, USER_STATEMENT, TRUSTED_PERSON_STATEMENT,
    OTHER_PERSON_STATEMENT, SYSTEM_STATE, TOOL_OUTPUT, LOCAL_FILE,
    DOCUMENT, DATABASE, WEB_RESOURCE, MODEL_INFERENCE, MODEL_GENERATED,
    IMPORTED_DATA, SIMULATION, HUMAN_VALIDATION, DERIVED_MEMORY,
})

# ---------------------------------------------------------------------------
# Canonical MemoryRecord (full field set)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CanonicalMemoryRecord:
    """Full canonical MemoryRecord with epistemic/verification state.

    Extends the base MemoryRecord with:
      - epistemic_status (OBSERVED/INFERRED/PREDICTED/SIMULATED/VERIFIED/UNKNOWN)
      - evidence_class (same as epistemic_status for evidence lineage)
      - independence_group (for corroboration checking)
      - lifecycle_state (CAPTURED/ADMITTED/ACTIVE/STALE/etc.)
      - validity_window (valid_from/valid_until)
      - derivation (how this record was derived from evidence)
      - governance_status (governed/ungoverned/restricted)
    """
    memory_id: str
    memory_type: str
    created_at: str
    content: Any
    confidence: float
    verification_status: str
    epistemic_status: str
    evidence_class: str
    privacy_class: str
    revision: int
    provenance: dict[str, Any]
    source_class: str = ""
    lifecycle_state: str = CAPTURED
    event_refs: tuple[str, ...] = ()
    entity_refs: tuple[str, ...] = ()
    semantic_index_ref: str | None = None
    temporal_context: dict[str, Any] | None = None
    spatial_context: dict[str, Any] | None = None
    retention_policy_ref: str | None = None
    dependency_refs: tuple[str, ...] = ()
    independence_group: str | None = None
    validity_window: dict[str, str | None] | None = None
    derivation: str = "direct"  # direct | inference | fusion | consolidation | simulation
    governance_status: str = "ungoverned"
    integrity_hash: str = ""

    def as_contract(self) -> dict[str, Any]:
        d = {
            "memory_id": self.memory_id,
            "memory_type": self.memory_type,
            "created_at": self.created_at,
            "content": self.content,
            "confidence": self.confidence,
            "verification_status": self.verification_status,
            "privacy_class": self.privacy_class,
            "revision": self.revision,
            "provenance": self.provenance,
            "event_refs": list(self.event_refs),
            "entity_refs": list(self.entity_refs),
            "dependency_refs": list(self.dependency_refs),
        }
        if self.semantic_index_ref is not None:
            d["semantic_index_ref"] = self.semantic_index_ref
        if self.temporal_context is not None:
            d["temporal_context"] = self.temporal_context
        if self.spatial_context is not None:
            d["spatial_context"] = self.spatial_context
        if self.retention_policy_ref is not None:
            d["retention_policy_ref"] = self.retention_policy_ref
        # Extended fields (not in the v1.0.0 schema but part of the canonical contract).
        d["epistemic_status"] = self.epistemic_status
        d["evidence_class"] = self.evidence_class
        d["source_class"] = self.source_class
        d["lifecycle_state"] = self.lifecycle_state
        d["independence_group"] = self.independence_group
        d["validity_window"] = self.validity_window
        d["derivation"] = self.derivation
        d["governance_status"] = self.governance_status
        d["integrity_hash"] = self.integrity_hash
        return d


# ---------------------------------------------------------------------------
# Admission result
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AdmissionResult:
    """Result of the write-gate admission pipeline."""
    accepted: bool
    memory_id: str | None
    decision: str
    reason: str
    gate_stage: str  # which gate stage accepted/rejected
    record: CanonicalMemoryRecord | None = None


# ---------------------------------------------------------------------------
# Retrieval result
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RetrievalResult:
    """Result of a retrieval query with explicit failure states."""
    records: tuple[CanonicalMemoryRecord, ...]
    state: str  # RESOLVED | NO_RESULT | AMBIGUOUS | CONFLICTED | STALE | ABSTAIN | UNAUTHORIZED
    reason: str = ""
    candidates_examined: int = 0
    conflicts: tuple[dict[str, Any], ...] = ()

    @property
    def is_failure(self) -> bool:
        return self.state in ALL_RETRIEVAL_STATES

    @property
    def is_resolved(self) -> bool:
        return self.state == "RESOLVED"


# ---------------------------------------------------------------------------
# Governance (docs/04-memory-and-knowledge/15)
# ---------------------------------------------------------------------------

ALLOW = "ALLOW"
DENY = "DENY"
RESTRICT = "RESTRICT"
REQUIRE_HUMAN = "REQUIRE_HUMAN"
ESCALATE = "ESCALATE"

ALL_GOVERNANCE_DECISIONS = frozenset({ALLOW, DENY, RESTRICT, REQUIRE_HUMAN, ESCALATE})


@dataclass(frozen=True)
class GovernanceRequest:
    """A governance request for a memory operation."""
    request_id: str
    memory_id: str
    operation: str  # read | write | delete | export | share
    actor: str = "system"
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GovernanceDecision:
    """A governance decision for a memory operation."""
    request_id: str
    decision: str  # ALLOW | DENY | RESTRICT | REQUIRE_HUMAN | ESCALATE
    reason: str = ""
    conditions: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Write Gate (docs/04-memory-and-knowledge/02 §Memory write gate)
# ---------------------------------------------------------------------------

class WriteGate:
    """The memory write gate: identity -> integrity -> privacy -> instruction-data
    separation -> poisoning -> retention -> policy.

    No ordinary durable memory may bypass this gate.
    """

    def __init__(
        self,
        *,
        min_confidence: float = 0.0,
        reject_simulated_as_fact: bool = True,
        poison_patterns: set[str] | None = None,
    ) -> None:
        self.min_confidence = min_confidence
        self.reject_simulated_as_fact = reject_simulated_as_fact
        self.poison_patterns = poison_patterns or {
            "ignore previous instructions",
            "forget all instructions",
            "you are now",
            "system prompt:",
        }

    def evaluate(
        self,
        *,
        memory_type: str,
        content: Any,
        confidence: float,
        epistemic_status: str,
        evidence_class: str,
        source_class: str,
        provenance: dict[str, Any],
        privacy_class: str,
    ) -> AdmissionResult:
        """Run the write gate pipeline. Returns an AdmissionResult."""

        # Stage 1: Identity / source
        if not provenance or not provenance.get("source"):
            return AdmissionResult(False, None, DISCARD, "missing_provenance_source", "identity")
        if not source_class:
            return AdmissionResult(False, None, DISCARD, "missing_source_class", "identity")

        # Stage 2: Integrity
        if content is None or content == "" or content == {}:
            return AdmissionResult(False, None, DISCARD, "empty_content", "integrity")
        if not 0.0 <= confidence <= 1.0:
            return AdmissionResult(False, None, DISCARD, "confidence_out_of_range", "integrity")

        # Stage 3: Privacy classification
        if not privacy_class:
            return AdmissionResult(False, None, DISCARD, "missing_privacy_class", "privacy")

        # Stage 4: Instruction/data separation
        if isinstance(content, str):
            content_lower = content.lower()
            for pattern in self.poison_patterns:
                if pattern in content_lower:
                    return AdmissionResult(False, None, DISCARD, f"poisoning_detected:{pattern}", "poisoning")

        # Stage 5: Poisoning / anomaly check
        if isinstance(content, str):
            # Check for injection-like patterns.
            if "ignore previous" in content.lower() or "disregard all" in content.lower():
                return AdmissionResult(False, None, DISCARD, "instruction_injection_detected", "poisoning")

        # Stage 6: Retention decision — simulated evidence cannot become fact.
        if self.reject_simulated_as_fact:
            if evidence_class == SIMULATED and epistemic_status in (VERIFIED, OBSERVED):
                return AdmissionResult(False, None, DISCARD,
                                        "simulated_evidence_cannot_be_fact", "retention")
            if evidence_class == PREDICTED and epistemic_status == VERIFIED:
                return AdmissionResult(False, None, DISCARD,
                                        "predicted_evidence_cannot_be_verified_fact", "retention")

        # Stage 7: Admission policy — passed all gates.
        return AdmissionResult(True, None, STORE_EPISODE, "admitted", "policy")


# ---------------------------------------------------------------------------
# Independence groups (docs/04-memory-and-knowledge/03 §Independence)
# ---------------------------------------------------------------------------

class IndependenceTracker:
    """Tracks independence groups so observations from the same source are not
    counted as independent corroboration.

    Two observations derived from the same underlying source (e.g. same camera
    frame -> object detector -> summary -> embedding) remain one evidence
    lineage, not four independent confirmations.
    """

    def __init__(self) -> None:
        self._groups: dict[str, set[str]] = {}  # group_id -> set of source_ids
        self._record_groups: dict[str, str] = {}  # memory_id -> group_id

    def assign(self, memory_id: str, source_id: str, *, parent_group: str | None = None) -> str:
        """Assign a record to an independence group. Returns the group_id."""
        if parent_group and parent_group in self._groups:
            group_id = parent_group
        else:
            group_id = f"ind:{source_id[:16]}"
        self._groups.setdefault(group_id, set()).add(source_id)
        self._record_groups[memory_id] = group_id
        return group_id

    def group_of(self, memory_id: str) -> str | None:
        return self._record_groups.get(memory_id)

    def restore(self, memory_id: str, group_id: str, *, source_id: str | None = None) -> None:
        """Restore a persisted (memory_id → group_id) mapping after a restart.

        This is the durable-store bridge: stores persist the independence_group
        column, and DurableMemoryStore.__init__ calls this for every row so
        corroboration counting survives restarts (gap-analysis Step 2).
        """
        if not group_id:
            return
        self._groups.setdefault(group_id, set())
        if source_id:
            self._groups[group_id].add(source_id)
        self._record_groups[memory_id] = group_id

    def tracked_record_ids(self) -> tuple[str, ...]:
        return tuple(self._record_groups)

    def tracked_group_count(self) -> int:
        return len(self._groups)

    def are_independent(self, memory_id_a: str, memory_id_b: str) -> bool:
        """True if two records are from independent evidence lineages."""
        ga = self._record_groups.get(memory_id_a)
        gb = self._record_groups.get(memory_id_b)
        if ga is None or gb is None:
            return True  # unknown → treat as independent (conservative for corroboration)
        return ga != gb

    def corroboration_count(self, memory_ids: Sequence[str]) -> int:
        """Count the number of independent evidence lineages among records."""
        groups = set()
        for mid in memory_ids:
            g = self._record_groups.get(mid)
            if g:
                groups.add(g)
        return len(groups)


# ---------------------------------------------------------------------------
# Contextual trust (docs/04-memory-and-knowledge/03 §Trust is contextual)
# ---------------------------------------------------------------------------

class ContextualTrust:
    """Contextual trust: trust(source, claim_type, context, time, consequence).

    A user can be authoritative about their own preference while a sensor can
    be authoritative about a measurement within its calibrated domain.
    """

    # Default trust scores: (source_class, claim_type) -> trust [0..1]
    _DEFAULTS: dict[tuple[str, str], float] = {
        (DIRECT_SENSOR, "measurement"): 0.9,
        (DIRECT_SENSOR, "preference"): 0.3,
        (USER_STATEMENT, "preference"): 0.95,
        (USER_STATEMENT, "measurement"): 0.3,
        (TRUSTED_PERSON_STATEMENT, "preference"): 0.7,
        (MODEL_INFERENCE, "classification"): 0.6,
        (MODEL_INFERENCE, "preference"): 0.2,
        (SIMULATION, "prediction"): 0.5,
        (SIMULATION, "fact"): 0.1,
        (HUMAN_VALIDATION, "fact"): 0.95,
    }

    def trust(self, source_class: str, claim_type: str, *, context: str = "", consequence: str = "") -> float:
        """Return contextual trust score [0..1]."""
        return self._DEFAULTS.get((source_class, claim_type), 0.5)

    def is_authoritative(self, source_class: str, claim_type: str) -> bool:
        """True if the source is authoritative for this claim type."""
        return self.trust(source_class, claim_type) >= 0.7


# ---------------------------------------------------------------------------
# HardenedMemoryManager — the full admission/retrieval pipeline
# ---------------------------------------------------------------------------

class HardenedMemoryManager:
    """Memory manager with the canonical MemoryRecord contract, write gate,
    retrieval failure states, contextual trust, and independence groups.

    This is an in-process semantic layer that can wrap any storage adapter.
    It does not own the storage engine (SQLite, etc.) — it enforces the
    contract boundary above storage.
    """

    def __init__(
        self,
        *,
        write_gate: WriteGate | None = None,
        trust: ContextualTrust | None = None,
        independence: IndependenceTracker | None = None,
        stale_threshold_seconds: float = 3600.0,  # 1 hour default staleness
    ) -> None:
        self._records: dict[str, CanonicalMemoryRecord] = {}
        self._deleted: set[str] = set()
        self.write_gate = write_gate or WriteGate()
        self.trust = trust or ContextualTrust()
        self.independence = independence or IndependenceTracker()
        self.stale_threshold = stale_threshold_seconds
        self._governance_decisions: dict[str, GovernanceDecision] = {}

    # ---- source class inference for backward compatibility ----

    _SOURCE_CLASS_MAP: dict[str, str] = {
        "perception": DIRECT_SENSOR,
        "observation": DIRECT_SENSOR,
        "utterance": USER_STATEMENT,
        "preference": USER_STATEMENT,
        "simulation": SIMULATION,
        "prediction": MODEL_INFERENCE,
        "summary": DERIVED_MEMORY,
        "narrative": DERIVED_MEMORY,
    }

    def _infer_source_class(self, memory_type: str, provenance: dict[str, Any]) -> str:
        """Infer the source class from memory_type and provenance."""
        # Check provenance source first.
        source = str(provenance.get("source", "")).lower()
        if "camera" in source or "sensor" in source or "vision" in source:
            return DIRECT_SENSOR
        if "audio" in source or "stt" in source or "microphone" in source:
            return DIRECT_SENSOR
        if "user" in source or "web" in source:
            return USER_STATEMENT
        if "sim" in source or "isaac" in source:
            return SIMULATION
        if "model" in source or "llm" in source or "ollama" in source:
            return MODEL_INFERENCE
        # Fall back to memory_type mapping.
        return self._SOURCE_CLASS_MAP.get(memory_type, SYSTEM_STATE)

    def admit(
        self,
        *,
        memory_type: str,
        content: Any,
        confidence: float,
        epistemic_status: str = OBSERVED,
        evidence_class: str = OBSERVED,
        verification_status: str = UNVERIFIED,
        source_class: str = "",
        privacy_class: str = "unclassified",
        provenance: dict[str, Any] | None = None,
        entity_refs: Iterable[str] = (),
        event_refs: Iterable[str] = (),
        dependency_refs: Iterable[str] = (),
        temporal_context: dict[str, Any] | None = None,
        spatial_context: dict[str, Any] | None = None,
        retention_policy_ref: str | None = None,
        validity_window: dict[str, str | None] | None = None,
        derivation: str = "direct",
        independence_source_id: str = "",
        created_at: str = "",
    ) -> AdmissionResult:
        """Run the full write-gate admission pipeline.

        Backward-compatible with DeterministicMemoryManager.admit(): the new
        parameters (epistemic_status, evidence_class, source_class) have sensible
        defaults so existing callers work without changes.
        """

        if provenance is None:
            provenance = {}

        # Infer source_class from provenance/memory_type if not provided.
        if not source_class:
            source_class = self._infer_source_class(memory_type, provenance)
        if not created_at:
            from datetime import datetime, timezone
            created_at = datetime.now(timezone.utc).isoformat()

        # Run the write gate.
        gate_result = self.write_gate.evaluate(
            memory_type=memory_type,
            content=content,
            confidence=confidence,
            epistemic_status=epistemic_status,
            evidence_class=evidence_class,
            source_class=source_class,
            provenance=provenance,
            privacy_class=privacy_class,
        )
        if not gate_result.accepted:
            return gate_result

        # Compute integrity hash.
        integrity_input = f"{memory_type}:{content}:{confidence}:{source_class}"
        integrity_hash = sha256(str(integrity_input).encode("utf-8")).hexdigest()[:16]

        # Create the canonical record. The id is a content hash (excluding
        # created_at) so identical content dedups consistently with the durable
        # path (DurableMemoryStore.admit), regardless of when it was observed.
        memory_id = "mem-" + sha256(
            f"{integrity_hash}".encode("utf-8")
        ).hexdigest()[:24]

        # Check for duplicate (idempotency).
        if memory_id in self._records:
            return AdmissionResult(True, memory_id, KEEP_EXISTING, "duplicate_admission", "policy",
                                    self._records[memory_id])

        record = CanonicalMemoryRecord(
            memory_id=memory_id,
            memory_type=memory_type,
            created_at=created_at,
            content=content,
            confidence=confidence,
            verification_status=verification_status,
            epistemic_status=epistemic_status,
            evidence_class=evidence_class,
            privacy_class=privacy_class,
            revision=0,
            provenance=provenance,
            source_class=source_class,
            lifecycle_state=ADMITTED,
            event_refs=tuple(event_refs),
            entity_refs=tuple(entity_refs),
            temporal_context=temporal_context,
            spatial_context=spatial_context,
            retention_policy_ref=retention_policy_ref,
            dependency_refs=tuple(dependency_refs),
            validity_window=validity_window,
            derivation=derivation,
            integrity_hash=integrity_hash,
        )
        self._records[memory_id] = record

        # Track independence.
        group_id = None
        if independence_source_id:
            group_id = self.independence.assign(memory_id, independence_source_id)

        # Promote to ACTIVE and set independence group.
        update_dict = {**record.__dict__, "lifecycle_state": ACTIVE}
        if group_id is not None:
            update_dict["independence_group"] = group_id
        self._records[memory_id] = CanonicalMemoryRecord(**update_dict)

        return AdmissionResult(True, memory_id, STORE_EPISODE, "admitted", "policy",
                                self._records[memory_id])

    def retrieve(
        self,
        query: str,
        *,
        entity: str | None = None,
        memory_type: str | None = None,
        limit: int = 5,
        min_confidence: float = 0.0,
        require_current: bool = False,
        privacy_scope: str = "default",
    ) -> tuple[CanonicalMemoryRecord, ...]:
        """Retrieve memory records (backward-compatible with DeterministicMemoryManager).

        Returns a tuple of records, sorted by relevance. For the full
        RetrievalResult with failure states, use retrieve_with_states().
        """
        result = self.retrieve_with_states(
            query, entity=entity, memory_type=memory_type,
            limit=limit, min_confidence=min_confidence,
            require_current=require_current, privacy_scope=privacy_scope,
        )
        return result.records

    def retrieve_indexed(
        self,
        query: str,
        *,
        entity: str | None = None,
        memory_type: str | None = None,
        limit: int = 5,
        min_confidence: float = 0.0,
        require_current: bool = False,
        privacy_scope: str = "default",
    ) -> tuple[CanonicalMemoryRecord, ...]:
        """Alias for retrieve() — compatible with DurableMemoryStore.retrieve_indexed."""
        return self.retrieve(query, entity=entity, memory_type=memory_type,
                             limit=limit, min_confidence=min_confidence,
                             require_current=require_current, privacy_scope=privacy_scope)

    def retrieve_with_states(
        self,
        query: str,
        *,
        entity: str | None = None,
        memory_type: str | None = None,
        limit: int = 5,
        min_confidence: float = 0.0,
        require_current: bool = False,
        privacy_scope: str = "default",
    ) -> RetrievalResult:
        """Retrieve memory records with explicit failure states.

        Returns a RetrievalResult with state:
          RESOLVED — records found and consistent.
          NO_RESULT — no matching records.
          AMBIGUOUS — multiple records with similar relevance.
          CONFLICTED — records with contradictory content.
          STALE — records found but all are stale.
          ABSTAIN — insufficient evidence for the consequence.
        """
        import json as _json
        from datetime import datetime, timezone

        if limit <= 0:
            return RetrievalResult((), NO_RESULT, "limit_is_zero", 0)

        terms = {term.lower() for term in query.split() if term}
        candidates: list[tuple[int, CanonicalMemoryRecord]] = []
        conflicts: list[dict[str, Any]] = []

        for memory_id, record in self._records.items():
            if memory_id in self._deleted:
                continue
            if entity is not None and entity not in record.entity_refs:
                continue
            if memory_type is not None and record.memory_type != memory_type:
                continue
            if record.confidence < min_confidence:
                continue
            # Privacy filtering.
            if privacy_scope == "restricted" and record.privacy_class != "unclassified":
                continue
            if privacy_scope == "default" and record.privacy_class in ("restricted", "private"):
                continue
            haystack = _json.dumps(record.content, sort_keys=True, default=str).lower()
            haystack += " " + " ".join(record.entity_refs)
            score = sum(1 for term in terms if term in haystack)
            if terms and score == 0:
                continue
            candidates.append((score, record))

        candidates.sort(key=lambda item: (-item[0], -item[1].confidence))

        if not candidates:
            return RetrievalResult((), NO_RESULT, "no_matching_records", 0)

        # Check for conflicts among top candidates.
        top_records = [r for _, r in candidates[:limit]]
        top_contents = [str(r.content) for r in top_records]

        # Check for explicit conflicts: records with overlapping entity_refs
        # where the content differs (same entity, different claims).
        conflicts: list[dict[str, Any]] = []
        conflict_groups: dict[str, list[CanonicalMemoryRecord]] = {}
        for r in top_records:
            key = " ".join(r.entity_refs) if r.entity_refs else r.memory_type
            conflict_groups.setdefault(key, []).append(r)
        for key, group in conflict_groups.items():
            if len(group) > 1 and len(set(str(r.content) for r in group)) > 1:
                conflicts.append({
                    "entity_key": key,
                    "records": [{"memory_id": r.memory_id, "content": r.content,
                                      "confidence": r.confidence, "epistemic_status": r.epistemic_status}
                                     for r in group],
                })

        # Check staleness.
        now = datetime.now(timezone.utc)
        stale_records = []
        fresh_records = []
        for r in top_records:
            is_stale = False
            if r.validity_window and r.validity_window.get("valid_until"):
                try:
                    valid_until = datetime.fromisoformat(r.validity_window["valid_until"].replace("Z", "+00:00"))
                    if now > valid_until:
                        is_stale = True
                except (ValueError, TypeError):
                    pass
            if r.verification_status == EXPIRED:
                is_stale = True
            if is_stale:
                stale_records.append(r)
            else:
                fresh_records.append(r)

        if require_current and not fresh_records and stale_records:
            return RetrievalResult(tuple(stale_records), STALE, "all_records_stale", len(candidates))

        if conflicts:
            return RetrievalResult(tuple(top_records), CONFLICTED, "contradictory_records",
                                   len(candidates), tuple(conflicts))

        if len(top_records) > 1 and len(set(str(r.content) for r in top_records)) > 1:
            return RetrievalResult(tuple(top_records), AMBIGUOUS, "multiple_distinct_results",
                                   len(candidates))

        return RetrievalResult(tuple(top_records), "RESOLVED", "", len(candidates))

    def get(self, memory_id: str) -> CanonicalMemoryRecord | None:
        if memory_id in self._deleted:
            return None
        return self._records.get(memory_id)

    def forget(self, memory_id: str) -> bool:
        if memory_id not in self._records or memory_id in self._deleted:
            return False
        self._deleted.add(memory_id)
        # Mark as DELETED lifecycle.
        if memory_id in self._records:
            record = self._records[memory_id]
            self._records[memory_id] = CanonicalMemoryRecord(
                **{**record.__dict__, "lifecycle_state": DELETED}
            )
        return True

    def govern(self, request: GovernanceRequest) -> GovernanceDecision:
        """Evaluate a governance request for a memory operation."""
        record = self.get(request.memory_id)
        if record is None:
            return GovernanceDecision(request.request_id, DENY, "record_not_found")
        if request.operation == "delete" and record.privacy_class == "protected":
            return GovernanceDecision(request.request_id, REQUIRE_HUMAN,
                                      "protected_record_requires_human_approval")
        if request.operation == "export" and record.privacy_class in ("restricted", "private"):
            return GovernanceDecision(request.request_id, RESTRICT,
                                      "restricted_privacy_class_export_limited")
        decision = GovernanceDecision(request.request_id, ALLOW)
        self._governance_decisions[request.request_id] = decision
        return decision

    @property
    def active_count(self) -> int:
        return sum(1 for mid in self._records if mid not in self._deleted)

    @property
    def deleted_count(self) -> int:
        return len(self._deleted)

    def all_records(self) -> tuple[CanonicalMemoryRecord, ...]:
        return tuple(r for mid, r in self._records.items() if mid not in self._deleted)
