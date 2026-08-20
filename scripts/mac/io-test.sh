#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
source .venv/bin/activate

python - <<'PY'
from pathlib import Path
from MAC_BRAIN.io import MacMicrophone, MacSpeaker

out = Path("mac_test_results/io")
out.mkdir(parents=True, exist_ok=True)

speaker = MacSpeaker()
print("Speaker available:", speaker.available())
if speaker.available():
    speaker.speak("Novi Mac Brain audio output test passed.")

print("Microphone test: recording 2 seconds...")
recording = MacMicrophone().record(2.0, out)
print("Recording:", recording.path)
print("Sample rate:", recording.sample_rate)
print("Channels:", recording.channels)
print("Duration:", recording.duration_s)
print("I/O TEST: PASS")
PY
