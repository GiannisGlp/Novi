# 14 — Privacy and Memory Data Governance

**Status:** CANONICAL — CONSOLIDATED V1.1

## Purpose
Define privacy controls specific to memory and knowledge while delegating infrastructure-wide lifecycle guarantees to the system erasure architecture.

## Core principle

```text
COLLECT MINIMALLY
→ CLASSIFY
→ USE FOR A DEFINED PURPOSE
→ DERIVE CAREFULLY
→ RETAIN NO LONGER THAN NEEDED
→ RESTRICT / DELETE / GENERALIZE
→ VERIFY
```

## Data classes

Memory should distinguish public, operational, personal, sensitive, credential, biometric, location, communication and derived data. Classification determines access, retention, replication and deletion behavior.

## Memory minimization

Store the minimum semantic detail required for future utility. Prefer references, summaries or coarse representations when exact raw content is unnecessary, but never discard provenance needed for accountability without an explicit retention decision.

## Privacy lifecycle

```text
COLLECT
 ↓
CLASSIFY
 ↓
PURPOSE-BIND
 ↓
USE
 ↓
DERIVE
 ↓
SHARE / DISCLOSE
 ↓
RETAIN / REVIEW
 ↓
RESTRICT / DELETE / GENERALIZE
 ↓
VERIFY
```

Each transition is policy-governed and auditable where material.

## Access

Memory access is scoped by principal, purpose, entity, sensitivity and policy. Retrieval must enforce authorization before content reaches the reasoning context.

Technical possession of a record is not permission to expose it.

## Derived data

Embeddings, summaries, graph relationships, causal models and skills may contain information derived from protected sources. They are privacy-relevant dependencies, not automatically anonymous.

Derived artifacts should carry privacy dependency metadata sufficient to determine whether restriction or deletion propagates to them.

## Purpose limitation

A memory admitted for one purpose must not silently become available for unrelated high-impact uses. Purpose expansion requires policy evaluation and, where applicable, renewed authorization/consent.

## User controls

Where applicable, users can inspect, correct, restrict and request deletion of their memory. Corrections preserve provenance; deletion must not be silently undone by recovery or synchronization.

## Privacy-preserving retrieval

Do not retrieve sensitive memory merely because it is semantically similar. Apply purpose, authorization, sensitivity and relevance filters before ranking.

When coarse information satisfies the task, prefer coarse information over exact identity/location/content.

## Audit privacy

Audit logs, provenance graphs, evaluation datasets and review packets can themselves contain sensitive information. They require classification, access control, retention and deletion treatment rather than blanket exemption.

## Safety invariants

1. Privacy policy is enforced before retrieval exposure.
2. Derived representations inherit relevant privacy dependencies.
3. Deletion cannot be defeated by stale replicas or recovery.
4. Exact location/identity data is not exposed when a coarser representation suffices.
5. Human oversight does not imply unrestricted memory access.
6. Audit records themselves receive privacy controls.
7. Purpose expansion requires explicit governance.
8. Privacy restrictions propagate to dependent representations where required.

## Evaluation

Test unauthorized retrieval, cross-user leakage, sensitive inference from derived data, stale-cache exposure, deletion propagation, backup/recovery restoration, purpose misuse and privacy-preserving generalization. Measure leakage rate, deletion verification rate, access-policy correctness and privacy impact of derived representations.

## Boundary with system erasure architecture

`14` defines semantic memory governance and privacy obligations. System architecture defines physical retention, dependency-aware erasure, replication, backup and recovery guarantees.

`15` defines machine governance; `16` defines human oversight.