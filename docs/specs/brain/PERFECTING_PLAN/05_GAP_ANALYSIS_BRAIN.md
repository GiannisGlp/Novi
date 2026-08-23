# 05 — Gap Analysis: Brain

## Docs (02-novi-brain)
Orchestrator modes; multi-speed System 0/1/2/3; supervisor lifecycle; health/
observability; B2 specialist models behind Protocol boundaries; model runtime; candidate
stack (Nemotron 3 Nano Omni, Cosmos Reason2, GR00T, Cosmos 3).

## Exists today
- BrainSupervisor lifecycle, B1 closed simulated loop, B2 model runtime + provider
  adapters, deterministic CI backends, health/observability, evaluation harness.
- MAC_BRAIN models: object detection (real SSDLite via torchvision), Ollama local LLM,
  router, deliberation, summarizer/narrator, STT (Whisper), recognition seams.

## Delta (what's missing)
- Multi-speed runtime (System 0/1/2/3) with a deterministic safety/reactivity tier that
  never waits on an LLM; current runtime is a single loop.
- Model lifecycle/registry manager (admission, versioning, capability routing) beyond the
  deterministic runtime.
- Real neural evaluation: B2.9+ (real models on actual sensors) is the documented NEXT
  step; only deterministic baselines are validated. Nemotron/Cosmos are thin adapters.
- Spatial/proprioceptive fusion; no TTS synthesis model (uses macOS 'say').
- Orchestrator cognitive modes + interruption/resume + resource modes
  (FULL/DEGRADED/REACTIVE_ONLY/SAFE_MINIMUM) not fully implemented.

## Next action
- Implement the multi-speed runtime split and a deterministic System-0 safety tier that
  gates any action before neural/deliberative stages (roadmap Step 3).
- Keep B2.9 real-model evaluation as a separate gated campaign (needs hardware/models),
  not part of the brain-phase core.

