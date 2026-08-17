# 106 — Memory Knowledge Human Oversight, Intervention, Accountability and Governance Architecture

## Status

**NORMATIVE ARCHITECTURE — CRITICAL / V1**

## Purpose

Define how Novi incorporates meaningful human oversight into memory, reasoning, authorization, learning, action, correction and incident governance.

This document resolves the P0 human-oversight gap identified by document 96 and completes the first 95–106 governance foundation. It builds directly on document 105's machine-verifiable policy layer: machine enforcement and human oversight are complementary controls, not substitutes for one another.

## 1. Core Principle

> **Human oversight must be meaningful, risk-proportionate, informed, timely, authorized, auditable and capable of changing the system's behavior.**

A human-in-the-loop label is insufficient if the human cannot understand the decision, intervene in time, reject it, or cause an effective system response.

## 2. Human Oversight Is Not a Single Mode

Novi should support:

```text
HUMAN-IN-THE-LOOP
HUMAN-ON-THE-LOOP
HUMAN-OUT-OF-THE-LOOP WITH OVERSIGHT
HUMAN-IN-COMMAND
```

The appropriate mode depends on risk, reversibility, latency and operational context.

## 3. Risk-Proportionate Oversight

```text
LOW RISK / REVERSIBLE
→ automated operation + monitoring

MEDIUM RISK
→ monitoring + intervention capability

HIGH RISK
→ pre-action approval or constrained autonomy

CRITICAL / IRREVERSIBLE
→ explicit authorized human decision where feasible
```

A single global approval rule is inappropriate.

## 4. Human Authority

Human authority must be explicit.

```text
PERSON
 ↓
AUTHENTICATED PRINCIPAL
 ↓
ROLE / AUTHORITY
 ↓
POLICY
 ↓
OVERSIGHT ACTION
```

Being present at a console does not automatically confer authorization.

## 5. Human Oversight vs Human Preference

A user preference is not necessarily a governance authorization.

```text
PREFERENCE
 ≠
AUTHORITY
```

105 remains authoritative for machine-enforced permission.

## 6. Oversight Objective

Human oversight should reduce unacceptable risk while preserving useful autonomy.

It should not become a decorative confirmation step that humans approve without meaningful information.

## 7. Oversight Decision Packet

For consequential decisions, the human should receive a concise decision packet containing, where appropriate:

- proposed action;
- target entity;
- relevant state;
- key evidence;
- uncertainty;
- expected outcome;
- material risks;
- applicable policy;
- competence status;
- model version;
- reversibility;
- deadline for intervention.

## 8. Evidence Traceability

The packet should link to underlying evidence without forcing the human to inspect every low-level artifact before every decision.

```text
SUMMARY
 ↓
KEY EVIDENCE
 ↓
FULL TRACE
```

This integrates documents 92 and 105.

## 9. Human-Readable Explanations

Explanations should distinguish:

```text
OBSERVED
INFERRED
PREDICTED
RECOMMENDED
AUTHORIZED
EXECUTED
```

A model prediction must never be presented as an observed fact.

## 10. Explanation Is Not Justification

An explanation can describe why the system reached a conclusion without proving that the conclusion was correct.

Human reviewers must have access to evidence and policy context, not merely a persuasive narrative.

## 11. Oversight Timing

Oversight may occur:

```text
BEFORE ACTION
DURING ACTION
AFTER ACTION
PERIODICALLY
ON EXCEPTION
ON DRIFT
ON INCIDENT
```

## 12. Pre-Action Approval

Required where consequences are high and intervention after execution would be too late.

```text
PROPOSAL
 ↓
HUMAN REVIEW
 ↓
APPROVE / MODIFY / DENY
 ↓
EXECUTE
```

## 13. Mid-Action Intervention

Long-running actions require a stop or modification channel.

```text
RUNNING
 ↓
HUMAN STOP
 ↓
SAFE TERMINATION
```

The stop path must be independent enough to remain usable if the main reasoning process fails.

## 14. Post-Action Review

For lower-latency actions where pre-approval is impractical:

```text
ACTION
 ↓
OUTCOME
 ↓
AUDIT
 ↓
LEARNING / CORRECTION
```

Post-action review cannot justify irreversible harm that should have required prior approval.

## 15. Human Intervention Semantics

A human action should be represented as an explicit event:

```text
HUMAN OVERRIDE
HUMAN APPROVAL
HUMAN DENIAL
HUMAN MODIFICATION
HUMAN ABORT
HUMAN CORRECTION
HUMAN ESCALATION
```

## 16. Override Is Not Omnipotence

A human override must itself be subject to authentication, authority and policy.

```text
HUMAN OVERRIDE
 ≠
BYPASS ALL CONTROLS
```

Some safety or legal constraints may be non-overridable by a particular role.

## 17. Emergency Stop

Novi should support an emergency stop for actions where continuing creates unacceptable risk.

The stop mechanism should minimize dependency on the model being asked to stop itself.

## 18. Fail-Safe vs Fail-Operational

The appropriate failure mode depends on the system and consequence.

```text
FAIL-SAFE
→ transition toward a safer state

FAIL-OPERATIONAL
→ continue limited operation when stopping itself creates greater risk
```

The chosen mode must be explicitly engineered and documented.

## 19. Loss of Human Connectivity

If an operation requires human availability and the human channel fails:

```text
CONNECTION LOST
 ↓
POLICY-SPECIFIC RESPONSE
```

Possible outcomes include pause, safe stop, restricted continuation or escalation.

## 20. Human Availability

Oversight design must account for:

- response latency;
- working hours;
- workload;
- fatigue;
- communication failure;
- multiple simultaneous approvals.

An oversight requirement that cannot be fulfilled operationally is not an effective control.

## 21. Automation Bias

Humans may over-trust automated recommendations.

Novi should therefore avoid presenting uncertain model outputs with unwarranted certainty and should expose material uncertainty and conflicting evidence.

## 22. Confirmation Fatigue

Excessive approval prompts can cause humans to approve mechanically.

Oversight frequency should therefore be risk-sensitive rather than maximized indiscriminately.

## 23. Adversarial or Manipulative Explanations

The explanation layer must not become an attack surface through which a model persuades a human to approve unsafe behavior.

Evidence and policy state must remain independently inspectable.

## 24. Human Factors

Oversight interfaces should consider:

- cognitive load;
- ambiguity;
- time pressure;
- accessibility;
- error recovery;
- clear affordances;
- confirmation of consequential operations.

## 25. Two-Person Controls

For especially sensitive operations, policy may require two independent authorized humans:

```text
REVIEWER A
     +
REVIEWER B
     ↓
AUTHORIZED ACTION
```

Independence requirements should be explicit.

## 26. Separation of Duties

The person proposing an action need not be the person authorized to approve it.

This reduces concentration of control for high-impact operations.

## 27. Human Correction of Memory

A human correction should become an explicit evidence-bearing event:

```text
OLD CLAIM
 ↓
HUMAN CORRECTION
 ↓
NEW CLAIM
```

The original claim remains traceable where retention permits.

## 28. Correction Is Not Automatically Truth

Human input is evidence, not universal ground truth.

The authority of a correction depends on identity, role, context and policy.

## 29. Identity Verification for Corrections

Sensitive memory correction should verify the authority of the correcting principal before changing protected identity or private data.

This integrates document 97.

## 30. Temporal Correction

Corrections must preserve temporal semantics.

A correction made today about an event yesterday should not silently change the historical time of the correction itself.

This integrates document 98.

## 31. Spatial Correction

Human corrections to location should preserve source and precision.

A reviewer changing an exact coordinate to a neighborhood should not be represented as merely correcting a numerical field; it changes information precision.

This integrates document 99.

## 32. Causal Correction

A human can dispute a causal model:

```text
CAUSAL CLAIM
 ↓
HUMAN REVIEW
 ↓
QUESTIONED / DEMOTED / REVISED
```

The reviewer should be able to inspect the causal evidence and assumptions.

This integrates document 100.

## 33. Cross-Modal Review

Where evidence is multimodal, reviewers should be able to see which modalities support the conclusion and whether multiple outputs derive from the same source.

This integrates document 101.

## 34. Competence Review

A human reviewer may restrict or revoke competence when evidence shows:

- regression;
- unsafe behavior;
- environmental drift;
- inadequate generalization;
- repeated intervention;
- hardware change.

This integrates document 102.

## 35. Model/Memory Review

A reviewer may approve, reject, quarantine or roll back a model/memory update.

This integrates document 104.

## 36. Policy Review

Human governance must be able to inspect policy versions and approve changes under 105's policy lifecycle.

## 37. Oversight State Machine

```text
NORMAL
 ↓
MONITORED
 ↓
REVIEW_REQUIRED
 ↓
HUMAN_DECISION
 ├─ APPROVE
 ├─ MODIFY
 ├─ DENY
 ├─ ABORT
 └─ ESCALATE
       ↓
RESOLVED
```

## 38. Escalation

Escalation should occur when:

- uncertainty exceeds threshold;
- policies conflict;
- identity is ambiguous;
- causal model is out of regime;
- competence is degraded;
- action is irreversible;
- evidence is insufficient;
- system integrity is uncertain.

## 39. Escalation Levels

```text
LEVEL 0 → automated handling
LEVEL 1 → operator
LEVEL 2 → specialist
LEVEL 3 → governance authority
LEVEL 4 → emergency / incident command
```

Actual levels are deployment-specific.

## 40. Escalation Context

Every escalation should carry enough context for the next reviewer to act without reconstructing the entire system state manually.

## 41. Accountability

Every consequential human or automated decision should be attributable to:

```text
ACTOR
MODEL
POLICY
EVIDENCE
TIME
CONTEXT
ACTION
OUTCOME
```

## 42. Accountability Does Not Mean Blame

The architecture records causal and governance responsibility for traceability and improvement; it does not infer legal or moral liability automatically.

## 43. Audit Trail

Oversight events should be append-only or otherwise tamper-evident where appropriate:

```text
PROPOSAL
 ↓
REVIEW
 ↓
DECISION
 ↓
EXECUTION
 ↓
OUTCOME
```

## 44. Audit Integrity

Audit records should include sufficient integrity metadata to detect unauthorized modification.

High-value audit systems should have independent protection from the component being audited.

## 45. Audit Privacy

Auditability must not become unrestricted surveillance.

Audit records should apply retention, access control and minimization requirements.

## 46. Evidence Retention

Retain enough evidence to support accountability and correction, subject to privacy, legal and operational requirements.

Do not retain everything merely because it might someday be useful.

## 47. Reproducibility

For important decisions, the system should preserve sufficient state to reconstruct the decision path:

```text
MEMORY SNAPSHOT
MODEL VERSION
POLICY VERSION
EVIDENCE
IDENTITY STATE
TEMPORAL STATE
SPATIAL STATE
CAUSAL MODEL
```

Exact reconstruction may not always be possible; limitations must be recorded.

## 48. Human Review Quality

Review systems should be evaluated for:

- false approvals;
- false denials;
- intervention latency;
- missed escalations;
- unnecessary escalations;
- correction quality;
- reviewer disagreement;
- downstream harm.

## 49. Reviewer Calibration

Human reviewers should receive appropriate training and feedback for high-consequence domains.

Agreement is not automatically correctness; disagreements should sometimes trigger evidence review rather than majority voting.

## 50. Reviewer Independence

Where independence matters, the system should detect conflicts of interest or shared incentives where the deployment can define them.

## 51. Human-in-the-Loop Failure Modes

Test:

- reviewer unavailable;
- reviewer delayed;
- reviewer confused;
- reviewer wrong;
- reviewer compromised;
- approval channel unavailable;
- duplicate approvals;
- conflicting reviewers;
- stale review packet;
- action changes after approval.

## 52. Stale Approval

An approval must have a defined validity window and scope.

```text
APPROVAL AT T1
 ≠
UNLIMITED AUTHORIZATION AT T2
```

## 53. State Change After Approval

If material state changes after approval:

```text
APPROVED
 ↓
STATE CHANGE
 ↓
RECHECK
```

The policy determines whether reapproval is required.

## 54. Approval Binding

An approval should specify:

- target;
- action;
- scope;
- constraints;
- time window;
- policy version;
- principal;
- relevant state assumptions.

## 55. Human Override Provenance

Overrides must be traceable to:

```text
WHO
WHAT
WHY / REASON CODE
WHEN
UNDER WHICH AUTHORITY
UNDER WHICH POLICY
```

Free-text explanations can supplement structured reason codes but should not replace them for high-impact events.

## 56. Human Governance of Learning

Humans should be able to restrict memory promotion, model updates, causal-model promotion and skill promotion.

```text
OBSERVATION
 ↓
CANDIDATE KNOWLEDGE
 ↓
VALIDATION
 ↓
PROMOTION
```

Governance can block promotion when evidence is insufficient.

## 57. Human Governance of Self-Improvement

Self-improvement recommendations must remain distinguishable from approved changes.

```text
SYSTEM PROPOSAL
 ↓
HUMAN / POLICY REVIEW
 ↓
APPROVED CHANGE
```

## 58. Autonomous Operation Boundaries

Every autonomous deployment should define:

- allowed actions;
- forbidden actions;
- maximum consequence;
- required evidence;
- escalation conditions;
- human override path;
- emergency stop;
- rollback strategy.

## 59. Capability Revocation

A human authority should be able to revoke a capability without requiring the model to agree.

```text
CAPABILITY ACTIVE
 ↓
REVOCATION
 ↓
CAPABILITY DISABLED
```

## 60. Revocation Propagation

In distributed systems, revocation must propagate to relevant agents, sessions, caches and action gateways within a defined bound appropriate to the risk.

## 61. Human Oversight Across Agents

For agent-to-agent systems, the architecture must identify:

```text
ORIGINATING AGENT
INTERMEDIATE AGENT
FINAL ACTOR
HUMAN AUTHORITY
```

Delegation must not erase accountability.

## 62. Delegated Authority

A delegated agent may only exercise the scope granted to it.

```text
HUMAN AUTHORITY
 ↓
AGENT A
 ↓
AGENT B
```

Agent B does not automatically receive more authority than A was granted.

## 63. Delegation Expiry

Delegated authority should have explicit scope and expiry where appropriate.

## 64. Human Review of Agent Messages

Agent-to-agent assertions should not bypass governance merely because another agent produced them.

Messages remain evidence and instructions subject to trust and policy checks.

## 65. Incident Response

Human oversight integrates with incident management:

```text
DETECT
 ↓
CONTAIN
 ↓
ESCALATE
 ↓
INVESTIGATE
 ↓
RECOVER
 ↓
LEARN
```

## 66. Incident Trigger Examples

- repeated safety failures;
- policy bypass;
- identity leakage;
- memory poisoning;
- model regression;
- unauthorized action;
- audit-integrity failure;
- unexplained behavior drift.

## 67. Incident Containment

Containment may include:

```text
PAUSE
REVOKE CAPABILITY
QUARANTINE MODEL
QUARANTINE MEMORY
DISABLE TOOL
ROLL BACK
REQUIRE HUMAN APPROVAL
```

## 68. Post-Incident Review

Post-incident analysis should identify:

- triggering conditions;
- evidence;
- model state;
- memory state;
- policy state;
- human actions;
- automated actions;
- missed controls;
- corrective actions.

## 69. No Blame-by-Default

Incident analysis should separate system failure, human error, policy deficiency, interface failure, data quality and malicious behavior rather than assuming one cause.

## 70. Governance Metrics

Track at least where appropriate:

- intervention rate;
- escalation rate;
- approval rate;
- denial rate;
- false approval rate;
- false denial rate;
- intervention latency;
- unsafe continuation rate;
- policy conflict rate;
- reviewer disagreement;
- rollback rate;
- post-action correction rate.

## 71. Oversight Effectiveness

A low intervention rate is not automatically good.

It could indicate:

```text
LOW RISK
```

or:

```text
OVERSIGHT FAILURE
```

Metrics must be interpreted with outcome and incident data.

## 72. Human Oversight Evaluation

Evaluation should include realistic scenarios with:

- ambiguous evidence;
- conflicting modalities;
- changing state;
- adversarial inputs;
- policy conflicts;
- reviewer fatigue;
- unavailable reviewers;
- false confidence;
- emergency events.

## 73. Simulation

Human oversight procedures can be stress-tested in simulation before deployment.

Simulated approval success must not be treated as evidence of real-world operational readiness without deployment-specific validation.

## 74. Accessibility

Oversight interfaces should be usable by authorized reviewers with relevant accessibility needs.

Accessibility is part of governance effectiveness, not merely UI polish.

## 75. Language and Localization

Critical governance messages should preserve semantic meaning across supported languages.

Ambiguous translations must not alter authorization or safety semantics.

## 76. Human Data Minimization

Reviewers should receive the minimum sensitive information needed for the decision.

```text
FULL MEMORY
   ↓
TASK-RELEVANT SUBSET
   ↓
REVIEWER
```

## 77. Reviewer Privacy

Reviewer identity, decisions and workload information are themselves sensitive operational data and require access controls.

## 78. Governance Configuration Versioning

Changes to oversight thresholds, escalation rules or reviewer roles must be versioned under document 105.

## 79. Governance Drift

Oversight effectiveness can degrade when:

- workflows change;
- models change;
- policies change;
- reviewer populations change;
- action speed changes;
- environments change.

Periodic revalidation is required.

## 80. Human Oversight and Model/Memory Co-Evolution

A model update can change the information presented to reviewers.

Therefore oversight UI and decision packets must be regression-tested after model and memory changes.

This integrates document 104.

## 81. Human Oversight and Schema Migration

Migration must not silently remove fields required for accountability.

This integrates document 103.

## 82. Human Oversight and Causal Models

When a causal model drives a consequential recommendation, the reviewer should be able to distinguish:

```text
OBSERVATION
CAUSAL ASSUMPTION
MODEL PREDICTION
UNCERTAINTY
```

This integrates document 100.

## 83. Human Oversight and Skill Verification

A reviewer approving autonomous execution should be able to see whether the relevant competence claim is current and in-regime.

This integrates document 102.

## 84. Human Oversight and Cross-Modal Evidence

Reviewers should be able to inspect evidence provenance and modality dependence where it materially affects the decision.

This integrates document 101.

## 85. Human Oversight and Temporal/Spatial State

Review packets must identify when and where relevant state was observed and whether it remains current.

This integrates documents 98 and 99.

## 86. Human Oversight and Identity

Reviewers must be able to distinguish confirmed identity from inferred or provisional identity.

This integrates document 97.

## 87. Human Oversight and Memory Erasure

A human governance action must respect privacy deletion and retention rules.

A reviewer must not be able to restore erased private memory merely by issuing a normal correction.

## 88. Non-Repudiation

Where required by risk and deployment, consequential human decisions should have strong authentication and integrity properties sufficient to establish that the decision came from the claimed principal.

## 89. Governance Recovery

After infrastructure failure, governance controls should recover before autonomous high-impact actions resume.

```text
SYSTEM RECOVERY
 ↓
POLICY RECOVERY
 ↓
AUTHORITY RECOVERY
 ↓
AUDIT RECOVERY
 ↓
AUTONOMY RESTORED
```

## 90. Default-Deny for Unknown Critical Governance State

Where critical governance state cannot be established, high-impact autonomous actions should default to the deployment's safe restricted state.

## 91. Governance Invariants

1. Human oversight must be meaningful, not ceremonial.
2. Human authority must be authenticated and scoped.
3. Human preference is not equivalent to authorization.
4. Oversight must be proportionate to risk and consequence.
5. Humans must receive sufficient information to make informed decisions.
6. Explanations do not replace evidence.
7. Human override does not automatically bypass all controls.
8. Emergency stop must not depend solely on the model cooperating.
9. Approvals have scope and validity.
10. Material state changes can invalidate prior approval.
11. Human corrections are evidence-bearing events.
12. Human input is not automatically ground truth.
13. Reviewer disagreement should remain visible where material.
14. Oversight actions must be attributable.
15. Audit records require integrity protection.
16. Auditability must respect privacy.
17. Delegation cannot silently increase authority.
18. Revocation must propagate to relevant enforcement points.
19. Self-improvement recommendations are not approved changes.
20. Capability can be revoked independently of model consent.
21. Incident response must include containment and recovery.
22. Oversight effectiveness must be measured by outcomes, not approval counts alone.
23. Current authentication and authorization override historical memory.
24. Governance state must recover before high-impact autonomy resumes.
25. Unknown critical governance state must not silently authorize consequential action.
26. Governance configuration changes must be versioned.
27. Human oversight must remain effective under model, memory and environment evolution.
28. Human governance cannot compensate for missing machine-enforceable controls.
29. Machine enforcement cannot eliminate the need for human governance in high-impact or ambiguous cases.
30. Accountability requires traceability across actor, model, policy, evidence, action and outcome.

## 92. Integration With Document 95

106 completes the reference pipeline:

```text
OBSERVATION
 ↓
IDENTITY
 ↓
TIME / SPACE
 ↓
EVIDENCE
 ↓
CAUSAL / SEMANTIC / SKILL REASONING
 ↓
MODEL + MEMORY STATE
 ↓
POLICY ENGINE
 ↓
HUMAN OVERSIGHT WHEN REQUIRED
 ↓
ACTION
 ↓
OUTCOME
 ↓
AUDIT / EVALUATION / CORRECTION
```

## 93. Integration With Document 105

105 provides machine-verifiable governance.

106 provides human oversight and accountability around that machine governance.

```text
105 MACHINE ENFORCEMENT
        +
106 HUMAN GOVERNANCE
        ↓
DEFENSE IN DEPTH
```

Neither layer should be treated as a replacement for the other.

## 94. Integration With Document 96

106 resolves the final P0 gap:

**Human Oversight / Escalation.**

The P0 sequence identified by 96 is therefore complete:

```text
97 Identity
98 Temporal
99 Spatial
100 Causal
101 Cross-Modal
102 Skill
103 Schema Evolution
104 Model/Memory Co-Evolution
105 Machine Governance
106 Human Oversight
```

## 95. Architecture Completion Checkpoint

Documents 95–106 now form a coherent governance and knowledge architecture spanning:

```text
MEANING
IDENTITY
TIME
SPACE
CAUSALITY
MODALITY
COMPETENCE
EVOLUTION
POLICY
HUMAN ACCOUNTABILITY
```

The completion of the P0 sequence does not imply that Novi is complete. It establishes a stable architectural foundation from which P1 distributed reliability, synchronization, recovery, privacy auditing and resource governance can be specified.

## 96. Final Principle

> **Novi should automate as much as safely possible while preserving meaningful human authority where consequences, uncertainty, ambiguity or governance requirements demand it. Human oversight must be capable of understanding, intervening, correcting, stopping and holding the system accountable—and every such intervention must itself remain governed, traceable and privacy-aware.**

Human oversight is therefore not an admission that the architecture failed. It is a deliberate safety and governance layer for a system operating under uncertainty and changing conditions.