# Novi — LocateAnything Implementation Plan

**Date:** 2026-08-28  
**Status:** IMPLEMENTING — §19 sequence steps 1–28 done; input-agnostic integration done (L1 full-flow scenario, L2 grounding service bridge, L3 `/api/grounding` web surface — same pipeline for web/CLI/body). Steps 29–32: spec + license record ready; execution blocked on NVIDIA hardware / legal review. Live tracking: `docs/07-locate-anything/08_IMPLEMENTATION_STATUS.md`.  
**Primary objective:** Integrate NVIDIA LocateAnything as an optional language-conditioned spatial-perception backend without weakening Novi's existing perception contracts, deterministic core, safety boundaries, Mac-first development posture, or future NVIDIA/Jetson portability.

---

## 1. Executive decision

Implement LocateAnything as a **secondary spatial-grounding backend** behind a Novi-owned interface.

Do **not**:

- replace SSDLite;
- make Transformers/CUDA/DeepSpeed mandatory Novi dependencies;
- let raw model output enter the world model;
- let the model choose actions;
- assume 3D position from a 2D box;
- assume Apple MPS support;
- assume commercial licensing;
- couple Novi's architecture to NVIDIA's worker class.

The target architecture is:

```text
CameraFrame
    |
    +--> Fast category perception (SSDLite)
    |
    +--> Language-conditioned spatial perception
             |
             +--> LocateAnything adapter
             |
             +--> future alternative backend

GroundingResult
    |
    v
validated spatial observations
    |
    v
tracking / association
    |
    v
world model
    |
    +--> memory
    +--> prediction
    +--> reasoning
    +--> planner
    +--> verification
```

---

# 2. Phase 0 — Freeze the boundary before implementation

### Step 0.1 — Record the architecture decision

Create a permanent architecture decision record stating:

- LocateAnything is a perception backend;
- SSDLite remains the baseline fast detector;
- cognition owns semantic queries;
- perception owns geometric localization;
- world state owns persistent interpretation;
- governance owns action permission;
- model licensing is tracked independently from code licensing.

**Acceptance:** reviewers can identify exactly which layer owns each responsibility.

### Step 0.2 — Freeze the external model version

Do not use a floating `main` model reference in production-like experiments.

Record:

- Hugging Face model ID;
- exact revision/commit;
- model config hash;
- tokenizer/processor revision;
- upstream code commit;
- model license revision.

**Acceptance:** the same revision can be reproduced later.

### Step 0.3 — Create an explicit capability state

The backend must report one of:

`available | loading | unavailable | unsupported | dependency_missing | model_missing | failed`.

**Acceptance:** missing LocateAnything never crashes normal Novi startup.

---

# 3. Phase 1 — Add typed Novi spatial contracts

## Step 1.1 — Introduce a canonical grounding contract

Add a new perception contract rather than overloading `Detection`.

Conceptual objects:

```text
SpatialQuery
GroundingObservation
GroundingResult
PointObservation
SpatialBackendCapabilities
SpatialInferencePolicy
```

### `SpatialQuery`

Fields should include:

- query text;
- frame ID;
- timestamp;
- requested output (`box`, `point`, `both`);
- maximum results;
- latency budget;
- risk class;
- privacy class;
- preferred mode;
- optional candidate labels;
- requester/source;
- correlation ID.

### `GroundingObservation`

Fields should include:

- observation ID;
- query;
- label/description;
- normalized box;
- pixel box;
- optional point;
- image width/height;
- model ID;
- model revision;
- backend version;
- inference mode;
- frame ID;
- timestamp;
- confidence/quality fields where actually supported;
- provenance;
- fallback status;
- latency.

### `GroundingResult`

Must include:

- success state;
- zero or more observations;
- backend status;
- model provenance;
- timing;
- validation errors;
- fallback statistics;
- raw-response hash if useful for audit/debugging.

**Acceptance:** no other Novi component needs to understand NVIDIA special tokens.

---

# 4. Phase 2 — Implement strict output parsing

## Step 2.1 — Parse NVIDIA's structured tokens

Implement a parser for:

```text
<ref>label</ref><box><x1><y1><x2><y2></box>
<box><x><y></box>
<box>none</box>
```

Do not use permissive regex behavior that silently repairs malformed output.

## Step 2.2 — Validate coordinates

Reject:

- non-integer coordinates;
- coordinates outside `[0,1000]`;
- missing tokens;
- inverted coordinates;
- zero-area boxes;
- impossible output nesting;
- excessive result counts;
- malformed category separators.

## Step 2.3 — Preserve source coordinates

Store normalized source coordinates and converted pixel coordinates.

## Step 2.4 — Add parser property tests

Test:

- one box;
- many boxes;
- one point;
- many points;
- none;
- duplicate labels;
- punctuation in labels;
- malformed tokens;
- truncated responses;
- out-of-range coordinates;
- inverted boxes;
- mixed valid/invalid blocks;
- empty response.

**Acceptance:** malformed output is never converted into a valid world observation.

---

# 5. Phase 3 — Build the backend adapter

## Step 3.1 — Add a LocateAnything backend module

Recommended structure:

```text
novi/perception/
    locate_anything.py
    locate_anything_runtime.py
```

The adapter must expose the Novi contract and hide NVIDIA implementation details.

## Step 3.2 — Lazy-load heavy dependencies

No import-time dependency on:

- Transformers;
- DeepSpeed;
- bitsandbytes;
- Triton;
- Liger Kernel;
- NVIDIA-specific CUDA libraries.

## Step 3.3 — Implement capability probing

Probe:

- Python/runtime compatibility;
- PyTorch availability;
- processor/model availability;
- device availability;
- memory capacity;
- attention backend availability;
- model revision;
- batch-runtime availability.

## Step 3.4 — Implement standard single-image inference

First implementation target:

```text
one frame + one query -> one validated GroundingResult
```

Do not start with streaming/batching.

## Step 3.5 — Implement inference modes

Support:

- `fast`;
- `slow`;
- `hybrid`.

Default: `hybrid`.

**Acceptance:** the backend can be tested independently from the Brain.

---

# 6. Phase 4 — Mac compatibility experiment

This phase is mandatory before deeper integration.

NVIDIA documents H100/A100 testing, not Apple MPS. Therefore the Mac path is experimental.

## Step 4.1 — Isolated environment

Create an optional environment/extra dedicated to LocateAnything.

Do not contaminate the default Novi `.venv` until compatibility is proven.

## Step 4.2 — Load-only test

Attempt to load:

`nvidia/LocateAnything-3B`

Record:

- Python version;
- PyTorch version;
- Transformers version;
- processor version;
- device;
- memory before/after load;
- load time;
- model revision.

## Step 4.3 — Single inference

Use Novi's existing `novi/assets/test-image.png` and a simple query such as:

`locate all objects visible in the image`

Record:

- successful load;
- inference time;
- output;
- parser result;
- peak memory;
- device.

## Step 4.4 — Grounding test

Use explicit queries:

- `locate the person`;
- `locate the largest object`;
- `locate the object nearest the center`;
- a query for an absent object.

## Step 4.5 — Stress test

Run:

- 1 query;
- 5 repeated queries;
- 10 repeated queries;
- multiple boxes;
- large image;
- small image;
- cluttered image.

Record p50/p95/p99 latency and memory.

## Step 4.6 — Decision gate

Possible outcomes:

### A. MPS is usable

Continue with local Mac backend.

### B. MPS works but is too slow/heavy

Keep the adapter but run the model in a separate local NVIDIA workstation/server.

### C. MPS cannot run it reliably

Do not force compatibility. Continue Novi development with SSDLite and use an NVIDIA backend for LocateAnything experiments.

**Acceptance:** one explicit compatibility decision is documented rather than assumed.

---

# 7. Phase 5 — Integrate with the existing perception pipeline

Current Novi pipeline:

`frame -> detector -> tracker -> optional face stage -> WorldObservation`.

Extend it without breaking existing behavior.

## Step 5.1 — Keep `ObjectDetector` stable

SSDLite continues to satisfy the existing contract.

## Step 5.2 — Add spatial grounding as an explicit capability

Do not force all perception through `ObjectDetector.detect()` because a natural-language query is not equivalent to a category list.

## Step 5.3 — Add optional grounding to `PerceptionPipeline`

Possible API:

```text
process_frame(...)
ground_frame(frame, query, policy)
```

Do not make grounding mandatory on every frame.

## Step 5.4 — Track grounding observations

Associate returned boxes with existing tracks where possible.

If association is uncertain, create a candidate observation rather than inventing continuity.

## Step 5.5 — Preserve frame provenance

Every grounding result must retain:

- source frame ID;
- timestamp;
- image dimensions;
- model revision;
- query.

**Acceptance:** LocateAnything can be added without breaking all existing SSDLite/perception tests.

---

# 8. Phase 6 — Add active perception

This is the most important Novi-specific phase.

## Step 6.1 — Define perception escalation rules

Examples:

```text
SSDLite confidence low
        -> grounding request

object category known but description ambiguous
        -> grounding request

planner needs precise target
        -> grounding request

prediction violated
        -> re-ground scene

memory says object should be here but it is not detected
        -> active search query
```

## Step 6.2 — Connect cognitive query generation

Cognition generates semantic queries.

Perception executes them.

Example:

`find my keys`

becomes a visual query based on memory/context, such as:

`small keyring on or near the desk`.

## Step 6.3 — Add query budget

Every active-perception request must have:

- time budget;
- compute budget;
- maximum retries;
- maximum frames;
- risk class.

## Step 6.4 — Add query deduplication

Do not repeatedly spend expensive inference on the exact same frame/query pair unless requested by policy.

## Step 6.5 — Add observation caching

Cache only short-lived query/frame results unless promoted to memory by Novi's normal memory policy.

---

# 9. Phase 7 — Integrate with prediction and memory

Novi now has sequence prediction and deliberation memory. LocateAnything should exploit them.

## Step 7.1 — Prediction verification

If Novi predicts an object will appear, grounding can verify the expectation.

## Step 7.2 — Prediction violation

If grounding contradicts an expected scene, emit a prediction violation event.

## Step 7.3 — Memory promotion

Only stable/salient spatial observations should be promoted to durable memory.

Example:

```text
Observed:
  blue cup near desk

Repeated observations:
  blue cup near desk

Promote:
  spatial relation = cup near desk
```

## Step 7.4 — Deliberation memory

Record important visual decisions:

- query;
- candidates;
- selected target;
- rejected candidates;
- evidence;
- outcome.

---

# 10. Phase 8 — Add spatial reasoning, but do not fake 3D

## Step 8.1 — Keep 2D as the first milestone

First acceptance:

`image -> query -> 2D grounding -> world observation`.

## Step 8.2 — Add depth only later

When depth sensors exist:

```text
2D grounding
 + depth
 + intrinsics
 + extrinsics
 + robot pose
 -> 3D point/volume
```

## Step 8.3 — Keep coordinate frames explicit

Every spatial observation must declare its frame:

- image pixel frame;
- normalized image frame;
- camera frame;
- robot base frame;
- world/map frame.

Do not silently transform between them.

---

# 11. Phase 9 — Safety and verification

## Step 9.1 — Never allow direct action

LocateAnything output is observational only.

## Step 9.2 — Require verification for high-risk actions

Example:

```text
Locate target
   ↓
plan
   ↓
re-observe target
   ↓
verify position
   ↓
action
```

## Step 9.3 — Confidence is not permission

Even a high-confidence localization does not authorize an action.

## Step 9.4 — Failure must be fail-closed

If localization fails, Novi must report unknown/uncertain rather than infer absence.

---

# 12. Phase 10 — Build the Novi benchmark

## Step 10.1 — Dataset

Create a versioned Novi-local evaluation set with rights/provenance metadata.

Categories:

- household objects;
- robot workspace;
- people/hands;
- clutter;
- occlusion;
- similar objects;
- small objects;
- text/signs;
- novel descriptions;
- negative queries.

## Step 10.2 — Ground truth

Each record should include:

- image hash;
- image dimensions;
- query;
- target boxes/points;
- expected object identity if applicable;
- source/license.

## Step 10.3 — Metrics

Measure:

- IoU@0.5;
- IoU@0.75;
- IoU@0.90/0.95;
- mean IoU;
- center error;
- precision;
- recall;
- false positives;
- false negatives;
- malformed outputs;
- Fast→Slow fallback rate;
- latency p50/p95/p99;
- memory;
- cold start;
- sustained throughput.

## Step 10.4 — Cognitive metrics

Measure whether grounding improves:

- search success;
- prediction verification;
- world-state accuracy;
- planner success;
- action verification.

The most important experiment is **baseline Novi vs Novi + LocateAnything**, not LocateAnything in isolation.

---

# 13. Phase 11 — Test the complete closed loop

Create deterministic tests first, then hardware-backed tests.

## Unit tests

- parser;
- coordinate conversion;
- contract validation;
- capability detection;
- policy selection;
- error mapping;
- provenance.

## Integration tests

- mock backend -> pipeline;
- grounding -> tracking;
- grounding -> world observation;
- grounding -> memory;
- prediction -> active grounding;
- planner -> verification.

## Real-IO acceptance

```text
real camera
 -> real frame
 -> LocateAnything
 -> typed grounding
 -> tracker
 -> world state
```

## Restart acceptance

Ensure durable memory survives restart while ephemeral frame-level grounding does not incorrectly become permanent fact.

---

# 14. Phase 12 — NVIDIA hardware path

Only after the model has demonstrated value should we optimize the NVIDIA path.

Potential runtime options to benchmark:

1. standard Transformers;
2. NVIDIA/upstream worker;
3. `la_flash` batch runtime;
4. vLLM;
5. SGLang;
6. later NVIDIA-native acceleration where supported by the target hardware.

Do not select a deployment runtime from documentation alone. Benchmark on the actual target GPU.

Target future architecture:

```text
Robot camera
    ↓
NVIDIA GPU
    ↓
LocateAnything runtime
    ↓
Novi perception adapter
    ↓
Novi brain
```

---

# 15. Phase 13 — Commercial/license gate

Before any commercial deployment:

1. identify exact model revision;
2. retain exact model license;
3. obtain legal review;
4. determine whether NVIDIA commercial permission is required;
5. obtain written permission if required;
6. record the decision in Novi's release evidence.

Until then the released model is research/evaluation only.

---

# 16. Phase 14 — Future visual-prompt capability

Do not implement visual prompts as an accepted production feature yet.

The upstream code has visual-prompt plumbing, but NVIDIA's README states the currently released 3B weights do not support visual-prompt inference out of the box.

When NVIDIA releases compatible weights:

1. pin the new revision;
2. re-read its model card/license;
3. test crop-based and image-based visual prompts;
4. compare with ordinary language grounding;
5. add a capability flag;
6. add regression tests;
7. update this plan.

---

# 17. Phase 15 — Remove experimental status

LocateAnything can graduate from experimental only when all are true:

- model loading is reproducible;
- target hardware is supported/validated;
- output parser is fully tested;
- grounding benchmark passes thresholds;
- sustained latency meets the perception budget;
- failure/degradation behavior is verified;
- tracking/world-state integration is verified;
- active perception improves a measurable Novi task;
- safety path is verified;
- provenance is complete;
- licensing is cleared for the intended deployment.

---

# 18. Proposed implementation milestones

## LA-0 — Research baseline

Deliverables:

- source documentation;
- model/license record;
- architecture decision;
- benchmark specification.

## LA-1 — Adapter

Deliverables:

- typed contracts;
- strict parser;
- optional backend;
- mocked tests.

## LA-2 — Mac feasibility

Deliverables:

- isolated runtime;
- load/inference evidence;
- latency/memory report;
- explicit MPS decision.

## LA-3 — Perception integration

Deliverables:

- grounding in pipeline;
- tracking association;
- provenance;
- web/CLI observability.

## LA-4 — Active perception

Deliverables:

- cognitive query generation;
- escalation policy;
- budgets;
- cache/deduplication.

## LA-5 — Cognitive integration

Deliverables:

- memory;
- sequence prediction verification;
- deliberation memory;
- world-state updates.

## LA-6 — Real-IO closed loop

Deliverables:

`camera -> LocateAnything -> world -> cognition -> verification`.

## LA-7 — NVIDIA hardware evaluation

Deliverables:

- target GPU benchmark;
- runtime comparison;
- deployment decision.

## LA-8 — Production decision

Deliverables:

- safety evidence;
- performance evidence;
- license clearance;
- release recommendation.

---

# 19. Exact first implementation sequence

When implementation starts, do it in this order and do not skip ahead:

1. Add the architecture decision.
2. Add `SpatialQuery`/`GroundingObservation`/`GroundingResult` contracts.
3. Add strict LocateAnything output parser.
4. Add coordinate conversion and geometry validation.
5. Add mocked `LocateAnythingBackend`.
6. Add unit tests for every parser/contract edge case.
7. Add optional dependency/runtime detection.
8. Create isolated LocateAnything environment.
9. Pin `nvidia/LocateAnything-3B` revision.
10. Attempt model load on the Mac.
11. Record memory/load results.
12. Run one real image/query.
13. Record inference result and latency.
14. Decide MPS/CPU/remote-NVIDIA feasibility.
15. Implement the real backend for the viable runtime.
16. Connect one frame to one grounding query.
17. Connect grounding observations to tracking.
18. Connect observations to world state.
19. Add active-perception escalation from SSDLite uncertainty.
20. Add query budgets and deduplication.
21. Connect prediction verification.
22. Connect deliberation memory for ambiguous target selection.
23. Add short-term spatial observation caching.
24. Add selective durable spatial memory.
25. Add benchmark corpus and ground truth.
26. Compare SSDLite-only vs SSDLite+LocateAnything.
27. Run real camera acceptance.
28. Add high-risk re-observation/verification.
29. Benchmark target NVIDIA hardware.
30. Evaluate deployment runtime options.
31. Complete license review.
32. Only then consider production integration.

---

# 20. Definition of done

The LocateAnything workstream is complete only when Novi can perform this reproducibly:

```text
User/brain goal
   |
   v
semantic visual query
   |
   v
real camera frame
   |
   v
LocateAnything grounding
   |
   v
strict typed observation
   |
   v
tracking / world state
   |
   v
memory + prediction + reasoning
   |
   v
planner
   |
   v
verification
   |
   v
safe action proposal
   |
   v
outcome
   |
   v
learning / durable knowledge where justified
```

The system must also demonstrate graceful operation when LocateAnything is unavailable.

---

# 21. Primary sources

- NVIDIA research page: https://research.nvidia.com/labs/lpr/locate-anything/
- NVIDIA paper: https://research.nvidia.com/labs/lpr/locate-anything/LocateAnything.pdf
- arXiv: https://arxiv.org/abs/2605.27365
- NVIDIA code: https://github.com/NVlabs/Eagle/tree/main/Embodied
- Model card: https://huggingface.co/nvidia/LocateAnything-3B
- Model license: https://github.com/NVlabs/Eagle/blob/main/Embodied/LICENSE_MODEL
- Training: https://github.com/NVlabs/Eagle/blob/main/Embodied/document/TRAINING.md
- Data preparation: https://github.com/NVlabs/Eagle/blob/main/Embodied/document/DATA_PREPARATION.md
- Evaluation: https://github.com/NVlabs/Eagle/blob/main/Embodied/evaluation/README.md
- Results: https://github.com/NVlabs/Eagle/blob/main/Embodied/document/RESULTS.md
- Streaming packing: https://github.com/NVlabs/Eagle/blob/main/Embodied/document/STREAMING_PACKING.md
