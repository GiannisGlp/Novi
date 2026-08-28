# 04 — Active Perception

## Objective

Turn perception from a passive stream into a capability Novi can deliberately invoke when additional information can improve a decision.

## Architecture

```text
Goal / uncertainty
       ↓
Information need
       ↓
Perception query
       ↓
SSDLite / LocateAnything / audio / depth / future sensors
       ↓
Observation validation
       ↓
World-state update
       ↓
Decision improvement
```

## Step-by-step

### Step 1 — Define `PerceptionQuery`

Fields:

- query ID;
- natural-language query;
- structured target if known;
- sensor requirements;
- spatial scope;
- maximum latency;
- confidence threshold;
- information value;
- privacy level;
- requester goal ID.

### Step 2 — Preserve SSDLite as continuous perception

SSDLite remains the low-cost continuous detector for known object categories and tracking. It should not be replaced by an expensive VLM.

### Step 3 — Add `LocateAnythingBackend`

Implement it behind a Novi-owned interface. It must:

1. accept an image and query;
2. invoke the optional model backend;
3. parse its coordinate representation strictly;
4. reject malformed/inverted/out-of-range boxes;
5. return typed observations;
6. attach model/version/provenance;
7. expose latency and failure reason.

The currently released NVIDIA LocateAnything model is research/non-commercial licensed, so keep it replaceable and do not make it a core commercial dependency.

### Step 4 — Add query arbitration

Only invoke expensive grounding when:

- the user asks for a specific object;
- SSDLite is ambiguous;
- object identity is uncertain;
- prediction error requires inspection;
- a plan needs a missing visual fact;
- map/world-state freshness is insufficient.

### Step 5 — Fuse results

Use IoU, semantic similarity, track identity and temporal proximity to decide whether a LocateAnything result refers to an existing SSDLite track.

Never merge two entities solely because their labels match.

### Step 6 — Add active search

If an object is not found:

1. query the current frame;
2. inspect likely spatial regions;
3. change viewpoint if possible;
4. query again;
5. update search belief;
6. stop after budget exhaustion;
7. report not-found uncertainty rather than hallucinating success.

### Step 7 — Add information-gain scoring

For each possible perception action estimate:

```text
expected decision improvement
÷
latency + energy + risk
```

Choose the highest-value safe observation.

### Step 8 — Add 2D→3D fusion later

A visual box is not a physical world coordinate. Fuse it with depth/stereo, camera intrinsics/extrinsics and robot pose before storing metric location.

### Step 9 — Add perception budgets

Every goal gets:

- maximum VLM queries;
- maximum camera search time;
- maximum energy/compute budget;
- maximum retries.

### Step 10 — Add uncertainty-aware escalation

Fast detector → tracking → targeted VLM → depth → viewpoint change → human clarification. Escalation should stop when confidence is sufficient or the budget is exhausted.

## Tests

Cover:

- exact query success;
- no-match;
- multiple matches;
- malformed model output;
- stale image;
- model unavailable;
- timeout;
- duplicate entity merge;
- ambiguous identity;
- privacy-sensitive query;
- budget exhaustion.

## Acceptance gate

`A-PERCEPT-01`: Novi must solve a known-object search scenario using continuous SSDLite plus targeted active perception, while producing no false positive after the search budget is exhausted.
