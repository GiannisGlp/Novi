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
- `13_GAP_AUDIT_IMPLEMENTATION_PLAN_2026-08-23.md`
- `18_SKILL_SYSTEM_DESIGN.md` — portable SKILL.md packages for Novi (maths/pdf/humanizer): analysis, loader/runner design, governance perimeter; dynamic activation (plan_auto + @skill convention) and novi/skills/README implemented
- `14_BRAIN_EXIT_CONTRACT.md`
- `15_VOICE_CONTINUOUS_DIALOG.md`
- `16_MULTIMODAL_INTEGRATION.md` — voice+perception+recognition wired into the engine via MultimodalRuntime; web handlers, /preview, durable RecognitionStore
- `17_REAL_IO.md` — real camera/mic/speakers live on Mac; listen→Whisper→brain→spoken replies; /preview v2
- `19_COGNITION_MATURATION_PLAN.md` — reasoning/cognition/knowledge/memory maturation: web thin-client (delete `_chat_busy`, `listen()`→`respond()`), initiative×speaking-lease fusion, prediction-error→curiosity, cross-modal verified-tier, perception cadence (`perception_every_n_cycles`). Implemented 2026-08-27.
- `20_DIALOGUE_AND_EVENT_DRIVEN_AUTONOMY_PLAN.md` — dialogue + event-driven autonomy: unified `respond()` for every modality (shipped), proactive autonomous speech from non-text events (SalienceToUtterance / `SurgeSalienceEvaluator`), naturalization guardrails for proactive remarks, multitask concurrency regression, and default model → `qwen3:4b`. IMPLEMENTED 2026-08-29 (wiring gaps GAP-1a/1b/2/3 closed via doc 21).
- `21_GAP_AND_BUG_ANALYSIS_2026-08-28.md` — gap & bug analysis of the uncommitted WIP (model persistence/runtime switch, preview downscale, narrative cache, poll changes) + plan-vs-code drift across 01_BRAIN / 02_PERCEPTION. Phased fix plan executed 2026-08-29: H1–H4/M1–M4/L1–L5, GAP-1b/2/3, ruff clean across `novi/`, CI lint gate widened to the whole package.
- `22_HUMAN_LIKE_SOCIAL_COGNITION_AND_NATURAL_INTERACTION_PLAN.md` — situated social cognition: perception→identity→world→memory→attention→situation→social state→dialogue policy→verbalization loop. Phase 0 (architecture truth map) COMPLETE 2026-08-30; ownership/disposition in `22_SOCIAL_COGNITION_IMPLEMENTATION_STATUS.md`.
- `23_NOVI_LEARNING_AND_TRAINING_PLAN.md` — learning & continuous improvement: trace export→sanitize→validate→dedup→annotate→curated datasets; 30-scenario behavioral benchmark + T1–T8 gates; LoRA SFT/DPO/retrieval/policy pipelines; model registry + rollback; shadow deployment. Steps 01–09/16/18–21/24–26/29 IMPLEMENTED 2026-08-30 (status in `23_LEARNING_AND_TRAINING_IMPLEMENTATION_STATUS.md`); training runs pending dataset volume + framework install.

## Hardware candidates

- Jetson AGX Orin 64GB — candidate.
- Jetson AGX Thor — candidate.

No hardware is selected by this index.

## Development constraint

Brain code and ordinary tests must remain runnable on the user's Mac. NVIDIA-specific execution is isolated behind backend/runtime boundaries and is validated separately on NVIDIA hardware.
