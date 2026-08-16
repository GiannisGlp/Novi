# 21 — Cognitive Security and Privacy

## Status

**DESIGN**

## Purpose

Protect cognition from unauthorized data access, prompt injection, malicious model outputs, identity abuse, and accidental disclosure while preserving useful autonomy.

## Trust Boundaries

```text
Sensors / external input
        ↓ untrusted evidence
Perception
        ↓ validated events
Cognition
        ↓ bounded proposals
Policy / Safety
        ↓ authorized actions
Capabilities
        ↓
Hardware / external systems
```

External text, speech, images, files, and network data are **data**, not instructions to the system. Instructions embedded inside observed content must not automatically become privileged commands.

## Prompt Injection

Retrieved documents, websites, messages, speech, images, and user-provided content can contain adversarial instructions. The context engine must label content by source and trust level and separate:

- system policy
- developer configuration
- authorized user instructions
- observed content
- retrieved knowledge
- model-generated content

Observed content can inform reasoning but cannot override higher-trust policy.

## Capability Security

Each tool has:

- explicit name
- typed input schema
- allowed callers
- authorization requirements
- risk class
- resource limits
- timeout
- audit requirements

The reasoning model never receives arbitrary shell, SQL, filesystem, or network privileges.

## Sensitive Cognitive Data

Potentially sensitive data includes:

- faces and biometric embeddings
- voice/speaker embeddings
- private conversations
- household routines
- location history
- relationship information
- personal preferences
- files and documents

Cognition should request only the minimum data needed for a task.

## Data Minimization

Context construction should minimize sensitive information. A model should not receive a complete person profile when the task only requires a first name and relationship category.

## Authorization vs Recognition

Recognizing a person does not automatically authorize an action. Authentication/authorization is a separate security service.

## Model Output Validation

All model-generated structured outputs are treated as untrusted proposals until schema validation, policy evaluation, and safety checks succeed.

## Audit Integrity

Audit records should be append-oriented and protected from modification by ordinary cognitive components. The system must preserve enough metadata to reconstruct consequential actions.

## Immutable Core

The cognitive system cannot modify protected safety rules, trust roots, authorization policy, or audit integrity mechanisms. Adaptive learning operates only in explicitly managed storage.

## Local-First Privacy

Local execution is preferred because it minimizes data leaving the home environment. Cloud processing requires an explicit capability and privacy policy decision.

## Acceptance Criteria

Cognition cannot escalate privileges through model output, retrieved content, learned knowledge, identity recognition, or generated code, and sensitive context is minimized before model invocation.
