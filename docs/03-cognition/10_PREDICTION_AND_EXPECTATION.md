# 10 — Prediction and Expectation

## Status

**DESIGN**

## Purpose

Prediction allows Novi to anticipate likely next states, compare expectations with observations, and use prediction errors as learning signals.

## Prediction Types

- next-event prediction
- location prediction
- routine prediction
- object-state prediction
- user-intent hypothesis
- navigation outcome prediction
- tool outcome prediction
- social interaction expectation

## Prediction Lifecycle

```text
current state
  ↓
retrieve relevant history
  ↓
generate candidate predictions
  ↓
assign confidence/time horizon
  ↓
observe future events
  ↓
compare expected vs actual
  ↓
update prediction reliability
```

## Prediction Is Not Fact

Predictions must remain explicitly marked as predicted. They cannot overwrite observed state merely because the prediction had high confidence.

## User Behavior

Novi may learn patterns such as a person usually arriving home around a certain time, but it must not assume the person will arrive or infer sensitive facts from routine deviations.

## Prediction Error

A prediction error can trigger:

- world-state reevaluation
- curiosity
- memory creation
- routine confidence reduction
- model evaluation
- replanning

## Acceptance Criteria

Prediction is useful only when it improves anticipation or planning without causing overconfident assumptions or unsafe action.
