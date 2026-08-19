# Mac Brain Software Stack

## Selection principles

Prefer the existing Novi stack and repository conventions. Add a dependency only when it provides a clear capability that cannot reasonably be implemented with existing components.

## Required layers

- Python runtime for Brain/model/evaluation components where the repository already uses Python.
- Existing Novi Brain packages and contracts.
- Local process/task orchestration.
- Structured logging and configuration.
- Test/evaluation tooling from `MAC_TESTING/`.
- Optional local service/container dependencies only where justified.

## AI application layer

Use stable provider interfaces for vision, multimodal reasoning, physical reasoning, speech-to-text and text-to-speech.

## Rule

Do not introduce a second application architecture merely for the Mac prototype. The prototype should exercise the same core contracts intended for the eventual robot.
