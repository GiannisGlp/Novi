# 03 — World State, Memory and Prediction

## Objective

Give autonomy a grounded internal state that distinguishes what Novi currently observes, what it remembers, what it believes, what it predicts and what it intends.

## Required state layers

```text
Raw sensor observation
        ↓
Perception result
        ↓
Fused world observation
        ↓
Current belief state
        ↓
Persistent semantic/spatial memory
        ↓
Prediction
        ↓
Goal/plan state
```

Never collapse these layers into one generic fact store.

## Step-by-step

### Step 1 — Define observation provenance

Every observation must include:

- source sensor/model;
- timestamp;
- frame ID;
- confidence;
- uncertainty;
- calibration/version metadata;
- freshness/TTL;
- transformation frame where applicable.

### Step 2 — Add freshness semantics

Each fact gets a freshness policy. A person location may expire quickly; a room name may remain stable; an inferred routine requires repeated evidence.

The planner must never treat expired data as current.

### Step 3 — Add contradiction handling

Represent contradictions explicitly:

```text
cup_on_table = true, source=camera, t1
cup_on_table = false, source=camera, t2
```

Do not overwrite history. Belief revision chooses the current belief while preserving evidence.

### Step 4 — Add spatial memory

Introduce spatial entities with:

- semantic ID;
- 2D image geometry;
- optional depth;
- camera pose;
- robot-frame pose;
- world-frame pose;
- covariance/uncertainty;
- last seen;
- observation count;
- source;
- relation to landmarks/containers.

This is the bridge for LocateAnything + depth/SLAM.

### Step 5 — Add semantic relations

Support relations such as:

- `inside`
- `on`
- `near`
- `left_of`
- `right_of`
- `in_front_of`
- `behind`
- `owned_by`
- `last_seen_at`
- `used_for`
- `associated_with`

Relations need confidence and provenance.

### Step 6 — Strengthen temporal prediction

Extend the existing sequence-prediction direction to support:

- event sequences;
- object movement;
- routine likelihood;
- expected sensor events;
- expected action outcomes.

Prediction output must contain probability/confidence and a prediction horizon.

### Step 7 — Add prediction error

After every prediction window, compare expected and observed state. Record:

- expected;
- actual;
- error magnitude;
- possible cause;
- whether the model should update;
- whether additional perception is warranted.

### Step 8 — Add belief revision policy

Classify evidence:

`DIRECT_OBSERVATION`, `MULTI_SENSOR_FUSION`, `RELIABLE_MEMORY`, `MODEL_INFERENCE`, `USER_ASSERTION`, `PREDICTION`.

Use source reliability and recency to revise beliefs. A hallucinated model statement must never outrank direct contradictory sensor evidence.

### Step 9 — Add memory utility scoring

Memory retrieval should consider:

- relevance to current goal;
- recency;
- reliability;
- spatial proximity;
- recurrence;
- outcome usefulness;
- contradiction status.

### Step 10 — Learn only from verified outcomes

Do not promote every model-generated hypothesis to long-term knowledge. Promote observations and action outcomes according to explicit evidence thresholds.

## Evaluation

Measure:

- stale-fact rate;
- contradiction resolution accuracy;
- object identity continuity;
- spatial localization error;
- prediction precision/recall;
- false-memory rate;
- useful-memory retrieval rate;
- belief revision latency.

## Acceptance gate

`A-WORLD-01`: In a 30-minute simulated scenario with object movement, missing observations and contradictory sensor events, Novi must maintain provenance, expire stale facts, revise beliefs correctly and never represent an unverified inference as a verified observation.
