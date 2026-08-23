# Mac Brain Virtual Body

## Objective

Provide a robot-like actuator abstraction without physical motors.

## Initial representation

Expose virtual pose, heading, velocity and action state. Render or log state so Brain decisions can be inspected.

## Interface

```text
move_forward
turn_left
turn_right
stop
wait
speak
observe
```

## Future replacement

The virtual actuator interface will later be implemented by real motor/controller drivers without changing Brain semantics.
