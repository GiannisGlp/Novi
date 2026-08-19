# Mac Brain Audio and Speech

## Objective

Give Novi a real conversational I/O channel while preserving structured audio events and provenance.

## Pipeline

```text
Microphone
 -> voice activity / audio event detection
 -> speech-to-text
 -> normalized utterance
 -> cognition
 -> response
 -> text-to-speech
 -> speakers
```

## Initial capabilities

- speech recognition;
- speaker/output playback;
- interruption handling;
- voice activity detection where practical;
- timestamps and correlation IDs.

## Acceptance direction

Speech failures, silence, noise and unavailable devices must be bounded. Audio I/O must never bypass the Brain's normal cognition and action boundaries.
