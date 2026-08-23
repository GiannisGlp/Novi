# Mac Brain Goals and Planning

## Objective

Allow Novi to accept bounded goals, decompose them into steps and track progress without granting unrestricted authority.

## Initial capabilities

- goal creation;
- priority and status;
- preconditions;
- plan generation;
- progress tracking;
- interruption/cancellation;
- replanning when observations change.

## Example

```text
Goal: monitor the room
 -> establish baseline
 -> observe changes
 -> classify meaningful events
 -> report relevant changes
 -> continue until cancelled
```

## Acceptance

Plans must be explicit, interruptible and validated before execution. A reasoning model may propose a plan but cannot directly execute arbitrary commands.
