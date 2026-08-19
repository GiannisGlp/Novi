# Mac Brain Model Runtime

## Objective

Run model providers through one observable, bounded runtime interface.

## Responsibilities

- model loading/lifecycle;
- provider selection;
- request correlation;
- timeout/deadline handling;
- structured output validation;
- provenance;
- health state;
- resource reporting where available.

## Mac requirements

The runtime must support local inference and deterministic test doubles. Remote inference, if used for experimentation, must be explicit and must not become a hidden production dependency.

## Portability

The same semantic provider interface must later support NVIDIA-accelerated backends.
