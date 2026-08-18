# Contract Compatibility Validation

This directory is reserved for compatibility fixtures and tests for versioned canonical contracts.

## Required checks

- same-version payloads remain valid;
- additive compatible changes follow the registry compatibility policy;
- breaking changes require a major semantic version;
- deprecated versions remain readable for their declared compatibility window;
- schema `$id`, registry version and fixture version agree.

The compatibility suite is a separate gate from structural JSON Schema validation. ARCH-CLOSE-001 remains open until compatibility evidence is executed and recorded.
