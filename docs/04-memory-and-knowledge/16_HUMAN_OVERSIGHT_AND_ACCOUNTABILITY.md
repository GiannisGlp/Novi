# 16 — Human Oversight and Accountability

**Status:** CANONICAL — CONSOLIDATED V1

## Purpose
Define how humans review, correct, approve, deny, interrupt and audit memory/knowledge-driven behavior while preserving meaningful authority.

## Core principle

> Human oversight must be informed, risk-proportionate, timely, authorized, auditable and capable of changing system behavior.

## Oversight modes

- human-in-the-loop;
- human-on-the-loop;
- post-action review;
- constrained autonomy;
- explicit human command.

The mode depends on consequence, reversibility, uncertainty and response latency.

## Decision packet

Consequential review should expose proposed action, target, relevant state, key evidence, uncertainty, applicable policy, model/memory versions, reversibility and intervention deadline.

## Approval semantics

An approval is scoped to action, target, policy version, state assumptions and time window. Material state changes can invalidate it. Historical approval never overrides current authentication or policy.

## Corrections

Human corrections are explicit evidence-bearing events with actor, authority, time, reason and previous state. They are not automatically truth.

## Emergency intervention

High-risk deployments require an independently usable stop/restrict mechanism. Human override does not automatically bypass non-overridable controls.

## Accountability

Consequential actions link actor, model, memory state, policy, evidence, decision, action and outcome. Audit records are tamper-evident where required and privacy-protected.

## Reviewer risks

The system must account for automation bias, confirmation fatigue, stale review packets, reviewer unavailability, conflicting reviewers and compromised review channels.

## Two-person controls

Policy may require independent reviewers for high-impact operations. Separation of duties is preferred where a proposer should not also authorize execution.

## Safety invariants

1. Human presence is not authority.
2. Approval is scoped and expires.
3. Material state changes can trigger reapproval.
4. Explanations do not replace evidence.
5. Human override remains governed.
6. Auditability does not justify unrestricted surveillance.

## Integration

`105` supplies machine-verifiable policy. `16` supplies human governance around memory and knowledge. `110` governs recovery after intervention/failure. `112` evaluates oversight effectiveness over time.