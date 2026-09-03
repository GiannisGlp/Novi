from __future__ import annotations

import argparse
import json
import sys
import threading
from pathlib import Path

from novi.brain.b2_perception import SpecialistPerception

from .engine import MacBrain, MacBrainConfig
from .io import CameraFrame, MacCamera
from novi.brain.models import NeuralPerceptionBackend, WhisperSTTProvider
from novi.brain.models.ollama_reasoning import DEFAULT_OLLAMA_MODEL


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

        return OllamaReasoningProvider(model=args.ollama_model or DEFAULT_OLLAMA_MODEL)
    if args.reasoning == "router":
        from .models import OllamaReasoningProvider
        from .models.router import ReasoningRouter

        llm = OllamaReasoningProvider(model=args.ollama_model or DEFAULT_OLLAMA_MODEL)
        return ReasoningRouter(llm=llm, confidence_threshold=args.route_threshold)
    return None  # MacBrain defaults to DeterministicReasoningProvider


def _auto_step_loop(brain, *, interval_s: float, stop_event: "threading.Event", stats: dict) -> None:
    """Step the engine until `stop_event` is set (terminal --chat autonomy).

    Mirrors the web auto-step thread so curiosity, initiative, and time-based
    cognition stay alive while the user types. Step errors are counted (first
    kept) — the loop never dies and never raises into the chat session.
    """
    steps = errors = 0
    first_error: str | None = None
    while not stop_event.wait(max(0.05, interval_s)):
        try:
            brain.step()
            steps += 1
        except Exception as exc:  # noqa: BLE001 - counted, first kept, loop survives
            errors += 1
            if first_error is None:
                first_error = f"{type(exc).__name__}: {exc}"
    stats["steps"] = steps
    stats["errors"] = errors
    if first_error is not None:
        stats["first_error"] = first_error


def _neural_without_image_source(args) -> bool:
    """True when --neural runs on the deterministic demo camera (no real pixels).

    The demo camera emits the literal bytes ``b"demo-frame"`` — the neural
    backend honestly detects nothing in those. Real pixels need
    ``--live-camera`` or ``--neural-image PATH``.
    """
    return bool(args.neural) and not args.live_camera and args.neural_image is None


CHAT_HISTORY_TURNS = 10
_CHAT_QUIT_WORDS = frozenset({"quit", "exit"})

# Bundled LoRA adapters (plans 23/24): used when the corresponding flag is
# left empty and the directory exists in the repo checkout.
DIALOGUE_ADAPTER_NAME = "novi-qwen3-8b-dialogue-v1"
EMOTIONAL_ADAPTER_NAME = "novi-qwen3-8b-emotional-v1"


def _default_adapter_dir(name: str) -> str:
    """Repo-bundled adapter dir for `name`, or "" when it isn't checked out."""
    cand = Path(__file__).resolve().parents[2] / "training" / "models" / "adapters" / name
    return str(cand) if cand.is_dir() else ""


def _resolve_adapter(value: str, default_name: str) -> str:
    """Explicit flag value wins; otherwise the bundled adapter dir (if present)."""
    return value or _default_adapter_dir(default_name)


def _brain_config_from_args(args) -> MacBrainConfig:
    """MacBrainConfig carrying the terminal's reply-transport flags.

    Mirrors the web server's trained-transport wiring so the terminal chats
    with the same trained data as the browser UI. Empty adapter flags fall
    back to the repo-bundled plan-23/24 adapters when they are checked out.
    """
    return MacBrainConfig(
        trained_reply_enabled=bool(getattr(args, "trained_reply", False)),
        trained_dialogue_adapter=_resolve_adapter(
            getattr(args, "trained_dialogue_adapter", "") or "", DIALOGUE_ADAPTER_NAME
        ),
        trained_emotional_adapter=_resolve_adapter(
            getattr(args, "trained_emotional_adapter", "") or "", EMOTIONAL_ADAPTER_NAME
        ),
        trained_base_model=getattr(args, "trained_base_model", "") or "Qwen/Qwen3-8B",
        brain_llm_enabled=bool(getattr(args, "brain_llm", False)),
        brain_llm_url=getattr(args, "brain_llm_url", "") or "http://localhost:11434",
        brain_llm_model=getattr(args, "brain_llm_model", "") or DEFAULT_OLLAMA_MODEL,
        brain_llm_server=getattr(args, "brain_llm_server", "") or "ollama",
    )


def run_chat_loop(brain, *, speaker=None, stdin=None, stdout=None, person: str = "") -> int:
    """Interactive terminal chat on the brain's full reply path.

    Each line goes through ``brain.respond()`` with conversation history and
    the brain's default transport (trained adapters when configured) — the
    same reply engine the web UI uses. History is bounded to the last
    ``CHAT_HISTORY_TURNS`` turns. Returns 0 on a clean exit (quit/EOF/Ctrl-C).
    """
    inp = stdin or sys.stdin
    out = stdout or sys.stdout
    history: list[dict[str, str]] = []
    print("Talking to Novi — type and press Enter (quit, or Ctrl-C, to stop).", file=out)
    while True:
        try:
            out.write("you: ")
            out.flush()
            line = inp.readline()
            if not line:
                break  # EOF (Ctrl-D)
        except KeyboardInterrupt:
            out.write("\n")
            break
        text = line.strip()
        if not text:
            continue
        if text.lower() in _CHAT_QUIT_WORDS:
            break
        transport = brain.default_llm_chat() if hasattr(brain, "default_llm_chat") else None
        recent_novi = [h["text"] for h in history if h.get("role") == "novi"][-4:]
        try:
            resp = brain.respond(
                text,
                person=person,
                history=list(history),
                llm_chat=transport,
                last_novi_text=recent_novi[0] if recent_novi else "",
                recent_novi=recent_novi,
                learn=True,
            )
        except KeyboardInterrupt:
            out.write("\n")
            break
        except Exception as exc:  # noqa: BLE001 - a failed turn must not kill the session
            print(f"[novi] reply failed ({exc}); try again.", file=out)
            continue
        reply = ((resp or {}).get("text") or "...").strip()
        print(f"novi: {reply}", file=out)
        history.append({"role": "user", "text": text})
        history.append({"role": "novi", "text": reply})
        if len(history) > 2 * CHAT_HISTORY_TURNS:
            del history[: -2 * CHAT_HISTORY_TURNS]
        if speaker is not None:
            try:
                speaker.speak(reply)
            except Exception as exc:  # noqa: BLE001 - speech failure must not kill the session
                print(f"[novi] speech failed ({exc}).", file=out)
    print("bye.", file=out)
    return 0


def asdict_flat(obj) -> dict:
    """Best-effort dataclass → dict for CLI evidence output."""
    return {k: (v if not hasattr(v, "__dict__") else asdict_flat(v)) for k, v in obj.__dict__.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Novi Mac Brain runtime")
    parser.add_argument("--live-camera", action="store_true", help="use the Mac camera instead of the deterministic camera")
    parser.add_argument("--neural-image", type=Path, default=None, metavar="PATH", help="serve a static image as the camera input (defaults to novi/assets/test-image.png) so real neural perception runs without hardware")
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
    parser.add_argument("--ollama-model", type=str, default=None, help="Ollama model name for --reasoning ollama/router (default: nemotron-3.5-lightning)")
    parser.add_argument("--goal-target", type=str, default=None, metavar="X,Y", help="adopt a bounded reach goal to (X, Y) in meters before running cycles")
    parser.add_argument("--goal-steps", type=int, default=100, help="max step budget for the reach goal (bounds movement)")
    parser.add_argument("--store", type=str, default=None, metavar="PATH", help="durable storage SQLite DB (default: novi/data/novi.db — the single canonical store; pass ':memory:' for ephemeral)")
    parser.add_argument("--evidence", type=Path, default=Path("brain_evidence.json"), help="write JSON evidence to this path")
    parser.add_argument("--chat", action="store_true", help="run the interactive terminal chat (full reply path with history, like the web UI)")
    parser.add_argument("--person", type=str, default="", help="who Novi is talking to (enables person-bound memory/voice matching in --chat)")
    parser.add_argument("--step-interval", type=float, default=2.0, help="engine auto-step cadence in seconds for --chat (curiosity/initiative stay alive while you type)")
    parser.add_argument("--trained-reply", action="store_true", help="reply with the trained dialogue/emotional LoRA adapters (same as the web --trained-reply)")
    parser.add_argument("--trained-dialogue-adapter", type=str, default="", help="path to the trained dialogue LoRA adapter dir (required with --trained-reply)")
    parser.add_argument("--trained-emotional-adapter", type=str, default="", help="path to the trained emotional LoRA adapter dir (optional with --trained-reply)")
    parser.add_argument("--trained-base-model", type=str, default="Qwen/Qwen3-8B", help="base model for the trained adapters (default: Qwen/Qwen3-8B)")
    parser.add_argument("--brain-llm", action="store_true", help="reply through the brain-owned Ollama transport (needs Ollama running locally)")
    parser.add_argument("--brain-llm-url", type=str, default="http://localhost:11434", help="Ollama base URL for --brain-llm")
    parser.add_argument("--brain-llm-model", type=str, default=None, help="Ollama model for --brain-llm (default: the bundled default model)")
    parser.add_argument("--brain-llm-server", choices=["ollama", "openai-compatible"], default="ollama", help="chat wire dialect for --brain-llm (default: ollama; openai-compatible speaks /v1 for llama.cpp/vLLM)")
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
    if args.chat and args.live:
        parser.error("--chat and --live are mutually exclusive")
    if args.trained_reply:
        dialogue = _resolve_adapter(args.trained_dialogue_adapter, DIALOGUE_ADAPTER_NAME)
        emotional = _resolve_adapter(args.trained_emotional_adapter, EMOTIONAL_ADAPTER_NAME)
        if not (dialogue or emotional):
            parser.error(
                "--trained-reply found no adapter: pass --trained-dialogue-adapter DIR "
                "(bundled dirs training/models/adapters/novi-qwen3-8b-{dialogue,emotional}-v1 "
                "are not checked out)"
            )
        print(
            f"[novi] trained adapters: dialogue={dialogue or '-'} emotional={emotional or '-'}",
            file=sys.stderr,
        )
    if _neural_without_image_source(args):
        print(
            "[novi] --neural on the deterministic demo camera sees no real pixels: "
            "add --live-camera or --neural-image PATH for real detections "
            "(continuing with empty detections).",
            file=sys.stderr,
        )

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

    # Canonical single DB (north star: one store for every interface). The
    # default persists to novi/data/novi.db relative to the repo root so CLI,
    # web app, and the future body all share one state; ':memory:' opts out.
    if args.store is None:
        args.store = str(Path(__file__).resolve().parents[2] / "novi" / "data" / "novi.db")
    brain = MacBrain(camera=camera, perception=perception, stt=stt, reasoning=_build_reasoning(args), store_path=args.store, config=_brain_config_from_args(args))
    brain.start()
    if args.chat:
        from .io import MacSpeaker

        if not args.live_camera and args.neural_image is None:
            print(
                "[novi] demo camera: the engine steps while you type, but faces and "
                "live seeing need --live-camera.",
                file=sys.stderr,
            )
        speaker = MacSpeaker(voice=args.say_voice) if args.say else None
        stop_stepping = threading.Event()
        step_stats: dict = {}
        stepper = threading.Thread(
            target=_auto_step_loop,
            kwargs={
                "brain": brain,
                "interval_s": args.step_interval,
                "stop_event": stop_stepping,
                "stats": step_stats,
            },
            daemon=True,
        )
        stepper.start()
        try:
            return run_chat_loop(brain, speaker=speaker, person=args.person)
        finally:
            stop_stepping.set()
            stepper.join(timeout=5.0)
            if step_stats.get("errors"):
                print(
                    f"[novi] auto-step stopped ({step_stats.get('steps', 0)} steps, "
                    f"{step_stats['errors']} errors; first: {step_stats.get('first_error')})",
                    file=sys.stderr,
                )
            brain.stop()
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
