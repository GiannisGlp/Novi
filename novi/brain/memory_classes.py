"""Memory-class decision + schema-evolution hooks (roadmap item 16).

Decision: which memory classes are implemented NOW vs DEFERRED to the body
phase (procedural, prospective, metamemory, autobiographical continuity are
heavy and depend on an embodied/operating Novi — see
docs/00-strategy ... item 15/16 and docs/04-memory-and-knowledge/12).

Implemented now (epistemic, provable with the current head/software stack):
  SEMANTIC (knowledge graph + durable stores), EPISODIC (observations, events,
  episodes, summaries), SPATIAL (SpatialMap), TEMPORAL (causal link model),
  PREFERENCE, ROUTINE_CANDIDATE, PROCEDURAL_CANDIDATE (candidate extraction
  only — promotion needs body verification, per lifecycle doc §Execution).

Deferred (body/skill phase; only the *candidate* pipeline exists now):
  PROCEDURAL_COMPETENCE, PROSPECTIVE (deferred intentions/promises),
  METAMEMORY, AUTOBIOGRAPHICAL_CONTINUITY.

Schema evolution follows the L0–L6 ladder of doc 12: autonomous memory/data
levels L0–L3 remain open; L4 (schema extension) requires proposal+validation;
L5 (runtime/software) and L6 (protected core) are NOT autonomous. This module
provides the classification + gate hooks.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class MemoryClass(str, Enum):
    """Canonical memory-class taxonomy (docs/04 §01 core model)."""

    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    SPATIAL = "spatial"
    TEMPORAL = "temporal"
    PREFERENCE = "preference"
    ROUTINE_CANDIDATE = "routine_candidate"
    PROCEDURAL_CANDIDATE = "procedural_candidate"
    PROCEDURAL_COMPETENCE = "procedural_competence"
    PROSPECTIVE = "prospective"
    METAMEMORY = "metamemory"
    AUTOBIOGRAPHICAL = "autobiographical"


IMPLEMENTED_NOW = frozenset({
    MemoryClass.SEMANTIC,
    MemoryClass.EPISODIC,
    MemoryClass.SPATIAL,
    MemoryClass.TEMPORAL,
    MemoryClass.PREFERENCE,
    MemoryClass.ROUTINE_CANDIDATE,
    MemoryClass.PROCEDURAL_CANDIDATE,
})

DEFERRED_CLASSES = frozenset({
    MemoryClass.PROCEDURAL_COMPETENCE,
    MemoryClass.PROSPECTIVE,
    MemoryClass.METAMEMORY,
    MemoryClass.AUTOBIOGRAPHICAL,
})

_DEFERRAL_RATIONALE = {
    MemoryClass.PROCEDURAL_COMPETENCE: (
        "depends on the body/actuator phase and verified execution outcomes; "
        "candidate extraction is implemented now, competence promotion is not"
    ),
    MemoryClass.PROSPECTIVE: (
        "deferred intentions/promises need long-horizon scheduling and real "
        "task commitments; planned with the autonomy/body phase"
    ),
    MemoryClass.METAMEMORY: (
        "self-assessment of memory quality needs error/access statistics across "
        "a long operating history; deferred to bounded metrology work"
    ),
    MemoryClass.AUTOBIOGRAPHICAL: (
        "long-horizon self-narrative continuity requires sustained identity "
        "assembly over real operation; heavy, deferred by design"
    ),
}


@dataclass(frozen=True)
class MemoryClassDecision:
    """One entry of the now-vs-defer decision registry (item 16)."""
    memory_class: MemoryClass
    state: str  # "implemented" | "deferred" | "candidate"
    deferral_phase: str  # "brain" (now) | "body" | "software"
    rationale: str = ""

    def snapshot(self) -> dict[str, Any]:
        return {
            "memory_class": self.memory_class.value,
            "state": self.state,
            "deferral_phase": self.deferral_phase,
            "rationale": self.rationale,
        }


class MemoryClassDecisionRegistry:
    """The recorded decision: what is implemented now vs deferred (item 16)."""

    def __init__(self) -> None:
        self._decisions: dict[MemoryClass, MemoryClassDecision] = {}
        for cls in IMPLEMENTED_NOW:
            self._decisions[cls] = MemoryClassDecision(
                memory_class=cls, state="implemented", deferral_phase="brain",
                rationale="memory-safe with the current perception/cognition/software stack",
            )
        for cls in DEFERRED_CLASSES:
            self._decisions[cls] = MemoryClassDecision(
                memory_class=cls, state="deferred", deferral_phase="body",
                rationale=_DEFERRAL_RATIONALE[cls],
            )

    def decision(self, memory_class: MemoryClass) -> MemoryClassDecision:
        return self._decisions[memory_class]

    def implemented(self) -> tuple[MemoryClass, ...]:
        return tuple(c for c, d in self._decisions.items() if d.state == "implemented")

    def deferred(self) -> tuple[MemoryClass, ...]:
        return tuple(c for c, d in self._decisions.items() if d.state == "deferred")

    def snapshot(self) -> dict[str, Any]:
        return {
            "implemented": sorted(c.value for c in self.implemented()),
            "deferred": sorted(c.value for c in self.deferred()),
            "decisions": [d.snapshot() for d in self._decisions.values()],
        }


class SchemaEvolutionLevel(str, Enum):
    """L0–L6 evolution ladder (doc 12 §Evolution levels)."""

    L0_RUNTIME_STATE = "L0_runtime_state"
    L1_MEMORY_CONTENT = "L1_memory_content"
    L2_KNOWLEDGE_CONTENT = "L2_knowledge_content"
    L3_NONSTRUCTURAL_METADATA = "L3_nonstructural_metadata"
    L4_SCHEMA_EXTENSION = "L4_schema_extension"
    L5_RUNTIME_SOFTWARE = "L5_runtime_software"
    L6_PROTECTED_CORE = "L6_protected_core"

    @property
    def autonomous(self) -> bool:
        """L0–L3 are autonomous within policy; L4+ are controlled."""
        return self in {
            SchemaEvolutionLevel.L0_RUNTIME_STATE,
            SchemaEvolutionLevel.L1_MEMORY_CONTENT,
            SchemaEvolutionLevel.L2_KNOWLEDGE_CONTENT,
            SchemaEvolutionLevel.L3_NONSTRUCTURAL_METADATA,
        }


@dataclass(frozen=True)
class SchemaEvolutionProposal:
    """A proposed schema change classified against the L0–L6 ladder."""
    change_id: str
    description: str
    level: SchemaEvolutionLevel
    compatibility: str  # COMPATIBLE | CONDITIONALLY_COMPATIBLE | MIGRATION_REQUIRED | ...

    @property
    def allowed(self) -> bool:
        """Autonomous execution only at L0–L3; L4+ is controlled/forbidden."""
        return self.level.autonomous


class SchemaEvolutionGate:
    """Hooks that gate schema evolution by level (L0–L6, doc 12)."""

    def __init__(self) -> None:
        self._proposals: list[SchemaEvolutionProposal] = []

    def propose(
        self,
        *,
        change_id: str,
        description: str,
        level: SchemaEvolutionLevel,
        compatibility: str,
    ) -> SchemaEvolutionProposal:
        proposal = SchemaEvolutionProposal(
            change_id=change_id, description=description,
            level=level, compatibility=compatibility,
        )
        self._proposals.append(proposal)
        return proposal

    def is_autonomously_allowed(self, level: SchemaEvolutionLevel) -> bool:
        return level.autonomous

    def proposals(self) -> tuple[SchemaEvolutionProposal, ...]:
        return tuple(self._proposals)

    def snapshot(self) -> dict[str, Any]:
        return {
            "levels": [lvl.value for lvl in SchemaEvolutionLevel],
            "proposals": [
                {"change_id": p.change_id, "level": p.level.value,
                 "compatibility": p.compatibility, "allowed": p.allowed}
                for p in self._proposals
            ],
        }
