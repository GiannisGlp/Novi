# Mac Brain Model Routing

## Objective

Choose the appropriate AI capability provider for each request without coupling cognition to a specific model.

## Routing examples

```text
object detection -> detector provider
scene interpretation -> multimodal provider
physical reasoning -> physical reasoning provider
speech -> speech provider
```

## Routing rules

- route by capability and constraints;
- enforce deadlines;
- retain provenance;
- allow fallback providers;
- reject unsupported requests explicitly;
- never route around safety/authorization boundaries.

## Future

Hardware-aware routing can later select optimized NVIDIA backends without changing the Brain's semantic interfaces.
