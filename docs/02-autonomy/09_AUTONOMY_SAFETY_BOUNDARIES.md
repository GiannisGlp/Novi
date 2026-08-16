# 09 — Autonomy Safety Boundaries

## Status

**DESIGN — SAFETY CRITICAL**

## Principle

Autonomy proposes behavior. Independent policy and safety systems decide whether behavior may execute.

## Immutable Boundary

The following must not be modifiable by the autonomy/learning system:

- emergency-stop logic;
- actuator safety limits;
- protected authorization rules;
- cryptographic trust roots;
- audit integrity mechanisms;
- hardware damage protections;
- protected software-update rules.

## Risk Classes

A baseline taxonomy:

- `R0` — informational/internal;
- `R1` — reversible digital action;
- `R2` — low-risk environmental/IoT action;
- `R3` — physical movement or consequential external action;
- `R4` — high-risk physical/security/privacy action;
- `R5` — prohibited without dedicated external safety authority.

Exact classifications must be defined per capability.

## Policy Pipeline

```text
model proposal
→ schema validation
→ identity/authorization
→ risk classification
→ policy evaluation
→ physical/environment checks
→ safety gate
→ execution
```

## Safety Overrides

The safety layer may:

- deny;
- modify parameters within safe bounds;
- require confirmation;
- pause;
- stop;
- enter safe degraded mode.

The model cannot override these outcomes.

## Human Confirmation

Confirmation requirements must be deterministic and capability-specific. Examples can include external communication, security-sensitive actions, or configurable high-impact IoT/physical operations.

## Sensor Confidence

Safety decisions must not rely on a single uncertain perception result when failure could cause harm. Multi-sensor confirmation or conservative behavior should be used where appropriate.

## Failure Defaults

When required safety information is unavailable, the system should fail to the safest useful state rather than guess.

Examples:

- uncertain obstacle → slow/stop;
- lost localization → stop/relocalize;
- actuator fault → disable affected action;
- temperature critical → controlled shutdown;
- battery critical → return/stop according to validated policy.

## Learning Boundary

Learning can propose policy improvements but cannot apply them to protected safety rules automatically.

## Acceptance Criteria

Safety tests must demonstrate that malicious, incorrect, hallucinated, or malformed model output cannot bypass the safety boundary.
