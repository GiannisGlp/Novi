# Mac Brain Implementation Status

## First executable slice

**Status: IMPLEMENTED — pending Mac execution.**

### Implemented

- `MAC_BRAIN` Python package;
- Mac camera adapter with optional OpenCV dependency;
- Mac microphone recorder with optional sounddevice dependency;
- Mac speaker adapter using native macOS `say`;
- virtual body with an explicit action allowlist;
- Mac Brain orchestrator composing the existing Novi B1/B2 runtime;
- existing perception/world/cognition/memory components reused rather than duplicated;
- Mac model provider boundary using the existing B2 model runtime and real-inference policy;
- deterministic Mac model provider tests;
- Mac Brain runtime tests;
- CLI launcher;
- Mac Brain test/evidence runner.

## Current execution path

```text
Mac camera / static image / microphone
   ↓
MacCamera / ImageCamera / MacMicrophone
   ↓
SpecialistPerception (neural)   ← optional Whisper STT
   ↓
TemporalWorldModel
   ↓
DeterministicCognition
   ↓
ReasoningProvider (deterministic | Ollama LLM)
   ↓
BrainSupervisor / safety
   ↓
VirtualBody
```

## M1 runtime integration (status: IMPLEMENTED)

Real neural perception now runs **through the live runtime**, not only standalone:

- `NeuralPerceptionBackend` (`MAC_BRAIN/models/neural_backend.py`) bridges `torchvision:ssdlite320_mobilenet_v3_large` output into the canonical `PerceptionBackend` contract.
- CLI paths: `--neural` (real backend), `--neural-image PATH` (headless static image), `--neural --live-camera` (real camera).
- Verified on-device on MPS: `python -m MAC_BRAIN.cli --neural --neural-image test-image.png --cycles 2` → detections `["tv", "laptop"]` flow through perception → world state → cognition → reasoning → authorized virtual action.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/M1-runtime-latest.json`.

The first slice therefore proves integration and runtime behavior with **real neural capability**, not only deterministic fixtures.

## Speech-to-text (status: IMPLEMENTED)

- `WhisperSTTProvider` (`MAC_BRAIN/models/stt.py`) — real offline STT via faster-whisper; one-time model download into the git-ignored `mac_test_results/STT/models` cache.
- `DeterministicSTTProvider` — CI/test fallback.
- `MacBrain.listen(seconds)` records via `MacMicrophone` and transcribes locally.
- CLI: `--transcribe PATH` (headless file transcription) and `--listen SECONDS` (live mic).
- Verified on-device: transcribed a TTS-generated WAV to "Hello world this is a speech to text test." (confidence 0.99).

## Reasoning + real actions (status: IMPLEMENTED)

- `DeterministicReasoningProvider` — bounded symbolic mapping of cognition conclusions to actions (default, CI-safe).
- `LLMReasoningProvider` / `OllamaReasoningProvider` — real local LLM reasoning through `MacModelProvider` + Ollama; the model is offered a fixed action allowlist and its choice is re-validated.
- The hardcoded `inspect` in `MacBrain.step()` is replaced with reasoning-driven action selection. The safety gateway allowlist now matches the virtual-body actions (`inspect/observe/wait/stop/move_forward/turn_left/turn_right`).
- Verified on-device: deterministic mapping yields `wait` for no-salience; the qwen3.8 LLM yields `observe` for the same neural input.

## Cognition + memory integration (status: IMPLEMENTED)

Speech transcripts and neural detections now flow into cognition **and** memory.

- `DeterministicCognition` recognizes a transient `speech` observation → conclusion `human_speech_observed` (speech is surfaced through the current cycle only, not a persistent world entity).
- `MacBrain.ingest_transcript(transcription)` admits the utterance to memory (`memory_type="utterance"`, with provenance + extracted entity refs) and runs a cognition pass over it.
- `MacBrain._admit_detections(...)` admits each detection to memory (`memory_type="perception"`) during `step()`, so detections are now durable evidence, not just transient world state.
- `MacBrain.listen()` / CLI `--listen` and `--transcribe` all feed transcripts through `ingest_transcript` (cognition + memory).
- Verified on-device: transcribing a WAV yields `human_speech_observed` and a retrievable utterance memory record; a neural cycle admits `tv`/`laptop` as perception memory records.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/STT-cognition-memory.json`, `perception-memory.json`.

## Bounded goals + virtual movement (status: IMPLEMENTED)

- `MAC_BRAIN/autonomy.py` — `Goal` (bounded: kind, target, priority, `max_steps`), `GoalState` (`active/completed/failed`), and `BoundedGoalController` that turns a reach goal into multi-cycle `turn_left/turn_right/move_forward` commands. Every cycle counts toward the step budget, so a goal can never move forever: it reaches its target within budget (`completed`) or is forced to `failed`.
- `MacBrain.set_goal(...)` adopts a goal; `step()` lets the active goal drive the action instead of the reactive one-shot action. Emits `goal.adopted` / `goal.status` events.
- CLI: `--goal-target X,Y` + `--goal-steps N` runs a bounded reach goal through the live runtime.
- Verified on-device: reach `(8,0)` moved forward and completed within the 0.5 m threshold; reach `(0,10)` turned to heading 90° then moved forward and completed.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/GOAL-reach.json`, `GOAL-turn.json`.

## Next implementation slice

## Memory recall into the autonomous loop (status: IMPLEMENTED)

- `MacBrain._recall_context(...)` retrieves relevant memories (queried from salient entities + detections) via the memory manager, then passes them as `recall` context into `reasoning.decide(...)`.
- `ReasoningProvider.decide` now accepts a `recall` argument; `DeterministicReasoningProvider` reflects it in the rationale (`recalled N relevant memories`), and `LLMReasoningProvider`/`OllamaReasoningProvider` pass the recalled memories to the model.
- Goal outcomes are admitted to memory (`memory_type="goal_outcome`), so past goal behavior is recallable.
- Emits `memory.recall` events.
- Verified on-device: detecting `alice` recalled 2 relevant memories; reasoning rationale showed `(recalled 2 relevant memories)`; the Ollama LLM path reported `recalled=1`.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/memory-recall.json`.

## Durable storage (Stage-1 per ADR-DATA-001) (status: IMPLEMENTED)

- `MAC_BRAIN/storage.py` — `DurableMemoryStore`, the ADR-DATA-001 candidate baseline: **SQLite, WAL journal mode, local, single-node**, offline. It is a durable persistence layer *below* the memory/autonomy semantics (it does not own cognition, memory, or authorization).
- Persists `MemoryRecord` (memory_type, content, confidence, verification, provenance, entity/event refs, temporal/spatial context) and bounded goal history to disk.
- `MacBrain(store_path=...)` uses the durable store as its memory when a path is given (falls back to the in-memory manager otherwise); `set_goal`/goal-terminal persist goal history; `stop()` closes the store.
- CLI: `--store PATH` enables durable storage.
- Verified on-device: after a full process restart on the same DB, **3 memory records + goal history survived**, `alice said hello` was retrievable, and `PRAGMA journal_mode` = `wal`.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/durability.json` (+ the persisted `novi-state.db`).

## Next implementation slice

1. Benchmark-gate the SQLite candidate (ARCH-CLOSE-003) and validate crash-recovery/fault-injection before ADR-DATA-001 can move from PROPOSED to ADOPTED.
2. Add memory consolidation/decay (expiration, archival) on top of the durable store.

## Evidence rule

Passing CI tests establishes software correctness for the first slice. The Mac prototype is not accepted until the actual Mac device path is exercised and evidence is collected through `scripts/mac-brain-test.sh` and the MAC_TESTING program.
