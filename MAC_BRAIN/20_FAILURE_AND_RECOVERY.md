# Mac Brain Failure and Recovery

## Required failures

- camera unavailable;
- microphone unavailable;
- speaker unavailable;
- model unavailable;
- model timeout;
- malformed model output;
- stale observations;
- memory failure;
- planning failure;
- action rejection;
- event-loop overload.

## Recovery principle

Failures must be explicit, observable and bounded. The Brain should degrade capability rather than invent certainty or continue an invalid action.

## Recovery examples

```text
Vision unavailable -> conversation remains available if safe
Reasoning timeout -> bounded fallback / wait / report
Speaker unavailable -> text/log output
Virtual action rejected -> stop and record failure
```
