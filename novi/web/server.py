"""Live web server for the Novi Brain.

A dependency-free (Python stdlib only) local HTTP server that owns a running
Brain (MacBrain) and serves a browser UI for live interaction: chat/"hear this" input,
a live state dashboard, action buttons, and a live event log.

The brain runs on a background thread (bounded auto-step loop). All brain
access is serialized through a lock. No external web framework or network
access is required.

Run:
    python -m web.server [--host 127.0.0.1] [--port 8080] [--store PATH]
                         [--auto-step] [--no-auto-step]
"""

from __future__ import annotations

import argparse
import contextlib
import json
import mimetypes
import os
import re
import tempfile
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from novi.brain.audio import AudioFrame
from novi.brain.autonomy import Goal
from novi.brain.b2_perception import SpecialistPerception
from novi.brain.contracts import utc_now
from novi.brain.dialogue import _extract_self_name
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.io import CameraFrame
from novi.brain.models.ollama_reasoning import DEFAULT_OLLAMA_MODEL, DEFAULT_OLLAMA_URL
from novi.brain.models.stt import TranscriptionResult
from novi.perception.detection import DeterministicObjectDetector
from novi.perception.grounding import SpatialInferencePolicy, SpatialPerceptionBackend, SpatialQuery
from novi.perception.grounding_client import GroundingClient
from novi.perception.grounding_rpc import observation_to_dict
from novi.perception.locate_anything import DeterministicLocateAnythingBackend
from novi.perception.pipeline import PerceptionPipeline
from novi.perception.tracking import ObjectTracker
from novi.web.integration_api import IntegrationMixin
from novi.web.runtime_budgets import WebRuntimeBudgets

_ROUTED = Path(__file__).resolve().parent

_UI_DIST = _ROUTED / "ui" / "dist"


def _resolve_ui_asset(rel_path: str) -> Path | None:
    """Resolve a URL path to a file under ui/dist, rejecting path traversal."""
    base = _UI_DIST.resolve()
    target = (base / rel_path).resolve()
    if not target.is_relative_to(base):
        return None
    return target if target.is_file() else None


def _model_choice_path(store_path: str | None) -> Path:
    """Persisted model choice lives next to the canonical DB (never a second DB)."""
    if store_path:  # noqa: SIM108 - if/else is clearer than a ternary here
        base = Path(store_path).resolve().parent
    else:
        base = Path(__file__).resolve().parents[1] / "data"
    return base / "model.json"


def _load_model_choice(store_path: str | None) -> str | None:
    """Read the last UI-selected model; None when unset or unreadable."""
    try:
        path = _model_choice_path(store_path)
        if not path.is_file():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        name = str(data.get("model") or "").strip()
        return name or None
    except Exception:  # noqa: BLE001 - a corrupt choice file degrades to the default
        return None


def _save_model_choice(store_path: str | None, name: str) -> None:
    """Persist the runtime-selected model so it survives restarts.

    Writes atomically (temp file + os.replace) so a crash mid-write never
    leaves a corrupt model.json that silently resets the model (L4).
    """
    try:
        path = _model_choice_path(store_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".model-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump({"model": name}, fh)
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
    except Exception:  # noqa: BLE001 - persistence is best-effort
        pass


class DemoCamera:
    """No-hardware deterministic camera (works without webcam permissions)."""

    def __init__(self) -> None:
        self.sequence = 0

    def read(self) -> CameraFrame:
        self.sequence += 1
        return CameraFrame(
            frame_id=f"web-{self.sequence}",
            captured_at=utc_now(),
            width=1,
            height=1,
            payload=b"web-frame",
            metadata={"backend": "deterministic-web"},
        )

    def close(self) -> None:
        return None


class _GroundingWithFallback:
    """L3: try the local grounding service; fall back to the deterministic
    backend when it is unreachable (Novi's never-crash rule — the web app
    keeps answering scripted results if the model service is down)."""

    def __init__(self, service_url: str | None = None) -> None:
        self._client = GroundingClient(service_url or os.environ.get("NOVI_GROUNDING_URL", "http://127.0.0.1:8721"))
        self._fallback = DeterministicLocateAnythingBackend(scripted={})

    def capabilities(self) -> Any:
        try:
            return self._client.capabilities()
        except ConnectionError:
            return self._fallback.capabilities()

    def ground(self, image: CameraFrame, query: SpatialQuery, policy: SpatialInferencePolicy) -> Any:
        try:
            return self._client.ground(image, query, policy)
        except ConnectionError:
            return self._fallback.ground(image, query, policy)

    def point(self, image: CameraFrame, query: SpatialQuery, policy: SpatialInferencePolicy) -> Any:
        try:
            return self._client.point(image, query, policy)
        except ConnectionError:
            return self._fallback.point(image, query, policy)

    def detect(self, image: CameraFrame, labels: tuple[str, ...], policy: SpatialInferencePolicy) -> Any:
        try:
            return self._client.detect(image, labels, policy)
        except ConnectionError:
            return self._fallback.detect(image, labels, policy)


class NoviWebServer(IntegrationMixin):
    """Owns a MacBrain and drives it from HTTP requests."""

    # Per-PERSON conversation threads (phase 2, multitasking): the web UI pane
    # is the "" thread; recognized in-home people and remote-app users get
    # their own threads so no conversation corrupts another (issue 3). The
    # _chat/_chat_seq names remain as property aliases for the "" thread so all
    # existing persistence/summarization code keeps working unchanged.
    @property
    def _chat(self) -> list[dict[str, Any]]:
        return self._threads[""]

    @_chat.setter
    def _chat(self, value: list[dict[str, Any]]) -> None:
        self._threads[""] = value

    @property
    def _chat_seq(self) -> int:
        return self._seqs[""]

    @_chat_seq.setter
    def _chat_seq(self, value: int) -> None:
        self._seqs[""] = value

    def _chat_thread(self, person: str = "") -> list[dict[str, Any]]:
        """The conversation thread for this person ("" = the web UI pane).

        Thread creation is LRU-bounded by ``budgets.max_chat_threads``: the
        "" pane is pinned and never evicted, the least-recently-used person
        thread (with its seq counter) is dropped. Without this, every
        distinct ``person`` key ever seen (remote-app users, face labels,
        query params) pins up to ``max_chat_turns`` turns with full traces
        forever — a slow unbounded leak in a long-lived server.
        """
        key = (person or "").lower()
        thread = self._threads.get(key)
        if thread is None:
            thread = []
            self._threads[key] = thread
        self._touch_thread(key)
        return thread

    def _touch_thread(self, key: str) -> None:
        """Mark a thread recently used and enforce the thread bound."""
        order = self._thread_order
        if key in order:
            order.remove(key)
        order.append(key)
        self._evict_threads()

    def _evict_threads(self) -> None:
        """Drop LRU person threads (never "") until within budget.

        Only the turn *data* is dropped; the per-key seq counter in
        ``_seqs`` is intentionally retained process-wide. Sequence numbers
        must stay monotonic per key: reusing them after an eviction would
        collide with the client's rendered-seq dedup set and silently drop
        the new generation's turns. One int per person ever seen is
        negligible next to up to ``max_chat_turns`` traced turns.
        """
        limit = max(1, int(self.budgets.max_chat_threads))
        while len(self._threads) > limit:
            victim = next((k for k in self._thread_order if k != ""), None)
            if victim is None:
                return
            self._thread_order.remove(victim)
            self._threads.pop(victim, None)

    def _bump_seq(self, person: str = "") -> int:
        key = (person or "").lower()
        self._seqs[key] = self._seqs.get(key, 0) + 1
        return self._seqs[key]

    def _seq_for(self, person: str = "") -> int:
        return self._seqs.get((person or "").lower(), 0)

    def _last_novi_text(self, person: str = "") -> str:
        return next((c["text"] for c in reversed(self._chat_thread(person)) if c.get("role") == "novi"), "")

    def __init__(
        self,
        *,
        host: str = "127.0.0.1",
        port: int = 8080,
        store_path: str | None = None,
        tick: float = 0.8,
        auto_step: bool = True,
        chat_llm: bool = True,
        trained_reply_enabled: bool = False,
        trained_dialogue_adapter: str = "",
        trained_emotional_adapter: str = "",
        trained_base_model: str = "Qwen/Qwen3-8B",
        say_voice: str | None = None,
        tts_provider: str = "say",
        tts_voice_model: str = "",
        llm_url: str = DEFAULT_OLLAMA_URL,
        llm_model: str | None = None,
        llm_server: str = "ollama",
        camera: str = "demo",
        reasoning: str = "router",
        route_threshold: float = 0.6,
        stt_model: str = "base",
        stt_device: str = "cpu",
        listen_seconds: float = 3.0,
        sleep_every_n_cycles: int = 500,
        available_models: tuple[str, ...] = (
            "nemotron-3.5-lightning",
            "qwen3:8b",
            "qwen3.8:27b",
            "qwen3:4b",
            "novi-trained",  # plan 23: qwen3:8b + Novi dialogue LoRA (ollama adapter)
        ),
        embedder: str = "auto",
        deliberation_rounds: int = 1,
        persist_model: bool = False,
        event_autonomy: bool = True,
        grounding_backend: SpatialPerceptionBackend | None = None,
        budgets: WebRuntimeBudgets | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.store_path = store_path
        self.tick = tick
        self.auto_step = auto_step
        self.sleep_every_n_cycles = max(0, int(sleep_every_n_cycles))
        self.chat_llm = chat_llm
        self.trained_reply_enabled = trained_reply_enabled
        self.trained_dialogue_adapter = trained_dialogue_adapter
        self.trained_emotional_adapter = trained_emotional_adapter
        self.trained_base_model = trained_base_model
        # Mac `say` voice for speak-back (None = system default). The Mac
        # voice is the single voice across terminal and web.
        self.say_voice = say_voice
        # TTS backend for speak-back: "say" (macOS) or "piper" (Jetson body
        # voice; needs --tts-voice-model pointing at a .onnx voice).
        self.tts_provider = tts_provider or "say"
        self.tts_voice_model = tts_voice_model
        self.llm_url = llm_url
        # Chat wire dialect: "ollama" speaks the native /api/* endpoints
        # (tuned think/budget behavior); "openai-compatible" speaks /v1 so
        # llama.cpp, vLLM, and TensorRT-LLM frontends are drop-in backends.
        self.llm_server = llm_server or "ollama"
        self._persist_model = bool(persist_model)
        self.available_models = list(available_models)
        resolved_model = llm_model
        if not resolved_model and self._persist_model:
            resolved_model = _load_model_choice(store_path)
        resolved_model = resolved_model or DEFAULT_OLLAMA_MODEL
        if resolved_model not in self.available_models and resolved_model != DEFAULT_OLLAMA_MODEL:
            self.available_models.insert(0, resolved_model)
        self.llm_model = resolved_model
        self.camera_mode = camera
        self.reasoning_mode = reasoning
        self.route_threshold = route_threshold
        self.event_autonomy = bool(event_autonomy)
        # L3: language grounding through the same capability every surface
        # uses. Default: the local grounding service with a deterministic
        # fallback (never-crash rule); tests inject a backend directly.
        self.grounding_backend = grounding_backend if grounding_backend is not None else _GroundingWithFallback()
        self._grounding_pipeline: PerceptionPipeline | None = None
        self.stt_model = stt_model
        self.stt_device = stt_device
        self.listen_seconds = listen_seconds
        self.embedder_mode = embedder
        self.deliberation_rounds = max(1, int(deliberation_rounds))
        # Live LLM components, held so switch_model can re-point them all at one
        # model (single source of truth for the chat/cognition stack).
        self._reasoning_provider: Any | None = None
        self._narrator_inner: Any | None = None
        self._summarizer_inner: Any | None = None
        self._conversation_summarizer_inner: Any | None = None
        # fast_* wrappers expose .model/.base_url for introspection; they are
        # refreshed by _apply_model_to_components so switch_model stays honest (L3).
        self._fast_narrator: Any | None = None
        self._fast_summarizer: Any | None = None
        self._fast_conv_summarizer: Any | None = None
        # Episodic narrative cache: regenerated only when new episodic memories
        # arrive, so the 2s /api/state poll never triggers an LLM narrator call.
        self._narrative_cache: list[str] | None = None
        self._narrative_sig: tuple[Any, ...] | None = None
        # Latch so a cache miss regenerates on a background thread (M3): the
        # engine step + the next state poll never double-run the narrator.
        self._narrative_regenerating = False
        self._llm_available: bool | None = None
        self._llm_probed_at: float = 0.0
        # How often to re-probe Ollama availability so a server that started
        # before the LLM was ready can reconnect without a restart.
        self._llm_probe_ttl = 3.0
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._brain_running = False
        # deduplication: track the last sent text + timestamp to reject
        # duplicate sends (double-click, Enter key race) within a short window.
        self._last_sent_text: str = ""
        self._last_sent_time: float = 0.0
        self._dedup_window_seconds: float = 15.0
        # Event pipeline budgets (plan 02, Phase 6). EventBus is the
        # authoritative bounded history; the compat list is a bounded window;
        # this server log is a bounded presentation cache keyed by server seq.
        # Explicit budgets win; otherwise NOVI_WEB_* env overrides apply.
        self.budgets: WebRuntimeBudgets = budgets or WebRuntimeBudgets.from_env()
        # Cursor into the brain's compat event `sequence` (EventBus sequence).
        # Sequence-based (not index-based) so source-side trimming can never
        # cause skips or duplicates.
        self._seen_seq = 0
        self._seq = 0
        self._log: list[dict[str, Any]] = []
        # Process-unique epoch so clients can detect a server restart (which
        # resets server seqs) and resync instead of dropping everything below
        # their stale cursor.
        self._epoch = os.urandom(8).hex()
        # SSE connection accounting (bounded clients, plan 02 §12.3).
        self._sse_clients = 0
        self._sse_lock = threading.Lock()
        # Request budget (plan 02 §12.4): at most max_concurrent_requests
        # handlers run at once; the HTTP layer 503s excess immediately.
        self.request_semaphore = threading.Semaphore(self.budgets.max_concurrent_requests)
        # chat conversation (user <-> Novi reasoning responses), per person
        self._threads: dict[str, list[dict[str, Any]]] = {"": []}
        self._seqs: dict[str, int] = {"": 0}
        # LRU order of thread keys (most-recent last); "" is pinned at all
        # times and never evicted. Bounds _threads under max_chat_threads.
        self._thread_order: list[str] = [""]
        # Length at the last chat summarization; used to gate summarization so the
        # LLM summarizer doesn't run on every single append past the threshold.
        self._last_summarized_len: int | None = None
        self.brain = self._build_brain()
        self.conversation_summarizer = self._build_conversation_summarizer()
        self._load_chat_history()
        self._last_step: dict[str, Any] | None = None
        # Multimodal + recognition integration (doc 16) — lazy so tests and
        # minimal deployments can run without it.
        try:
            self._integration_init()
        except Exception:  # noqa: BLE001 - integration is additive, never fatal
            self.mm_runtime = None  # type: ignore[assignment]
            self.mm_store = None  # type: ignore[assignment]
            self.mm_camera_feed = None
            self.mm_last_frame_b64 = None
        # Auto-enable real I/O when --camera real so preview + Listen + speak-back
        # just work without a manual POST /api/real/enable. Honest degradation
        # if hardware/deps are absent (never fatal for demo/CI).
        if getattr(self, "camera_mode", "demo") == "real" and getattr(self, "mm_runtime", None) is not None:
            with contextlib.suppress(Exception):
                self.real_enable(camera=True, mic=True, speaker=True)

    def _build_conversation_summarizer(self) -> Any:
        """LLM conversation summarizer when Ollama is available."""
        from novi.brain.models.conversation_summarizer import ConversationSummarizer

        inner = ConversationSummarizer(model=self.llm_model, base_url=self.llm_url)
        self._conversation_summarizer_inner = inner

        def fast_conv_summarizer(turns):  # type: ignore[no-untyped-def]
            if not self.chat_llm or not self._llm_up():
                return None
            from novi.brain.models.ollama_reasoning import disable_thinking_for

            if not disable_thinking_for(self.llm_model):
                return None  # heavy-thinking tier: deterministic summary
            return inner(turns)

        fast_conv_summarizer.model = inner.model  # type: ignore[attr-defined]
        fast_conv_summarizer.base_url = inner.base_url  # type: ignore[attr-defined]
        self._fast_conv_summarizer = fast_conv_summarizer
        return fast_conv_summarizer

    def _load_chat_history(self) -> None:
        """Restore the chat thread from the durable store on restart (conversation persistence)."""
        store = getattr(self.brain, "memory", None)
        if store is None or not hasattr(store, "load_chat"):
            return
        try:
            rows = store.load_chat()
        except Exception:  # noqa: BLE001 - chat restore is best-effort
            return
        if rows:
            self._chat = rows
            self._chat_seq = max((int(r.get("seq", 0)) for r in rows), default=0)

    # ---- brain construction (real sensing / reasoning router) ----
    def _build_brain(self) -> MacBrain:
        if self.camera_mode == "real":
            from novi.brain.io import MacCamera

            cam: Any = MacCamera()
        else:
            cam = DemoCamera()
        stt = self._build_stt() if self.camera_mode == "real" else None
        reasoning = self._build_reasoning()
        summary_consolidator = self._build_summary_consolidator()
        narrator = self._build_narrator()
        perception = self._build_perception() if self.camera_mode == "real" else None
        speaker_id = self._build_speaker_id() if self.camera_mode == "real" else None
        return MacBrain(
            camera=cam,
            stt=stt,
            reasoning=reasoning,
            store_path=self.store_path,
            embedder=self.embedder_mode,
            summary_consolidator=summary_consolidator,
            narrator=narrator,
            perception=perception,
            speaker_id=speaker_id,
            config=MacBrainConfig(
                initiative_enabled=True,
                event_autonomy_enabled=self.event_autonomy,
                sleep_every_n_cycles=self.sleep_every_n_cycles,
                trained_reply_enabled=self.trained_reply_enabled,
                trained_dialogue_adapter=self.trained_dialogue_adapter,
                trained_emotional_adapter=self.trained_emotional_adapter,
                trained_base_model=self.trained_base_model,
            ),
        )

    def _build_perception(self) -> Any:
        """Real neural perception backend for the ENGINE's own step() vision.

        Without this the engine's SpecialistPerception defaults to the
        deterministic contract backend (detects nothing), so the brain never
        'sees' the person even with a live webcam. NeuralPerceptionBackend
        bridges SSDLite-on-MPS into the canonical PerceptionBackend boundary.
        """
        try:
            from novi.brain.models.neural_backend import NeuralPerceptionBackend

            backend = NeuralPerceptionBackend(confidence_threshold=0.45)
            self.perception_backend = f"ssdlite:{backend.detector.device}"
            return SpecialistPerception(backend=backend)
        except Exception:  # noqa: BLE001 - neural deps optional, honest degrade
            self.perception_backend = "deterministic"
            return None

    def _build_speaker_id(self) -> Any:
        """Voiceprint speaker identification wired into the engine (rule 6).

        Adapts RealSpeakerRecognizer to the engine's speaker_id contract
        (identify(audio_features={"audio_path": ...}) -> {name, confidence}).
        On each brain.listen() the engine calls _identify_speaker, so an
        enrolled voice becomes dialogue-grade identity evidence automatically.
        """
        try:
            from novi.integration.real_io_voice import RealSpeakerRecognizer
            from novi.integration.recognition_store import RecognitionStore

            store = RecognitionStore(Path(self.store_path)) if self.store_path else RecognitionStore(":memory:")
            recognizer = RealSpeakerRecognizer(store=store)

            class _EngineSpeakerID:
                """Contract adapter: engine calls identify(audio_features); we match the wav."""

                @staticmethod
                def identify(audio_features: dict):
                    wav = str((audio_features or {}).get("audio_path", ""))
                    if not wav:
                        return None
                    m = recognizer.match(wav)
                    if m is None:
                        return None

                    class _R:
                        name: str = ""
                        confidence: float = 0.0

                    r = _R()
                    r.name = m.label
                    r.confidence = float(m.similarity)
                    return r

            return _EngineSpeakerID()
        except Exception:  # noqa: BLE001 - voice id optional
            return None

    def _build_narrator(self) -> Any:
        """LLM narrator for episodic "what happened" recaps when Ollama is available."""
        from novi.brain.models.narrator import LLMNarrator

        inner = LLMNarrator(model=self.llm_model, base_url=self.llm_url)
        self._narrator_inner = inner

        def fast_narrator(episodes):  # type: ignore[no-untyped-def]
            # When chat LLM is disabled or Ollama is offline, fail fast instead of 5s LLM timeout.
            if not self.chat_llm or not self._llm_up():
                return None
            from novi.brain.models.ollama_reasoning import disable_thinking_for

            if not disable_thinking_for(self.llm_model):
                # Heavy-thinking tier (~3 tok/s): never serve 5s-timeout
                # background calls — the brain uses the deterministic recap.
                return None
            return inner(episodes)

        # Attach inner for introspection, but expose fast wrapper as callable
        fast_narrator.model = inner.model  # type: ignore[attr-defined]
        fast_narrator.base_url = inner.base_url  # type: ignore[attr-defined]
        self._fast_narrator = fast_narrator
        return fast_narrator

    def _build_summary_consolidator(self) -> Any:
        """SummaryConsolidator with an LLM summarizer when Ollama is available."""
        from novi.brain.consolidation import SummaryConsolidator
        from novi.brain.models.summarizer import LLMSummarizer

        inner = LLMSummarizer(model=self.llm_model, base_url=self.llm_url)
        self._summarizer_inner = inner

        def fast_summarizer(entity, records):  # type: ignore[no-untyped-def]
            if not self.chat_llm or not self._llm_up():
                return None
            from novi.brain.models.ollama_reasoning import disable_thinking_for

            if not disable_thinking_for(self.llm_model):
                return None  # heavy-thinking tier: deterministic summary
            return inner(entity, records)

        fast_summarizer.model = inner.model  # type: ignore[attr-defined]
        fast_summarizer.base_url = inner.base_url  # type: ignore[attr-defined]
        self._fast_summarizer = fast_summarizer
        return SummaryConsolidator(None, summarizer=fast_summarizer)

    def _build_reasoning(self) -> Any:
        mode = self.reasoning_mode
        if mode in ("ollama", "router"):
            from novi.brain.models import DeliberativeLLMReasoningProvider

            # Single-round deliberation for the web path: one /api/generate call
            # (30s cap) instead of the multi-round critique loop, so a chat turn
            # never blocks the server for minutes. max_tokens=300 with thinking
            # disabled on fast tiers: the analysis/options/decision JSON fits in
            # ~220 tokens; 600 let the model ramble at ~30 tok/s (~20s/turn).
            llm = DeliberativeLLMReasoningProvider(
                model=self.llm_model,
                base_url=self.llm_url,
                max_rounds=self.deliberation_rounds,
                max_tokens=300,
                timeout=30,
            )
            if mode == "router":
                from novi.brain.models.router import ReasoningRouter

                self._reasoning_provider = ReasoningRouter(llm=llm, confidence_threshold=self.route_threshold)
                return self._reasoning_provider
            self._reasoning_provider = llm
            return llm
        return None  # MacBrain defaults to DeterministicReasoningProvider

    def _build_stt(self) -> Any:
        try:
            from novi.brain.models.stt import WhisperSTTProvider

            return WhisperSTTProvider(model_size=self.stt_model, device=self.stt_device)
        except Exception:  # noqa: BLE001 - STT optional; brain falls back to deterministic
            return None

    # ---- lifecycle (plan 02, Phase 7: owned, idempotent start/stop) ----
    def start(self) -> None:
        """Start the brain loop. Safe to call twice: no second thread/loop."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        if not self._brain_running:
            self.brain.start()
            self._brain_running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="novi-brain-loop")
        self._thread.start()

    def stop(self) -> None:
        """Stop the brain loop. Safe to call twice or without start()."""
        self._stop.set()
        thread, self._thread = self._thread, None
        if thread is not None:
            thread.join(timeout=2.0)
        if self._brain_running:
            with self._lock, contextlib.suppress(Exception):
                self.brain.stop()
            self._brain_running = False

    def _loop(self) -> None:
        while not self._stop.wait(self.tick):
            if self.auto_step:
                # The loop keeps ticking continuously (SCENARIO-V1). A slow LLM
                # reply no longer freezes it: the brain's speaking lease gates
                # spontaneous initiative, so a concurrent step cannot fire a
                # duplicate remark while a reply is being composed.
                try:
                    with self._lock:
                        self._last_step = self.brain.step()
                except Exception as exc:  # noqa: BLE001 - keep the loop alive
                    self._record_event({"event_type": "web.error", "cycle": -1, "message": str(exc)})
            else:
                self._drain()

    # ---- brain operations (all under lock) ----
    def _record_event(self, event: dict[str, Any]) -> None:
        self._seq += 1
        self._log.append({"seq": self._seq, "ts": time.time(), "event": event})
        if len(self._log) > self.budgets.max_events:
            self._log = self._log[-self.budgets.max_events :]

    def _drain(self) -> None:
        """Pull newly emitted brain events into the bounded event log.

        Ownership (plan 02, Phase 2): the EventBus is the authoritative
        bounded history; the compat list is only a bounded window. This is a
        consumer/cursor operation — NOT the mechanism that prevents OOM (the
        brain bounds itself at the source). The cursor is the compat
        ``sequence`` so trimming at the source can never cause a skip or a
        duplicate, no matter how far behind this consumer falls.
        """
        with self._lock:
            compat = self.brain.events
            new = [ev for ev in compat if int(ev.get("sequence", 0) or 0) > self._seen_seq]
            if new:
                self._seen_seq = max(int(ev.get("sequence", 0) or 0) for ev in new)
            for ev in new:
                self._seq += 1
                self._log.append({"seq": self._seq, "ts": time.time(), "event": ev})
                if ev.get("event_type") == "speech.initiated":
                    # Surface Novi's unprompted remark as a conversation turn so
                    # the chat UI shows it (rule 5). Appended directly (no LLM
                    # summarizer here) to avoid a model call under the runtime lock.
                    p = ev.get("payload", {})
                    self._chat_seq += 1
                    self._chat.append(
                        {
                            "seq": self._chat_seq,
                            "role": "novi",
                            "text": str(p.get("text", "")),
                            "trace": {
                                "action": "initiate",
                                "route": "initiative",
                                "conclusion": str(p.get("text", "")),
                                "rationale": str(p.get("reason", "")),
                                "cycle": ev.get("cycle"),
                            },
                            "cycle": ev.get("cycle"),
                            "llm": False,
                        }
                    )
                    if len(self._chat) > self.budgets.max_chat_turns:
                        self._chat = self._chat[-self.budgets.max_chat_turns :]
                    self._persist_chat()
            if len(self._log) > self.budgets.max_events:
                self._log = self._log[-self.budgets.max_events :]
            # No legacy trim of brain.events here: the brain bounds its compat
            # window at the source (plan 02 PR1). This drain is purely a cursor.

    def hear(self, text: str, confidence: float = 0.9) -> dict[str, Any]:
        # Unified input path (north star §4.2): submit through the brain's bus;
        # the next cognition cycle ingests it like any other source. The reply
        # composition still happens here (synchronous HTTP contract) via
        # respond() with the LLM outside the lock (§4.4).
        self.brain.submit("web", "chat", {"text": self._clean_chat_text(text)})
        with self._lock:
            r = self.brain.ingest_transcript(
                TranscriptionResult(
                    text=self._clean_chat_text(text),
                    language="en",
                    confidence=confidence,
                    audio_path="",
                    provider="web",
                    model_id="web",
                )
            )
        adm = r["admission"]
        return {
            "accepted": adm.accepted,
            "memory_id": adm.memory_id,
            "reasoning": r["reasoning"],
            "confidence": r["confidence"],
        }

    def _clean_chat_text(self, text: str) -> str:
        """Strip the '[heard] ' display marker before text reaches the LLM/history,
        so Novi doesn't think the user addressed 'the system' or a 'heard' marker."""
        return re.sub(r"^\s*\[heard\]\s*", "", text)

    def _face_person(self) -> str:
        """The currently-seen NAMED person, or "" when nobody identifiable.

        Face-bound identity: when the camera sees an enrolled face, Novi knows
        who it is talking to without being told. Placeholders ("new-person-N")
        and anonymous sightings ("someone") do not count — only a real name.
        """
        runtime = getattr(self, "mm_runtime", None)
        name = (getattr(runtime, "current_person", None) or "") if runtime is not None else ""
        name = str(name).strip()
        if not name or name == "someone" or name.startswith("new-person-"):
            return ""
        return name

    #: Turns of conversation history supplied to the LLM per reply. 10 turns ×
    #: 400 chars (~1K tokens of prefill) sustains multi-turn coherence without
    #: unbounded prompt growth. Still a hard cap, not a full log.
    HISTORY_TURNS = 10
    HISTORY_CHARS_PER_TURN = 400

    def _build_history(self, limit: int = HISTORY_TURNS, person: str = "") -> list[dict[str, Any]]:
        # Capped turns AND per-turn text: history rides inside the LLM prompt
        # (user_payload.conversation_so_far), so unbounded turns inflate prefill
        # time on every reply.
        thread = self._chat_thread(person)
        return [
            {"role": c["role"], "text": self._clean_chat_text(c["text"])[: self.HISTORY_CHARS_PER_TURN]}
            for c in thread[-limit:]
        ]

    def _recent_novi(self, limit: int = 4, person: str = "") -> list[str]:
        thread = self._chat_thread(person)
        return [self._clean_chat_text(c["text"]) for c in reversed(thread) if c.get("role") == "novi"][:limit]

    def _bind_introduced_name(self, text: str) -> None:
        """Bind a self-introduction to a placeholder person (conversational naming).

        When the current camera-tracked person is an auto-enrolled placeholder
        (``new-person-N``) and the user says "I'm <name>", the brain's own reply
        already acknowledges the introduction; this renames the placeholder in the
        durable + in-memory identity records so future frames resolve the real name.
        """
        runtime = getattr(self, "mm_runtime", None)
        if runtime is None:
            return
        name = _extract_self_name(text)
        if not name:
            return
        current = runtime.current_person
        if not current.startswith("new-person-"):
            return
        # naming is best-effort, never blocks a reply
        with contextlib.suppress(Exception):
            runtime.name_person(current, name.title())

    def chat_send(self, text: str, confidence: float = 0.9, person: str = "") -> dict[str, Any]:
        """Hear the user message, let the brain decide, and append a chat turn.

        ``person`` is the optional identity of the sender (the remote-app user,
        or the recognized in-home person). It scopes the speaking lease so one
        person never gets two simultaneous streams while others stay free
        (phase 2 multitasking).
        """
        # Strip the '[heard] ' STT display marker off the incoming message before
        # detection/compose_reply, so a greeting like '[heard] Hello.' is recognised
        # as a greeting (the raw prefix would defeat the greeting/clarification
        # detectors and let the LLM mis-handle it).
        text = self._clean_chat_text(text)

        # Deduplication: reject duplicate sends within the dedup window.
        # This prevents double-sends from double-clicks or Enter key races.
        import time as _time

        now = _time.time()
        with self._lock:
            if text == self._last_sent_text and (now - self._last_sent_time) < self._dedup_window_seconds:
                # Return the last novi if available; otherwise a bare dedup marker.
                # Do not create new rows — the previous turn is still in-flight.
                for c in reversed(self._chat_thread(person)):
                    if c.get("role") == "novi":
                        return {
                            "novi": c,
                            "accepted": True,
                            "memory_id": None,
                            "llm": c.get("llm", False),
                            "deduplicated": True,
                            "after": self._seq_for(person),
                        }
                return {"accepted": False, "deduplicated": True, "after": self._seq_for(person)}
            self._last_sent_text = text
            self._last_sent_time = now

        # Unified input path (north star §4.2/4.4): submit through the bus so
        # this message is one input among many (a home-voice turn may arrive in
        # the same cycle), then ingest + step under a short lock, and compose
        # the reply with the LLM OUTSIDE the lock.
        self.brain.submit("web", "chat", {"text": text})
        # Hold the brain's speaking lease for THIS addressee while composing so
        # a concurrent step cannot fire a duplicate initiative at the same
        # person (replaces the old _chat_busy loop-freeze; the loop keeps
        # ticking — SCENARIO-V1; other people stay free — phase 2).
        # Face-bound identity comes before text resolution: a recognized face
        # tells Novi who it is talking to without being told.
        addressee = person or self._face_person() or self.brain.resolve_addressee(text)
        self.brain.acquire_speaking_lease(addressee)
        try:
            with self._lock:
                r = self.brain.ingest_transcript(
                    TranscriptionResult(
                        text=text, language="en", confidence=confidence, audio_path="", provider="web", model_id="web"
                    )
                )
                adm = r["admission"]
                conclusion = r["reasoning"]
                heard_conf = r["confidence"]
                step = self.brain.step()
                trace = dict(self.brain._last_reasoning_trace)

            # The brain owns the reply (docs/06-soul/07 §2): it renders a natural
            # communicative act grounded in soul/relationship/identity/memory and
            # enforces the no-assistant/no-repetition rules. The web layer only
            # supplies conversation history and the LLM transport; the brain's
            # respond() detects the addressee, learns from the message, and
            # composes the reply (or the deterministic fallback) in one call.
            history = self._build_history(person=person)
            recent_novi = self._recent_novi(4, person)
            last_novi = self._last_novi_text(person)
            transport = self._reply_transport()
            resp = self.brain.respond(
                text,
                person=addressee,
                history=history,
                llm_chat=transport,
                last_novi_text=last_novi,
                recent_novi=recent_novi,
                learn=True,
            )
            self._bind_introduced_name(text)
            novi_text = resp.get("text")
            reply_source = resp.get("reply_source", "dialogue")
            llm = reply_source == "dialogue"
            # The trace always records the real cognition conclusion; only the
            # spoken text is rendered naturally. For a dialogue reply the conclusion
            # is the reply; for a deterministic fallback it stays the cognition label.
            trace["conclusion"] = novi_text if llm else conclusion
            trace["action"] = "respond"
            trace["rationale"] = (
                resp.get("reason") or "Natural reply grounded in recalled knowledge, relationships and self-state."
            )
            if llm:
                trace["route"] = f"ollama:{self.llm_model}"
                trace["route_reason"] = "local LLM"
                trace["confidence"] = 0.85
            else:
                trace["route"] = "deterministic"
                # Honest label: transport existed but the reply was rejected/
                # empty (or a designed fallback path) vs. no transport at all.
                designed = (resp.get("grounding") or {}).get("route")
                trace["route_reason"] = designed or (
                    "llm_reply_rejected" if transport is not None else "no_llm_transport"
                )
                self._note_transport_error(trace, transport)
                trace["confidence"] = heard_conf
            novi = {"role": "novi", "text": novi_text, "trace": trace, "cycle": step.get("cycle"), "llm": llm}
            self._append_chat({"role": "user", "text": text}, person)
            self._append_chat(novi, person)
            spoken = self._speak_back(novi_text)
            return {"novi": novi, "accepted": bool(adm.accepted), "memory_id": adm.memory_id, "llm": llm, "spoken": spoken}
        finally:
            self.brain.release_speaking_lease(addressee)

    def listen(self, seconds: float | None = None) -> dict[str, Any]:
        """Record from the microphone, transcribe locally, and respond in chat.

        Requires real sensing (the server must be started with the real camera/
        STT so the brain has a non-deterministic STT provider).

        The mic recording + STT run OUTSIDE the shared brain lock: audio capture
        can take seconds (and PortAudio init can stall on device changes), and
        holding the lock here would freeze the auto-step loop and every HTTP
        endpoint. Only transcript ingestion takes the lock.
        """
        seconds = seconds or self.listen_seconds
        if self.camera_mode != "real":
            raise RuntimeError("real speech-to-text is not enabled (start with --camera real)")
        stt = getattr(self.brain, "stt", None)
        if stt is None or not hasattr(stt, "transcribe"):
            raise RuntimeError("real speech-to-text is not enabled (start with --camera real)")
        # Record + transcribe with NO lock held (audio hardware is its own resource).
        result = self.brain.listen(seconds)
        text = result["transcription"].text
        if not text.strip():
            return {"heard": "", "accepted": True, "novi": None, "llm": False}
        with self._lock:
            step = self.brain.step()
            trace = dict(self.brain._last_reasoning_trace)
        # Hold the speaking lease for THIS addressee while composing (replaces
        # _chat_busy loop-freeze). The recognized in-home person scopes the
        # lease: their voice turn gates their own stream only (phase 2).
        # Placeholders/anonymous sightings do not count (see _face_person).
        addressee = self._face_person() or self.brain.resolve_addressee(text)
        self.brain.acquire_speaking_lease(addressee)
        try:
            # Brain-owned reply orchestration (north-star R1/R3): the brain
            # resolves the addressee, learns from the message, and composes the
            # natural reply (or the deterministic fallback) in one call. The web
            # layer only supplies conversation history and the LLM transport.
            # History comes from the shared device thread (""): typed turns and
            # voice mirrors all live there, so voice replies see the same
            # conversation the user sees. The addressee scopes the lease and
            # the brain's relationship context, not the visible log.
            history = self._build_history()
            recent_novi = self._recent_novi(4)
            last_novi = self._last_novi_text()
            transport = self._reply_transport()
            resp = self.brain.respond(
                text,
                person=addressee,
                history=history,
                llm_chat=transport,
                last_novi_text=last_novi,
                recent_novi=recent_novi,
                learn=True,
            )
            self._bind_introduced_name(text)
            novi_text = resp.get("text")
            reply_source = resp.get("reply_source", "dialogue")
            llm = reply_source == "dialogue"
            # The trace always records the real cognition conclusion; only the
            # spoken text is rendered naturally.
            trace["conclusion"] = novi_text if llm else result["reasoning"]
            trace["action"] = "respond"
            trace["rationale"] = (
                resp.get("reason") or "Natural reply grounded in recalled knowledge, relationships and self-state."
            )
            if llm:
                trace["route"] = f"ollama:{self.llm_model}"
                trace["route_reason"] = "local LLM"
                trace["confidence"] = 0.85
            else:
                trace["route"] = "deterministic"
                designed = (resp.get("grounding") or {}).get("route")
                trace["route_reason"] = designed or (
                    "llm_reply_rejected" if transport is not None else "no_llm_transport"
                )
                self._note_transport_error(trace, transport)
                trace["confidence"] = result.get("confidence", 0.8)
            novi = {"role": "novi", "text": novi_text, "trace": trace, "cycle": step.get("cycle"), "llm": llm}
            self._append_chat({"role": "user", "text": f"[heard] {text}"})
            self._append_chat(novi)
            spoken = self._speak_back(novi_text)
            return {"heard": text, "accepted": True, "novi": novi, "llm": llm, "spoken": spoken}
        finally:
            self.brain.release_speaking_lease(addressee)

    def _llm_up(self) -> bool:
        # Re-probe when the cached result is stale so a server that started
        # before Ollama was reachable (or when a model was still loading)
        # reconnects automatically instead of staying offline forever.
        now = time.time()
        if self._llm_available is None or (now - self._llm_probed_at) > self._llm_probe_ttl:
            if self.llm_server == "openai-compatible":
                self._llm_available = self._generic_server().probe(self.llm_model)
                if not self._llm_available:
                    import sys as _sys

                    print(
                        f"[llm] availability probe failed for {self.llm_model} @ {self.llm_url} "
                        f"({self.llm_server} dialect)",
                        file=_sys.stderr,
                        flush=True,
                    )
                self._llm_probed_at = now
                return self._llm_available
            try:
                req = urllib.request.Request(f"{self.llm_url}/api/tags", method="GET")
                with urllib.request.urlopen(req, timeout=2) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    # Only claim availability when the CURRENT model is actually
                    # pulled — a 200 with an unpulled model would otherwise let
                    # _llm_chat raise a 404 mid-reply (M2). Normalize ':latest'
                    # so 'nemotron-3.5-lightning' matches the '…:latest' tag.
                    models = {str(m.get("name", "")).removesuffix(":latest") for m in data.get("models", [])}
                    self._llm_available = self.llm_model in models
            except Exception as exc:  # noqa: BLE001 - offline fallback
                self._llm_available = False
                import sys as _sys

                print(
                    f"[llm] availability probe failed for {self.llm_model} @ {self.llm_url}: "
                    f"{type(exc).__name__}: {exc}",
                    file=_sys.stderr,
                    flush=True,
                )
            self._llm_probed_at = now
        return self._llm_available

    def model(self) -> dict[str, Any]:
        return {"current": self.llm_model, "available": list(self.available_models)}

    def switch_model(self, name: str) -> dict[str, Any]:
        """Switch the chat/reasoning LLM at runtime (kept models: qwen + nemotron).

        The choice is propagated to every LLM component (deliberation, narrator,
        summarizer, conversation summarizer) so the whole cognition stack runs
        ONE model, and persisted so it survives a server restart.
        """
        name = name.strip()
        if name not in self.available_models:
            raise ValueError(f"unknown model '{name}'; available: {self.available_models}")
        # Mutate shared state under the lock: _llm_chat/_llm_chat_stream/state
        # read self.llm_model from the HTTP and brain-loop threads (M1).
        with self._lock:
            self.llm_model = name
            self._llm_available = None  # re-probe availability for the new model
            self._apply_model_to_components()
            if self._persist_model:
                _save_model_choice(self.store_path, name)
        return {"current": self.llm_model, "available": list(self.available_models)}

    def _apply_model_to_components(self) -> None:
        """Re-point the deliberation/narrator/summarizer providers at self.llm_model."""
        reasoning = self._reasoning_provider
        if reasoning is not None:
            llm = getattr(reasoning, "llm", reasoning)
            if hasattr(llm, "set_model"):
                # set_model rebuilds the provider's backend closure; a bare .model
                # assignment would leave the captured model name stale (H3).
                llm.set_model(self.llm_model)
            elif hasattr(llm, "model"):
                llm.model = self.llm_model
        for inner in (self._narrator_inner, self._summarizer_inner, self._conversation_summarizer_inner):
            if inner is not None:
                inner.model = self.llm_model
        # The fast_* wrappers carry a copied .model for introspection; keep it
        # in sync so anything reading brain.narrator.model sees the live model (L3).
        for fast in (self._fast_narrator, self._fast_summarizer, self._fast_conv_summarizer):
            if fast is not None:
                fast.model = self.llm_model  # type: ignore[attr-defined]

    def _generic_server(self) -> Any:
        """OpenAI-compatible (/v1) chat server for the configured URL."""
        from novi.brain.models.chat_server import OpenAICompatibleChatServer

        return OpenAICompatibleChatServer(self.llm_url)

    def _reply_transport(self) -> Any:
        """The chat reply transport: the trained adapters when configured, else
        the Ollama transport (when chat_llm is on and Ollama is up).

        Plan 25: the brain's trained dialogue/emotional adapters are the
        preferred talk path — "everything with the trained data". The Ollama
        transport remains the fallback (and the streaming-capable path).
        """
        if self.trained_reply_enabled:
            trained = self.brain.default_llm_chat()
            if trained is not None:
                return trained
        return self._llm_chat if (self.chat_llm and self._llm_up()) else None

    @staticmethod
    def _transport_error(transport: Any) -> str:
        """Last reported error from a reply transport, if it exposes one.

        Transports that fail (e.g. a trained adapter that never loaded) record
        the reason on themselves; surfacing it in the trace tells the operator
        WHY the reply fell back instead of leaving a bare rejection label.
        """
        for attr in ("last_error", "load_error"):
            try:
                err = getattr(transport, attr, "")
            except Exception:  # noqa: BLE001 - a broken transport must not break tracing
                err = ""
            if err:
                return str(err)[:200]
        return ""

    def _note_transport_error(self, trace: dict[str, Any], transport: Any) -> None:
        """Attach the transport's last error to a fallback trace (when any)."""
        if transport is not None:
            err = self._transport_error(transport)
            if err:
                trace["llm_error"] = err

    def _llm_chat(self, *, system: str, user: str, temperature: float = 0.5, timeout: int = 120) -> str | None:
        from novi.brain.models.ollama_reasoning import can_disable_thinking, num_predict_for

        if self.llm_server == "openai-compatible":
            # Generic dialect: no think control exists, so keep the tuned
            # token budget (thought + answer) and rely on think-stripping.
            reply = self._generic_server().chat(
                model=self.llm_model,
                system=system,
                user=user,
                temperature=temperature,
                max_tokens=num_predict_for(self.llm_model, 320),
                timeout=max(timeout, 300),
            )
            if reply:
                import sys as _sys

                print(f"[llm-debug] reply[{self.llm_model}] first80={reply[:80]!r}", file=_sys.stderr, flush=True)
            else:
                import sys as _sys

                print(
                    f"[llm] chat call failed for {self.llm_model} ({self.llm_server} dialect)",
                    file=_sys.stderr,
                    flush=True,
                )
            return reply
        options: dict[str, Any] = {"temperature": temperature, "num_predict": num_predict_for(self.llm_model, 320)}
        payload: dict[str, Any] = {
            "model": self.llm_model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "stream": False,
            "options": options,
        }
        if can_disable_thinking(self.llm_model):
            # Only models the installed Ollama build actually honors
            # `think:false` for (verified: nemotron). Qwen3 still emits its
            # chain-of-thought as `content` when it is sent, which the dialogue
            # filters reject -> deterministic fallback.
            payload["think"] = False
        else:
            # Thinking models (qwen3): the CoT cannot be disabled here, so give
            # the call room to finish thinking; num_predict_for() provides the
            # budget for thought + answer (the answer lands in `content`).
            timeout = max(timeout, 300)
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.llm_url}/api/chat", data=body, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            import sys as _sys

            print(
                f"[llm] chat call failed for {self.llm_model}: {type(exc).__name__}: {exc}",
                file=_sys.stderr,
                flush=True,
            )
            return None
        message = data.get("message", {}) or {}
        reply = (message.get("content") or "").strip()
        if reply:
            import sys as _sys

            print(f"[llm-debug] reply[{self.llm_model}] first80={reply[:80]!r}", file=_sys.stderr, flush=True)
            return reply
        # Reasoning models (e.g. NVIDIA Nemotron 3.5 Lightning) may emit only a
        # chain-of-thought; surface its final line as a fallback.
        thinking = (message.get("thinking") or "").strip()
        if thinking:
            return thinking.splitlines()[-1].strip() or None
        return None

    def _llm_chat_stream(self, *, system: str, user: str, temperature: float = 0.5, timeout: int = 120):
        """Yield token deltas from Ollama with stream=True (SSE-like)."""
        from novi.brain.models.ollama_reasoning import can_disable_thinking, num_predict_for

        if self.llm_server == "openai-compatible":
            yield from self._generic_server().chat_stream(
                model=self.llm_model,
                system=system,
                user=user,
                temperature=temperature,
                max_tokens=num_predict_for(self.llm_model, 320),
                timeout=max(timeout, 300),
            )
            return
        options: dict[str, Any] = {"temperature": temperature, "num_predict": num_predict_for(self.llm_model, 320)}
        payload: dict[str, Any] = {
            "model": self.llm_model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "stream": True,
            "options": options,
        }
        if can_disable_thinking(self.llm_model):
            payload["think"] = False  # honored only by nemotron on this Ollama
        else:
            timeout = max(timeout, 300)  # qwen3 thinking needs room
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.llm_url}/api/chat", data=body, headers={"Content-Type": "application/json"}
        )
        # Stream-parse NDJSON lines from Ollama.
        with urllib.request.urlopen(req, timeout=timeout) as response:
            buf = b""
            while True:
                chunk = response.read(1024)
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line.decode("utf-8"))
                    except Exception:
                        continue
                    msg = data.get("message", {}) or {}
                    delta = msg.get("content") or ""
                    if delta:
                        yield delta
                    if data.get("done"):
                        # Flush any trailing thinking fallback if content was empty.
                        if not delta:
                            thinking = (msg.get("thinking") or "").strip()
                            if thinking:
                                yield thinking.splitlines()[-1]
                        return
                    # Handle pure thinking chunks (Nemotron) — ignore until final.
                    if msg.get("thinking") and not delta:
                        continue

    def chat_send_stream(self, text: str, confidence: float = 0.9, person: str = ""):
        """Streaming variant of chat_send: yields {'token': str} then {'done': novi}."""
        text = self._clean_chat_text(text)
        import time as _time

        now = _time.time()
        with self._lock:
            if text == self._last_sent_text and (now - self._last_sent_time) < self._dedup_window_seconds:
                # Deduplicated: do NOT create new chat rows. This handles double-click
                # races where the second request arrives while the first is still
                # in-flight and hasn't yet appended to _chat (so checking last role
                # would fail and allow a duplicate).
                # Return the last novi if available, otherwise a bare dedup marker.
                last_novi = None
                for c in reversed(self._chat_thread(person)):
                    if c.get("role") == "novi":
                        last_novi = c
                        break
                if last_novi is not None:
                    yield {
                        "deduplicated": True,
                        "novi": last_novi,
                        "after": self._seq_for(person),
                        "accepted": True,
                        "memory_id": None,
                        "llm": last_novi.get("llm", False),
                    }
                else:
                    yield {"deduplicated": True, "after": self._seq_for(person), "accepted": False}
                return
            self._last_sent_text = text
            self._last_sent_time = now
        # Hold the speaking lease for THIS addressee while composing (replaces
        # _chat_busy loop-freeze; phase 2: scoped per sender). Face-bound
        # identity first, then the explicit sender, then text resolution.
        addressee = person or self._face_person() or self.brain.resolve_addressee(text)
        self.brain.acquire_speaking_lease(addressee)
        try:
            with self._lock:
                r = self.brain.ingest_transcript(
                    TranscriptionResult(
                        text=text, language="en", confidence=confidence, audio_path="", provider="web", model_id="web"
                    )
                )
                adm = r["admission"]
                conclusion = r["reasoning"]
                heard_conf = r["confidence"]
                step = self.brain.step()
                trace = dict(self.brain._last_reasoning_trace)
            history = self._build_history()
            addressee = person or self._face_person() or self.brain.resolve_addressee(text)
            discourse_hint = self.brain.note_user_message(text)["resolved_topic"]
            self.brain._learn_from_chat(text, addressee)
            recent_novi = self._recent_novi(4)
            last_novi = next((c["text"] for c in reversed(self._chat) if c.get("role") == "novi"), "")
            # If no reply transport is available, fallback without streaming.
            transport = self._reply_transport()
            if transport is None:
                fb = self.brain.natural_reply_fallback(text=text, cycle=step.get("cycle"))
                trace["conclusion"] = conclusion
                trace["action"] = "respond"
                trace["rationale"] = fb.get("reason") or "No LLM reply available; used a natural acknowledgement."
                trace["route"] = "deterministic"
                trace["route_reason"] = "no_llm_transport"
                trace["confidence"] = heard_conf
                novi_text = fb["text"]
                # Stream the fallback as one chunk for uniform UI handling.
                for ch in [novi_text[i : i + 12] for i in range(0, len(novi_text), 12)]:
                    yield {"token": ch}
                novi = {"role": "novi", "text": novi_text, "trace": trace, "cycle": step.get("cycle"), "llm": False}
                user_stored = self._append_chat({"role": "user", "text": text}, person)
                novi_stored = self._append_chat(novi, person)
                spoken = self._speak_back(novi_text)
                yield {
                    "done": True,
                    "user": user_stored,
                    "novi": novi_stored,
                    "accepted": bool(adm.accepted),
                    "memory_id": adm.memory_id,
                    "llm": False,
                    "spoken": spoken,
                    "after": self._seq_for(person),
                }
                return
            # Streaming path: compose_reply non-streaming, then stream the full reply
            # token-chunked (feels streaming without NDJSON complexity).
            full_reply_obj = self.brain.compose_reply(
                text,
                person=addressee,
                history=history,
                llm_chat=transport,
                last_novi_text=last_novi,
                addressee_name=addressee,
                recent_novi=recent_novi,
                topic_hint=discourse_hint,
            )
            full_reply = full_reply_obj.get("text") if full_reply_obj else None
            if full_reply is None:
                fb = self.brain.natural_reply_fallback(text=text, cycle=step.get("cycle"))
                trace["conclusion"] = conclusion
                trace["action"] = "respond"
                trace["rationale"] = fb.get("reason") or "No LLM reply available; used a natural acknowledgement."
                trace["route"] = "deterministic"
                designed = (full_reply_obj.get("grounding") or {}).get("route") if full_reply_obj else None
                trace["route_reason"] = designed or "llm_reply_rejected"
                self._note_transport_error(trace, transport)
                trace["confidence"] = heard_conf
                novi_text = fb["text"]
                for ch in [novi_text[i : i + 16] for i in range(0, len(novi_text), 16)]:
                    yield {"token": ch}
                novi = {"role": "novi", "text": novi_text, "trace": trace, "cycle": step.get("cycle"), "llm": False}
                user_stored = self._append_chat({"role": "user", "text": text}, person)
                novi_stored = self._append_chat(novi, person)
                spoken = self._speak_back(novi_text)
                yield {
                    "done": True,
                    "user": user_stored,
                    "novi": novi_stored,
                    "accepted": bool(adm.accepted),
                    "memory_id": adm.memory_id,
                    "llm": False,
                    "spoken": spoken,
                    "after": self._seq_for(person),
                }
                return
            # We have a full reply; stream it in small chunks to simulate token streaming
            # (true NDJSON streaming would require deeper brain integration; this chunked
            # approach delivers the same perceived latency improvement without fragility).
            trace["conclusion"] = full_reply
            trace["action"] = "respond"
            trace["rationale"] = (
                full_reply_obj.get("reason")
                or "Natural reply grounded in recalled knowledge, relationships and self-state."
            )
            trace["route"] = f"ollama:{self.llm_model}"
            trace["route_reason"] = "fallback" if full_reply_obj.get("fallback") else "local LLM"
            trace["confidence"] = 0.8 if full_reply_obj.get("fallback") else 0.85
            # Stream the reply in ~18-char chunks with no artificial delay (network is the bottleneck)
            chunk_size = 14
            for i in range(0, len(full_reply), chunk_size):
                yield {"token": full_reply[i : i + chunk_size]}
            novi = {"role": "novi", "text": full_reply, "trace": trace, "cycle": step.get("cycle"), "llm": True}
            user_stored = self._append_chat({"role": "user", "text": text}, person)
            novi_stored = self._append_chat(novi, person)
            spoken = self._speak_back(full_reply)
            yield {
                "done": True,
                "user": user_stored,
                "novi": novi_stored,
                "accepted": bool(adm.accepted),
                "memory_id": adm.memory_id,
                "llm": True,
                "spoken": spoken,
                "after": self._seq_for(person),
            }
        finally:
            self.brain.release_speaking_lease(addressee)

    def _knowledge_context(self, text: str, limit: int = 6) -> str:
        # Brain-owned grounding (docs/06-soul/07 §2); the web layer is a caller
        # of the mind, not an owner of it.
        return self.brain._chat_knowledge(text, limit=limit)

    def _known_persons(self) -> list[str]:
        return self.brain._chat_known_persons()

    def _memory_context(self, limit: int = 3) -> list[str]:
        """Recent consolidated summary memories for chat grounding (summary recall)."""
        return self.brain._chat_memory_summaries(limit=limit)

    def _append_chat(self, entry: dict[str, Any], person: str = "") -> dict[str, Any]:
        with self._lock:
            seq = self._bump_seq(person)
            stored = {"seq": seq, **entry}
            thread = self._chat_thread(person)
            thread.append(stored)
            if len(thread) > self.budgets.max_chat_turns:
                self._threads[(person or "").lower()] = thread[-self.budgets.max_chat_turns :]
            # copy for persistence outside the lock to keep the lock short
            snapshot = list(self._chat)
        self._persist_chat_snapshot(snapshot)
        self._maybe_summarize_chat()
        return stored

    def _persist_chat_snapshot(self, snapshot: list[dict[str, Any]]) -> None:
        store = getattr(self.brain, "memory", None)
        if store is None or not hasattr(store, "save_chat"):
            return
        with contextlib.suppress(Exception):
            store.save_chat(snapshot)

    def _maybe_summarize_chat(self, threshold: int = 30, keep_recent: int = 8) -> None:
        """When the thread grows long, distill the older turns into a durable summary.

        Gated so the LLM summarizer only runs once the thread has grown by
        `keep_recent` new turns since the last summary (not on every append),
        which avoids a slow LLM call under the runtime lock on every message.
        """
        if len(self._chat) <= threshold:
            return
        if self._last_summarized_len is not None and len(self._chat) - self._last_summarized_len < keep_recent:
            return
        older = self._chat[:-keep_recent]
        recent = self._chat[-keep_recent:]
        summary: str | None = None
        if self.conversation_summarizer is not None:
            try:
                summary = self.conversation_summarizer([{"role": c["role"], "text": c["text"]} for c in older])
            except Exception:  # noqa: BLE001 - summarizer is best-effort
                summary = None
        if not summary:
            summary = "Conversation: " + "; ".join(f"{c['role']}: {c['text']}" for c in older[-6:])
        with contextlib.suppress(Exception):
            self.brain.memory.admit(
                memory_type="conversation_summary",
                content=summary,
                confidence=0.8,
                verification_status="consolidated",
                privacy_class="public",
                provenance={"source": "conversation_summarization", "kind": "thread_summary"},
            )
        self._chat = recent
        self._last_summarized_len = len(self._chat)
        self._persist_chat()

    def _persist_chat(self) -> None:
        """Persist the chat thread to the durable store (conversation persistence)."""
        # snapshot under lock, persist outside to avoid holding lock during I/O
        with self._lock:
            snapshot = list(self._chat)
        self._persist_chat_snapshot(snapshot)

    def chat(self, after: int = 0, person: str = "") -> dict[str, Any]:
        with self._lock:
            thread = self._chat_thread(person)
            entries = [c for c in thread if c["seq"] > after]
            next_after = thread[-1]["seq"] if thread else after
            # return copies to avoid caller mutating live list
            return {"entries": [dict(e) for e in entries], "after": next_after}

    def clear_chat(self, person: str = "") -> dict[str, Any]:
        """Drop the live conversation thread (durable store is updated)."""
        key = (person or "").lower()
        with self._lock:
            self._threads[key] = []
            self._seqs[key] = 0
            self._touch_thread(key)
            self._last_summarized_len = None
            self._persist_chat()
        return {"cleared": True}

    def hear_audio(
        self, *, event_hint: str | None, rms: float, novelty: float = 0.0, speech: bool = False, confidence: float = 0.0
    ) -> dict[str, Any]:
        frame = AudioFrame(
            rms=float(rms),
            speech=speech,
            event_hint=event_hint,
            hint_confidence=float(confidence) if confidence else 0.0,
            novelty=float(novelty),
        )
        with self._lock:
            return self.brain.ingest_audio_frame(frame)

    def step(self) -> dict[str, Any]:
        with self._lock:
            result = self.brain.step()
            self._last_step = result
            return result

    def set_goal(self, *, x: float, y: float, max_steps: int = 60) -> dict[str, Any]:
        with self._lock:
            state = self.brain.set_goal(Goal.reach(float(x), float(y), max_steps=int(max_steps)))
            return {
                "goal_id": state.goal.goal_id,
                "kind": state.goal.kind,
                "target": [state.goal.target[0], state.goal.target[1]],
                "status": state.status.value,
            }

    def health(self) -> dict[str, Any]:
        with self._lock:
            return self.brain.health_report()

    def _guard_event_entry(self, entry: dict[str, Any]) -> dict[str, Any]:
        """Enforce the per-entry payload budget at the web boundary.

        Oversized entries keep seq/ts/type metadata but have their payload
        replaced with a truncation summary — a slow/verbose producer must not
        be able to blow up a poll response or pin memory in clients.
        """
        try:
            size = len(json.dumps(entry.get("event", {}), default=str))
        except Exception:  # noqa: BLE001 - unserializable means oversized
            size = self.budgets.max_event_payload_bytes + 1
        if size <= self.budgets.max_event_payload_bytes:
            return entry
        event = entry.get("event", {})
        summary = {
            "event_type": event.get("event_type", "unknown"),
            "cycle": event.get("cycle"),
            "__truncated__": True,
            "bytes": size,
        }
        return {"seq": entry["seq"], "ts": entry["ts"], "event": summary}

    def poll_events(self, after: int) -> dict[str, Any]:
        """Return events after client cursor ``after`` (cursor-based delivery).

        Contract (plan 02, Phase 2):
        - at most ``budgets.event_batch_size`` entries per call; the client
          re-requests with the returned ``after`` to page forward;
        - ``gap=True`` when ``after`` predates the oldest retained entry, so
          the client drops its window and resyncs from the fresh snapshot
          instead of assuming continuity;
        - ``after`` always advances to the newest delivered seq (or stays when
          there is nothing new). No client can force unbounded retention.
        """
        self._drain()
        with self._lock:
            epoch = self._epoch
            log = self._log
            if not log:
                return {"events": [], "after": after, "gap": False, "epoch": epoch}
            oldest = log[0]["seq"]
            gap = after < oldest - 1 and after != 0 and len(log) >= self.budgets.max_events
            # A cursor of 0 (fresh client) is a snapshot request, not a gap.
            if after == 0:
                gap = False
            fresh = [e for e in log if e["seq"] > after]
            batch = fresh[: self.budgets.event_batch_size]
            guarded = [self._guard_event_entry(e) for e in batch]
            # The cursor never moves backwards: an empty batch means "nothing
            # new", so the client's cursor stands.
            next_after = batch[-1]["seq"] if batch else after
            has_more = len(fresh) > len(batch)
            return {"events": guarded, "after": next_after, "gap": gap, "has_more": has_more, "epoch": epoch}

    @staticmethod
    def _process_rss_bytes() -> int | None:
        """Best-effort current RSS in bytes (stdlib only; None when unknown)."""
        try:
            import sys

            if sys.platform.startswith("linux"):
                with open("/proc/self/status", encoding="utf-8") as fh:
                    for line in fh:
                        if line.startswith("VmRSS:"):
                            return int(line.split()[1]) * 1024
                return None
            if sys.platform == "darwin":
                import os
                import subprocess

                out = subprocess.run(
                    ["ps", "-o", "rss=", "-p", str(os.getpid())],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if out.returncode == 0 and out.stdout.strip():
                    return int(out.stdout.strip()) * 1024
                return None
            return None
        except Exception:  # noqa: BLE001 - metrics are best-effort
            return None

    def runtime_metrics(self) -> dict[str, Any]:
        """Lightweight memory/resource observability (plan 02, Phase 9).

        Exposes the counters that prove bounded operation: compat window vs
        limit, EventBus vs limit, server log vs limit, SSE clients vs limit,
        latest preview bytes, and worker threads. Poll cheaply; RSS slope over
        a moving window is the soak-test signal (stable/oscillating = healthy,
        persistent positive slope = investigate).
        """
        with self._lock:
            log_size = len(self._log)
            sse = self._sse_clients
        brain = self.brain
        try:
            bus_size = len(brain.event_bus.events())
            bus_limit = int(brain.event_bus.health().get("max_events", -1))
        except Exception:  # noqa: BLE001
            bus_size, bus_limit = -1, -1
        try:
            compat_size = len(brain.events)
            compat_limit = brain._compat_event_limit()
        except Exception:  # noqa: BLE001
            compat_size, compat_limit = -1, -1
        try:
            loop_steps = len(brain.closed_loop.steps)
            loop_limit = brain.closed_loop.max_steps
        except Exception:  # noqa: BLE001
            loop_steps, loop_limit = -1, -1
        try:
            preview_bytes = len(getattr(self, "mm_last_frame_b64", None) or "")
        except Exception:  # noqa: BLE001
            preview_bytes = -1
        thread = self._thread
        return {
            "rss_bytes": self._process_rss_bytes(),
            "compat_event_count": compat_size,
            "compat_event_limit": compat_limit,
            "loop_step_count": loop_steps,
            "loop_step_limit": loop_limit,
            "eventbus_size": bus_size,
            "eventbus_limit": bus_limit,
            "server_log_size": log_size,
            "server_log_limit": self.budgets.max_events,
            "active_sse_clients": sse,
            "sse_limit": self.budgets.max_sse_clients,
            "preview_frame_bytes": preview_bytes,
            "preview_max_bytes": self.budgets.preview_max_bytes,
            "worker_threads": threading.active_count(),
            "brain_thread_alive": bool(thread is not None and thread.is_alive()),
            "auto_step": self.auto_step,
        }

    def state(self) -> dict[str, Any]:
        with self._lock:
            step = self._last_step
            body = (
                self.brain.body.snapshot()
                if hasattr(self.brain.body, "snapshot")
                else {
                    "x_m": self.brain.body.x_m,
                    "y_m": self.brain.body.y_m,
                    "heading_deg": self.brain.body.heading_deg,
                }
            )
            active_goal = self.brain.goals.active
            goals = [
                {"goal_id": s.goal.goal_id, "kind": s.goal.kind, "status": s.status.value, "steps_taken": s.steps_taken}
                for s in list(self.brain.goals.history)[-5:]
            ]
            plan = None
            distance = None
            if active_goal is not None:
                p = self.brain._plans.get(active_goal.goal.goal_id)
                if p is not None:
                    plan = p.snapshot()
                try:
                    tx, ty = active_goal.goal.target[0], active_goal.goal.target[1]
                    distance = round(((self.brain.body.x_m - tx) ** 2 + (self.brain.body.y_m - ty) ** 2) ** 0.5, 3)
                except Exception:  # noqa: BLE001
                    distance = None
            return {
                "cycle": self.brain._cycle,
                "run_id": self.brain.run_id,
                "last_step": step,
                "reasoning_trace": self.brain._last_reasoning_trace,
                "body": body,
                "soul": {
                    "identity": self.brain.soul.identity.name,
                    "persona": self.brain.soul.identity.persona,
                    "tone": self.brain.soul.tone({}).get("tone"),
                    "traits": dict(self.brain.soul.personality.traits),
                    "values": dict(self.brain.soul.personality.values),
                    "affect": dict(self.brain.soul.affect.dimensions),
                },
                "active_goal": {
                    "goal_id": active_goal.goal.goal_id,
                    "kind": active_goal.goal.kind,
                    "target": str(active_goal.goal.target),
                    "steps_taken": active_goal.steps_taken,
                    "status": active_goal.status.value,
                    "distance_to_goal": distance,
                }
                if active_goal is not None
                else None,
                "plan": plan,
                "goals_history": goals,
                "knowledge": self.brain.knowledge.counts(),
                "hearing": self.brain._last_audio_events,
                "memory": {
                    "active": getattr(self.brain.memory, "active_count", None),
                    "summaries": self._memory_summaries(),
                    "embedder": self._embedding_info(),
                },
                "narrative": self._cached_narrative(),
                # Phase P1/P2 observability: sleep-cycle health + per-class routing.
                "sleep_cycle": self._sleep_cycle_info(),
                "router": self._router_info(),
                "health": self.brain.health.run(self.brain).snapshot(),
                "identity": self.brain.identity.snapshot() if hasattr(self.brain, "identity") else None,
                "self_model": self.brain.self_model(),
            }

    def _embedding_info(self) -> dict[str, Any]:
        try:
            emb = getattr(self.brain.memory, "_embedder", None)
            if emb is None:
                emb = getattr(self.brain.memory, "_embed_index", None)
                if emb is not None:
                    emb = getattr(emb, "provider", None)
            if emb is None:
                return {"provider": "unknown", "dimension": None}
            provider = type(emb).__name__
            dim = emb.dimension() if hasattr(emb, "dimension") else None
            available = getattr(emb, "is_available", None)
            if callable(available):
                available = emb.is_available
            elif hasattr(emb, "is_available"):
                available = bool(emb.is_available)
            else:
                available = True
            err = getattr(emb, "load_error", None)
            return {
                "provider": provider,
                "dimension": dim,
                "available": available,
                "error": err,
                "mode": getattr(self, "embedder_mode", "auto"),
            }
        except Exception:
            return {"provider": "unknown", "dimension": None}

    def _sleep_cycle_info(self) -> dict[str, Any]:
        """Phase P1 observability: last sleep-phase report + cadence."""
        sc = getattr(self.brain, "_sleep_cycle", None)
        if sc is None:
            return {"enabled": False}
        return {
            "enabled": True,
            "every_n_cycles": getattr(sc, "every_n_cycles", None),
            "last_phase": getattr(sc, "last_report", None),
            "phases_run": getattr(sc, "phases_run", 0),
        }

    # -- language grounding (L3: same capability, any surface) -------------

    def _grounding_frame(self, data: dict) -> CameraFrame:
        """The frame to ground: client-supplied > live camera feed > demo."""
        import base64

        b64 = data.get("frame_b64")
        if b64:
            payload = base64.b64decode(str(b64))
            return CameraFrame(
                frame_id="web-ground",
                captured_at=utc_now(),
                width=int(data.get("width", 640)),
                height=int(data.get("height", 480)),
                payload=payload,
            )
        feed = getattr(self, "mm_camera_feed", None)
        if feed is not None:
            rec = feed.poll()
            if rec is not None:
                f = rec.frame
                return CameraFrame(
                    frame_id=f.frame_id, captured_at=f.captured_at, width=f.width, height=f.height, payload=f.payload
                )
        return DemoCamera().read()

    def _pipeline_for_grounding(self) -> PerceptionPipeline:
        if self._grounding_pipeline is None:
            self._grounding_pipeline = PerceptionPipeline(
                detector=DeterministicObjectDetector(scripted={}),
                grounding_backend=self.grounding_backend,
                tracker=ObjectTracker(),
            )
        return self._grounding_pipeline

    def _api_grounding(self, data: dict) -> tuple[dict, int]:
        query_text = str(data.get("query", "")).strip()
        if not query_text:
            return {"error": "empty query"}, 400
        frame = self._grounding_frame(data)
        query = SpatialQuery(text=query_text, frame_id=frame.frame_id, timestamp=frame.captured_at)
        outcome = self._pipeline_for_grounding().ground_frame(frame, query, SpatialInferencePolicy())
        r = outcome.result
        return (
            {
                "success": r.success,
                "no_object": r.no_object,
                "backend_status": r.backend_status,
                "model_id": r.model_id,
                "model_revision": r.model_revision,
                "latency_ms": r.latency_ms,
                "frame_id": r.frame_id,
                "query": r.query,
                "validation_errors": list(r.validation_errors),
                "observations": [observation_to_dict(o) for o in r.observations],
                "associations": [
                    {"observation_id": a.observation.observation_id, "track_id": a.track_id, "status": a.status}
                    for a in outcome.associations
                ],
            },
            200,
        )

    def _router_info(self) -> dict[str, Any]:
        """Phase P2 observability: per-input-class route counts."""
        router = getattr(self.brain, "reasoning", None)
        snap = router.snapshot() if hasattr(router, "snapshot") else {}
        return {
            "last_route": snap.get("last_route"),
            "last_reason": snap.get("last_reason"),
            "route_counts": snap.get("route_counts"),
            "route_counts_by_class": snap.get("route_counts_by_class"),
            "cache_size": len(getattr(router, "_route_cache", {}) or {}),
        }

    def _cached_narrative(self) -> list[str]:
        """Episodic narrative for the dashboard.

        Regenerated only when NEW episodic memories arrive (the last-5 episodic
        memory_ids are the cache key). The /api/state poll therefore never
        triggers an LLM narrator call while the world is quiet. In-memory
        stores don't expose active_rows, so there is nothing to narrate.

        The narrator call runs on a background thread (M3): a cache miss
        returns the stale narrative immediately instead of blocking the web
        lock for the whole narrator call, and the ``_narrative_regenerating``
        latch prevents the engine step + state poll from double-running it.
        """
        try:
            rows = self.brain.memory.active_rows()
        except Exception:  # noqa: BLE001 - a memory hiccup degrades to no narrative
            return []
        episodic = [item["record"] for item in rows if item["record"].memory_type in {"utterance", "perception"}]
        episodic.sort(key=lambda r: r.created_at)
        sig = tuple(r.memory_id for r in episodic[-5:])
        if sig == self._narrative_sig and self._narrative_cache is not None:
            return self._narrative_cache
        if self._narrative_regenerating:
            return self._narrative_cache or []
        self._narrative_regenerating = True
        target_sig = sig

        def _regenerate() -> None:
            try:
                narrative = self.brain._episodic_narrative()
            except Exception:  # noqa: BLE001 - a narrator failure degrades to no narrative
                narrative = []
            with self._lock:
                self._narrative_cache = narrative
                self._narrative_sig = target_sig
                self._narrative_regenerating = False

        threading.Thread(target=_regenerate, daemon=True, name="novi-narrative").start()
        return self._narrative_cache or []

    def _memory_summaries(self, limit: int = 5) -> list[dict[str, Any]]:
        """Recent consolidated summary memories for the web UI."""
        try:
            rows = self.brain.memory.active_rows()
        except Exception:  # noqa: BLE001 - summaries are best-effort UI data
            return []
        summaries = [r["record"] for r in rows if r["record"].memory_type == "summary"]
        summaries.sort(key=lambda r: r.created_at, reverse=True)
        return [
            {"content": s.content, "confidence": s.confidence, "entity_refs": list(s.entity_refs)}
            for s in summaries[:limit]
        ]

    # ---- observability slices (for dedicated widget panels) ----
    def attention(self) -> dict[str, Any]:
        with self._lock:
            return {
                "cycle": self.brain._cycle,
                "candidates": list(getattr(self.brain, "_last_attention_candidates", []) or []),
                "situations": list(getattr(self.brain, "_last_situations", []) or []),
                "typed_cognition": getattr(self.brain, "_last_typed_cognition", None),
            }

    def context_package(self) -> dict[str, Any]:
        with self._lock:
            pkg = getattr(self.brain, "_last_context_package", None)
            if pkg is None:
                # fallback: assemble from current world state for the first cycle
                try:
                    pkg = self.brain._assemble_world_context(
                        "",
                        person="",
                        vision_provider=getattr(self.brain, "_vision_provider", None),
                    )
                except Exception:
                    pkg = {}
            discourse = {}
            try:
                discourse = self.brain.discourse.snapshot()
                discourse.pop("turns", None)  # keep the API payload bounded
            except Exception:
                pass
            return {"cycle": self.brain._cycle, "package": pkg, "discourse": discourse}

    def soul_detail(self) -> dict[str, Any]:
        with self._lock:
            s = self.brain.soul
            return {
                "cycle": self.brain._cycle,
                "identity": {"name": s.identity.name, "persona": s.identity.persona, "origin": s.identity.origin},
                "traits": dict(s.personality.traits),
                "values": dict(s.personality.values),
                "motivations": dict(s.motivations) if hasattr(s, "motivations") else {},
                "affect": dict(s.affect.dimensions),
                "baseline": dict(s.affect.baseline),
                "tone": s.tone({}).get("tone") if hasattr(s, "tone") else None,
            }

    def identity_detail(self) -> dict[str, Any]:
        with self._lock:
            snap = self.brain.identity.snapshot() if hasattr(self.brain, "identity") else {}
            belief = self.brain.identity.identity_for("person") if hasattr(self.brain, "identity") else None
            return {
                "cycle": self.brain._cycle,
                "snapshot": snap,
                "current": belief.snapshot() if belief else None,
            }

    def knowledge_query(self, entity: str, limit: int = 10) -> dict[str, Any]:
        with self._lock:
            entity = (entity or "").strip()
            if not entity:
                return {"entity": "", "triples": [], "counts": self.brain.knowledge.counts()}
            try:
                triples = self.brain.knowledge.context(entity, limit=limit)
                out = []
                for t in triples:
                    if hasattr(t, "snapshot"):
                        out.append(t.snapshot())
                    elif isinstance(t, dict):
                        out.append(t)
                    else:
                        out.append({"raw": str(t)})
            except Exception:
                out = []
            return {"entity": entity, "triples": out, "counts": self.brain.knowledge.counts()}

    def memory_query(self, query: str, limit: int = 8) -> dict[str, Any]:
        with self._lock:
            query = (query or "").strip() or "memory"
            limit = max(1, min(20, int(limit)))
            try:
                retrieve = getattr(self.brain.memory, "retrieve_indexed", self.brain.memory.retrieve)
                rows = list(retrieve(query, limit=limit))
                out = []
                for r in rows:
                    out.append(
                        {
                            "memory_id": r.memory_id,
                            "memory_type": r.memory_type,
                            "content": r.content if isinstance(r.content, str) else str(r.content),
                            "confidence": r.confidence,
                            "entity_refs": list(r.entity_refs),
                            "created_at": r.created_at,
                        }
                    )
            except Exception:
                out = []
            retrieval_state = None
            try:
                if hasattr(self.brain.memory, "retrieve_with_states"):
                    ret = self.brain.memory.retrieve_with_states(query, limit=limit)
                    retrieval_state = ret.state if hasattr(ret, "state") else None
            except Exception:
                pass
            return {"query": query, "results": out, "retrieval_state": retrieval_state}


class Handler(BaseHTTPRequestHandler):
    server: "NoviWebHTTPServer"  # type: ignore[misc]
    protocol_version = "HTTP/1.1"

    def setup(self) -> None:
        # Transport deadline (plan 02 §12.4): socket I/O on this connection
        # fails instead of stalling forever behind a slow client. Sizing comes
        # from the owning server's budgets so tests can construct the server
        # without binding a socket.
        try:
            self.timeout: float | None = self.server.novi.budgets.request_timeout_s
        except Exception:  # noqa: BLE001 - fall back to blocking sockets
            self.timeout = None
        super().setup()

    def log_message(self, fmt: str, *args: Any) -> None:  # quieter logs
        pass

    def _send(self, code: int, body: bytes, content_type: str = "application/json") -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj: Any, status: int = 200) -> None:
        self._send(status, json.dumps(obj).encode())

    def _serve_spa(self) -> None:
        """Serve the built React SPA shell (novi/web/ui/dist/index.html)."""
        dist_index = _UI_DIST / "index.html"
        if dist_index.is_file():
            self._send(200, dist_index.read_bytes(), "text/html")
        else:
            self._send(
                503,
                b"novi web ui is not built - run `npm run build` in novi/web/ui",
                "text/plain",
            )

    def _serve_ui_asset(self, rel_path: str) -> None:
        target = _resolve_ui_asset(rel_path)
        if target is None:
            self._send(404, b"not found", "text/plain")
            return
        ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self._send(200, target.read_bytes(), ctype)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except Exception:  # noqa: BLE001
            return {}

    def _admit(self) -> bool:
        """Non-blocking take of the request budget; 503 + False when full."""
        sem = self.server.novi.request_semaphore
        if sem.acquire(blocking=False):
            return True
        try:
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.send_header("Retry-After", "2")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b'{"error": "server busy"}')
        except Exception:  # noqa: BLE001 - client already gone
            pass
        return False

    def do_GET(self) -> None:
        # Long-lived SSE streams are bounded by max_sse_clients, not the
        # request budget: pinning a request slot for the stream's whole
        # lifetime (potentially hours) would starve snapshot polls and push
        # clients into retry storms. The streaming chat POST keeps its slot
        # — it is an expensive LLM op where bounded concurrency is wanted.
        if self.path.split("?")[0] == "/api/events/stream":
            self._do_GET()
            return
        if not self._admit():
            return
        try:
            self._do_GET()
        finally:
            self.server.novi.request_semaphore.release()

    def _do_GET(self) -> None:
        path = self.path.split("?")[0]
        if path.startswith("/assets/"):
            self._serve_ui_asset(path.lstrip("/"))
            return
        if path == "/api/events/stream":
            # Server-Sent Events: push brain events as they appear (replaces polling)
            from urllib.parse import parse_qs, urlparse

            try:
                after = int(parse_qs(urlparse(self.path).query).get("after", ["0"])[0])
            except Exception:
                after = 0
            novi = self.server.novi
            # SSE budget (plan 02 §12.3): bounded clients with heartbeat,
            # disconnect detection, and cleanup. Slow browsers must not grow
            # server memory: delivery reuses the bounded poll_events batches.
            budgets = novi.budgets
            with novi._sse_lock:
                if novi._sse_clients >= budgets.max_sse_clients:
                    self.send_response(503)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Retry-After", "5")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    with contextlib.suppress(Exception):
                        self.wfile.write(b'{"error": "too many event subscribers"}')
                    return
                novi._sse_clients += 1
            try:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                # Send initial comment to confirm connection
                try:
                    self.wfile.write(b": connected\n\n")
                    self.wfile.flush()
                except Exception:
                    return
                last = after
                # Track last heartbeat to avoid spamming
                heartbeat_interval = budgets.sse_heartbeat_s
                last_beat = time.time()
                while not novi._stop.is_set():
                    try:
                        chunk = novi.poll_events(last)
                        if chunk.get("events"):
                            payload = json.dumps(chunk)
                            self.wfile.write(f"data: {payload}\n\n".encode("utf-8"))
                            self.wfile.flush()
                            last = chunk.get("after", last)
                            last_beat = time.time()
                        else:
                            if time.time() - last_beat > heartbeat_interval:
                                self.wfile.write(b": ping\n\n")
                                self.wfile.flush()
                                last_beat = time.time()
                    except (BrokenPipeError, ConnectionResetError, OSError):
                        break
                    except Exception:
                        # Keep the SSE stream alive even if one poll fails
                        try:
                            self.wfile.write(b": error\n\n")
                            self.wfile.flush()
                        except Exception:
                            break
                    # Poll interval — 250ms gives <300ms initiative latency vs 1.2s polling
                    if novi._stop.wait(budgets.sse_poll_interval_s):
                        break
            finally:
                with novi._sse_lock:
                    novi._sse_clients = max(0, novi._sse_clients - 1)
            return
        if path in ("/", "/index.html"):
            self._serve_spa()
            return
        if path in ("/camera", "/camera.html", "/live"):
            self._serve_spa()
            return
        if path == "/api/state":
            self._json(self.server.novi.state())
            return
        if path == "/api/model":
            self._json(self.server.novi.model())
            return
        if path == "/api/health":
            self._json({"result": self.server.novi.health()})
            return
        if path == "/api/runtime/metrics":
            self._json(self.server.novi.runtime_metrics())
            return
        if path == "/api/attention":
            self._json(self.server.novi.attention())
            return
        if path == "/api/context":
            self._json(self.server.novi.context_package())
            return
        if path == "/api/soul":
            self._json(self.server.novi.soul_detail())
            return
        if path == "/api/identity":
            self._json(self.server.novi.identity_detail())
            return
        if path == "/api/memory":
            # /api/memory?query=alice&limit=8
            query = ""
            limit = 8
            if "?" in self.path:
                from urllib.parse import parse_qs, urlparse

                qs = parse_qs(urlparse(self.path).query)
                query = qs.get("query", [""])[0]
                try:
                    limit = int(qs.get("limit", ["8"])[0])
                except Exception:
                    limit = 8
            self._json(self.server.novi.memory_query(query, limit))
            return
        if path == "/api/knowledge":
            entity = ""
            limit = 10
            if "?" in self.path:
                from urllib.parse import parse_qs, urlparse

                qs = parse_qs(urlparse(self.path).query)
                entity = qs.get("entity", [""])[0]
                try:
                    limit = int(qs.get("limit", ["10"])[0])
                except Exception:
                    limit = 10
            self._json(self.server.novi.knowledge_query(entity, limit))
            return
        if path.startswith("/api/chat") and "after=" in self.path:
            try:
                after = int(self.path.split("after=")[-1].split("&")[0])
            except Exception:  # noqa: BLE001
                after = 0
            person = ""
            if "person=" in self.path:
                from urllib.parse import parse_qs, urlparse

                person = parse_qs(urlparse(self.path).query).get("person", [""])[0]
            self._json(self.server.novi.chat(after, person))
            return
        if path.startswith("/api/events"):
            after = 0
            try:
                after = int(self.path.split("after=")[-1].split("&")[0]) if "after=" in self.path else 0
            except Exception:  # noqa: BLE001
                after = 0
            self._json(self.server.novi.poll_events(after))
            return
        if path == "/healthz":
            self._json({"ok": True})
            return
        # ---- multimodal integration (doc 16) ----
        novi = self.server.novi
        if path == "/api/perception/state":
            self._json(novi.perception_state() if novi.mm_runtime else {"error": "integration unavailable"})
            return
        if path == "/api/recognition":
            kind = None
            if "?" in self.path:
                from urllib.parse import parse_qs, urlparse

                qs = parse_qs(urlparse(self.path).query)
                kind = qs.get("kind", [None])[0]
            self._json(novi.recognition_list(kind) if novi.mm_runtime else {"error": "integration unavailable"})
            return
        if path == "/api/recognition/proposals":
            # The React UI polls this via GET (issue 9: it was POST-only →
            # 404 → the Perception page's proposal poll errored and broke the
            # page). POST remains supported for symmetry.
            self._json({"result": novi.proposal_list()} if novi.mm_runtime else {"error": "integration unavailable"})
            return
        if path == "/api/preview":
            self._json(novi.preview_frame() if novi.mm_runtime else {"error": "integration unavailable"})
            return
        # ---- real I/O (doc 17) ----
        if path == "/api/real/status":
            self._json(
                {
                    "enabled": novi.real_io_enabled,
                    "devices": dict(novi.real_io),
                    "speak_back": novi.speak_back_enabled,
                }
            )
            return
        if path == "/api/real/speakback":
            pass  # handled in POST below; GET returns current state only
        if path == "/api/p0-gate":
            with self.server.novi._lock:
                result = self.server.novi.brain.p0_gate()
            self._json(result)
            return
        # SPA fallback: any other non-API GET serves the React shell so client-side
        # routes (/overview, /cognition, ...) work on refresh.
        if not path.startswith("/api/"):
            self._serve_spa()
            return
        self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:
        if not self._admit():
            return
        try:
            self._do_POST()
        finally:
            self.server.novi.request_semaphore.release()

    def _do_POST(self) -> None:
        path = self.path.split("?")[0]
        # Streaming chat: POST /api/chat/stream — yields SSE token events, then done
        if path == "/api/chat/stream":
            data = self._read_json()
            text = str(data.get("text", "")).strip()
            if not text:
                self._json({"error": "empty text"})
                return
            conf = float(data.get("confidence", 0.9))
            # Clamp confidence
            conf = max(0.0, min(1.0, conf))
            if len(text) > 2000:
                self._json({"error": "text too long (max 2000 chars)"}, status=400)
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            gen = None
            try:
                gen = self.server.novi.chat_send_stream(text, confidence=conf)
                for evt in gen:
                    line = json.dumps(evt, ensure_ascii=False)
                    self.wfile.write(f"data: {line}\n\n".encode("utf-8"))
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass
            except Exception as exc:
                try:
                    err = json.dumps({"error": str(exc)})
                    self.wfile.write(f"data: {err}\n\n".encode("utf-8"))
                    self.wfile.flush()
                except Exception:
                    pass
            finally:
                if gen is not None:
                    with contextlib.suppress(Exception):
                        gen.close()
                    # Ensure the speaking lease is released even if the client
                    # disconnected mid-stream before the generator's own finally ran.
                    try:
                        with self.server.novi._lock:
                            self.server.novi.brain.release_speaking_lease()
                    except Exception:
                        pass
                # Ensure the connection closes so the client's fetch stream sees EOF.
                with contextlib.suppress(Exception):
                    self.close_connection = True
            return
        data = self._read_json()
        novi = self.server.novi
        try:
            if path == "/api/hear":
                text = str(data.get("text", "")).strip()
                if not text:
                    self._json({"error": "empty text"})
                    return
                self._json({"result": novi.hear(text, confidence=float(data.get("confidence", 0.9)))})
            elif path == "/api/grounding":
                payload, status = novi._api_grounding(data)
                self._json(payload, status)
            elif path == "/api/chat":
                text = str(data.get("text", "")).strip()
                if not text:
                    self._json({"error": "empty text"})
                    return
                self._json(
                    {
                        "result": novi.chat_send(
                            text,
                            confidence=float(data.get("confidence", 0.9)),
                            person=str(data.get("person", "") or ""),
                        )
                    }
                )
            elif path == "/api/audio":
                self._json(
                    {
                        "result": novi.hear_audio(
                            event_hint=data.get("event_hint"),
                            rms=data.get("rms", 0.6),
                            novelty=data.get("novelty", 0.0),
                            speech=bool(data.get("speech", False)),
                            confidence=float(data.get("confidence", 0.0)),
                        )
                    }
                )
            elif path == "/api/listen":
                self._json({"result": novi.listen(float(data.get("seconds") or 0) or None)})
            elif path == "/api/model":
                try:
                    self._json({"result": novi.switch_model(str(data.get("model", "")))})
                except ValueError as exc:
                    self._json({"error": str(exc)}, status=400)
            elif path == "/api/chat/clear":
                self._json({"result": novi.clear_chat()})
                return
            elif path == "/api/step":
                self._json({"result": novi.step()})
            elif path == "/api/goal":
                self._json(
                    {
                        "result": novi.set_goal(
                            x=data.get("x", 1.0), y=data.get("y", 1.0), max_steps=int(data.get("max_steps", 60))
                        )
                    }
                )
            elif path == "/api/health":
                self._json({"result": novi.health()})
            elif path == "/api/episode/start":
                with novi._lock:
                    novi.brain.start_recording(
                        task_name=str(data.get("task_name", "runtime_observation")),
                        description=str(data.get("description", "")),
                    )
                self._json({"result": {"recording": True, "task_name": data.get("task_name", "runtime_observation")}})
            elif path == "/api/episode/stop":
                with novi._lock:
                    episode = novi.brain.stop_recording()
                if episode is None:
                    self._json({"error": "not recording"}, 400)
                else:
                    fmt = str(data.get("format", "novi_native"))
                    exported = novi.brain.export_episode(episode, format=fmt)
                    self._json(
                        {
                            "result": {
                                "episode_id": episode.episode_id,
                                "step_count": len(episode.steps),
                                "format": fmt,
                                "export": exported,
                            }
                        }
                    )
            elif path == "/api/episode/status":
                with novi._lock:
                    self._json(
                        {
                            "result": {
                                "recording": novi.brain.is_recording,
                                "step_count": novi.brain.recording_step_count,
                            }
                        }
                    )
            elif path == "/api/perception/frame":
                self._json(
                    {"result": novi.perception_frame(data)} if novi.mm_runtime else {"error": "integration unavailable"}
                )
            elif path == "/api/voice/turn":
                self._json(
                    {"result": novi.voice_turn(data)} if novi.mm_runtime else {"error": "integration unavailable"}
                )
            elif path == "/api/recognition/person":
                self._json(
                    {"result": novi.recognize_person(data)} if novi.mm_runtime else {"error": "integration unavailable"}
                )
            elif path == "/api/recognition/enroll":
                self._json(
                    {"result": novi.enroll_place_or_noise(data)}
                    if novi.mm_runtime
                    else {"error": "integration unavailable"}
                )
            elif path == "/api/recognition/privacy":
                self._json(
                    {"result": novi.recognition_privacy(data)}
                    if novi.mm_runtime
                    else {"error": "integration unavailable"}
                )
            elif path == "/api/real/enable":
                res = novi.real_enable(
                    camera=bool(data.get("camera", False)),
                    mic=bool(data.get("mic", False)),
                    speaker=bool(data.get("speaker", False)),
                )
                self._json({"result": res})
            elif path == "/api/voice/listen":
                try:
                    self._json(
                        {
                            "result": novi.voice_listen(
                                float(data.get("seconds", 3.0)),
                                client_speaks=bool(data.get("client_speaks", False)),
                            )
                        }
                    )
                except RuntimeError as exc:
                    self._json({"error": str(exc)}, status=400)
            elif path == "/api/voice/tts":
                self._json({"result": novi.tts_speak(data)})
            elif path == "/api/real/speakback":
                novi.speak_back_enabled = bool(data.get("enabled", True))
                self._json({"result": {"speak_back": novi.speak_back_enabled}})
            elif path == "/api/recognition/voice":
                try:
                    self._json({"result": novi.enroll_voice(data)})
                except RuntimeError as exc:
                    self._json({"error": str(exc)}, status=400)
            elif path == "/api/recognition/enroll-face":
                # Enroll a face from the CURRENT live camera frame: server grabs
                # the newest JPEG, embeds it with SFace, stores under `name`.
                self._json({"result": novi.enroll_face_from_camera(str(data.get("name", "")))})
            elif path == "/api/recognition/enroll-voice":
                # Record ~4s from the real mic now and save the voiceprint.
                try:
                    self._json({"result": novi.enroll_voice_live(str(data.get("name", "")))})
                except RuntimeError as exc:
                    self._json({"error": str(exc)}, status=400)
            elif path == "/api/recognition/object":
                # Enroll an object instance from a supplied embedding.
                self._json(
                    {"result": novi.recognize_object(data)} if novi.mm_runtime else {"error": "integration unavailable"}
                )
            elif path == "/api/recognition/enroll-object":
                # Enroll an object from the CURRENT live camera frame: server
                # embeds the largest non-person crop with ResNet18 and stores it.
                self._json({"result": novi.enroll_object_from_camera(str(data.get("name", "")))})
            elif path == "/api/observation/last-sighting":
                self._json(
                    {"result": novi.observation_last_sighting(data)}
                    if novi.mm_runtime
                    else {"error": "integration unavailable"}
                )
            elif path == "/api/observation/in-place":
                self._json(
                    {"result": novi.observation_in_place(data)}
                    if novi.mm_runtime
                    else {"error": "integration unavailable"}
                )
            elif path == "/api/observation/search":
                self._json(
                    {"result": novi.observation_search(data)}
                    if novi.mm_runtime
                    else {"error": "integration unavailable"}
                )
            elif path == "/api/association":
                # person-object co-occurrence memory: objects_with | seen_with |
                # recent_summary for a person (or the recognized person in view)
                self._json(
                    {"result": novi.association_query(data)}
                    if novi.mm_runtime
                    else {"error": "integration unavailable"}
                )
            elif path == "/api/recognition/proposals":
                self._json(
                    {"result": novi.proposal_list()} if novi.mm_runtime else {"error": "integration unavailable"}
                )
            elif path == "/api/recognition/name-object":
                self._json(
                    {"result": novi.name_proposal_object(data)}
                    if novi.mm_runtime
                    else {"error": "integration unavailable"}
                )
            else:
                self._json({"error": "unknown endpoint"}, 404)
        except Exception as exc:  # noqa: BLE001
            self._json({"error": str(exc)}, 500)


class NoviWebHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, addr: Any, novi: NoviWebServer) -> None:
        self.novi = novi
        super().__init__(addr, Handler)

    def handle_error(self, request, client_address):  # type: ignore[override]
        import sys

        exc_type, exc = sys.exc_info()[:2]
        # Expected when a browser/SSE client disconnects mid-request (reload, close tab,
        # EventSource reconnect). Suppress the noisy traceback that ThreadingMixIn.prints.
        if isinstance(exc, (ConnectionResetError, BrokenPipeError, OSError)):
            return
        super().handle_error(request, client_address)


def main() -> None:
    # Silence verified-benign third-party startup noise (torchao import notes,
    # transformers load bars) before any heavy component loads below.
    from novi.brain.third_party_quiet import quiet_third_party_startup_noise

    quiet_third_party_startup_noise()
    parser = argparse.ArgumentParser(description="Novi Mac Brain live web app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--store", default=None, help="durable SQLite DB path")
    parser.add_argument("--tick", type=float, default=0.8, help="seconds per auto-step")
    parser.add_argument("--no-auto-step", action="store_true", help="advance only on manual 'step'")
    parser.add_argument(
        "--camera",
        choices=["demo", "real"],
        default="demo",
        help="'demo' = no-hardware camera; 'real' = live webcam + real speech-to-text",
    )
    parser.add_argument(
        "--reasoning",
        choices=["deterministic", "ollama", "router"],
        default="router",
        help="brain decision backend; 'router' escalates uncertain steps to the local LLM (default: router — falls back to deterministic when Ollama is offline)",
    )
    parser.add_argument(
        "--route-threshold",
        type=float,
        default=0.6,
        help="confidence below which the router escalates to the local LLM",
    )
    parser.add_argument(
        "--ollama-model",
        type=str,
        default=None,
        help="Ollama model for reasoning + chat replies (default: nemotron-3.5-lightning, or the last UI-selected model)",
    )
    parser.add_argument(
        "--model",
        dest="model",
        type=str,
        default=None,
        help="default chat model; falls back to the persisted UI selection, then nemotron-3.5-lightning (switch at runtime via the UI)",
    )
    parser.add_argument(
        "--trained-reply",
        action="store_true",
        help="reply with the trained dialogue/emotional LoRA adapters (plan 25) instead of the Ollama chat model",
    )
    parser.add_argument(
        "--trained-dialogue-adapter",
        type=str,
        default="",
        help="path to the trained dialogue LoRA adapter dir (required with --trained-reply)",
    )
    parser.add_argument(
        "--trained-emotional-adapter",
        type=str,
        default="",
        help="path to the trained emotional LoRA adapter dir (optional with --trained-reply)",
    )
    parser.add_argument(
        "--trained-base-model",
        type=str,
        default="Qwen/Qwen3-8B",
        help="base model for the trained adapters (default: Qwen/Qwen3-8B)",
    )
    parser.add_argument(
        "--say-voice",
        type=str,
        default=None,
        help="macOS `say` voice for speak-back (default: system voice; same voice as terminal --say-voice)",
    )
    parser.add_argument(
        "--llm-server",
        choices=["ollama", "openai-compatible"],
        default="ollama",
        help="chat wire dialect: 'ollama' speaks the native /api/* endpoints (default); "
        "'openai-compatible' speaks /v1 so llama.cpp, vLLM, and TensorRT-LLM frontends work",
    )
    parser.add_argument(
        "--tts-provider",
        choices=["say", "piper"],
        default="say",
        help="TTS backend for speak-back: 'say' (macOS) or 'piper' (Jetson-body neural voice)",
    )
    parser.add_argument(
        "--tts-voice-model",
        type=str,
        default="",
        help="Piper voice model (.onnx) for --tts-provider piper",
    )
    parser.add_argument(
        "--stt-model",
        type=str,
        default="base",
        help="faster-whisper model size for real microphone STT (tiny/base/small)",
    )
    parser.add_argument("--stt-device", type=str, default="cpu", help="STT device (cpu or mps)")
    parser.add_argument(
        "--listen-seconds", type=float, default=3.0, help="microphone recording length for the Listen button"
    )
    parser.add_argument(
        "--no-event-autonomy", action="store_true", help="disable proactive speech from camera/presence events"
    )
    parser.add_argument(
        "--sleep-every",
        type=int,
        default=500,
        help="run the memory sleep-cycle (consolidate/decay/strengthen) every N brain cycles (0 disables)",
    )
    parser.add_argument(
        "--embedder",
        choices=["auto", "hash", "minilm"],
        default="auto",
        help="embedding provider for memory recall: 'auto' tries MiniLM (MPS, 384d) then falls back to hashing; 'hash' forces deterministic hashing (256d)",
    )
    args = parser.parse_args()

    novi = NoviWebServer(
        host=args.host,
        port=args.port,
        store_path=args.store,
        tick=args.tick,
        auto_step=not args.no_auto_step,
        camera=args.camera,
        reasoning=args.reasoning,
        route_threshold=args.route_threshold,
        llm_model=args.ollama_model or args.model,
        trained_reply_enabled=args.trained_reply,
        trained_dialogue_adapter=args.trained_dialogue_adapter,
        trained_emotional_adapter=args.trained_emotional_adapter,
        trained_base_model=args.trained_base_model,
        say_voice=args.say_voice,
        tts_provider=args.tts_provider,
        tts_voice_model=args.tts_voice_model,
        llm_server=args.llm_server,
        stt_model=args.stt_model,
        persist_model=True,
        stt_device=args.stt_device,
        listen_seconds=args.listen_seconds,
        sleep_every_n_cycles=args.sleep_every,
        embedder=args.embedder,
        event_autonomy=not args.no_event_autonomy,
    )
    httpd = NoviWebHTTPServer((args.host, args.port), novi)
    novi.start()
    print(f"Novi live web app -> http://{args.host}:{args.port}")
    print(f"  camera={args.camera} reasoning={args.reasoning} model={novi.llm_model}")
    print("Ctrl-C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        novi.stop()


if __name__ == "__main__":
    main()
