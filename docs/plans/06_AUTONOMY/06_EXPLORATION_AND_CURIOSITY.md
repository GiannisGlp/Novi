# 06 — Exploration and Curiosity

## Objective

Allow Novi to intentionally acquire useful knowledge instead of remaining passive when no explicit task is active, while preventing uncontrolled wandering or endless self-generated objectives.

## Core concept

Curiosity is an **information-seeking policy**, not a desire to stay busy.

```text
Unknown / uncertainty
       ↓
Potential information gain
       ↓
Expected usefulness
       ↓
Risk + cost
       ↓
Exploration goal
       ↓
Safe observation
       ↓
Knowledge update
```

## Step-by-step

### Step 1 — Define novelty

Novelty sources:

- unseen object;
- unexplored map region;
- unexpected event;
- prediction error;
- contradictory observations;
- newly available sensor;
- changed environment.

### Step 2 — Define curiosity candidates

Generate candidates only when Novi has spare autonomy budget. Each candidate needs an information hypothesis: what uncertainty will the action reduce?

### Step 3 — Score information gain

Estimate:

`expected uncertainty reduction × future usefulness - cost - risk`.

Do not explore merely because something is novel.

### Step 4 — Bound exploration

Every exploration episode has:

- maximum duration;
- maximum distance;
- maximum energy;
- maximum perception calls;
- maximum retries;
- forbidden regions;
- immediate stop conditions.

### Step 5 — Explore incrementally

Prefer safe observations first:

1. use existing sensors;
2. rotate camera if safe;
3. inspect nearby area;
4. move only if necessary;
5. update map/world state;
6. stop once information gain is below threshold.

### Step 6 — Convert discoveries into memory carefully

A discovery becomes long-term knowledge only after evidence thresholds are met. Preserve source and confidence.

### Step 7 — Learn exploration preferences

Over time record which exploration actions actually improved future task performance. Do not optimize solely for novelty.

### Step 8 — Add maintenance exploration

Safe background tasks can include map refresh, sensor health checks and stale-object verification, but must never interrupt urgent user/safety goals.

## Evaluation

Measure:

- information gain per minute;
- map coverage;
- unknown-area reduction;
- redundant exploration rate;
- energy per useful discovery;
- interruption compliance;
- unsafe exploration count.

## Acceptance gate

`A-CURIOSITY-01`: In a simulated environment containing hidden but useful information, Novi should discover high-value unknowns within a fixed budget while avoiding low-value wandering.
