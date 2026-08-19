# Mac Brain Scope and Boundaries

## In scope

Camera/audio ingestion, model runtime, perception, speech recognition/synthesis, world state, memory, cognition, reasoning, goals, planning, bounded autonomy, virtual actuation, closed-loop scenarios, observability, evidence and regression.

## Out of scope for v0.1

Physical actuators, final robot compute, final power system, final sensor suite and hardware-specific acceleration.

## Authority boundaries

Neural inference supplies evidence or proposals. Deterministic world-state validation, autonomy policy, safety constraints and action authorization remain explicit system components.

## Portability requirement

Every Mac-specific capability must have a clearly defined interface so a future Jetson implementation can replace it without redesigning the Brain semantics.
