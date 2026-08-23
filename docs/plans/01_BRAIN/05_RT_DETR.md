# Brain — RT-DETR

## Role

Primary object-detection candidate for Novi specialist perception.

## Current state

**ADAPTER IMPLEMENTED / CI VALIDATED. REAL CHECKPOINT VALIDATION OPEN.**

## Test strategy

Mac/CI:
- adapter contract;
- detection schema;
- confidence/validity handling;
- malformed output;
- lifecycle and timeout behavior.

Real hardware:
- controlled detection dataset;
- precision/recall/mAP where ground truth exists;
- false-positive/negative analysis;
- p50/p95/p99 latency;
- FPS;
- memory/utilization;
- power/thermal behavior;
- robustness to lighting, occlusion and motion.

## Comparison policy

RT-DETR is not permanently selected. If it fails Novi requirements, compare alternatives such as YOLO-family or other supported detectors using the same evaluation harness.

## Acceptance

Passes only when detection quality and real-time operational requirements are satisfied for the intended sensor configuration.
