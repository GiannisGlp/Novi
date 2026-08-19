# Mac Brain Uncertainty and Confidence

## Objective

Prevent uncertain neural or sensor outputs from becoming silently authoritative state.

## Requirements

- distinguish observation from inference;
- preserve model confidence where available;
- track freshness;
- represent missing/unknown information explicitly;
- allow conflicting evidence;
- propagate uncertainty into planning and action policy.

## Example

```text
Person detected: confidence 0.91
Depth: stale
Collision prediction: uncertain
=> autonomy constrained until fresh evidence arrives
```

## Acceptance

Scenarios must demonstrate correct behavior when evidence is incomplete or uncertain.
