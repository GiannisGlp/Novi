# 16 — Cognitive Failure Modes

## Status

**DESIGN**

## Purpose

Define expected failures of cognition and the required safe behavior.

## Failure Categories

### Perception uncertainty

The system cannot confidently identify what it sees/hears.

**Response:** preserve ambiguity, seek additional evidence, or ask when useful.

### Identity ambiguity

Multiple people may match the evidence.

**Response:** avoid sensitive personalization or authorization until resolved.

### Knowledge conflict

Sources disagree.

**Response:** retain both claims with provenance and lower confidence until verified.

### Model hallucination

A model proposes unsupported information.

**Response:** require retrieval/evidence for factual or consequential claims; never treat generated text as authoritative fact by default.

### Context failure

Required context is missing or stale.

**Response:** retrieve again, request clarification, or defer.

### Tool failure

A capability is unavailable or fails.

**Response:** return structured failure, use validated fallback, replan, or ask the user.

### Resource exhaustion

CPU/GPU/memory/thermal/battery constraints prevent normal processing.

**Response:** degrade non-critical workloads and preserve safety.

### Contradictory world state

Sensors disagree.

**Response:** maintain competing hypotheses, seek corroboration, and avoid unsafe actions based on the conflict.

### Model unavailable

Primary reasoning model cannot run.

**Response:** use deterministic or specialized local fallback where possible.

### Corrupted persistent data

Memory/knowledge data cannot be trusted.

**Response:** isolate affected records, use verified backups/redundant state, and never silently invent replacement data.

## Degraded Modes

Novi should support explicitly named modes such as:

- perception-degraded
- identity-degraded
- reasoning-degraded
- memory-degraded
- network-offline
- compute-constrained
- safety-only

## Fail-Closed vs Fail-Open

The correct behavior depends on capability risk. Safety-critical controls fail safe. Non-critical informational capabilities may fail open to a lower-quality fallback.

## Acceptance Criteria

Every major cognitive dependency has defined failure semantics, fallback behavior, user-facing behavior where applicable, and test coverage.
