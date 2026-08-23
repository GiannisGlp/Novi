# Mac Brain AI and Neural Stack

## Candidate capabilities

- RT-DETR for object detection.
- ESS and FoundationStereo for depth where local execution is practical.
- Nemotron for multimodal understanding.
- Cosmos Reason2 for physical/spatiotemporal reasoning.
- Speech-to-text provider for microphone input.
- Text-to-speech provider for speaker output.

## Important distinction

These are candidate capability providers, not irreversible architectural decisions. The Brain must remain functional with deterministic test doubles and should support provider replacement.

## Mac strategy

Use models that can execute locally at useful quality/latency when practical. If a model is too large or hardware-specific, provide a bounded adapter and deterministic/local alternative so the Brain itself remains testable.

## Neural-network principle

Neural networks are used where learned perception/reasoning provides value. Deterministic software remains responsible for contracts, state validation, orchestration, safety boundaries and action authorization.
