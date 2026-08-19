# Brain Implementation Workstream

The Brain is the first active implementation workstream under the Novi-wide implementation program.

## Scope

This workstream covers model runtime, multimodal understanding, physical reasoning, specialist neural perception, evaluation, real-model validation, evidence, hardware acceleration and Brain integration.

## Existing implementation state

```text
Runtime/contracts                 COMPLETE
Nemotron adapter                  COMPLETE
Real inference infrastructure    COMPLETE
Provenance/evaluation             COMPLETE
Cosmos Reason2 adapter            COMPLETE
Perception boundary               COMPLETE
Perception evaluation             COMPLETE
Specialist model adapters         COMPLETE

Real neural evaluation            NEXT
Hardware benchmarking             LATER
Full neural integration           LATER
B2 acceptance                     LATER
```

## Planned documents

- `01_MODEL_RUNTIME.md`
- `02_NEMOTRON.md`
- `03_COSMOS_REASON2.md`
- `04_SPECIALIST_PERCEPTION.md`
- `05_RT_DETR.md`
- `06_DEPTH_ESS.md`
- `07_DEPTH_FOUNDATIONSTEREO.md`
- `08_REAL_MODEL_VALIDATION.md`
- `09_COMBINED_NEURAL_PIPELINE.md`
- `10_RESOURCE_THERMAL_TESTING.md`
- `11_FAILURE_DEGRADED_MODE_TESTING.md`
- `12_BRAIN_INTEGRATION_GATE.md`

## Hardware candidates

- Jetson AGX Orin 64GB — candidate.
- Jetson AGX Thor — candidate.

No hardware is selected by this index.

## Development constraint

Brain code and ordinary tests must remain runnable on the user's Mac. NVIDIA-specific execution is isolated behind backend/runtime boundaries and is validated separately on NVIDIA hardware.
