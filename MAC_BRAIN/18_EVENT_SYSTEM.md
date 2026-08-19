# Mac Brain Event System

## Objective

Represent asynchronous observations, speech, model results, goals, actions and failures as correlated events.

## Event requirements

Each event should have type, timestamp, correlation/causation identifiers, source, payload/schema version and validity where applicable.

## Initial event classes

- sensor observation;
- perception result;
- audio utterance;
- world-state change;
- memory operation;
- reasoning result;
- goal update;
- plan update;
- action proposal;
- action result;
- failure/degradation;
- system health.

## Rule

Events must be observable and replayable where practical so scenarios can be reproduced.
