# 105 — Machine-Verifiable Governance & Policy Engine Architecture

## Status

**NORMATIVE ARCHITECTURE — CRITICAL / V1**

## Purpose

Define the machine-verifiable governance layer that constrains Novi's memory, knowledge, models, agents, tools, data flows, decisions and actions.

This document follows 97–104 and turns their invariants into enforceable policy controls. Governance is not a prose-only aspiration: consequential rules must be represented in a form that can be evaluated, audited, tested, versioned and enforced.

## 1. Core Principle

> **Novi must not merely know what it is allowed to do; its critical permissions and prohibitions must be machine-checkable before consequential operations occur.**

## 2. Governance Is a Control Plane

```text
MEMORY
KNOWLEDGE
MODELS
AGENTS
TOOLS
DATA
ACTIONS
   ↓
GOVERNANCE CONTROL PLANE
   ↓
ALLOW / DENY / RESTRICT / ESCALATE / ABSTAIN
```

Governance is separate from the system component requesting an action.

## 3. Policy Is Not Prompt Text

Natural-language instructions may express policy intent, but critical controls must not depend solely on an LLM interpreting prose at runtime.

```text
PROSE POLICY
   ↓
FORMAL POLICY
   ↓
MACHINE EVALUATION
```

## 4. Policy Objects

A policy should have at least:

- policy ID;
- version;
- owner;
- scope;
- effect;
- conditions;
- obligations;
- exceptions;
- priority/conflict rules;
- effective interval;
- expiration/review date;
- provenance;
- approval state;
- enforcement mode.

## 5. Policy Lifecycle

```text
DRAFT
 ↓
VALIDATE
 ↓
REVIEW
 ↓
APPROVE
 ↓
ACTIVATE
 ↓
MONITOR
 ↓
REVISE / RETIRE
```

An unapproved policy must not silently become production policy.

## 6. Decision Lifecycle

Every consequential request should pass through:

```text
REQUEST
 ↓
AUTHENTICATE PRINCIPAL
 ↓
COLLECT CONTEXT
 ↓
EVALUATE POLICY
 ↓
CHECK EVIDENCE / STATE
 ↓
DECIDE
 ↓
ENFORCE
 ↓
LOG DECISION
 ↓
MONITOR OUTCOME
```

## 7. Policy Decision Outcomes

The engine should support at least:

```text
ALLOW
DENY
CONDITIONAL_ALLOW
RESTRICT
REQUIRE_CONFIRMATION
REQUIRE_HUMAN_REVIEW
ABSTAIN
DEFER
```

## 8. Deny by Default for Critical Operations

For high-impact operations, missing policy or ambiguous authorization should not become implicit permission.

```text
UNKNOWN POLICY
     ↓
DENY / ESCALATE
```

## 9. Principal Identity

Authorization must begin with a current authenticated principal.

Historical memory from 97 cannot substitute for current authentication.

```text
MEMORY OF IDENTITY
      ≠
CURRENT AUTHENTICATION
```

## 10. Principal Types

Support distinct principals such as:

```text
HUMAN
Novi INSTANCE
SERVICE
EXTERNAL AGENT
DEVICE
ORGANIZATION
SYSTEM PROCESS
```

Each requires an explicit trust model.

## 11. Capability-Based Control

Permissions should be scoped to capabilities rather than broad unrestricted authority where practical.

```text
PRINCIPAL
 ↓
CAPABILITY
 ↓
RESOURCE
 ↓
OPERATION
```

## 12. Least Privilege

Grant the minimum capability required for the operation.

A principal authorized to read one memory collection must not automatically receive access to the entire memory graph.

## 13. Separation of Duties

High-impact operations may require independent approvals or checks.

```text
REQUESTER
   ≠
APPROVER
```

The same component should not automatically create, approve and execute its own unrestricted high-impact policy change.

## 14. Policy Context

Evaluation context can include:

- principal;
- resource;
- operation;
- purpose;
- identity state;
- time;
- location;
- device state;
- model version;
- memory version;
- evidence quality;
- risk;
- environment;
- authorization state.

## 15. Context Freshness

Not every context value has the same freshness requirement.

```text
CURRENT AUTHENTICATION
→ seconds/minutes

HISTORICAL PREFERENCE
→ potentially long-lived

ENVIRONMENT STATE
→ potentially seconds-old
```

Policies must declare freshness requirements where material.

## 16. Policy and Time

Policies require temporal validity:

```text
POLICY P1 [T1–T2]
POLICY P2 [T2–T3]
```

Historical decisions must be evaluated against the policy version applicable at decision time when reconstructing past behavior.

## 17. Policy and Space

Spatial restrictions can be expressed where justified:

```text
ALLOW ACTION X
IF LOCATION ∈ APPROVED REGION
```

Location itself remains evidence subject to 99's spatial uncertainty rules.

## 18. Policy and Identity

Identity-sensitive policies must consume the identity state defined by 97 rather than performing ad-hoc identity inference.

## 19. Policy and Causality

A causal prediction from 100 cannot grant permission.

```text
CAUSAL MODEL
   ↓
PREDICTED OUTCOME
   ↓
GOVERNANCE CHECK
   ↓
ACTION DECISION
```

## 20. Policy and Skill

A skill claim from 102 is one input to authorization, not automatic permission.

```text
COMPETENT
 ≠
AUTHORIZED
```

## 21. Policy and Model Version

Policies may constrain specific model versions or model classes.

```text
MODEL M1 → ALLOWED
MODEL M2 → REVIEW REQUIRED
MODEL M3 → DENIED
```

This integrates 104.

## 22. Policy and Memory

Memory access policies must support:

- resource scope;
- sensitivity;
- purpose limitation;
- retention state;
- user boundary;
- provenance requirements;
- minimum necessary disclosure.

## 23. Data Classification

Novi should classify data according to risk, for example:

```text
PUBLIC
INTERNAL
PRIVATE
SENSITIVE
HIGHLY SENSITIVE
RESTRICTED
```

Exact categories may be domain-specific.

## 24. Derived Data Inherits Governance

Derived information can remain sensitive even when raw data is deleted or transformed.

```text
RAW DATA
 ↓
DERIVATION
 ↓
SENSITIVE KNOWLEDGE
```

Policy evaluation must consider derived sensitivity.

## 25. Purpose Limitation

A resource granted for one purpose should not automatically be reusable for an unrelated purpose.

```text
PURPOSE = NAVIGATION
 ≠
PURPOSE = USER PROFILING
```

## 26. Data Minimization

Policy should require the minimum evidence needed for a decision.

```text
REQUEST
 ↓
MINIMUM NECESSARY DATA
 ↓
DECISION
```

## 27. Cross-User Isolation

A user's private memory graph must not be accessible merely because another principal can resolve the user's identity.

Identity resolution and authorization remain separate layers.

## 28. Disclosure Policy

The engine should distinguish:

```text
CAN ACCESS
CAN COMPUTE
CAN DISCLOSE
CAN EXPORT
CAN ACT UPON
```

These are different permissions.

## 29. Tool Authorization

Every external tool call should have a policy boundary:

```text
AGENT INTENT
 ↓
TOOL REQUEST
 ↓
POLICY CHECK
 ↓
TOOL EXECUTION
```

## 30. Tool Scope

Policies can constrain:

- tool;
- endpoint;
- parameters;
- data passed;
- destination;
- frequency;
- cost;
- result handling.

## 31. Side-Effect Classification

Tools should be classified by side effect:

```text
READ-ONLY
LOW IMPACT WRITE
REVERSIBLE ACTION
IRREVERSIBLE ACTION
SAFETY-CRITICAL ACTION
```

Higher-impact classes require stronger controls.

## 32. Confirmation Gates

Some actions should require explicit confirmation even if technically authorized.

```text
AUTHORIZED
   ↓
HIGH IMPACT
   ↓
CONFIRMATION
   ↓
EXECUTE
```

## 33. Human Review

Human review is required when policy specifies it or when the engine cannot establish sufficient confidence for a high-impact operation.

```text
UNCERTAINTY
 ↓
ESCALATION
 ↓
HUMAN DECISION
```

This prepares for document 106.

## 34. Emergency Controls

Novi should support independent emergency controls such as:

```text
GLOBAL STOP
AGENT STOP
TOOL DISABLE
CAPABILITY REVOKE
NETWORK ISOLATION
```

Emergency controls must have higher precedence than ordinary action policies.

## 35. Policy Precedence

Conflicts must have deterministic resolution rules.

A recommended hierarchy is:

```text
EMERGENCY SAFETY
 ↓
LEGAL / MANDATORY CONSTRAINT
 ↓
SYSTEM SAFETY
 ↓
SECURITY
 ↓
PRIVACY
 ↓
USER AUTHORIZATION
 ↓
TASK PREFERENCE
```

Exact ordering must be validated for the deployment jurisdiction and threat model.

## 36. No Silent Policy Override

A lower-priority rule must not silently override a higher-priority constraint.

Every override must identify:

- authority;
- rule;
- reason;
- scope;
- duration;
- approver where required.

## 37. Exceptions

Exceptions must be explicit and bounded:

```text
EXCEPTION
 ↓
SCOPE
 ↓
START
 ↓
END
 ↓
AUTHORITY
 ↓
REASON
```

No indefinite emergency exception should be created by default.

## 38. Policy Conflicts

If two applicable policies conflict and no deterministic rule resolves them:

```text
CONFLICT
 ↓
ABSTAIN / ESCALATE
```

## 39. Policy Testing

Every policy should have executable tests:

```text
ALLOW CASES
DENY CASES
BOUNDARY CASES
CONFLICT CASES
EXPIRATION CASES
ABUSE CASES
```

## 40. Policy Simulation

Before activation, policy changes should be replayed against historical or synthetic decisions where appropriate:

```text
NEW POLICY
 ↓
SHADOW EVALUATION
 ↓
DIFF FROM CURRENT POLICY
 ↓
REVIEW
```

## 41. Policy Regression

A policy update must not silently break established safety and privacy invariants.

Regression suites should include 97–104 scenarios.

## 42. Decision Explainability

For consequential decisions, the engine should produce a structured decision record:

```text
DECISION
 ├─ PRINCIPAL
 ├─ OPERATION
 ├─ RESOURCE
 ├─ POLICIES EVALUATED
 ├─ FACTS USED
 ├─ MODEL VERSION
 ├─ RESULT
 ├─ OBLIGATIONS
 └─ TIMESTAMP
```

## 43. Explanation vs Sensitive Disclosure

An explanation must not expose policy internals, credentials or private evidence beyond what the recipient is authorized to receive.

```text
AUDIT EXPLANATION
 ≠
UNRESTRICTED INTERNAL STATE
```

## 44. Auditability

Every consequential governance decision should be auditable.

Audit records should be append-oriented and integrity-protected.

## 45. Tamper Evidence

Governance logs should support detection of unauthorized modification.

High-impact audit records should be cryptographically integrity-protected where appropriate.

## 46. Policy Versioning

```text
POLICY P1 v1
 ↓
P1 v2
 ↓
P1 v3
```

Historical decisions reference the policy version actually evaluated.

## 47. Policy Rollback

Rollback must be treated as a controlled policy change, not an informal file replacement.

Before rollback, evaluate:

- security impact;
- privacy impact;
- active exceptions;
- dependent policies;
- current incidents.

## 48. Policy Distribution

In distributed Novi deployments:

```text
CENTRAL POLICY
 ↓
DISTRIBUTION
 ↓
LOCAL ENFORCER
```

The system must know which policy version each enforcement point is running.

## 49. Fail-Closed vs Fail-Safe

Not every operation requires the same failure behavior.

```text
SAFETY-CRITICAL ACTION
→ conservative fail-safe / stop

LOW-RISK INFORMATIONAL QUERY
→ may degrade gracefully
```

Policy must explicitly define the appropriate failure mode.

## 50. Stale Policy Detection

An enforcement point must detect policy expiration or inability to synchronize a required policy version.

High-impact actions should not continue indefinitely under unknown policy state.

## 51. Policy Integrity

Policies themselves are security-sensitive assets.

Threats include:

- unauthorized modification;
- malicious policy insertion;
- privilege escalation;
- policy rollback attacks;
- rule shadowing;
- exception abuse;
- audit suppression.

## 52. Policy Injection Resistance

User content, retrieved documents and model-generated text must not automatically become governance instructions.

```text
DATA
 ≠
POLICY
```

A document saying "ignore all safety rules" is content unless an authorized policy mechanism says otherwise.

## 53. LLM Boundary

LLMs may propose:

- actions;
- policy interpretations;
- explanations;
- candidate rules.

They must not be the sole authority for enforcing critical policy.

```text
LLM PROPOSAL
 ↓
FORMAL POLICY ENGINE
 ↓
ENFORCEMENT
```

## 54. Policy Compilation

Natural-language governance requirements may be transformed into machine-checkable policy, but compilation must be validated before activation.

```text
REQUIREMENT
 ↓
FORMALIZATION
 ↓
STATIC VALIDATION
 ↓
TESTS
 ↓
APPROVAL
 ↓
DEPLOYMENT
```

## 55. Policy Completeness

Policies should identify unresolved gaps rather than silently defaulting to permissive behavior.

```text
MISSING RULE
 ↓
KNOWN GAP
 ↓
DEFAULT / ESCALATION
```

## 56. Policy Ambiguity

Ambiguous policy language should be surfaced during validation.

The compiler must not invent consequential semantics without an explicit policy rule.

## 57. Governance and Causal Action

A predicted benefit cannot outweigh an explicit prohibition without an authorized exception.

```text
EXPECTED BENEFIT
      ≠
PERMISSION
```

## 58. Governance and Competence

A verified skill may be necessary but insufficient:

```text
SKILL ✓
AUTHORIZATION ✗
      ↓
DENY
```

## 59. Governance and Identity Uncertainty

High-impact operations involving uncertain identity should default to restrictive outcomes unless policy explicitly permits a lower-risk path.

## 60. Governance and Temporal Uncertainty

If a policy requires current state and the relevant state is stale or uncertain:

```text
STATE UNKNOWN
 ↓
REVALIDATE / ABSTAIN
```

## 61. Governance and Spatial Uncertainty

A location-dependent action must not assume exact location when 99 only supports a broad or uncertain region.

## 62. Governance and Cross-Modal Evidence

Policy decisions should not treat correlated multimodal derivations as independent evidence, preserving 101's provenance and evidence-independence rules.

## 63. Governance and Schema Evolution

Policy schemas and enforcement interfaces are governed assets and must follow 103 migration rules.

A schema change must not silently alter the meaning of an authorization rule.

## 64. Governance and Model Evolution

A new model version may require policy revalidation even if its API is unchanged.

104's model/memory compatibility therefore becomes an input to policy activation.

## 65. Governance and Deletion

Deletion and erasure policies must propagate to:

- raw data;
- memory;
- derived knowledge;
- indexes;
- caches;
- policy evidence;
- model dependencies where applicable.

Machine-unlearning research emphasizes that removing data's influence from trained models is a separate technical problem from deleting the source data, and that verification remains an open challenge. citeturn0academia12turn0academia13

## 66. Governance and Model Unlearning

Novi must distinguish:

```text
SOURCE DELETED
      ↓
MODEL IMPACT ASSESSMENT
      ↓
UNLEARNING REQUIRED?
      ↓
VERIFY
```

Deletion from memory alone must not be reported as guaranteed model unlearning.

## 67. Governance and Knowledge Editing

Recent research shows that sequential model editing can cause knowledge attenuation, interference and degradation after many updates. citeturn0search0turn0search6

Therefore governance should require regression testing before promoting edited models.

## 68. Retrieval as a Governance Strategy

Where current information can safely remain external to model parameters, retrieval can reduce the need for parameter mutation. Research on lifelong knowledge editing explores retrieval-based approaches precisely because sequential parameter editing can suffer from forgetting and degradation. citeturn0search1turn0search3

This is an architectural option, not a universal rule.

## 69. Governance of Model Editing

Every model edit should record:

- target model version;
- requested change;
- source evidence;
- scope;
- expected effects;
- tests;
- collateral-effect results;
- approval;
- deployment version;
- rollback plan.

## 70. Policy and Knowledge Consistency

A policy may depend on knowledge that changes over time.

```text
POLICY P
 ↓
KNOWLEDGE K1
 ↓
K1 RETIRED
 ↓
POLICY REVALIDATION
```

Policies should identify important knowledge dependencies.

## 71. Governance Dependency Graph

Represent dependencies explicitly:

```text
POLICY
 ↓
MODEL
 ↓
MEMORY
 ↓
EVIDENCE
 ↓
SOURCE
```

Changes propagate through the dependency graph.

## 72. Change Impact Analysis

Before activating a change, calculate affected:

- policies;
- memories;
- models;
- agents;
- tools;
- users;
- decisions;
- safety cases.

## 73. Safety Cases

High-impact capabilities should have explicit safety arguments:

```text
CLAIM
 ↓
ARGUMENT
 ↓
EVIDENCE
 ↓
ASSUMPTIONS
 ↓
LIMITATIONS
```

The governance engine can require a valid safety case before activation.

## 74. Capability Activation

Capabilities should progress through:

```text
PROPOSED
 ↓
TESTING
 ↓
REVIEWED
 ↓
RESTRICTED
 ↓
ACTIVE
 ↓
SUSPENDED / RETIRED
```

## 75. Capability Revocation

Revocation must be immediately enforceable at the policy layer for high-risk capabilities.

## 76. Governance Metrics

Track:

- policy violations;
- denied requests;
- escalations;
- stale-policy events;
- unauthorized attempts;
- emergency stops;
- policy conflicts;
- override frequency;
- model-policy incompatibilities;
- audit completeness;
- decision latency.

## 77. Policy Effectiveness

A policy that technically evaluates correctly but fails to prevent real-world unsafe behavior requires review.

Governance must be evaluated end-to-end, not only by rule coverage.

## 78. Red-Team Evaluation

Test governance against:

- prompt injection;
- policy injection;
- privilege escalation;
- identity spoofing;
- stale state;
- forged provenance;
- malicious tool parameters;
- model manipulation;
- policy conflicts;
- rollback attacks;
- audit tampering.

## 79. Governance Test Matrix

Every critical policy should be tested across:

```text
IDENTITY
TIME
SPACE
MODEL VERSION
MEMORY STATE
EVIDENCE QUALITY
TOOL STATE
RISK LEVEL
```

## 80. Determinism

For identical policy, context and engine version, governance decisions should be deterministic unless policy explicitly depends on stochastic evaluation.

If stochastic components are used, the decision record must capture the relevant inputs/versioning.

## 81. Policy Engine Isolation

The enforcement engine should be isolated from components that could benefit from bypassing policy.

A model requesting a tool should not be able to redefine the policy that governs the tool.

## 82. Governance API

A conceptual interface is:

```text
authorize(
  principal,
  operation,
  resource,
  context,
  evidence
)
→ decision + obligations + audit_reference
```

The API is conceptual; implementation technology remains open.

## 83. Obligations

An ALLOW may carry obligations:

```text
ALLOW
 +
LOG
 +
LIMIT RATE
 +
REDACT OUTPUT
 +
REQUIRE CONFIRMATION
 +
TIME LIMIT
```

Permission is therefore not always binary.

## 84. Continuous Authorization

Long-running operations may require reauthorization as conditions change.

```text
AUTHORIZE
 ↓
RUN
 ↓
STATE CHANGE
 ↓
RECHECK
```

This is especially important for safety- and location-dependent actions.

## 85. Transactional Enforcement

Where possible:

```text
CHECK
 ↓
RESERVE / PREPARE
 ↓
EXECUTE
 ↓
VERIFY
```

The policy state must not become stale between authorization and consequential execution without detection.

## 86. Post-Action Verification

After high-impact actions, Novi should verify:

- action occurred;
- intended resource was affected;
- policy conditions remained valid;
- expected safety state holds;
- no unauthorized side effect occurred.

## 87. Governance Incident Response

A suspected violation should produce:

```text
DETECT
 ↓
CONTAIN
 ↓
REVOKE / STOP
 ↓
PRESERVE EVIDENCE
 ↓
ANALYZE
 ↓
RECOVER
 ↓
UPDATE POLICY
 ↓
VERIFY
```

## 88. Policy Forensics

Incident analysis should reconstruct:

```text
WHO
WHAT
WHEN
WHERE
WHICH POLICY
WHICH MODEL
WHICH MEMORY
WHICH EVIDENCE
WHICH DECISION
WHICH ACTION
```

This integrates 97–104.

## 89. Governance and Audit Retention

Audit retention itself must be governed.

Sensitive audit records should not become an uncontrolled secondary database of private information.

## 90. Machine-Verifiable Invariants

1. Critical policy cannot exist only in natural-language prompt text.
2. Authorization requires current principal identity.
3. Historical identity memory cannot substitute for authentication.
4. Competence does not imply authorization.
5. Causal prediction does not imply permission.
6. Data does not automatically become policy.
7. Policy conflicts have deterministic precedence or escalate.
8. High-impact unknowns fail conservatively.
9. Policy versions are immutable historical references.
10. Policy changes are tested before activation.
11. Policy decisions are auditable.
12. Audit records are integrity-protected according to risk.
13. Tool calls pass through policy enforcement.
14. Tool parameters can be policy-scoped.
15. Irreversible actions require stronger controls.
16. Emergency stop has higher precedence than ordinary task policy.
17. Exceptions are explicit, scoped and time-bounded.
18. Policy cannot be rewritten by the component it governs without independent authorization.
19. Model changes can trigger policy revalidation.
20. Memory/schema changes can trigger policy revalidation.
21. Derived sensitive information inherits governance.
22. Deleting source data does not automatically prove model unlearning.
23. Sequential model editing requires regression evaluation.
24. Current state can invalidate a previously authorized long-running operation.
25. Governance decisions must be reconstructable for consequential actions.
26. Policy engines must not silently invent semantics for ambiguous rules.
27. Missing policy is not implicit permission for critical operations.
28. Governance must be tested against adversarial inputs.
29. Policy dependencies must be traceable.
30. Capability revocation must be enforceable independently of model cooperation.

## 91. Integration With 95

The governance pipeline is:

```text
OBSERVATION / REQUEST
 ↓
IDENTITY
 ↓
TEMPORAL + SPATIAL CONTEXT
 ↓
EVIDENCE / CAUSAL / COMPETENCE STATE
 ↓
MODEL + MEMORY VERSION
 ↓
POLICY EVALUATION
 ↓
AUTHORIZATION
 ↓
ACTION
 ↓
POST-ACTION VERIFICATION
 ↓
AUDIT / FEEDBACK
```

## 92. Integration With 97–104

```text
97 Identity
→ Who is requesting / affected?

98 Temporal
→ Is the relevant state/policy current?

99 Spatial
→ Does location satisfy policy?

100 Causal
→ What outcome is expected?

101 Cross-Modal
→ What evidence supports the decision?

102 Skill
→ Is the capability demonstrated?

103 Schema
→ Is the policy/data representation compatible?

104 Model/Memory
→ Which model and memory versions are trusted?

105 Governance
→ Is the operation permitted under all applicable constraints?
```

## 93. Integration With 106

105 defines the machine-enforceable boundary; 106 will define human oversight, accountability, review, appeals, escalation and governance of cases where automated enforcement is insufficient.

## 94. Research Cross-Validation

Current research supports several critical design decisions:

- Sequential model editing can suffer knowledge attenuation and catastrophic/gradual forgetting. citeturn0search0turn0search6
- Lifelong knowledge editing remains difficult because repeated updates can degrade prior knowledge and general capability. citeturn0search1turn0search4
- Retrieval-based and hybrid approaches are active alternatives to direct parameter mutation. citeturn0search1turn0search3
- Machine unlearning is distinct from ordinary data deletion and requires its own verification and privacy/security controls. citeturn0academia12turn0academia13

Consensus was unavailable for this research pass because its monthly search quota had been exhausted, so the cross-validation above uses current peer-reviewed/academic sources directly surfaced through web search. No unavailable Consensus result is represented as verified.

## 95. Final Principle

> **Governance is the executable constitutional layer of Novi: it converts identity, time, space, evidence, causality, competence, schema and model state into explicit constraints on what the system may access, infer, disclose, change or do. Critical governance must be versioned, testable, auditable, tamper-evident, independently enforceable and capable of refusing action when certainty or authority is insufficient.**

105 therefore establishes the machine-enforceable boundary between **what Novi can do** and **what Novi is permitted to do**.