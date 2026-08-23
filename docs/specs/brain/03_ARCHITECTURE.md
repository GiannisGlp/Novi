# Mac Brain Architecture

## High-level architecture

```text
Camera ──> Perception ──┐
                        ├─> World State ─> Memory ─> Cognition
Microphone ─> Audio ────┘                         │
                                                  ├─> Goals/Planning
                                                  │
                                                  └─> Action Proposal
                                                          │
                                                   Safety/Authorization
                                                          │
                                                   Virtual Body / I/O
                                                          │
                                                   Speaker / simulated action
                                                          │
                                                     new observations
```

## Core components

- Sensor Manager
- Perception Engine
- Audio Engine
- World State Engine
- Memory Engine
- Cognition Engine
- Planner
- Autonomy Engine
- Action Engine
- Orchestrator
- Observability/Evidence subsystem

## Design requirement

Components communicate through versioned contracts. AI providers are dependencies behind capability interfaces rather than being embedded into core state ownership.
