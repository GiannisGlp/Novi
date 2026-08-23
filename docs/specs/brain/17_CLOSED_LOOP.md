# Mac Brain Closed Loop

## Objective

Prove that Novi can operate continuously rather than merely answer isolated requests.

## Loop

```text
sensor input
 -> perception/audio
 -> world state
 -> memory/context
 -> cognition
 -> goal/plan
 -> action validation
 -> virtual action
 -> environment/state update
 -> next observation
```

## Initial scenarios

- person enters camera view;
- object appears/disappears;
- spoken goal changes;
- virtual movement changes simulated state;
- uncertainty causes replanning;
- failure causes bounded recovery.

## Acceptance

The loop must preserve state consistency, correlation, bounded latency and safe termination over repeated cycles.
