# 07 — Metacognition, Recovery and Continual Learning

## Objective

Make Novi aware of the reliability of its own decisions and able to recover from failures without turning every failure into uncontrolled learning.

## Step-by-step

### Step 1 — Build confidence decomposition

Separate:

- perception confidence;
- world-state confidence;
- identity confidence;
- plan confidence;
- action confidence;
- verification confidence.

Never use one global confidence number for all decisions.

### Step 2 — Add self-health assessment

At every autonomy tick compute whether critical components are healthy, degraded or unavailable.

### Step 3 — Add uncertainty escalation

When confidence is insufficient:

1. gather more perception;
2. retrieve relevant memory;
3. ask another reasoning model if available;
4. use a deterministic fallback;
5. ask the human;
6. stop safely.

### Step 4 — Implement failure taxonomy

Classify failures as:

- perception;
- localization;
- world-model;
- planning;
- precondition;
- execution;
- verification;
- resource;
- safety;
- dependency;
- human interruption.

Each class gets explicit recovery strategies.

### Step 5 — Add bounded retries

Every retry consumes a budget. Retry policy must vary by failure type. Repeating an action that has physically failed without new information is forbidden.

### Step 6 — Add replanning

If the world changes, invalidate affected plan steps rather than continuing a stale plan.

### Step 7 — Add counterfactual failure analysis

After failure record:

- what Novi believed;
- what it expected;
- what happened;
- why the discrepancy occurred;
- what information would have prevented it;
- whether the planner or perception policy should change.

### Step 8 — Add continual learning gates

Learning pipeline:

`experience → candidate lesson → evidence aggregation → validation → promotion → rollback capability`.

No single LLM response may directly rewrite trusted knowledge or policy.

### Step 9 — Add routine learning

Use repeated event sequences to identify routines. Require recurrence, temporal consistency and outcome evidence before promotion.

### Step 10 — Add regression memory

Every promoted lesson should create a regression scenario when practical. This prevents Novi from relearning a failure in a future version.

### Step 11 — Add model routing later

A routing layer can choose between deterministic reasoning, local LLM, VLM, specialist perception or fallback logic based on task complexity, confidence, latency and resource budget. This is where the previously researched LLMRouter direction can eventually fit.

## Metrics

- recovery success rate;
- mean time to recover;
- repeated-failure rate;
- false-confidence rate;
- calibration error;
- learning promotion precision;
- regression recurrence rate;
- human escalation rate.

## Acceptance gate

`A-META-01`: Inject 500 mixed failures and verify that Novi either recovers, replans, asks for help or safely stops, with zero infinite retry loops and zero unverified learning promotions.
