# Mac Brain Hardware Interfaces

## Inputs

- Built-in/external camera.
- Built-in/external microphone.

## Outputs

- Built-in/external speakers.
- Virtual actuator interface for robot-like actions.

## Interface rule

The Brain must not depend directly on macOS device APIs. Use a normalized sensor/output interface so future robot camera, microphone, speaker and actuator drivers can replace Mac adapters.

## Hardware metadata

Capture device identity, resolution/sample rate, timestamps and health state where available.
