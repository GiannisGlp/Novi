# 16 — Human Oversight and Accountability

**Status:** CANONICAL — CONSOLIDATED V1.1

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

## Review state machine

```text
REVIEW_REQUESTED
      ↓
PACKET_PREPARED
      ↓
REVIEWED
 ┌────┼───────────┐
 ↓    ↓           ↓
APPROVED  DENIED  ESCALATED
 ↓                    ↓
EXECUTABLE         FURTHER_REVIEW
 ↓
EXECUTED
 ↓
AUDITED
```

Additional states include `EXPIRED`, `INVALIDATED`, `WITHDRAWN`, `REVIEWER_UNAVAILABLE` and `CONFLICTED_REVIEW`.

## Approval semantics

An approval is scoped to action, target, policy version, state assumptions and time window. Material state changes can invalidate it. Historical approval never overrides current authentication or policy.

## Reviewer qualification

High-impact review must require appropriately authorized reviewers. Policy may require two-person approval, separation of duties, domain expertise or independent review. The reviewer identity and authority are recorded.

## Corrections

Human corrections are explicit evidence-bearing events with actor, authority, time, reason and previous state. They are not automatically truth.

## Emergency intervention

High-risk deployments require an independently usable stop/restrict mechanism. Human override does not automatically bypass non-overridable controls.

## Accountability

Consequential actions link actor, model, memory state, policy, evidence, decision, action and outcome. Audit records are tamper-evident where required and privacy-protected.

## Reviewer risks

The system must account for automation bias, confirmation fatigue, stale review packets, reviewer unavailability, conflicting reviewers and compromised review channels.

## Reapproval triggers

Re-review is required when material changes affect:

```text
identity
target
policy
safety state
evidence
uncertainty
model/memory version
action scope
time window
```

## Safety invariants

1. Human presence is not authority.
2. Approval is scoped and expires.
3. Material state changes can trigger reapproval.
4. Explanations do not replace evidence.
5. Human override remains governed.
6. Auditability does not justify unrestricted surveillance.
7. High-impact review requires appropriate reviewer authority.

## Evaluation

Evaluate review latency, false approvals, false denials, stale-packet approvals, reviewer disagreement, override effectiveness, automation-bias indicators and emergency-stop availability. Test reviewer unavailability and compromised review channels.

## Integration

`15` supplies machine-verifiable policy. `16` supplies human governance around memory and knowledge. System recovery architecture governs recovery after intervention/failure. `18` defines audit and longitudinal evaluation expectations.