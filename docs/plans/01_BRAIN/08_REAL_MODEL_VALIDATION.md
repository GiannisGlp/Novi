# Brain — Real Model Validation

## Objective

Move from adapter-level correctness to empirical validation of actual neural checkpoints and runtimes.

## Environment split

### Mac

Primary development/test environment. Run contract, unit, deterministic integration and evaluation-harness tests through GitHub CI and locally when available. Lightweight local inference is optional and must not be confused with NVIDIA deployment evidence.

### NVIDIA hardware

Run actual accelerator-backed checkpoints and collect deployment evidence. Hardware remains an external validation environment until the platform decision is made.

## Validation sequence

```text
RT-DETR
ESS
FoundationStereo
Nemotron
Cosmos Reason2
      ↓
Individual evidence
      ↓
Pairwise/concurrent workloads
      ↓
Full neural pipeline
```

## Required measurements

- functional correctness;
- task-specific capability;
- p50/p95/p99 latency;
- throughput;
- peak memory;
- accelerator/CPU utilization;
- power;
- temperature;
- deadline misses;
- failure/degraded behavior.

## Dataset discipline

Use versioned, fixed datasets and scenario manifests so candidate models receive identical inputs. Record ground truth where possible.

## Output

Each run produces a provenance-rich evidence package. Conclusions must reference run IDs and must not rely on unrecorded manual observations.

## Exit criteria

Every candidate has sufficient evidence to either pass its intended role, fail it, or remain explicitly unresolved with a documented reason.
