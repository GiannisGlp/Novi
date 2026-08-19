# Mac Brain Security and Privacy

## Objective

Keep the prototype safe to run continuously with local camera and microphone input.

## Rules

- default to local processing;
- explicit device permissions;
- no credential exposure to models;
- no arbitrary OS command execution from model output;
- strict action allowlists;
- sensitive recordings are opt-in and local by default;
- logs redact secrets and unnecessary personal data.

## Model boundary

AI-generated text must never be interpreted as an executable shell command or unrestricted operating-system instruction.
