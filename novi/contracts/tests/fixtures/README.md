# Contract Fixtures

This directory is the deterministic fixture set for the 18 canonical system contracts.

Each contract requires:

- one minimal valid positive fixture;
- one missing-required-field negative fixture;
- one wrong-type negative fixture;
- one unexpected-property negative fixture.

Fixtures are intentionally minimal and must remain independent of runtime-specific implementations. Domain-specific semantic tests belong to the owning domain.

## Coverage manifest

The required contracts are:

1. EventEnvelope
2. Observation
3. Evidence
4. Entity
5. Relationship
6. WorldStateChange
7. MemoryRecord
8. KnowledgeRecord
9. Goal
10. Plan
11. ActionProposal
12. AuthorizationDecision
13. SafetyDecision
14. ActionExecution
15. ActionOutcome
16. ModelInvocation
17. HardwareHealth
18. DeploymentManifest

A fixture is not evidence of semantic correctness by itself; it is evidence that the executable schema accepts/rejects the expected structural shape.
