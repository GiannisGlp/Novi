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
Mac camera
   ↓
MacCamera
   ↓
SpecialistPerception
   ↓
TemporalWorldModel
   ↓
DeterministicCognition
   ↓
BrainSupervisor / safety
   ↓
VirtualBody
```

This first slice deliberately uses the existing deterministic perception backend unless a real Mac-compatible model provider is injected. It therefore proves integration and runtime behavior, not real neural capability.

## Next implementation slice

1. Verify the runtime on the actual Mac.
2. Install only the Mac dependencies required for live camera/audio.
3. Select the first real Mac-compatible neural vision model.
4. Implement it behind the `SpecialistPerception` backend.
5. Add speech-to-text behind the audio provider interface.
6. Add a real Mac-compatible reasoning model behind `MacModelProvider`.
7. Connect real multimodal evidence to cognition.
8. Add memory admission/retrieval to the live loop.
9. Add bounded goals and virtual movement only after the observation-only gate passes.

## Evidence rule

Passing CI tests establishes software correctness for the first slice. The Mac prototype is not accepted until the actual Mac device path is exercised and evidence is collected through `scripts/mac-brain-test.sh` and the MAC_TESTING program.
