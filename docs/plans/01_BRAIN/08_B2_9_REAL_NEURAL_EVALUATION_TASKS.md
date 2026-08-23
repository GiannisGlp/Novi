# B2.9 — Real Neural Evaluation & Evidence Tasks

## Objective

Turn the existing Brain model adapters and evaluation contracts into a reproducible real-model validation program. This stage produces evidence; it does not yet select Orin 64GB vs Thor.

## Environment rule

Mac-first development remains mandatory. All benchmark orchestration, manifests, metric calculation, evidence validation and deterministic tests must be runnable on the user's Mac and in GitHub CI without NVIDIA hardware.

Real checkpoint execution and accelerator measurements are a separate hardware-validation layer.

## Work breakdown

### B2.9.1 — Benchmark specification

Define the official benchmark suite, scenario taxonomy, sample counts, warm-up policy, repetition policy, timeout policy and metrics.

**Output:** benchmark specification.

### B2.9.2 — Dataset and scenario manifests

Create versioned manifests for image, stereo, video and multimodal scenarios. Each case receives a stable ID and declares expected evidence/ground truth where available.

**Output:** reproducible manifests; no model-specific hidden inputs.

### B2.9.3 — Evidence schema

Define the machine-readable evidence record for model identity, runtime, hardware, dataset, configuration, measurements, failures and conclusion.

**Output:** schema + validation tests.

### B2.9.4 — Benchmark runner

Implement a hardware-neutral runner that invokes the existing model/evaluation contracts and records timing and results. The runner must support deterministic fake backends on Mac/CI and real backends on NVIDIA hardware.

**Output:** runner + Mac tests.

### B2.9.5 — RT-DETR experiment

Run the first real specialist experiment once a suitable NVIDIA GPU environment is available. Establish detection quality and runtime baseline.

### B2.9.6 — ESS experiment

Measure real-time stereo depth quality and runtime.

### B2.9.7 — FoundationStereo experiment

Measure higher-quality stereo depth and compare directly with ESS using identical inputs.

### B2.9.8 — Nemotron experiment

Evaluate multimodal understanding and structured reasoning on Novi-specific scenarios, plus runtime/resource behavior.

### B2.9.9 — Cosmos Reason2 experiment

Evaluate spatial/temporal/physical reasoning on controlled scenarios with explicit ground-truth facts.

### B2.9.10 — Combined neural pipeline

Run perception + world-state + Nemotron/Cosmos concurrently and measure end-to-end behavior.

### B2.9.11 — Resource/thermal validation

Run sustained workloads on real NVIDIA hardware. Record memory, utilization, power, temperature, throttling and deadline misses.

### B2.9.12 — Failure/degraded-mode validation

Inject unavailable backends, timeouts, malformed output, stale inputs and resource stress. Verify bounded degradation.

## Official experiment order

```text
Specification
    ↓
Manifests + evidence schema
    ↓
Mac benchmark runner + CI
    ↓
RT-DETR
    ↓
ESS
    ↓
FoundationStereo
    ↓
Nemotron
    ↓
Cosmos Reason2
    ↓
Combined pipeline
    ↓
Resource / thermal
    ↓
Failure / degraded modes
    ↓
B2.9 evidence review
```

## B2.9 exit criteria

B2.9 is complete only when:

- the benchmark runner passes Mac/CI tests;
- benchmark cases are versioned and reproducible;
- evidence records validate against the schema;
- every available real-model candidate has either measured evidence or an explicit blocked status;
- combined workload behavior has been measured on real hardware when hardware is available;
- failures and degraded modes have evidence;
- no model or hardware selection is declared without the required decision record.

## First experiment

The first real experiment is **RT-DETR object detection** because it provides a bounded specialist task with clear ground truth and straightforward latency/throughput measurements. The first run should establish the benchmark plumbing before attempting the full multimodal stack.
