# 08 — Safety, Governance and Human Override

## Objective

Make safety an independent authority that can stop or constrain autonomous behavior even when cognition, perception or planning is wrong.

## Safety architecture

```text
Sensors / world state
        ↓
Safety monitors ───────────────┐
        ↓                       │
Risk assessment                │
        ↓                       │
Policy decision                │
        ↓                       │
ALLOW / MODIFY / DENY / STOP ←─┘
        ↓
Executor
```

## Step-by-step

### Step 1 — Define action risk classes

At minimum:

- informational;
- reversible digital;
- low-risk physical;
- movement;
- manipulation;
- high-energy/high-force;
- privacy-sensitive;
- irreversible.

Each class has a minimum authority level.

### Step 2 — Define invariants

Examples:

- never move while emergency stop is active;
- never execute with stale pose beyond configured TTL;
- never enter forbidden zones;
- never exceed velocity/force limits;
- never operate without required sensor health;
- never bypass human approval for configured high-risk skills.

### Step 3 — Build independent safety monitor

The safety monitor must not depend solely on the same LLM reasoning path it is supervising.

### Step 4 — Add pre-action risk assessment

Evaluate:

- proximity to humans/obstacles;
- uncertainty;
- speed/force;
- environment state;
- action reversibility;
- authority;
- expected consequence.

### Step 5 — Add runtime monitoring

Safety must continue while an action executes. A previously approved action can become unsafe when the environment changes.

### Step 6 — Add emergency stop semantics

Emergency stop must:

1. cancel active action;
2. halt command generation;
3. enter `SAFE_STOP`;
4. record cause;
5. require explicit recovery conditions;
6. never auto-resume dangerous physical behavior.

### Step 7 — Add human approval

Approval requests must state:

- what Novi wants to do;
- why;
- expected effect;
- risk;
- confidence;
- alternatives;
- timeout.

Approval is explicit, scoped and non-transferable to unrelated actions.

### Step 8 — Add policy versioning

Every action decision records the policy version used. Policy changes create regression requirements.

### Step 9 — Add adversarial tests

Test prompt injection, misleading visual labels, contradictory sensors, stale state, malformed model outputs, compromised tool responses and unsafe user instructions.

### Step 10 — Add physical safety hardware boundary

When physical hardware exists, software safety is not sufficient. Define emergency-stop hardware, motor controller limits, watchdogs and independent power/actuator protections before real autonomous motion.

## Acceptance gate

`A-SAFE-01`: Across all autonomy scenarios, any configured unsafe condition must prevent or interrupt physical execution within the defined response budget. No model-generated instruction may bypass the safety gate.
