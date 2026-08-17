# 114 — Multi-Agent Coordination, Delegation & Shared Memory

**Status:** P2 architecture foundation / future capability  
**Depends on:** 00–113

## 1. Purpose

Define the future boundary for multiple Novi processes, specialist agents or embodied Novi instances coordinating without weakening authorization, provenance, safety or consistency.

This document does not require multi-agent implementation in the first Novi runtime.

## 2. Agent identity

Each agent/process has an identity distinct from:

```text
USER
DEVICE
NODE
MODEL
SERVICE
```

Agent identity does not itself grant authority.

## 3. Delegation

A delegating agent may grant only authority it possesses and only within explicit scope.

```text
PRINCIPAL
 ↓
DELEGATION
 ↓
AGENT
 ↓
CAPABILITY
```

## 4. Delegation record

A delegation should include:

- delegator;
- delegate;
- capability;
- scope;
- purpose;
- constraints;
- time validity;
- resource budget;
- policy version;
- revocation state;
- provenance.

## 5. No authority amplification

```text
A grants B scope X
B cannot grant C scope X+Y
```

Delegation must not amplify privilege.

## 6. Task decomposition

A complex task may be decomposed:

```text
Goal
 ↓
Task graph
 ├── perception
 ├── retrieval
 ├── planning
 └── execution
```

Each task has an owner and explicit dependencies.

## 7. Shared memory

Shared memory is not a shared unstructured vector database.

Shared state must preserve:

- provenance;
- identity;
- version;
- authority;
- privacy classification;
- consistency class;
- deletion state.

## 8. Read permissions

An agent may read only the memory/data required for its delegated purpose.

## 9. Write permissions

An agent may write only to explicitly permitted state classes.

High-impact knowledge promotion or policy changes may require human or higher-level authorization.

## 10. Conflict handling

Multi-agent conflicts use 108/109 semantics.

Never apply universal last-write-wins to semantic or safety-critical state.

## 11. Coordination

Coordination mechanisms may include:

- task queues;
- leases;
- reservations;
- locks;
- causal dependencies;
- consensus where justified.

The mechanism is selected by state semantics, not convenience.

## 12. Failure

An agent failure must not leave unrecoverable ownership.

Tasks require:

- timeout;
- heartbeat/health where appropriate;
- lease expiry;
- reassignment;
- cancellation;
- recovery state.

## 13. Safety

Delegated agents never bypass the central governance/safety boundary.

```text
agent proposal
 ↓
policy
 ↓
safety
 ↓
execution
```

## 14. Privacy

Shared memory must obey 111. Delegation does not override privacy classification.

## 15. Offline coordination

Disconnected agents may continue only within their locally authorized autonomy envelope.

Reconnection requires synchronization and conflict resolution according to 109.

## 16. Future NVIDIA relevance

NVIDIA distributed/physical-AI infrastructure may eventually provide useful orchestration or inference capabilities, but these remain backend implementations behind Novi's coordination contracts.

## 17. Implementation status

Multi-agent coordination is explicitly deferred until single-agent Novi has validated:

- durable state;
- governance;
- safety;
- recovery;
- resource governance;
- shared-memory semantics.

## 18. Final rule

> **More agents must never mean less authority control, weaker provenance, weaker safety or ambiguous ownership.**
