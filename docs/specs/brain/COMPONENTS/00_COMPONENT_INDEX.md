# Mac Brain Components

## Components

1. Sensor Manager
2. Perception Engine
3. Audio Engine
4. World State Engine
5. Memory Engine
6. Cognition Engine
7. Planner
8. Autonomy Engine
9. Action Engine
10. Orchestrator

## Implementation order

```text
Sensor/Audio I/O
 -> model runtime
 -> perception/audio
 -> world state
 -> memory
 -> cognition
 -> goals/planning
 -> autonomy
 -> action/virtual body
 -> orchestration
 -> closed loop
```

Each component must have a contract, tests, failure behavior and observability before it is considered complete.
