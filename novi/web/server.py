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
import json
import re
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from novi.brain.audio import AudioFrame
from novi.brain.autonomy import Goal
from novi.brain.contracts import utc_now
from novi.web.integration_api import IntegrationMixin
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.b2_perception import SpecialistPerception
from novi.brain.io import CameraFrame
from novi.brain.models.ollama_reasoning import DEFAULT_OLLAMA_MODEL, DEFAULT_OLLAMA_URL
from novi.brain.models.stt import TranscriptionResult

_ROUTED = Path(__file__).resolve().parent


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


class NoviWebServer(IntegrationMixin):
    """Owns a MacBrain and drives it from HTTP requests."""

    def __init__(
        self,
        *,
        host: str = "127.0.0.1",
        port: int = 8080,
        store_path: str | None = None,
        tick: float = 0.8,
        auto_step: bool = True,
        chat_llm: bool = True,
        llm_url: str = DEFAULT_OLLAMA_URL,
        llm_model: str = DEFAULT_OLLAMA_MODEL,
        camera: str = "demo",
        reasoning: str = "router",
        route_threshold: float = 0.6,
        stt_model: str = "base",
        stt_device: str = "cpu",
        listen_seconds: float = 3.0,
        sleep_every_n_cycles: int = 500,
        available_models: tuple[str, ...] = ("qwen3:32b", "qwen3:8b", "qwen3:4b", "nemotron-3.5-lightning"),
        embedder: str = "auto",
    ) -> None:
        self.host = host
        self.port = port
        self.store_path = store_path
        self.tick = tick
        self.auto_step = auto_step
        self.sleep_every_n_cycles = max(0, int(sleep_every_n_cycles))
        self.chat_llm = chat_llm
        self.llm_url = llm_url
        self.available_models = list(available_models)
        if llm_model not in self.available_models and llm_model != DEFAULT_OLLAMA_MODEL:
            self.available_models.insert(0, llm_model)
        self.llm_model = llm_model
        self.camera_mode = camera
        self.reasoning_mode = reasoning
        self.route_threshold = route_threshold
        self.stt_model = stt_model
        self.stt_device = stt_device
        self.listen_seconds = listen_seconds
        self.embedder_mode = embedder
        self._llm_available: bool | None = None
        self._llm_probed_at: float = 0.0
        # How often to re-probe Ollama availability so a server that started
        # before the LLM was ready can reconnect without a restart.
        self._llm_probe_ttl = 3.0
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        # deduplication: track the last sent text + timestamp to reject
        # duplicate sends (double-click, Enter key race) within a short window.
        self._last_sent_text: str = ""
        self._last_sent_time: float = 0.0
        self._dedup_window_seconds: float = 15.0
        # event log with stable seq numbers (bounded)
        self._seen = 0
        self._seq = 0
        self._log: list[dict[str, Any]] = []
        # chat conversation (user <-> Novi reasoning responses)
        self._chat_seq = 0
        self._chat: list[dict[str, Any]] = []
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
            try:
                self.real_enable(camera=True, mic=True, speaker=True)
            except Exception:  # noqa: BLE001 - hardware optional
                pass

    def _build_conversation_summarizer(self) -> Any:
        """LLM conversation summarizer when Ollama is available."""
        from novi.brain.models.conversation_summarizer import ConversationSummarizer

        inner = ConversationSummarizer(model=self.llm_model)

        def fast_conv_summarizer(turns):  # type: ignore[no-untyped-def]
            if not self.chat_llm or not self._llm_up():
                return None
            return inner(turns)

        fast_conv_summarizer.model = inner.model  # type: ignore[attr-defined]
        fast_conv_summarizer.base_url = inner.base_url  # type: ignore[attr-defined]
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
            config=MacBrainConfig(initiative_enabled=True, sleep_every_n_cycles=self.sleep_every_n_cycles),
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

        inner = LLMNarrator(model=self.llm_model)

        def fast_narrator(episodes):  # type: ignore[no-untyped-def]
            # When chat LLM is disabled or Ollama is offline, fail fast instead of 5s LLM timeout.
            if not self.chat_llm or not self._llm_up():
                return None
            return inner(episodes)

        # Attach inner for introspection, but expose fast wrapper as callable
        fast_narrator.model = inner.model  # type: ignore[attr-defined]
        fast_narrator.base_url = inner.base_url  # type: ignore[attr-defined]
        return fast_narrator

    def _build_summary_consolidator(self) -> Any:
        """SummaryConsolidator with an LLM summarizer when Ollama is available."""
        from novi.brain.consolidation import SummaryConsolidator
        from novi.brain.models.summarizer import LLMSummarizer

        inner = LLMSummarizer(model=self.llm_model)

        def fast_summarizer(entity, records):  # type: ignore[no-untyped-def]
            if not self.chat_llm or not self._llm_up():
                return None
            return inner(entity, records)

        fast_summarizer.model = inner.model  # type: ignore[attr-defined]
        fast_summarizer.base_url = inner.base_url  # type: ignore[attr-defined]
        return SummaryConsolidator(None, summarizer=fast_summarizer)

    def _build_reasoning(self) -> Any:
        mode = self.reasoning_mode
        if mode in ("ollama", "router"):
            from novi.brain.models import DeliberativeLLMReasoningProvider

            llm = DeliberativeLLMReasoningProvider(model=self.llm_model)
            if mode == "router":
                from novi.brain.models.router import ReasoningRouter

                return ReasoningRouter(llm=llm, confidence_threshold=self.route_threshold)
            return llm
        return None  # MacBrain defaults to DeterministicReasoningProvider

    def _build_stt(self) -> Any:
        try:
            from novi.brain.models.stt import WhisperSTTProvider

            return WhisperSTTProvider(model_size=self.stt_model, device=self.stt_device)
        except Exception:  # noqa: BLE001 - STT optional; brain falls back to deterministic
            return None

    # ---- lifecycle ----
    def start(self) -> None:
        self.brain.start()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="novi-brain-loop")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        with self._lock:
            try:
                self.brain.stop()
            except Exception:  # noqa: BLE001 - shutdown best-effort
                pass

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
        if len(self._log) > 500:
            self._log = self._log[-500:]

    def _drain(self) -> None:
        """Pull newly emitted brain events into the bounded event log."""
        with self._lock:
            new = list(self.brain.events[self._seen:])
            self._seen = len(self.brain.events)
            for ev in new:
                self._seq += 1
                self._log.append({"seq": self._seq, "ts": time.time(), "event": ev})
                if ev.get("event_type") == "speech.initiated":
                    # Surface Novi's unprompted remark as a conversation turn so
                    # the chat UI shows it (rule 5). Appended directly (no LLM
                    # summarizer here) to avoid a model call under the runtime lock.
                    p = ev.get("payload", {})
                    self._chat_seq += 1
                    self._chat.append({"seq": self._chat_seq, "role": "novi", "text": str(p.get("text", "")), "trace": {"action": "initiate", "route": "initiative", "conclusion": str(p.get("text", "")), "rationale": str(p.get("reason", "")), "cycle": ev.get("cycle")}, "cycle": ev.get("cycle"), "llm": False})
                    if len(self._chat) > 200:
                        self._chat = self._chat[-200:]
                    self._persist_chat()
            if len(self._log) > 500:
                self._log = self._log[-500:]
            if self._seen > 10000:
                self.brain.events = self.brain.events[-1000:]
                self._seen = len(self.brain.events)

    def hear(self, text: str, confidence: float = 0.9) -> dict[str, Any]:
        # Unified input path (north star §4.2): submit through the brain's bus;
        # the next cognition cycle ingests it like any other source. The reply
        # composition still happens here (synchronous HTTP contract) via
        # respond() with the LLM outside the lock (§4.4).
        self.brain.submit("web", "chat", {"text": self._clean_chat_text(text)})
        with self._lock:
            r = self.brain.ingest_transcript(TranscriptionResult(text=self._clean_chat_text(text), language="en", confidence=confidence, audio_path="", provider="web", model_id="web"))
        adm = r["admission"]
        return {"accepted": adm.accepted, "memory_id": adm.memory_id, "reasoning": r["reasoning"], "confidence": r["confidence"]}

    def _clean_chat_text(self, text: str) -> str:
        """Strip the '[heard] ' display marker before text reaches the LLM/history,
        so Novi doesn't think the user addressed 'the system' or a 'heard' marker."""
        return re.sub(r"^\s*\[heard\]\s*", "", text)

    def _build_history(self, limit: int = 12) -> list[dict[str, Any]]:
        return [{"role": c["role"], "text": self._clean_chat_text(c["text"])} for c in self._chat[-limit:]]

    def _recent_novi(self, limit: int = 4) -> list[str]:
        return [self._clean_chat_text(c["text"]) for c in reversed(self._chat) if c.get("role") == "novi"][:limit]

    def chat_send(self, text: str, confidence: float = 0.9) -> dict[str, Any]:
        """Hear the user message, let the brain decide, and append a chat turn."""
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
            if (text == self._last_sent_text
                    and (now - self._last_sent_time) < self._dedup_window_seconds):
                # Return the last novi if available; otherwise a bare dedup marker.
                # Do not create new rows — the previous turn is still in-flight.
                for c in reversed(self._chat):
                    if c.get("role") == "novi":
                        return {"novi": c, "accepted": True, "memory_id": None, "llm": c.get("llm", False), "deduplicated": True, "after": self._chat_seq}
                return {"accepted": False, "deduplicated": True, "after": self._chat_seq}
            self._last_sent_text = text
            self._last_sent_time = now

        # Unified input path (north star §4.2/4.4): submit through the bus so
        # this message is one input among many (a home-voice turn may arrive in
        # the same cycle), then ingest + step under a short lock, and compose
        # the reply with the LLM OUTSIDE the lock.
        self.brain.submit("web", "chat", {"text": text})
        # Hold the brain's speaking lease while composing so a concurrent step
        # cannot fire a duplicate initiative (replaces the old _chat_busy
        # loop-freeze; the loop keeps ticking — SCENARIO-V1).
        self.brain.acquire_speaking_lease()
        try:
            with self._lock:
                r = self.brain.ingest_transcript(TranscriptionResult(text=text, language="en", confidence=confidence, audio_path="", provider="web", model_id="web"))
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
            history = self._build_history(12)
            recent_novi = self._recent_novi(4)
            last_novi = next((c["text"] for c in reversed(self._chat) if c.get("role") == "novi"), "")
            transport = self._llm_chat if (self.chat_llm and self._llm_up()) else None
            resp = self.brain.respond(
                text, history=history, llm_chat=transport,
                last_novi_text=last_novi, recent_novi=recent_novi, learn=True,
            )
            novi_text = resp.get("text")
            reply_source = resp.get("reply_source", "dialogue")
            llm = reply_source == "dialogue"
            # The trace always records the real cognition conclusion; only the
            # spoken text is rendered naturally. For a dialogue reply the conclusion
            # is the reply; for a deterministic fallback it stays the cognition label.
            trace["conclusion"] = novi_text if llm else conclusion
            trace["action"] = "respond"
            trace["rationale"] = resp.get("reason") or "Natural reply grounded in recalled knowledge, relationships and self-state."
            if llm:
                trace["route"] = f"ollama:{self.llm_model}"
                trace["route_reason"] = "local LLM"
                trace["confidence"] = 0.85
            else:
                trace["route"] = "deterministic"
                trace["route_reason"] = "no_llm_transport"
                trace["confidence"] = heard_conf
            novi = {"role": "novi", "text": novi_text, "trace": trace, "cycle": step.get("cycle"), "llm": llm}
            self._append_chat({"role": "user", "text": text})
            self._append_chat(novi)
            return {"novi": novi, "accepted": bool(adm.accepted), "memory_id": adm.memory_id, "llm": llm}
        finally:
            self.brain.release_speaking_lease()

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
        # Hold the speaking lease while composing (replaces _chat_busy loop-freeze).
        self.brain.acquire_speaking_lease()
        try:
            # Brain-owned reply orchestration (north-star R1/R3): the brain
            # resolves the addressee, learns from the message, and composes the
            # natural reply (or the deterministic fallback) in one call. The web
            # layer only supplies conversation history and the LLM transport.
            history = self._build_history(12)
            recent_novi = self._recent_novi(4)
            last_novi = next((c["text"] for c in reversed(self._chat) if c.get("role") == "novi"), "")
            transport = self._llm_chat if (self.chat_llm and self._llm_up()) else None
            resp = self.brain.respond(
                text, history=history, llm_chat=transport,
                last_novi_text=last_novi, recent_novi=recent_novi, learn=True,
            )
            novi_text = resp.get("text")
            reply_source = resp.get("reply_source", "dialogue")
            llm = reply_source == "dialogue"
            # The trace always records the real cognition conclusion; only the
            # spoken text is rendered naturally.
            trace["conclusion"] = novi_text if llm else result["reasoning"]
            trace["action"] = "respond"
            trace["rationale"] = resp.get("reason") or "Natural reply grounded in recalled knowledge, relationships and self-state."
            if llm:
                trace["route"] = f"ollama:{self.llm_model}"
                trace["route_reason"] = "local LLM"
                trace["confidence"] = 0.85
            else:
                trace["route"] = "deterministic"
                trace["route_reason"] = "no_llm_transport"
                trace["confidence"] = result.get("confidence", 0.8)
            novi = {"role": "novi", "text": novi_text, "trace": trace, "cycle": step.get("cycle"), "llm": llm}
            self._append_chat({"role": "user", "text": f"[heard] {text}"})
            self._append_chat(novi)
            return {"heard": text, "accepted": True, "novi": novi, "llm": llm}
        finally:
            self.brain.release_speaking_lease()

    def _llm_up(self) -> bool:
        # Re-probe when the cached result is stale so a server that started
        # before Ollama was reachable (or when a model was still loading)
        # reconnects automatically instead of staying offline forever.
        now = time.time()
        if self._llm_available is None or (now - self._llm_probed_at) > self._llm_probe_ttl:
            try:
                req = urllib.request.Request(f"{self.llm_url}/api/tags", method="GET")
                with urllib.request.urlopen(req, timeout=2) as response:
                    self._llm_available = response.status == 200
            except Exception:  # noqa: BLE001 - offline fallback
                self._llm_available = False
            self._llm_probed_at = now
        return self._llm_available

    def model(self) -> dict[str, Any]:
        return {"current": self.llm_model, "available": list(self.available_models)}

    def switch_model(self, name: str) -> dict[str, Any]:
        """Switch the chat/reasoning LLM at runtime (kept models: qwen + nemotron)."""
        name = name.strip()
        if name not in self.available_models:
            raise ValueError(f"unknown model '{name}'; available: {self.available_models}")
        self.llm_model = name
        self._llm_available = None  # re-probe availability for the new model
        return {"current": self.llm_model, "available": list(self.available_models)}

    def _llm_chat(self, *, system: str, user: str, temperature: float = 0.5, timeout: int = 120) -> str | None:
        options: dict[str, Any] = {"temperature": temperature, "num_predict": 512}
        payload: dict[str, Any] = {
            "model": self.llm_model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "stream": False,
            "options": options,
        }
        if "nemotron" in self.llm_model.lower():
            # NVIDIA Nemotron 3.5 Lightning is a chain-of-thought model; set the
            # top-level `think:false` so chat replies are instant instead of
            # exhausting the token budget mid-thought (empty content field).
            payload["think"] = False
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(f"{self.llm_url}/api/chat", data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        message = data.get("message", {}) or {}
        reply = (message.get("content") or "").strip()
        if reply:
            return reply
        # Reasoning models (e.g. NVIDIA Nemotron 3.5 Lightning) may emit only a
        # chain-of-thought; surface its final line as a fallback.
        thinking = (message.get("thinking") or "").strip()
        if thinking:
            return thinking.splitlines()[-1].strip() or None
        return None

    def _llm_chat_stream(self, *, system: str, user: str, temperature: float = 0.5, timeout: int = 120):
        """Yield token deltas from Ollama with stream=True (SSE-like)."""
        options: dict[str, Any] = {"temperature": temperature, "num_predict": 512}
        payload: dict[str, Any] = {
            "model": self.llm_model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "stream": True,
            "options": options,
        }
        if "nemotron" in self.llm_model.lower():
            payload["think"] = False
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(f"{self.llm_url}/api/chat", data=body, headers={"Content-Type": "application/json"})
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

    def chat_send_stream(self, text: str, confidence: float = 0.9):
        """Streaming variant of chat_send: yields {'token': str} then {'done': novi}."""
        text = self._clean_chat_text(text)
        import time as _time
        now = _time.time()
        with self._lock:
            if (text == self._last_sent_text and (now - self._last_sent_time) < self._dedup_window_seconds):
                # Deduplicated: do NOT create new chat rows. This handles double-click
                # races where the second request arrives while the first is still
                # in-flight and hasn't yet appended to _chat (so checking last role
                # would fail and allow a duplicate).
                # Return the last novi if available, otherwise a bare dedup marker.
                last_novi = None
                for c in reversed(self._chat):
                    if c.get("role") == "novi":
                        last_novi = c
                        break
                if last_novi is not None:
                    yield {"deduplicated": True, "novi": last_novi, "after": self._chat_seq, "accepted": True, "memory_id": None, "llm": last_novi.get("llm", False)}
                else:
                    yield {"deduplicated": True, "after": self._chat_seq, "accepted": False}
                return
            self._last_sent_text = text
            self._last_sent_time = now
        # Hold the speaking lease while composing (replaces _chat_busy loop-freeze).
        self.brain.acquire_speaking_lease()
        try:
            with self._lock:
                r = self.brain.ingest_transcript(TranscriptionResult(text=text, language="en", confidence=confidence, audio_path="", provider="web", model_id="web"))
                adm = r["admission"]
                conclusion = r["reasoning"]
                heard_conf = r["confidence"]
                step = self.brain.step()
                trace = dict(self.brain._last_reasoning_trace)
            history = self._build_history(12)
            addressee = self.brain.resolve_addressee(text)
            discourse_hint = self.brain.note_user_message(text)["resolved_topic"]
            self.brain._learn_from_chat(text, addressee)
            recent_novi = self._recent_novi(4)
            last_novi = next((c["text"] for c in reversed(self._chat) if c.get("role") == "novi"), "")
            # If LLM is down, fallback without streaming.
            if not (self.chat_llm and self._llm_up()):
                fb = self.brain.natural_reply_fallback(text=text, cycle=step.get("cycle"))
                trace["conclusion"] = conclusion
                trace["action"] = "respond"
                trace["rationale"] = fb.get("reason") or "No LLM reply available; used a natural acknowledgement."
                trace["route"] = "deterministic"
                trace["route_reason"] = "no_llm_transport"
                trace["confidence"] = heard_conf
                novi_text = fb["text"]
                # Stream the fallback as one chunk for uniform UI handling.
                for ch in [novi_text[i:i+12] for i in range(0, len(novi_text), 12)]:
                    yield {"token": ch}
                novi = {"role": "novi", "text": novi_text, "trace": trace, "cycle": step.get("cycle"), "llm": False}
                user_stored = self._append_chat({"role": "user", "text": text})
                novi_stored = self._append_chat(novi)
                yield {"done": True, "user": user_stored, "novi": novi_stored, "accepted": bool(adm.accepted), "memory_id": adm.memory_id, "llm": False, "after": self._chat_seq}
                return
            # Streaming path: we need to capture the system/user that compose_reply would build
            # to call _llm_chat_stream ourselves, then feed the assembled reply back.
            # Instead of re-implementing compose_reply internals, we monkey-patch a
            # streaming transport that yields tokens while capturing the full reply.
            # Simplest: call compose_reply with a wrapper that streams via _llm_chat_stream.
            streamed_tokens: list[str] = []
            token_yielded = False

            def streaming_transport(*, system: str, user: str, temperature: float = 0.5, timeout: int = 120):
                nonlocal token_yielded
                full = ""
                try:
                    for delta in self._llm_chat_stream(system=system, user=user, temperature=temperature, timeout=timeout):
                        full += delta
                        streamed_tokens.append(delta)
                        token_yielded = True
                        yield delta  # not used directly — we yield from outer
                except Exception:
                    # Fall back to non-streaming
                    result = self._llm_chat(system=system, user=user, temperature=temperature, timeout=timeout)
                    if result:
                        full = result
                        streamed_tokens.append(result)
                        token_yielded = True
                        yield result
                # The wrapper must return the full text for compose_reply's contract.
                # Since Python generators can't return via yield, we store on the function.
                streaming_transport.full = full  # type: ignore[attr-defined]
                return full

            # We need to actually drive compose_reply in a way that streams.
            # Workaround: manually reproduce compose_reply's prompt assembly but call
            # _llm_chat_stream directly, streaming tokens as they arrive.
            # For now, call brain.compose_reply with a transport that internally
            # captures tokens and yields them via closure — we do this by calling
            # compose_reply in a thread and forwarding tokens? Simpler: directly
            # call brain's internal helpers if available, else just stream the final reply.
            # Fallback simple: call compose_reply non-streaming to get the full reply,
            # then stream it token-chunked (still feels streaming without NDJSON complexity).
            # This preserves correctness while delivering the UX improvement.
            # We attempt true streaming when the brain exposes _compose_system_prompt.
            full_reply_obj = self.brain.compose_reply(
                text, person=addressee, history=history, llm_chat=self._llm_chat,
                last_novi_text=last_novi, addressee_name=addressee, recent_novi=recent_novi,
                topic_hint=discourse_hint,
            )
            full_reply = full_reply_obj.get("text") if full_reply_obj else None
            if full_reply is None:
                fb = self.brain.natural_reply_fallback(text=text, cycle=step.get("cycle"))
                trace["conclusion"] = conclusion
                trace["action"] = "respond"
                trace["rationale"] = fb.get("reason") or "No LLM reply available; used a natural acknowledgement."
                trace["route"] = "deterministic"
                trace["route_reason"] = "no_llm_transport"
                trace["confidence"] = heard_conf
                novi_text = fb["text"]
                for ch in [novi_text[i:i+16] for i in range(0, len(novi_text), 16)]:
                    yield {"token": ch}
                novi = {"role": "novi", "text": novi_text, "trace": trace, "cycle": step.get("cycle"), "llm": False}
                user_stored = self._append_chat({"role": "user", "text": text})
                novi_stored = self._append_chat(novi)
                yield {"done": True, "user": user_stored, "novi": novi_stored, "accepted": bool(adm.accepted), "memory_id": adm.memory_id, "llm": False, "after": self._chat_seq}
                return
            # We have a full reply; stream it in small chunks to simulate token streaming
            # (true NDJSON streaming would require deeper brain integration; this chunked
            # approach delivers the same perceived latency improvement without fragility).
            trace["conclusion"] = full_reply
            trace["action"] = "respond"
            trace["rationale"] = full_reply_obj.get("reason") or "Natural reply grounded in recalled knowledge, relationships and self-state."
            trace["route"] = f"ollama:{self.llm_model}"
            trace["route_reason"] = "fallback" if full_reply_obj.get("fallback") else "local LLM"
            trace["confidence"] = 0.8 if full_reply_obj.get("fallback") else 0.85
            # Stream the reply in ~18-char chunks with no artificial delay (network is the bottleneck)
            chunk_size = 14
            for i in range(0, len(full_reply), chunk_size):
                yield {"token": full_reply[i:i+chunk_size]}
            novi = {"role": "novi", "text": full_reply, "trace": trace, "cycle": step.get("cycle"), "llm": True}
            user_stored = self._append_chat({"role": "user", "text": text})
            novi_stored = self._append_chat(novi)
            yield {"done": True, "user": user_stored, "novi": novi_stored, "accepted": bool(adm.accepted), "memory_id": adm.memory_id, "llm": True, "after": self._chat_seq}
        finally:
            self.brain.release_speaking_lease()

    def _knowledge_context(self, text: str, limit: int = 6) -> str:
        # Brain-owned grounding (docs/06-soul/07 §2); the web layer is a caller
        # of the mind, not an owner of it.
        return self.brain._chat_knowledge(text, limit=limit)

    def _known_persons(self) -> list[str]:
        return self.brain._chat_known_persons()

    def _memory_context(self, limit: int = 3) -> list[str]:
        """Recent consolidated summary memories for chat grounding (summary recall)."""
        return self.brain._chat_memory_summaries(limit=limit)

    def _append_chat(self, entry: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self._chat_seq += 1
            stored = {"seq": self._chat_seq, **entry}
            self._chat.append(stored)
            if len(self._chat) > 200:
                self._chat = self._chat[-200:]
            # copy for persistence outside the lock to keep the lock short
            snapshot = list(self._chat)
        self._persist_chat_snapshot(snapshot)
        self._maybe_summarize_chat()
        return stored

    def _persist_chat_snapshot(self, snapshot: list[dict[str, Any]]) -> None:
        store = getattr(self.brain, "memory", None)
        if store is None or not hasattr(store, "save_chat"):
            return
        try:
            store.save_chat(snapshot)
        except Exception:
            pass


    def _maybe_summarize_chat(self, threshold: int = 20, keep_recent: int = 8) -> None:
        """When the thread grows long, distill the older turns into a durable summary.

        Gated so the LLM summarizer only runs once the thread has grown by
        `keep_recent` new turns since the last summary (not on every append),
        which avoids a slow LLM call under the runtime lock on every message.
        """
        if len(self._chat) <= threshold:
            return
        if (self._last_summarized_len is not None
                and len(self._chat) - self._last_summarized_len < keep_recent):
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
        try:
            self.brain.memory.admit(
                memory_type="conversation_summary",
                content=summary,
                confidence=0.8,
                verification_status="consolidated",
                privacy_class="public",
                provenance={"source": "conversation_summarization", "kind": "thread_summary"},
            )
        except Exception:  # noqa: BLE001 - summary admission is best-effort
            pass
        self._chat = recent
        self._last_summarized_len = len(self._chat)
        self._persist_chat()

    def _persist_chat(self) -> None:
        """Persist the chat thread to the durable store (conversation persistence)."""
        # snapshot under lock, persist outside to avoid holding lock during I/O
        with self._lock:
            snapshot = list(self._chat)
        self._persist_chat_snapshot(snapshot)

    def chat(self, after: int = 0) -> dict[str, Any]:
        with self._lock:
            entries = [c for c in self._chat if c["seq"] > after]
            next_after = self._chat[-1]["seq"] if self._chat else after
            # return copies to avoid caller mutating live list
            return {"entries": [dict(e) for e in entries], "after": next_after}

    def clear_chat(self) -> dict[str, Any]:
        """Drop the live conversation thread (durable store is updated)."""
        with self._lock:
            self._chat = []
            self._chat_seq = 0
            self._persist_chat()
        return {"cleared": True}

    def hear_audio(self, *, event_hint: str | None, rms: float, novelty: float = 0.0, speech: bool = False, confidence: float = 0.0) -> dict[str, Any]:
        frame = AudioFrame(rms=float(rms), speech=speech, event_hint=event_hint, hint_confidence=float(confidence) if confidence else 0.0, novelty=float(novelty))
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
            return {"goal_id": state.goal.goal_id, "kind": state.goal.kind, "target": [state.goal.target[0], state.goal.target[1]], "status": state.status.value}

    def health(self) -> dict[str, Any]:
        with self._lock:
            return self.brain.health_report()

    def poll_events(self, after: int) -> dict[str, Any]:
        self._drain()
        entries = [e for e in self._log if e["seq"] > after]
        next_after = self._log[-1]["seq"] if self._log else after
        return {"events": entries, "after": next_after}

    def state(self) -> dict[str, Any]:
        with self._lock:
            step = self._last_step
            body = self.brain.body.snapshot() if hasattr(self.brain.body, "snapshot") else {"x_m": self.brain.body.x_m, "y_m": self.brain.body.y_m, "heading_deg": self.brain.body.heading_deg}
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
                "active_goal": {"goal_id": active_goal.goal.goal_id, "kind": active_goal.goal.kind, "target": str(active_goal.goal.target), "steps_taken": active_goal.steps_taken, "status": active_goal.status.value, "distance_to_goal": distance} if active_goal is not None else None,
                "plan": plan,
                "goals_history": goals,
                "knowledge": self.brain.knowledge.counts(),
                "hearing": self.brain._last_audio_events,
                "memory": {"active": getattr(self.brain.memory, "active_count", None), "summaries": self._memory_summaries(), "embedder": self._embedding_info()},
                "narrative": self.brain._episodic_narrative(),
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
            return {"provider": provider, "dimension": dim, "available": available, "error": err, "mode": getattr(self, "embedder_mode", "auto")}
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
                    pkg = self.brain._assemble_world_context("", person="")
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
                    out.append({
                        "memory_id": r.memory_id,
                        "memory_type": r.memory_type,
                        "content": r.content if isinstance(r.content, str) else str(r.content),
                        "confidence": r.confidence,
                        "entity_refs": list(r.entity_refs),
                        "created_at": r.created_at,
                    })
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

    def do_GET(self) -> None:
        path = self.path.split("?")[0]
        if path == "/api/events/stream":
            # Server-Sent Events: push brain events as they appear (replaces polling)
            from urllib.parse import parse_qs, urlparse
            try:
                after = int(parse_qs(urlparse(self.path).query).get("after", ["0"])[0])
            except Exception:
                after = 0
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
            heartbeat_interval = 12.0
            last_beat = time.time()
            while not self.server.novi._stop.is_set():
                try:
                    chunk = self.server.novi.poll_events(last)
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
                if self.server.novi._stop.wait(0.25):
                    break
            return
        if path in ("/", "/index.html"):
            html = (_ROUTED / "static" / "index.html").read_text(encoding="utf-8")
            self._send(200, html.encode("utf-8"), "text/html")
            return
        if path in ("/camera", "/camera.html", "/live"):
            html = (_ROUTED / "static" / "camera.html").read_text(encoding="utf-8")
            self._send(200, html.encode("utf-8"), "text/html")
            return
        if path == "/api/state":
            self._json(self.server.novi.state())
            return
        if path == "/api/model":
            self._json(self.server.novi.model())
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
            self._json(self.server.novi.chat(after))
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
        if path == "/preview":
            html = (_ROUTED / "static" / "preview.html").read_text(encoding="utf-8")
            self._send(200, html.encode("utf-8"), "text/html")
            return
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
        if path == "/api/preview":
            self._json(novi.preview_frame() if novi.mm_runtime else {"error": "integration unavailable"})
            return
        # ---- real I/O (doc 17) ----
        if path == "/api/real/status":
            self._json({
                "enabled": novi.real_io_enabled,
                "devices": dict(novi.real_io),
                "speak_back": novi.speak_back_enabled,
            })
            return
        if path == "/api/real/speakback":
            pass  # handled in POST below; GET returns current state only
        if path == "/api/p0-gate":
            with self.server.novi._lock:
                result = self.server.novi.brain.p0_gate()
            self._json(result)
            return
        self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:
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
                    try:
                        gen.close()
                    except Exception:
                        pass
                    # Ensure the speaking lease is released even if the client
                    # disconnected mid-stream before the generator's own finally ran.
                    try:
                        with self.server.novi._lock:
                            self.server.novi.brain.release_speaking_lease()
                    except Exception:
                        pass
                # Ensure the connection closes so the client's fetch stream sees EOF.
                try:
                    self.close_connection = True
                except Exception:
                    pass
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
            elif path == "/api/chat":
                text = str(data.get("text", "")).strip()
                if not text:
                    self._json({"error": "empty text"})
                    return
                self._json({"result": novi.chat_send(text, confidence=float(data.get("confidence", 0.9)))})
            elif path == "/api/audio":
                self._json({"result": novi.hear_audio(event_hint=data.get("event_hint"), rms=data.get("rms", 0.6), novelty=data.get("novelty", 0.0), speech=bool(data.get("speech", False)), confidence=float(data.get("confidence", 0.0)))})
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
                self._json({"result": novi.set_goal(x=data.get("x", 1.0), y=data.get("y", 1.0), max_steps=int(data.get("max_steps", 60)))})
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
                    self._json({"result": {"episode_id": episode.episode_id, "step_count": len(episode.steps), "format": fmt, "export": exported}})
            elif path == "/api/episode/status":
                with novi._lock:
                    self._json({"result": {"recording": novi.brain.is_recording, "step_count": novi.brain.recording_step_count}})
            elif path == "/api/perception/frame":
                self._json({"result": novi.perception_frame(data)} if novi.mm_runtime else {"error": "integration unavailable"})
            elif path == "/api/voice/turn":
                self._json({"result": novi.voice_turn(data)} if novi.mm_runtime else {"error": "integration unavailable"})
            elif path == "/api/recognition/person":
                self._json({"result": novi.recognize_person(data)} if novi.mm_runtime else {"error": "integration unavailable"})
            elif path == "/api/recognition/enroll":
                self._json({"result": novi.enroll_place_or_noise(data)} if novi.mm_runtime else {"error": "integration unavailable"})
            elif path == "/api/recognition/privacy":
                self._json({"result": novi.recognition_privacy(data)} if novi.mm_runtime else {"error": "integration unavailable"})
            elif path == "/api/real/enable":
                res = novi.real_enable(
                    camera=bool(data.get("camera", False)),
                    mic=bool(data.get("mic", False)),
                    speaker=bool(data.get("speaker", False)),
                )
                self._json({"result": res})
            elif path == "/api/voice/listen":
                try:
                    self._json({"result": novi.voice_listen(float(data.get("seconds", 3.0)))})
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
    parser = argparse.ArgumentParser(description="Novi Mac Brain live web app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--store", default=None, help="durable SQLite DB path")
    parser.add_argument("--tick", type=float, default=0.8, help="seconds per auto-step")
    parser.add_argument("--no-auto-step", action="store_true", help="advance only on manual 'step'")
    parser.add_argument("--camera", choices=["demo", "real"], default="demo", help="'demo' = no-hardware camera; 'real' = live webcam + real speech-to-text")
    parser.add_argument("--reasoning", choices=["deterministic", "ollama", "router"], default="router", help="brain decision backend; 'router' escalates uncertain steps to the local LLM (default: router — falls back to deterministic when Ollama is offline)")
    parser.add_argument("--route-threshold", type=float, default=0.6, help="confidence below which the router escalates to the local LLM")
    parser.add_argument("--ollama-model", type=str, default=None, help="Ollama model for reasoning + chat replies (default: nemotron-3.5-lightning)")
    parser.add_argument("--model", dest="model", type=str, default="nemotron-3.5-lightning", help="default chat model (switch at runtime via the UI)")
    parser.add_argument("--stt-model", type=str, default="base", help="faster-whisper model size for real microphone STT (tiny/base/small)")
    parser.add_argument("--stt-device", type=str, default="cpu", help="STT device (cpu or mps)")
    parser.add_argument("--listen-seconds", type=float, default=3.0, help="microphone recording length for the Listen button")
    parser.add_argument("--sleep-every", type=int, default=500, help="run the memory sleep-cycle (consolidate/decay/strengthen) every N brain cycles (0 disables)")
    parser.add_argument("--embedder", choices=["auto", "hash", "minilm"], default="auto", help="embedding provider for memory recall: 'auto' tries MiniLM (MPS, 384d) then falls back to hashing; 'hash' forces deterministic hashing (256d)")
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
        stt_model=args.stt_model,
        stt_device=args.stt_device,
        listen_seconds=args.listen_seconds,
        sleep_every_n_cycles=args.sleep_every,
        embedder=args.embedder,
    )
    httpd = NoviWebHTTPServer((args.host, args.port), novi)
    novi.start()
    print(f"Novi live web app -> http://{args.host}:{args.port}")
    print(f"  camera={args.camera} reasoning={args.reasoning} model={args.ollama_model or args.model}")
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
