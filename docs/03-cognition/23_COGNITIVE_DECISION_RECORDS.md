# 23 — Cognitive Decision Records

## Status

**DESIGN**

## Purpose

Capture durable architectural decisions affecting cognition so future implementations do not accidentally reverse important constraints.

## Decision Template

Each decision record should contain:

- decision ID
- date
- problem
- considered options
- constraints
- selected approach
- rationale
- rejected alternatives
- benchmark/evidence requirements
- consequences
- review trigger

## Initial Decisions

### COG-001 — Vendor Neutrality

Novi will not make cognition dependent on a single vendor ecosystem. Existing open-source local solutions are evaluated and selected by evidence.

### COG-002 — Local First

Local execution is the default. Cloud services require an explicit exception.

### COG-003 — Stable Capability Interfaces

Models, databases, perception systems, and vendor runtimes are accessed through stable Novi contracts where practical.

### COG-004 — Model Is Not Source of Truth

Language and vision models produce interpretations/proposals. Authoritative memory, knowledge, identity, authorization, and safety remain external services.

### COG-005 — Structured Actions

Physical or external actions require typed capability requests. Free-form model text cannot directly become an executable action.

### COG-006 — Immutable Safety Boundary

Learning and adaptive data cannot modify the protected safety/security core.

### COG-007 — Evidence and Provenance

Important derived cognition must retain evidence/provenance and distinguish observation, inference, hypothesis, prediction, and verified knowledge.

### COG-008 — Silence Is Valid

The cognitive system must be capable of deciding that no external response is appropriate.

## Review Triggers

Decisions should be revisited when:

- new open-source technology materially changes capability;
- target hardware changes;
- benchmark evidence invalidates an assumption;
- safety requirements change;
- privacy requirements change;
- a major failure exposes an architectural weakness.
