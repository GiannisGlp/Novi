# 01 — Brain Implementation Rules

## 1. Architecture is authoritative

Implementation must conform to the canonical Novi Brain architecture and contracts. A convenient implementation must not redefine semantic ownership.

## 2. Neural models are capability providers

A neural model may provide perception, multimodal interpretation, physical reasoning or learned skills. It must not silently become the authority for safety, durable memory semantics, autonomy authorization, motor control or physical actuation.

## 3. Stable interfaces, replaceable models

Model and hardware choices must remain behind stable Novi interfaces. Replacing Nemotron, Cosmos Reason2, RT-DETR, ESS, FoundationStereo, Orin or Thor must not require rewriting the semantic Brain architecture.

## 4. Deterministic CI

Normal GitHub CI must remain reproducible. Large checkpoints, proprietary hardware dependencies and nondeterministic performance experiments must not become ordinary unit-test requirements.

## 5. Real evidence is separate

A real-model result is evidence only when the model version/digest, runtime, hardware, configuration, dataset, benchmark version and measurements are recorded.

## 6. Benchmark before selecting

Neither a model nor a hardware platform is accepted because of parameter count, TOPS, marketing claims or a single successful demo. Selection requires workload-specific evidence.

## 7. Acceptance criteria are explicit

Every implementation unit must have acceptance criteria before the final result is evaluated. Where possible, thresholds are defined before observing benchmark results.

## 8. Failure is a first-class result

Timeouts, model failures, invalid outputs, resource exhaustion, degraded operation and stale data must be tested explicitly. A system that works only when every dependency works is not autonomous-ready.

## 9. No unsafe authority escalation

Inference output is evidence or a candidate proposal. Physical action requires deterministic governance, safety checks and controller ownership.

## 10. Provenance is mandatory

Every production-relevant model result must be traceable to model identity, artifact digest, runtime/backend, configuration, hardware and invocation correlation.

## 11. No hidden hardware decision

Orin 64GB and Thor remain candidates until the formal hardware evaluation gate. Development on one platform must not be described as selection of that platform.

## 12. Keep the repository navigable

Architecture specifications, implementation plans, executable code, tests and experimental evidence should remain separate concerns with explicit cross-references.
