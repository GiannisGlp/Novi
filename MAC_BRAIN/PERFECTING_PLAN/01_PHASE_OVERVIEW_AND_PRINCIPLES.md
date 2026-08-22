# 01 — Phase Overview and Principles

## Scope of "brain phase"
Novi is not in full-robot development. The phase is the **cognitive core** that will
later be embodied. Per the strategy, the mind is developed before the body and must
remain conceptually independent of hardware. NVIDIA is a reference acceleration/simulation
ecosystem; it does **not** define Novi's semantics.

## Authority hierarchy (docs/00-strategy, 01-system-architecture)
North Star → Project strategy → System Architecture → Domain architecture → detailed
spec → ADR → implementation spec → validation evidence.
- A validation result may trigger a new ADR; it never silently rewrites architecture.
- One canonical owner per concept; others consume/derive but never redefine.
- "Document exists" is not completion — completion needs evidence (E2+).

## Ownership split (canonical)
- **Brain** coordinates/lifecycle/scheduling/model-registry/perception-runtime/body telemetry.
- **Cognition** understands: world/situation model, reasoning, model selection.
- **Memory & Knowledge** remembers/knows: MemoryRecord, knowledge graph, provenance.
- **Autonomy** chooses/pursues goals, attention, communication decisions.
- **Soul** defines who Novi is: identity, self-model, personality, values, affect, lexicon.
- **Policy/Safety** permits/denies at the boundary; **Hardware** executes.

## Cross-cutting invariants (apply to every step)
- language ≠ physical capability ≠ authorization ≠ safe-now ≠ executed action.
- installed ≠ validated ≠ available; commanded ≠ executed ≠ outcome.
- models are capability providers, never authorities; neural output is evidence/proposal.
- memory must never override live telemetry; memory never mutates schema.
- observation ≠ evidence ≠ memory ≠ knowledge ≠ belief; prediction ≠ fact.
- trust ≠ authorization; confidence ≠ provenance; retrieval ≠ truth.
- deterministic controls stay deterministic; fail-closed on unsafe ambiguity.
- local-first, connectivity-independent (tested runtime profile), vendor-neutral core.

## Evidence classes (10_ARCHITECTURE_VALIDATION_AND_TRACEABILITY)
E0 project assertion → E1 vendor/standards docs → E2 reproducible benchmark →
E3 integration → E4 physical → E5 long-duration. Critical claims may not remain E0.
The plan's acceptance bar maps each gap to an evidence class and a reproducible check.

## Portability
One logical capability contract runs across Development (Mac) → Simulation → Edge
(Jetson AGX Orin 64GB candidate) → Physical robot; only platform adapters/model
runtimes/sensor drivers change. All new logic goes in MAC_BRAIN/brain (portable), not
in web/server.py.

