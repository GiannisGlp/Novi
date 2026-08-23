from __future__ import annotations

import argparse
import json
from pathlib import Path

from brain.b2_perception import SpecialistPerception

from .io import CameraFrame, MacCamera
from .models import NeuralPerceptionBackend, WhisperSTTProvider
from .runtime import MacBrain


class DemoCamera:
    """No-hardware camera used for CI and first runtime smoke tests."""

    def __init__(self) -> None:
        self.sequence = 0

    def read(self) -> CameraFrame:
        self.sequence += 1
        return CameraFrame(
            frame_id=f"demo-{self.sequence}",
            captured_at="2026-08-19T00:00:00Z",
            width=1,
            height=1,
            payload=b"demo-frame",
            metadata={"backend": "deterministic-demo"},
        )

    def close(self) -> None:
        return None


class ImageCamera:
    """Serves a single static image as the camera source.

    Lets the full MacBrain runtime run real neural perception end-to-end
    without requiring camera hardware, which keeps the M1 integration testable
    and reproducible.
    """

    def __init__(self, path: Path) -> None:
        from PIL import Image

        self._path = path
        self._image = Image.open(path).convert("RGB")
        self._sequence = 0

    def read(self) -> CameraFrame:
        self._sequence += 1
        width, height = self._image.size
        return CameraFrame(
            frame_id=f"image-{self._sequence}",
            captured_at="2026-08-19T00:00:00Z",
            width=width,
            height=height,
            payload=self._image.copy(),
            metadata={"backend": "neural-image", "input": str(self._path)},
        )

    def close(self) -> None:
        return None


def _build_reasoning(args) -> object:
    if args.reasoning == "ollama":
        from .models import OllamaReasoningProvider

        return OllamaReasoningProvider(model=args.ollama_model or "qwen3.8")
    if args.reasoning == "router":
        from .models import OllamaReasoningProvider
        from .models.router import ReasoningRouter

        llm = OllamaReasoningProvider(model=args.ollama_model or "qwen3.8")
        return ReasoningRouter(llm=llm, confidence_threshold=args.route_threshold)
    return None  # MacBrain defaults to DeterministicReasoningProvider


def asdict_flat(obj) -> dict:
    """Best-effort dataclass → dict for CLI evidence output."""
    return {k: (v if not hasattr(v, "__dict__") else asdict_flat(v)) for k, v in obj.__dict__.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Novi Mac Brain runtime")
    parser.add_argument("--live-camera", action="store_true", help="use the Mac camera instead of the deterministic camera")
    parser.add_argument("--neural-image", type=Path, default=None, metavar="PATH", help="serve a static image as the camera input (defaults to test-image.png) so real neural perception runs without hardware")
    parser.add_argument("--neural", action="store_true", help="run the real Mac neural object-detection backend instead of the deterministic perception backend")
    parser.add_argument("--device", type=str, default=None, help="torch device for neural inference (default: mps if available, else cpu)")
    parser.add_argument("--cycles", type=int, default=1)
    parser.add_argument("--speak", type=str, default=None)
    parser.add_argument("--listen", type=float, default=0.0, metavar="SECONDS", help="record SECONDS from the microphone and transcribe locally")
    parser.add_argument("--transcribe", type=Path, default=None, metavar="PATH", help="transcribe an existing audio file (no microphone needed)")
    parser.add_argument("--stt-model", type=str, default="base", help="faster-whisper model size for speech-to-text (tiny/base/small)")
    parser.add_argument("--stt-device", type=str, default="cpu", help="device for speech-to-text (cpu or mps)")
    parser.add_argument("--reasoning", choices=["deterministic", "ollama", "router"], default="deterministic", help="reasoning backend: deterministic symbolic, a local LLM via Ollama, or a confidence-based router between them")
    parser.add_argument("--route-threshold", type=float, default=0.6, help="confidence below which the router escalates to the local LLM")
    parser.add_argument("--ollama-model", type=str, default=None, help="Ollama model name for --reasoning ollama/router (default: qwen3.8)")
    parser.add_argument("--goal-target", type=str, default=None, metavar="X,Y", help="adopt a bounded reach goal to (X, Y) in meters before running cycles")
    parser.add_argument("--goal-steps", type=int, default=100, help="max step budget for the reach goal (bounds movement)")
    parser.add_argument("--store", type=str, default=None, metavar="PATH", help="enable durable storage: persist memory and goal history to a SQLite DB at PATH")
    parser.add_argument("--evidence", type=Path, default=Path("MAC_BRAIN_evidence.json"), help="write JSON evidence to this path")
    parser.add_argument("--live", action="store_true", help="run the interactive live demo loop (camera + STT + decide + soul + TTS)")
    parser.add_argument("--rounds", type=int, default=1, help="number of live rounds (default 1; use a large value for a sustained session)")
    parser.add_argument("--live-steps", type=int, default=1, help="vision steps per live round")
    parser.add_argument("--listen-seconds", type=float, default=3.0, help="seconds of microphone audio per live round")
    parser.add_argument("--demo-hear", type=str, default=None, metavar="TEXT", help="inject a deterministic transcript instead of using the microphone (offline/test)")
    parser.add_argument("--say", action="store_true", help="enable text-to-speech via macOS `say` (TTS)")
    parser.add_argument("--say-voice", type=str, default=None, metavar="VOICE", help="macOS `say` voice name for TTS")
    args = parser.parse_args()

    image_source = bool(args.neural_image)
    if args.live_camera and image_source:
        parser.error("--live-camera and --neural-image are mutually exclusive")
    if args.cycles <= 0:
        parser.error("--cycles must be > 0")

    stt = WhisperSTTProvider(model_size=args.stt_model, device=args.stt_device) if (args.transcribe or args.listen or (args.live and args.listen_seconds > 0 and args.demo_hear is None)) else None

    if args.neural_image is not None:
        camera = ImageCamera(args.neural_image)
    elif args.live_camera:
        camera = MacCamera()
    else:
        camera = DemoCamera()

    perception = None
    if args.neural:
        backend = NeuralPerceptionBackend(device=args.device)
        perception = SpecialistPerception(backend=backend)

    brain = MacBrain(camera=camera, perception=perception, stt=stt, reasoning=_build_reasoning(args), store_path=args.store)
    brain.start()
    if args.live:
        from .io import MacSpeaker
        from .live import LiveSession

        speaker = MacSpeaker(voice=args.say_voice) if args.say else None
        session = LiveSession(
            brain=brain,
            rounds=args.rounds,
            per_round_steps=args.live_steps,
            listen_seconds=args.listen_seconds,
            demo_hear=args.demo_hear,
            speaker=speaker,
            on_round=lambda i, r: print(f"[round {i}] saw={r['steps'][-1].get('detections') if r['steps'] else None} heard={r.get('heard')!r} tone={r['tone'].get('tone')} -> {r['reply']}"),
        )
        summary = session.run()
        print(json.dumps(summary, indent=2, sort_keys=True, default=str))
        if args.evidence:
            args.evidence.parent.mkdir(parents=True, exist_ok=True)
            args.evidence.write_text(json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
        return 0
    results = []
    transcriptions = []
    try:
        if args.goal_target:
            tx, ty = (float(v) for v in args.goal_target.split(","))
            from .autonomy import Goal
            brain.set_goal(Goal.reach(tx, ty, max_steps=args.goal_steps))
        for _ in range(args.cycles):
            results.append(brain.step())
        if args.transcribe:
            transcription = brain.stt.transcribe(args.transcribe)
            ingested = brain.ingest_transcript(transcription)
            transcriptions.append({
                "source": "file",
                "path": str(args.transcribe),
                "text": transcription.text,
                "language": transcription.language,
                "confidence": transcription.confidence,
                "provider": transcription.provider,
                "model_id": transcription.model_id,
                "memory_id": ingested["admission"].memory_id,
                "reasoning": ingested["reasoning"],
            })
            print(f"Transcribed: {transcription.text!r} (language={transcription.language}, confidence={transcription.confidence:.2f}) | reasoning={ingested['reasoning']}")
        elif args.listen:
            ingested = brain.listen(args.listen)
            transcription = ingested["transcription"]
            transcriptions.append({
                "source": "microphone",
                "text": transcription.text,
                "language": transcription.language,
                "confidence": transcription.confidence,
                "provider": transcription.provider,
                "model_id": transcription.model_id,
                "memory_id": ingested["admission"].memory_id,
                "reasoning": ingested["reasoning"],
                "audio_path": transcription.audio_path,
            })
            print(f"Heard: {transcription.text!r} (language={transcription.language}, confidence={transcription.confidence:.2f}) | reasoning={ingested['reasoning']}")
        if args.speak:
            brain.speak(args.speak)
    finally:
        brain.stop()

    evidence = {
        "run_id": brain.run_id,
        "mode": "live_camera" if args.live_camera else ("neural_image" if image_source else "deterministic_demo"),
        "perception_backend": "neural" if args.neural else "deterministic",
        "results": results,
        "transcriptions": transcriptions,
        "events": brain.events,
    }
    encoded = json.dumps(evidence, indent=2, sort_keys=True, default=str)
    print(encoded)
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(encoded + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
