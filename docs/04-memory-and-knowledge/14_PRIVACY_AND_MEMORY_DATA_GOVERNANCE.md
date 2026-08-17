# 14 — Privacy and Memory Data Governance

**Status:** CANONICAL — CONSOLIDATED V1

## Purpose
Define privacy controls specific to memory and knowledge while delegating infrastructure-wide lifecycle guarantees to document 111.

## Core principle

```text
COLLECT MINIMALLY
→ USE FOR A DEFINED PURPOSE
→ DERIVE CAREFULLY
→ RETAIN NO LONGER THAN NEEDED
→ DELETE / RESTRICT / ANONYMISE
→ VERIFY
```

## Data classes

Memory should distinguish public, operational, personal, sensitive, credential, biometric, location, communication and derived data. Classification determines access, retention, replication and deletion behavior.

## Memory minimization

Store the minimum semantic detail required for future utility. Prefer references, summaries or coarse representations when exact raw content is unnecessary, but never discard provenance needed for accountability without an explicit retention decision.

## Access

Memory access is scoped by principal, purpose, entity, sensitivity and policy. Retrieval must enforce authorization before content reaches the reasoning context.

## Derived data

Embeddings, summaries, graph relationships, causal models and skills may contain information derived from protected sources. They are privacy-relevant dependencies, not automatically anonymous.

## Retention

Retention rules are purpose- and class-specific. Expiry creates a deletion/restriction obligation and must propagate through replicas, indexes, caches, snapshots and backups under `111`.

## User controls

Where applicable, users can inspect, correct, restrict and request deletion of their memory. Corrections preserve provenance; deletion must not be silently undone by recovery or synchronization.

## Privacy-preserving retrieval

Do not retrieve sensitive memory merely because it is semantically similar. Apply purpose, authorization, sensitivity and relevance filters before ranking.

## Safety invariants

1. Privacy policy is enforced before retrieval exposure.
2. Derived representations inherit relevant privacy dependencies.
3. Deletion cannot be defeated by stale replicas or recovery.
4. Exact location/identity data is not exposed when a coarser representation suffices.
5. Human oversight does not imply unrestricted memory access.
6. Audit records themselves receive privacy controls.

## Boundary with 111

`14` defines semantic memory governance. `111` defines the system-wide retention, dependency-aware erasure, replication and recovery lifecycle. `105/106` define authorization and human governance.