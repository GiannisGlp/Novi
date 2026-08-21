"""Live web server for the Novi Mac Brain.

A dependency-free (Python stdlib only) local HTTP server that owns a running
MacBrain and serves a browser UI for live interaction: chat/"hear this" input,
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
import os
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from brain.contracts import utc_now

from MAC_BRAIN.audio import AudioFrame
from MAC_BRAIN.autonomy import Goal
from MAC_BRAIN.io import CameraFrame
from MAC_BRAIN.models.ollama_reasoning import DEFAULT_OLLAMA_MODEL, DEFAULT_OLLAMA_URL
from MAC_BRAIN.models.stt import TranscriptionResult
from MAC_BRAIN.runtime import MacBrain, MacBrainConfig

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


class NoviWebServer:
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
        reasoning: str = "deterministic",
        route_threshold: float = 0.6,
        stt_model: str = "base",
        stt_device: str = "cpu",
        listen_seconds: float = 3.0,
        available_models: tuple[str, ...] = ("qwen3.8:latest", "nemotron-3.5-lightning"),
    ) -> None:
        self.host = host
        self.port = port
        self.store_path = store_path
        self.tick = tick
        self.auto_step = auto_step
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
        self._llm_available: bool | None = None
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        # event log with stable seq numbers (bounded)
        self._seen = 0
        self._seq = 0
        self._log: list[dict[str, Any]] = []
        # chat conversation (user <-> Novi reasoning responses)
        self._chat_seq = 0
        self._chat: list[dict[str, Any]] = []
        self.brain = self._build_brain()
        self._last_step: dict[str, Any] | None = None

    # ---- brain construction (real sensing / reasoning router) ----
    def _build_brain(self) -> MacBrain:
        if self.camera_mode == "real":
            from MAC_BRAIN.io import MacCamera

            cam: Any = MacCamera()
        else:
            cam = DemoCamera()
        stt = self._build_stt() if self.camera_mode == "real" else None
        reasoning = self._build_reasoning()
        summary_consolidator = self._build_summary_consolidator()
        narrator = self._build_narrator()
        return MacBrain(camera=cam, stt=stt, reasoning=reasoning, store_path=self.store_path, summary_consolidator=summary_consolidator, narrator=narrator, config=MacBrainConfig())

    def _build_narrator(self) -> Any:
        """LLM narrator for episodic "what happened" recaps when Ollama is available."""
        from MAC_BRAIN.models.narrator import LLMNarrator

        return LLMNarrator(model=self.llm_model)

    def _build_summary_consolidator(self) -> Any:
        """SummaryConsolidator with an LLM summarizer when Ollama is available."""
        from MAC_BRAIN.consolidation import SummaryConsolidator
        from MAC_BRAIN.models.summarizer import LLMSummarizer

        return SummaryConsolidator(None, summarizer=LLMSummarizer(model=self.llm_model))

    def _build_reasoning(self) -> Any:
        mode = self.reasoning_mode
        if mode in ("ollama", "router"):
            from MAC_BRAIN.models import DeliberativeLLMReasoningProvider

            llm = DeliberativeLLMReasoningProvider(model=self.llm_model)
            if mode == "router":
                from MAC_BRAIN.models.router import ReasoningRouter

                return ReasoningRouter(llm=llm, confidence_threshold=self.route_threshold)
            return llm
        return None  # MacBrain defaults to DeterministicReasoningProvider

    def _build_stt(self) -> Any:
        try:
            from MAC_BRAIN.models.stt import WhisperSTTProvider

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
        self._log.append({"seq": self._seq, "event": event})
        if len(self._log) > 500:
            self._log = self._log[-500:]

    def _drain(self) -> None:
        """Pull newly emitted brain events into the bounded event log."""
        with self._lock:
            new = list(self.brain.events[self._seen:])
            self._seen = len(self.brain.events)
            for ev in new:
                self._seq += 1
                self._log.append({"seq": self._seq, "event": ev})
            if len(self._log) > 500:
                self._log = self._log[-500:]
            if self._seen > 10000:
                self.brain.events = self.brain.events[-1000:]
                self._seen = len(self.brain.events)

    def hear(self, text: str, confidence: float = 0.9) -> dict[str, Any]:
        with self._lock:
            r = self.brain.ingest_transcript(TranscriptionResult(text=text, language="en", confidence=confidence, audio_path="", provider="web", model_id="web"))
        adm = r["admission"]
        return {"accepted": adm.accepted, "memory_id": adm.memory_id, "reasoning": r["reasoning"], "confidence": r["confidence"]}

    def chat_send(self, text: str, confidence: float = 0.9) -> dict[str, Any]:
        """Hear the user message, let the brain decide, and append a chat turn."""
        with self._lock:
            r = self.brain.ingest_transcript(TranscriptionResult(text=text, language="en", confidence=confidence, audio_path="", provider="web", model_id="web"))
            adm = r["admission"]
            conclusion = r["reasoning"]
            heard_conf = r["confidence"]
            step = self.brain.step()
            trace = dict(self.brain._last_reasoning_trace)

        # A real, meaningful reply via the local LLM (falls back to the
        # deterministic conclusion if Ollama is unreachable).
        reply, llm_trace = self._generate_reply(text)
        self._append_chat({"role": "user", "text": text})
        if reply is not None:
            trace["conclusion"] = reply
            trace["action"] = "respond"
            trace["rationale"] = "Generated a conversational reply with the local qwen model, grounded in recalled knowledge and my current self-state."
            trace["route"] = f"ollama:{self.llm_model}"
            trace["route_reason"] = "local LLM"
            trace["confidence"] = 0.85
            novi_text = reply
        else:
            trace["conclusion"] = conclusion  # deterministic conclusion
            trace["confidence"] = heard_conf
            novi_text = conclusion
        novi = {"role": "novi", "text": novi_text, "trace": trace, "cycle": step.get("cycle"), "llm": bool(reply is not None)}
        self._append_chat(novi)
        return {"novi": novi, "accepted": bool(adm.accepted), "memory_id": adm.memory_id, "llm": bool(reply is not None)}

    def listen(self, seconds: float | None = None) -> dict[str, Any]:
        """Record from the microphone, transcribe locally, and respond in chat.

        Requires real sensing (the server must be started with the real camera/
        STT so the brain has a non-deterministic STT provider).
        """
        seconds = seconds or self.listen_seconds
        if self.camera_mode != "real":
            raise RuntimeError("real speech-to-text is not enabled (start with --camera real)")
        stt = getattr(self.brain, "stt", None)
        if stt is None or not hasattr(stt, "transcribe"):
            raise RuntimeError("real speech-to-text is not enabled (start with --camera real)")
        with self._lock:
            result = self.brain.listen(seconds)
            text = result["transcription"].text
            if text.strip():
                step = self.brain.step()
                trace = dict(self.brain._last_reasoning_trace)
        if not text.strip():
            return {"heard": "", "accepted": True, "novi": None, "llm": False}
        reply, _used = self._generate_reply(text)
        self._append_chat({"role": "user", "text": f"[heard] {text}"})
        if reply is not None:
            trace["conclusion"] = reply
            trace["action"] = "respond"
            trace["route"] = f"ollama:{self.llm_model}"
            trace["route_reason"] = "local LLM"
            trace["confidence"] = 0.85
            novi_text, llm = reply, True
        else:
            novi_text, llm = result["reasoning"], False
        novi = {"role": "novi", "text": novi_text, "trace": trace, "cycle": step.get("cycle"), "llm": llm}
        self._append_chat(novi)
        return {"heard": text, "accepted": True, "novi": novi, "llm": llm}

    def _llm_up(self) -> bool:
        if self._llm_available is None:
            try:
                req = urllib.request.Request(f"{self.llm_url}/api/tags", method="GET")
                with urllib.request.urlopen(req, timeout=2) as response:
                    self._llm_available = response.status == 200
            except Exception:  # noqa: BLE001 - offline fallback
                self._llm_available = False
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

    def _knowledge_context(self, text: str, limit: int = 6) -> str:
        kg = self.brain.knowledge
        if kg is None:
            return ""
        known = {e for e in kg.entity_types()} if hasattr(kg, "entity_types") else set()
        words = {w.strip(".,!?") for w in text.split()}
        hits = [w for w in words if w and w.lower() in {k.lower() for k in known}]
        if not hits:
            hits = list(known)[:2]
        facts: list[str] = []
        for e in hits[:4]:
            for t in kg.context(e, limit=limit):
                facts.append(f"{t.subject} {t.predicate} {t.object}")
        return "; ".join(facts)

    def _known_persons(self) -> list[str]:
        idn = getattr(self.brain, "identity", None)
        if idn is None:
            return []
        try:
            snap = idn.snapshot()
            names: set[str] = set()
            for binds in snap.get("bindings", {}).values():
                names.update(binds.keys())
            return sorted(names)
        except Exception:  # noqa: BLE001
            return []

    def _memory_context(self, limit: int = 3) -> list[str]:
        """Recent consolidated summary memories for chat grounding (summary recall)."""
        try:
            rows = self.brain.memory.active_rows()
        except Exception:  # noqa: BLE001 - memory context is best-effort
            return []
        summaries = [r["record"] for r in rows if r["record"].memory_type == "summary"]
        summaries.sort(key=lambda r: r.created_at, reverse=True)
        return [s.content for s in summaries[:limit]]

    def _generate_reply(self, text: str) -> tuple[str | None, bool]:
        if not self.chat_llm or not self._llm_up():
            return None, False
        tone = self.brain.soul.tone({}).get("tone", "neutral")
        facts = self._knowledge_context(text)
        facts_list = [f for f in facts.split("; ") if f]
        facts_list.extend(self._memory_context())
        narrative = self.brain._episodic_narrative()
        if narrative:
            facts_list.append("Recent events: " + " ".join(narrative))
        known = self._known_persons()
        if known:
            facts_list.extend(f"I know the person named {p}" for p in known)
        system = (
            "You are Novi, a curious embodied AI who remembers things you have been told. "
            "You are given a list of facts that you DO know. "
            "If a fact is relevant to the user's question, ANSWER USING THAT FACT — say plainly what you know "
            "(e.g. 'I remember that alice moved the door'). "
            "Only say you don't know something when the facts list gives you nothing relevant. "
            "Reply in 1-3 short, natural spoken sentences. Never invent facts beyond the ones provided. "
            "Do NOT show a chain of thought or reasoning — output only the final answer, directly."
        )
        user_payload = {
            "user_says": text,
            "facts_i_know": facts_list,
            "my_tone": tone,
        }
        try:
            reply = self._llm_chat(system=system, user=json.dumps(user_payload, sort_keys=True))
            return reply, True
        except Exception:  # noqa: BLE001 - offline / model error -> deterministic fallback
            return None, False

    def _append_chat(self, entry: dict[str, Any]) -> None:
        self._chat_seq += 1
        self._chat.append({"seq": self._chat_seq, **entry})
        if len(self._chat) > 200:
            self._chat = self._chat[-200:]

    def chat(self, after: int = 0) -> dict[str, Any]:
        entries = [c for c in self._chat if c["seq"] > after]
        next_after = self._chat[-1]["seq"] if self._chat else after
        return {"entries": entries, "after": next_after}

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
                "soul": {"identity": self.brain.soul.identity.name, "tone": self.brain.soul.tone({}).get("tone"), "affect": self.brain.soul.affect.dimensions},
                "active_goal": {"goal_id": active_goal.goal.goal_id, "kind": active_goal.goal.kind, "target": str(active_goal.goal.target), "steps_taken": active_goal.steps_taken, "status": active_goal.status.value, "distance_to_goal": distance} if active_goal is not None else None,
                "plan": plan,
                "goals_history": goals,
                "knowledge": self.brain.knowledge.counts(),
                "hearing": self.brain._last_audio_events,
                "memory": {"active": getattr(self.brain.memory, "active_count", None), "summaries": self._memory_summaries()},
                "narrative": self.brain._episodic_narrative(),
                "health": self.brain.health.run(self.brain).snapshot(),
                "identity": self.brain.identity.snapshot() if hasattr(self.brain, "identity") else None,
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
        if path in ("/", "/index.html"):
            html = (_ROUTED / "static" / "index.html").read_text(encoding="utf-8")
            self._send(200, html.encode("utf-8"), "text/html")
            return
        if path == "/api/state":
            self._json(self.server.novi.state())
            return
        if path == "/api/model":
            self._json(self.server.novi.model())
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
        self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:
        path = self.path.split("?")[0]
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
            elif path == "/api/step":
                self._json({"result": novi.step()})
            elif path == "/api/goal":
                self._json({"result": novi.set_goal(x=data.get("x", 1.0), y=data.get("y", 1.0), max_steps=int(data.get("max_steps", 60)))})
            elif path == "/api/health":
                self._json({"result": novi.health()})
            else:
                self._json({"error": "unknown endpoint"}, 404)
        except Exception as exc:  # noqa: BLE001
            self._json({"error": str(exc)}, 500)


class NoviWebHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, addr: Any, novi: NoviWebServer) -> None:
        self.novi = novi
        super().__init__(addr, Handler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Novi Mac Brain live web app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--store", default=None, help="durable SQLite DB path")
    parser.add_argument("--tick", type=float, default=0.8, help="seconds per auto-step")
    parser.add_argument("--no-auto-step", action="store_true", help="advance only on manual 'step'")
    parser.add_argument("--camera", choices=["demo", "real"], default="demo", help="'demo' = no-hardware camera; 'real' = live webcam + real speech-to-text")
    parser.add_argument("--reasoning", choices=["deterministic", "ollama", "router"], default="deterministic", help="brain decision backend; 'router' escalates uncertain steps to the local LLM")
    parser.add_argument("--route-threshold", type=float, default=0.6, help="confidence below which the router escalates to the local LLM")
    parser.add_argument("--ollama-model", type=str, default=None, help="Ollama model for reasoning + chat replies (default: nemotron-3.5-lightning)")
    parser.add_argument("--model", dest="model", type=str, default="nemotron-3.5-lightning", help="default chat model (switch at runtime via the UI)")
    parser.add_argument("--stt-model", type=str, default="base", help="faster-whisper model size for real microphone STT (tiny/base/small)")
    parser.add_argument("--stt-device", type=str, default="cpu", help="STT device (cpu or mps)")
    parser.add_argument("--listen-seconds", type=float, default=3.0, help="microphone recording length for the Listen button")
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
