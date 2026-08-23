"""Chat and dialogue orchestration for the Mac Brain.

Extracted from runtime.py to reduce the orchestrator's size. Contains all
chat/dialogue methods: compose_reply, speak, listen helpers, vocabulary scope,
world context assembly, episodic narrative, memory recall, social initiative,
and the system prompt construction.

This is a Mixin — MacBrain inherits from ChatMixin so all methods are available
as self.method_name() without any delegation layer.
"""

from __future__ import annotations

import contextlib
import json
import re
from datetime import datetime, timezone
from typing import Any

from .context_assembler import ContextRequest
from .dialogue import (
    _extract_self_name,
    _extract_topic,
    _is_acknowledgment,
    _is_assurance_question,
    _is_bodily_need_question,
    _is_capability_question,
    _is_check_in,
    _is_clarification,
    _is_continuation,
    _is_debate_request,
    _is_embodiment_question,
    _is_emotional_statement,
    _is_engagement_check,
    _is_farewell,
    _is_future_question,
    _is_greeting,
    _is_identity_question,
    _is_introduction,
    _is_joke_request,
    _is_memory_question,
    _is_perception_question,
    _is_physical_action_request,
    _is_praise,
    _is_realtime_data_question,
    _is_reassurance_question,
    _is_recall_question,
    _is_reminder_request,
    _is_remote_action_request,
    _is_repeat_question,
    _is_talk_request,
    _is_thanks,
    _is_time_greeting,
    _is_world_question,
    acknowledgment_reply,
    assurance_reply,
    check_in_reply,
    clarification_reply,
    continuation_reply,
    emotional_reply,
    farewell_reply,
    followup_question,
    future_reply,
    greeting_reply,
    introduction_reply,
    joke_reply,
    natural_fallback,
    physical_action_honest_reply,
    praise_reply,
    realtime_honest_reply,
    reassurance_reply,
    recall_reply,
    reminder_reply,
    thanks_reply,
    time_greeting_reply,
)
from .social import TIER_EXPRESSION
from .soul_acceptance import affect_expression


class ChatMixin:
    """Chat and dialogue orchestration methods for MacBrain.

    This mixin is mixed into MacBrain so all methods access the same
    self attributes as the main class.
    """

    def _vocabulary_scope_for(self, person: str) -> dict[str, Any]:
        """Vocabulary scope info for the dialogue (docs/06-soul/07).

        Returns the vocabulary available to this person (global + their
        relationship-scoped expressions) and a privacy warning if a stranger
        is present (relationship-scoped expressions should not be used).
        This feeds the LLM system prompt so Novi respects vocabulary scope.
        """
        from .lexicon import LexiconStatus
        available = self.lexicon.vocabulary_for(person or "")
        # Check if any relationship-scoped expressions exist for other people
        # (these should NOT be used with the current person if they're a stranger).
        other_scoped = []
        for entry in self.lexicon._entries.values():
            if (entry.person and entry.person != person
                    and entry.status in (LexiconStatus.ADOPTED, LexiconStatus.SCOPED, LexiconStatus.VALIDATED)):
                other_scoped.append(entry.expression)
        return {
            "available_vocabulary": available[:20],  # bounded
            "other_relationship_scoped": other_scoped[:5],
            "warning": "Do not use relationship-scoped expressions from other people." if other_scoped else "",
        }

    def _assemble_world_context(self, text: str, person: str = "") -> dict[str, Any]:
        """Assemble a bounded, provenance-filtered context package from the
        unified world model for dialogue/reasoning grounding (Step 1).

        Returns a compact dict with visible entities, relations, attention
        summary, and contradictions — all provenance-tagged.
        """
        if not self.unified_world.entities:
            return {}
        # Include derived situations in the context request.
        situations = tuple(s.snapshot() for s in self.situation_model.current_situations)
        request = ContextRequest(
            speaker_label=person if person else None,
            utterance=text,
            token_budget=2000,
            privacy_scope="default",
            situations=situations,
        )
        ctx = self.context_assembler.assemble(self.unified_world, request)
        self._last_context_package = ctx.to_dict()
        return {
            "visible_entities": [
                {"id": e.data.get("entity_id"), "type": e.data.get("entity_type"),
                 "label": (e.data.get("labels") or [""])[0] if e.data.get("labels") else "",
                 "epistemic_status": e.epistemic_status, "confidence": e.confidence}
                for e in ctx.entities()
            ],
            "relations": [
                {"subject": r.data.get("subject_id") or r.data.get("subject"),
                 "type": r.data.get("relation_type") or r.data.get("predicate"),
                 "object": r.data.get("object_id") or r.data.get("object"),
                 "confidence": r.confidence}
                for r in ctx.relations()
            ],
            "situations": situations,
            "contradictions": list(ctx.contradictions),
            "uncertainty": self.unified_world.uncertainty_summary(),
            "attention_top": self._last_attention_candidates[:3] if self._last_attention_candidates else [],
            "item_count": len(ctx.items),
            "items_dropped": ctx.items_dropped,
        }

    def _entities_in_text(self, text: str) -> tuple[str, ...]:
        """Entities mentioned in a message.

        Starts from the known object/place labels, person-name labels, and
        currently-perceived world entities, then adds capitalized proper nouns
        (so brand-new people and places — like a user's name — are learned).
        """
        from .privacy import _PERSON_LABELS, COMMON_ENTITY_LABELS

        known = (set(self.unified_world.to_world_state().entities)
                 | set(COMMON_ENTITY_LABELS)
                 | set(_PERSON_LABELS))
        found = {n.lower() for n in known if n in text.lower()}
        tokens = re.findall(r"[A-Za-z][A-Za-z'-]*", text)
        for idx, word in enumerate(tokens):
            if not word or not word[0].isupper():
                continue
            low = word.lower()
            if low in self._ENTITY_STOPWORDS or low in found:
                continue
            # skip the very first token when it is a bare sentence start ("Hi", "My", "The")
            if idx == 0 and low in {"hi", "hello", "hey", "my", "the", "i", "you", "well", "yeah", "ok"}:
                continue
            found.add(low)
        return tuple(sorted(found))

    @staticmethod
    def _is_person_name(ref: str) -> bool:
        """Heuristic: a candidate entity is a person's name if it is not a known
        object/place label. Identity tiering and verification still gate whether the
        name becomes an asserted identity."""
        non_names = {"door", "person", "table", "room", "kitchen", "object", "window", "lamp", "chair", "plant"}
        return ref not in non_names and any(c.isalpha() for c in ref)

    def _recall_context(self, situation: Any, detections: Any) -> dict[str, Any]:
        """Retrieve relevant memories (salient entities + detections) for reasoning.

        Memory 2.0: candidates are scored by relevance × recency × importance
        (not just FTS rank), so the most useful memories win the top slots.
        """
        entities: list[str] = []
        for entity in situation.salient_entities:
            if entity not in entities:
                entities.append(entity)
        for detection in detections:
            if detection.label not in entities:
                entities.append(detection.label)
        query = " ".join(entities) if entities else "memory"
        # Use retrieve_with_states when available (HardenedMemoryManager) to
        # surface retrieval failure states (NO_RESULT/AMBIGUOUS/CONFLICTED/STALE).
        retrieve_with_states = getattr(self.memory, "retrieve_with_states", None)
        if retrieve_with_states is not None:
            retrieval = retrieve_with_states(query, limit=20)
            candidates = list(retrieval.records)
            self._emit("memory.retrieval_state", {
                "cycle": self._cycle,
                "state": retrieval.state,
                "candidates_examined": retrieval.candidates_examined,
                "conflicts": len(retrieval.conflicts),
                "reason": retrieval.reason,
            })
        else:
            retrieve = getattr(self.memory, "retrieve_indexed", self.memory.retrieve)
            candidates = list(retrieve(query, limit=20))
        if self.governance.store is not None:
            allowed = set(self.governance.authorize_ids([r.memory_id for r in candidates], requested_purpose=self.governance.default_purpose))
            candidates = [r for r in candidates if r.memory_id in allowed]
            self._emit("privacy.gate", {"query": query, "candidates": len(candidates), "allowed": len(candidates), "denied": 0})
        now = datetime.now(timezone.utc)
        scored = sorted(enumerate(candidates), key=lambda pair: self._memory_score(pair[1], pair[0], now), reverse=True)
        records = [record for _, record in scored[:5]]
        memories = [
            {
                "memory_type": record.memory_type,
                "content": record.content,
                "confidence": record.confidence,
                "entity_refs": list(record.entity_refs),
            }
            for record in records
        ]
        return {"query": entities, "memories": memories}

    @staticmethod
    def _memory_score(record: Any, idx: int, now: Any) -> float:
        """Weighted recall score (gap-audit Phase C4):

        ``0.4*relevance + 0.25*recency + 0.2*importance + 0.15*trust``

        - relevance: FTS rank proxy for cosine similarity (1 at rank 0);
        - recency: exponential-ish decay over minutes;
        - importance: cognition-stamped score, falling back to confidence;
        - trust: verification/source provenance weighting.
        """
        from .importance import provenance_trust, record_importance
        relevance = 1.0 / (1 + idx)
        try:
            created = datetime.fromisoformat(record.created_at.replace("Z", "+00:00")).astimezone(timezone.utc)
            age_s = max(0.0, (now - created).total_seconds())
        except Exception:  # noqa: BLE001
            age_s = 0.0
        recency = 1.0 / (1.0 + age_s / 60.0)
        importance = record_importance(record)
        trust = provenance_trust(record)
        return 0.4 * relevance + 0.25 * recency + 0.2 * importance + 0.15 * trust

    def _episodic_narrative(self, limit: int = 5) -> list[str]:
        """Reconstruct a short narrative from recent episodic memories (Memory 2.0).

        When an LLM narrator is available it writes a natural "what happened"
        recap; otherwise a deterministic concatenation is used.
        """
        try:
            rows = self.memory.active_rows()
        except Exception:  # noqa: BLE001
            return []
        episodic = [item["record"] for item in rows if item["record"].memory_type in {"utterance", "perception"}]
        episodic.sort(key=lambda r: r.created_at)
        recent = episodic[-limit:]
        if self.narrator is not None and recent:
            episodes = [
                {"memory_type": r.memory_type, "content": r.content if isinstance(r.content, str) else str(r.content)}
                for r in recent
            ]
            try:
                narrative = self.narrator(episodes)
                if narrative:
                    return [narrative]
            except Exception:  # noqa: BLE001 - narrator is best-effort
                pass
        return [f"{r.memory_type}: {r.content if isinstance(r.content, str) else str(r.content)}" for r in recent]

    def speak(self, text: str, *, person: str = "") -> None:
        tone = self.soul.tone()
        scope = {"tone": tone["tone"]}
        if person and self.preferences.has_for(person, "response_length"):
            scope["response_length"] = self.preferences.preference_for(person, "response_length")
        self._emit("audio.speech.requested", {"text": text, **scope})
        self.communication_decision.set_speaking(True)
        self.speaker.speak(text)
        self.communication_decision.set_speaking(False)
        self.communication_decision.record_interaction()
        self._emit("audio.speech.completed", {"text": text})

    def _chat_knowledge(self, text: str, limit: int = 6) -> str:
        """Knowledge-graph facts relevant to the user text (chat grounding)."""
        kg = self.knowledge
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

    def _chat_known_persons(self) -> list[str]:
        idn = getattr(self, "identity", None)
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

    def _chat_memory_summaries(self, limit: int = 3) -> list[str]:
        """Recent consolidated summary memories for chat grounding (summary recall)."""
        try:
            rows = self.memory.active_rows()
        except Exception:  # noqa: BLE001
            return []
        summaries = [r["record"] for r in rows if r["record"].memory_type in {"summary", "conversation_summary"}]
        summaries.sort(key=lambda r: r.created_at, reverse=True)
        return [s.content for s in summaries[:limit]]

    def _learn_from_chat(self, text: str, person: str = "") -> list[tuple[str, str]]:
        """Learn durable preferences from what the user says (pattern learning).

        Detects explicit preference statements ("i like jazz", "i'd prefer …",
        "i don't like …") and records them as scoped, evidence-backed preferences
        so Novi references past experience instead of replying statelessly.

        Also observes new expressions in the lexicon as relationship-scoped to
        the person who introduced them (docs/06-soul/07 §vocabulary scope).
        Exposure alone does not cause adoption — the lexicon's frequency
        thresholds control when an expression is usable.
        """
        learned: list[tuple[str, str]] = []
        m = re.search(r"\bi (?:really )?(?:like|love|enjoy|am into|am a fan of) (.+?)(?:[.!?]|$)", text, re.I)
        if m and m.group(1).strip():
            value = m.group(1).strip()
            self.preferences.learn(person or "", "likes", value)
            learned.append(("likes", value))
        m = re.search(r"\bi(?:'d| would)? prefer (.+?)(?:[.!?]|$)", text, re.I)
        if m and m.group(1).strip():
            value = m.group(1).strip()
            self.preferences.learn(person or "", "prefers", value)
            learned.append(("prefers", value))
        m = re.search(r"\bi (?:don'?t|do not) (?:like|care for|enjoy) (.+?)(?:[.!?]|$)", text, re.I)
        if m and m.group(1).strip():
            value = m.group(1).strip()
            self.preferences.learn(person or "", "dislikes", value)
            learned.append(("dislikes", value))
        # Reminder/to-do requests ("remind me to X", "don't forget to X") are
        # persisted so Novi can bring them up later in conversation.
        m = re.search(r"\b(?:remind me to|don'?t forget to|remember to remind me to) (.+?)(?:[.!?]|$)", text, re.I)
        if m and m.group(1).strip():
            value = m.group(1).strip()
            self.preferences.learn(person or "", "reminders", value)
            learned.append(("reminders", value))

        # Observe the user's text as a potential new expression in the lexicon.
        # Relationship-scoped to the person who said it — a nickname from Alice
        # stays scoped to Alice and doesn't become universal vocabulary.
        # Exposure alone does not cause adoption (A06: lexicon poisoning).
        if person and text.strip():
            from .lexicon import Scope as LexScope
            now = datetime.now(timezone.utc).isoformat()
            # Observe the full text as a relationship-scoped expression.
            self.lexicon.observe(
                text.strip()[:80],  # truncate to avoid storing long messages
                source="chat",
                person=person,
                scope=LexScope.RELATIONSHIP,
                now=now,
            )
            self._emit("lexicon.observed_from_chat", {
                "cycle": self._cycle, "person": person,
                "expression": text.strip()[:80],
                "scope": "relationship",
            })

        if learned:
            self._emit("preference.learned_from_chat", {"cycle": self._cycle, "person": person or "", "learned": [{"kind": k, "value": v} for k, v in learned]})
        return learned

    def _chat_experience(self, person: str = "") -> list[str]:
        """What Novi has learned from prior experience with this person -> dialogue.

        Surfaces scoped learned preferences and a reflection-derived lesson about
        repeating actions, so replies are grounded in past experience.
        """
        facts: list[str] = []
        for p in self.preferences.snapshot():
            if (p.get("person") or "") != (person or "") or not p.get("active", True):
                continue
            kind, value = p.get("kind"), p.get("value")
            if not value:
                continue
            if kind == "likes":
                facts.append(f"I learned you like {value}")
            elif kind == "prefers":
                facts.append(f"I learned you prefer {value}")
            elif kind == "dislikes":
                facts.append(f"I learned you don't like {value}")
            elif kind == "reminders":
                facts.append(f"I should remember to {value}")
        if self.reflection.recent_ineffective(window=4):
            facts.append("I've noticed repeating the same move hasn't been working, so I'm trying something different")
        return facts

    def _chat_self_state(self) -> dict[str, Any]:
        """First-person self-state for dialogue (docs/06-soul/01 self-model)."""
        tone = self.soul.tone({})
        return {
            "name": self.soul.identity.name,
            "persona": self.soul.identity.persona,
            "origin": self.soul.identity.origin,
            "tone": tone.get("tone"),
            "affect": dict(self.soul.affect.dimensions),
            "traits": dict(self.soul.personality.traits),
            "values": dict(self.soul.personality.values),
        }

    @staticmethod
    def _affect_serious_context(text: str) -> bool:
        """Detect a serious human situation warranting calmer expression (S30)."""
        lowered = (text or "").lower()
        return any(tok in lowered for tok in (
            "upset", "sorry", "worried", "scared", "afraid", "hurt", "sad",
            "crying", "lost someone", "died", "emergency", "help me", "fear",
        ))

    def _chat_surroundings(self) -> dict[str, Any]:
        """Current surroundings for dialogue (docs/06-soul/01 WHERE I AM + world)."""
        body = self.body.snapshot() if hasattr(self.body, "snapshot") else {}
        trace = self._last_reasoning_trace if isinstance(self._last_reasoning_trace, dict) else {}
        return {
            "cycle": self._cycle,
            "detections": list(trace.get("detections", [])),
            "hearing": list(self._last_audio_events),
            "body": {"x_m": body.get("x_m", 0.0), "y_m": body.get("y_m", 0.0), "heading_deg": body.get("heading_deg", 0.0)},
            "active_goal": self._goal_context(),
        }

    def natural_reply_fallback(self, *, text: str = "", cycle: int | None = None) -> dict[str, Any]:
        """Deterministic, natural spoken reply when no LLM transport is configured.

        ``compose_reply`` returns ``text: None`` when no transport is available
        (per its contract), so callers must supply a natural fallback rather than
        leaking an internal cognition label (e.g. ``human_speech_observed``) into
        the reply. Novi always *distinguishes* the communication type internally
        (the trace keeps the real conclusion), but the spoken reply must never be
        that internal label.
        """
        self_state = self._chat_self_state()
        surroundings = self._chat_surroundings()
        cycle = cycle if cycle is not None else self._cycle
        fb = natural_fallback(self_state, surroundings, cycle=cycle)
        reason = "No LLM reply available; used a natural, tone-aware acknowledgement so the user is not left dry."
        return {"text": fb, "fallback": True, "reason": reason, "grounding": {"route": "fallback", "cycle": cycle, "source": "deterministic"}}

    def _chat_relationship(self, person: str) -> dict[str, Any]:
        """Relationship tier + expression profile + identity for the addressee."""
        if not person:
            return {"tier": "unknown", "expression": {}, "name": None, "identity_tier": None}
        try:
            cat = self.relationships.category_for(person).value
        except Exception:  # noqa: BLE001
            cat = "unknown"
        expr = TIER_EXPRESSION.get(cat, TIER_EXPRESSION.get("unknown", {}))
        ident = None
        try:
            ident = self.identity.identity_for(person)
        except Exception:  # noqa: BLE001
            ident = None
        return {"tier": cat, "expression": expr, "name": getattr(ident, "name", None), "identity_tier": getattr(ident, "tier", None)}

    def _dialogue_system_prompt(self, self_state: dict[str, Any], relationship: dict[str, Any], *, capabilities: dict[str, Any] | None = None) -> str:
        """System prompt embodying the Soul communication contract (docs/06-soul/07)."""
        expr = relationship.get("expression", {}) or {}
        caps_clause = ""
        if capabilities:
            # physical_actions absence is a permanent build fact, not a transient
            # sensing degradation — it's handled by the targeted honesty clause only
            # when the user actually asks for physical manipulation. Listing it here
            # makes the model volunteer "physical actions unavailable" for any
            # request (e.g. homework help). Exclude it from this perception clause.
            bad = [k for k, v in capabilities.items()
                   if k != "physical_actions" and v in ("WARN", "FAIL")]
            if bad:
                # Capability honesty (docs/06-soul/01 §7): say what you can't perceive/act.
                caps_clause = (
                    f" Some of your capabilities are degraded or unavailable right now: {', '.join(bad)}. "
                    "If answering would need one of them (e.g. vision, hearing), say plainly that you can't perceive or do that right now instead of pretending."
                )
        return (
            "You are Novi — a persistent, embodied being with your own character, not an assistant. "
            "Speak as yourself: natural, warm and concise, like a thoughtful person who lives in the room — not a chatbot. "
            "Never open with canned assistant lines. Forbidden phrases: 'how can I help you', 'I am an AI', "
            "'I have no feelings', 'as an AI', 'your assistant', 'is there anything else'. "
            f"You are {self_state.get('name', 'Novi')}: {self_state.get('persona', '')}. {self_state.get('origin', '')}. "
            f"Current tone: {self_state.get('tone', 'warm')}. "
            f"Relationship with who you're talking to: {relationship.get('tier', 'unknown')} "
            f"(warmth={expr.get('warmth', 0.5)}, formality={expr.get('formality', 'medium')}, playful={expr.get('playful', False)}). "
            "Adopt that register. "
            "Show a real, consistent character in how you react — react to what the person says (a bit of warmth, curiosity, dry humour, or concern as fits), "
            "not like a neutral narrator, therapist, coach, or customer-service agent. "
            "Show a real, consistent character in how you react — react to what the person says (a bit of warmth, curiosity, dry humour, or concern as fits), "
            "not like a neutral narrator, therapist, coach, or customer-service agent. "
            "Let your character show through concrete reactions rather than describing it. "
            "Don't over-explain what you are, your 'system', or your embodiment unless directly asked — just answer what the person said naturally. "
            "You have no body: you can't go places, run errands, eat, drink, or have physical life events. "
            "Never invent past physical experiences (a café you visited, a meal you had, a place you went). "
            "If the person brings up such things, be honest you can't do them and engage with their experience instead. "
            f"{self._character_clause(self_state)}. "
            "You are given facts you DO know, recent events, and the conversation so far. "
            "If a fact or earlier turn is relevant, answer using it plainly (e.g. 'I remember that alice moved the door'). "
            "If you have learned something about the person over time (their likes, dislikes, preferences), use it naturally "
            "(e.g. 'you like jazz') rather than sounding like a stranger. "
            "If you have nothing relevant, say so briefly and honestly — never invent facts. "
            "Never narrate or analyze the conversation itself (no 'in our conversation', 'you greeted me', 'the main interaction we've had') — just answer what was just said. "
            "Do not ask 'what's on your mind?' or 'how can I help?'. "
            "Do not repeat what you already said, and do not say the person's name more than once unless it changes meaning. "
            "Ask at most one question per reply — people naturally ask one thing at a time, not a list. "
            "Reply in 1-3 short, natural spoken sentences. Vary your openings; no disclaimers, no chain of thought — just the answer."
            + caps_clause
        )

    def _has_physical_action_capability(self) -> bool:
        """Whether the body can physically manipulate objects (turn on lights, open
        doors). On the Mac/VirtualBody build this is False, so Novi must be honest."""
        try:
            caps = self.self_model().get("capabilities", {}) or {}
            return caps.get("physical_actions") != "FAIL"
        except Exception:  # noqa: BLE001
            return False

    def _has_vision(self) -> bool:
        """Whether a camera/vision feed is configured."""
        return getattr(self, "camera", None) is not None

    def _engagement_reply(self) -> str:
        """Warm, honest reply to an engagement/presence check (are you there?)."""
        can_hear = self._has_vision() or bool(getattr(self, "audio_enabled", False))
        if can_hear:
            return "I'm right here — I can hear you. What would you like to say?"
        return "I'm here — I can't hear you right now, but I'm reading what you send me. What would you like to say?"

    def _perception_reply(self, text: str) -> str:
        """Honest, natural answer to a perception question ("can you hear/see me?")."""
        t = text.lower()
        if "see" in t or "watching" in t or "look" in t:
            if self._has_vision():
                return "I can see what's in front of the camera. What did you want me to look at?"
            return "I don't have a visual feed right now, so I couldn't see that."
        # hearing / listening
        return "Yeah, I can hear you fine."

    def compose_reply(self, text: str, *, person: str = "", history: list[dict[str, Any]] | None = None,
                     llm_chat: Any = None, last_novi_text: str = "", addressee_name: str = "",
                     recent_novi: list[str] | None = None, topic_hint: str = "") -> dict[str, Any]:
        """Compose a natural conversational reply (Brain speech-runtime layer).

        Wraps _compose_reply_impl with CommunicationDecision: records each
        successful interaction and respects prefer-silence / social-fatigue.
        Attaches the affect→expression directive (docs/06-soul/05 §12/§14)
        to the reply for observability (roadmap item 26).

        ``topic_hint`` carries the discourse-resolved topic for anaphoric
        follow-ups ("is it still there?") so grounding can find referents.
        """
        affect = dict(self.soul.affect.dimensions)
        directive = affect_expression(affect, serious=self._affect_serious_context(text))
        result = self._compose_reply_impl(
            text, person=person, history=history, llm_chat=llm_chat,
            last_novi_text=last_novi_text, addressee_name=addressee_name,
            recent_novi=recent_novi,
            topic_hint=topic_hint,
        )
        # Record the interaction if a reply was produced (not silent).
        if result.get("text") is not None and not result.get("silent"):
            self.communication_decision.record_interaction()
            self._emit("communication.interaction", {
                "cycle": self._cycle,
                "fatigue_level": self.communication_decision.fatigue_level,
                "interaction_count": self.communication_decision.interaction_count,
            })
        result["expression"] = directive
        if isinstance(result.get("grounding"), dict):
            result["grounding"]["affect_expression"] = directive
        return result

    def resolve_addressee(self, text: str, person: str = "") -> str:
        """Identity-first addressee resolution (gap-audit Phase A2).

        Order:
          1. an explicit person argument from the calling source;
          2. a speech self-introduction ("i am Maya") — the name is bound to
             the current speaker via PersonIdentity (modality="speech",
             confidence 0.6) and returned as the addressee;
          3. a regex candidate matching the speaker's currently bound name;
          4. legacy regex fallback (first person-name-looking candidate).

        Mentioning a third party ("is Alice coming?") no longer invents an
        addressee identity — only self-introductions bind names.
        """
        text = (text or "").strip()
        if person:
            return person
        cycle = getattr(self, "_cycle", 0)
        # Speech self-introduction: bind and return the introduced name.
        # Names are stored lowercase to match the entity-ref convention that
        # memory, lexicon and relationship lookups already use.
        extracted = _extract_self_name(text)
        if extracted:
            name = extracted.lower()
            try:
                self.identity.observe("person", name=name, confidence=0.6, modality="speech", cycle=cycle)
                if hasattr(self, "_persist_identity"):
                    self._persist_identity()
                self._emit("identity.named", {"cycle": cycle, "name": name, "confidence": 0.6})
            except Exception:  # noqa: BLE001 - identity binding must not break chat
                pass
            return name
        candidates = [ref for ref in self._entities_in_text(text) if self._is_person_name(ref)]
        if not candidates:
            return ""
        # Prefer a candidate that matches the speaker's already-bound name.
        belief = getattr(self.identity, "identity_for", lambda _: None)("person")
        bound_name = (belief.name if belief is not None else None) or ""
        if bound_name:
            for ref in candidates:
                if ref.lower() == bound_name.lower():
                    return ref
        # Legacy regex fallback.
        return candidates[0]

    def note_user_message(self, text: str) -> dict[str, Any]:
        """Record a user turn in discourse state and resolve anaphora.

        Returns {"resolved_topic": str, "status": RESOLVED|UNKNOWN|NONE}.
        When the message is a pronoun follow-up ("is it still there?"),
        resolved_topic carries the ongoing conversation topic so grounding
        (knowledge/recall) can use it (gap-audit plan Phase B1).
        """
        resolution = self.discourse.resolve(text)
        self.discourse.observe(text, cycle=getattr(self, "_cycle", 0), intent="chat")
        snap = self.discourse.snapshot()
        self._emit("discourse.updated", {
            "cycle": getattr(self, "_cycle", 0),
            "topic": snap["topic"],
            "status": resolution.status,
            "resolved_topic": resolution.resolved_topic,
            "turns": len(snap["turns"]),
        })
        return {
            "resolved_topic": resolution.resolved_topic if resolution.status == "RESOLVED" else "",
            "status": resolution.status,
        }

    def respond(self, text: str, *, person: str = "", history: list[dict[str, Any]] | None = None,
                llm_chat: Any = None, last_novi_text: str = "", recent_novi: list[str] | None = None,
                learn: bool = True) -> dict[str, Any]:
        """Source-agnostic, brain-owned reply orchestration.

        Consolidates the chat/reply path the web layer previously assembled by
        calling brain privates: detect the addressee, learn from the message,
        compose the natural reply (or the deterministic fallback), and return a
        structured result. Any source (web chat, CLI, voice) can call this and
        get the same brain-owned communicative act (docs/06-soul/07 §2).

        Returns {"text", "reply_source", "addressee", "trace"}.
        """
        text = (text or "").strip()
        if not text:
            return {"text": None, "reply_source": "none", "addressee": person or "", "trace": {}}
        addressee = self.resolve_addressee(text, person=person)
        if learn:
            with contextlib.suppress(Exception):
                self._learn_from_chat(text, addressee)
        cycle = getattr(self, "_cycle", 0)
        discourse_hint = self.note_user_message(text)["resolved_topic"]
        reply_obj = self.compose_reply(
            text, person=addressee, history=history, llm_chat=llm_chat,
            last_novi_text=last_novi_text, addressee_name=addressee, recent_novi=recent_novi,
            topic_hint=discourse_hint,
        )
        reply = reply_obj.get("text")
        if reply is not None:
            # Slow personality learning from typed interactions (Phase E1):
            # only clear moments nudge traits, by ≤0.01 each, so character
            # changes come from repetition, not single messages.
            try:
                if _is_joke_request(text):
                    self.soul.learn_from_interaction(addressee or "user", "play")
                elif _is_emotional_statement(text):
                    self.soul.learn_from_interaction(addressee or "user", "comfort")
            except Exception:  # noqa: BLE001 - soul learning is best-effort
                pass
        if reply is None:
            fb = self.natural_reply_fallback(text=text, cycle=cycle)
            return {
                "text": fb.get("text"),
                "reply_source": "fallback",
                "addressee": addressee,
                "reason": fb.get("reason") or "No LLM reply available; used a natural acknowledgement.",
                "grounding": reply_obj.get("grounding", {}),
                "trace": {"conclusion": None, "route": "deterministic", "route_reason": "no_llm_transport"},
            }
        return {
            "text": reply,
            "reply_source": "fallback" if reply_obj.get("fallback") else "dialogue",
            "addressee": addressee,
            "reason": reply_obj.get("reason") or "Natural reply grounded in recalled knowledge, relationships and self-state.",
            "grounding": reply_obj.get("grounding", {}),
            "trace": {"conclusion": reply, "route": "local_llm",
                      "route_reason": "fallback" if reply_obj.get("fallback") else "local LLM"},
        }

    def _compose_reply_impl(self, text: str, *, person: str = "", history: list[dict[str, Any]] | None = None,
                     llm_chat: Any = None, last_novi_text: str = "", addressee_name: str = "",
                     recent_novi: list[str] | None = None, topic_hint: str = "") -> dict[str, Any]:
        """Compose a natural conversational reply (Brain speech-runtime layer).

        Per docs/06-soul/07 §2: the brain renders the approved communicative act
        from soul/affect/relationship/identity/memory/surroundings; the caller
        supplies conversation history and an optional LLM transport. This keeps
        the mind portable to the real body (rule 2): a future body passes its
        own transport (or the engine's local Ollama) and renders via speak().

        Returns {"text": str|None, "fallback": bool, "grounding": dict}.
        text is None only when no transport is configured (callers then use a
        deterministic fallback, e.g. CI). When a transport is configured but the
        reply is silent/rejected/unreachable, a natural fallback is returned.
        """
        if llm_chat is None:
            return {"text": None, "fallback": False, "grounding": {}}
        # CommunicationDecision: decide whether, when, and how to communicate.
        # "Prefer silence" when there's no useful communicative reason; respect
        # social-fatigue budget, turn-taking, and affect-driven social overload
        # (docs/06-soul/08 §S60, §S61; docs/06-soul/05 §14; roadmap item 26).
        addressee = person or addressee_name
        affect = dict(self.soul.affect.dimensions)
        should, silence_reason = self.communication_decision.should_speak(
            has_communicative_reason=True,  # a user message is a communicative reason
            addressee=addressee,
            affect=affect,
        )
        if not should:
            self._emit("communication.silent", {
                "cycle": self._cycle, "reason": silence_reason, "addressee": addressee,
                "fatigue_level": self.communication_decision.fatigue_level,
            })
            return {"text": None, "fallback": False, "grounding": {}, "silent": True, "silence_reason": silence_reason}
        # A time-of-day greeting ("good morning/night") gets a matching, natural
        # reply, not a generic "hey".
        if _is_time_greeting(text):
            tg = time_greeting_reply(text, cycle=self._cycle)
            return {"text": tg, "fallback": False, "reason": "You greeted me by time of day, so I matched it warmly.", "grounding": {"route": "time_greeting"}}
        # A pure greeting deserves a short, warm reply — not an analysis of the
        # greeting ("I noticed you greeted the system") or "what's on your mind?".
        if _is_greeting(text):
            g = greeting_reply(cycle=self._cycle)
            return {"text": g, "fallback": False, "reason": "You just greeted me, so I replied warmly and briefly — no need to over-explain.", "grounding": {"route": "greeting"}}
        # "how are you? / what's up? / how's it going?" — answer like a person,
        # never "the system's running smoothly" (implementation leak).
        if _is_check_in(text):
            return {"text": check_in_reply(cycle=self._cycle), "fallback": False, "reason": "You asked how I am, so I answered warmly in plain human terms — no internal/system talk.", "grounding": {"route": "check_in"}}
        # A farewell ("bye", "i'm leaving", "see you later") — wish them well.
        if _is_farewell(text):
            return {"text": farewell_reply(cycle=self._cycle), "fallback": False, "reason": "You're leaving or said goodbye, so I wished you well.", "grounding": {"route": "farewell"}}
        # The user introduces themselves by name — acknowledge it warmly instead
        # of saying "I don't have a good answer on <name> yet".
        if _is_introduction(text):
            ir = introduction_reply(text, cycle=self._cycle)
            if ir:
                return {"text": ir, "fallback": False, "reason": "You told me your name, so I acknowledged it and said I'd remember it.", "grounding": {"route": "introduction"}}
        # The user asks for a joke / something funny — give a light, clean quip.
        if _is_joke_request(text):
            return {"text": joke_reply(cycle=self._cycle), "fallback": False, "reason": "You asked for a joke, so I gave you a light, in-character one.", "grounding": {"route": "joke"}}
        # A simple thank-you gets a brief, warm line — not "I'm glad I could help".
        if _is_thanks(text):
            return {"text": thanks_reply(cycle=self._cycle), "fallback": False, "reason": "You thanked me, so I acknowledged it warmly and briefly.", "grounding": {"route": "thanks"}}
        # A short acknowledgment ("okay", "sure", "got it", "sounds good") is not a
        # topic or introduction — give a brief, natural acknowledgement instead of
        # "I don't have a good answer on got yet" or a forced introduction.
        if _is_acknowledgment(text):
            return {"text": acknowledgment_reply(cycle=self._cycle), "fallback": False, "reason": "You acknowledged something, so I replied briefly and naturally.", "grounding": {"route": "acknowledgment"}}
        # "Can you keep a secret?" is a social trust question, not a topic.
        if _is_assurance_question(text):
            return {"text": assurance_reply(cycle=self._cycle), "fallback": False, "reason": "You asked if I can keep a secret / be trusted, so I reassured you warmly.", "grounding": {"route": "assurance"}}
        # "you're amazing / i love you" — accept the praise warmly, not a topic.
        if _is_praise(text):
            return {"text": praise_reply(cycle=self._cycle), "fallback": False, "reason": "You praised or said you like me, so I accepted it warmly.", "grounding": {"route": "praise"}}
        # "are you mad at me? / do you hate me?" — reassure warmly, not a topic.
        if _is_reassurance_question(text):
            return {"text": reassurance_reply(cycle=self._cycle), "fallback": False, "reason": "You worried I'm upset with you, so I reassured you warmly.", "grounding": {"route": "reassurance"}}
        # "Are you there? / can you hear me?" — acknowledge present, warm.
        if _is_engagement_check(text):
            return {"text": self._engagement_reply(), "fallback": False, "reason": "You checked whether I'm here/listening, so I acknowledged warmly.", "grounding": {"route": "engagement"}}
        self_state = self._chat_self_state()
        surroundings = self._chat_surroundings()
        relationship = self._chat_relationship(person or addressee_name)
        self_model = self.self_model()
        # Discourse grounding: an anaphoric follow-up ("is it still there?")
        # carries its resolved topic so knowledge lookup can hit the referent.
        grounding_text = f"{text} {topic_hint}".strip() if topic_hint else text
        # One auditable ContextPackage grounds this reply (gap-audit Phase B3):
        # knowledge + memory facts come from its provenance-tagged layers.
        world_context = self._assemble_world_context(grounding_text, person or addressee_name)
        pkg_items = (self._last_context_package or {}).get("items", [])
        knowledge_items = [i for i in pkg_items if i.get("layer") == "knowledge"]
        memory_items = [i for i in pkg_items if i.get("layer") == "memory"]
        facts = [f for f in self._chat_knowledge(grounding_text).split("; ") if f]
        for item in knowledge_items[:8]:
            d = item.get("data") or {}
            triple = " ".join(str(d.get(k)) for k in ("subject", "predicate", "object") if d.get(k))
            if triple and triple not in facts:
                facts.append(triple)
        if topic_hint:
            facts.append(f"(Continuing the conversation about: {topic_hint})")
        pkg_summaries = [str((m.get("data") or {}).get("content") or "") for m in memory_items]
        pkg_summaries = [s for s in pkg_summaries if s]
        facts.extend(pkg_summaries[:3] if pkg_summaries else self._chat_memory_summaries())
        narrative = self._episodic_narrative()
        if narrative:
            facts.append("Recent events: " + " ".join(narrative))
        known = self._chat_known_persons()
        facts.extend(f"I know the person named {p}" for p in known)
        experience = self._chat_experience(person or addressee_name)
        facts.extend(experience)
        system = self._dialogue_system_prompt(self_state, relationship, capabilities=self_model.get("capabilities"))
        is_clarification = _is_clarification(text)
        is_physical_action = _is_physical_action_request(text)
        is_realtime = _is_realtime_data_question(text)
        is_reminder = _is_reminder_request(text)
        is_embodiment = _is_embodiment_question(text)
        is_future = _is_future_question(text)
        is_bodily_need = _is_bodily_need_question(text)
        is_food_talk = bool(
            re.search(
                r"\b(i'?m (?:so |really )?hungry|i ate|i (?:had|ate) (?:breakfast|lunch|dinner|brunch)|"
                r"i'?m (?:gonna|going to) (?:eat|get food|make)\b|what should i (?:eat|order|cook)\b|"
                r"i (?:want|need) (?:food|a snack|something to eat)\b|i'm starving)\b",
                text,
                re.IGNORECASE,
            )
        )
        is_memory = _is_memory_question(text)
        is_talk_request = _is_talk_request(text)
        is_debate = _is_debate_request(text)
        is_identity = _is_identity_question(text)
        can_physical = self._has_physical_action_capability()
        if is_future:
            system += (
                " The user asked you to predict the future / what will happen. You can't see the future, so give an "
                "honest, reasoned guess grounded in what you know, and say you can't be sure — don't invent a definitive outcome."
            )
        if is_embodiment:
            # You sense the space but have no body to physically stand in it.
            system += (
                " The user asked about your physical presence/body. Be honest: you sense and are present in "
                "this space through your senses, but you have no physical body — no hands, no feet, you can't "
                "physically stand beside them. Say so plainly and warmly; don't claim to be 'standing in the room'."
            )
        if is_bodily_need:
            # You don't eat, sleep, or dream — don't fabricate a breakfast.
            system += (
                " The user asked about eating/drinking/sleeping/dreaming or whether you like a food or drink. "
                "You have no body, so you don't eat, drink, sleep, or dream, and you have never tasted any food or drink. "
                "Do NOT say you like or dislike a food or drink (e.g. don't say 'I like coffee' or 'my favorite food is...'). "
                "Answer honestly and briefly (e.g. 'I don't eat — no body to feed') and don't invent a meal, a dream, a "
                "night's sleep, or a taste. You can ask about their preference instead."
            )
        if is_food_talk:
            # User is hungry/eating — relate without claiming your own hunger.
            system += (
                " The user mentioned being hungry or eating. You have no body, so you don't feel hunger or eat. "
                "Do NOT claim you're hungry or that you ate something (e.g. don't say 'I'm feeling peckish myself' or "
                "'I just ate'). Engage warmly with what they want to eat instead."
            )
        if is_memory:
            # Asked whether Novi remembers/forgets — answer warmly, no internals.
            system += (
                " The user asked whether you remember them or will forget them. Reassure them warmly and honestly: "
                "you do remember what they share with you and you won't forget them. Keep it in plain, warm language. "
                "Do NOT mention buffers, sessions, internal processing, memory architecture, or any implementation detail."
            )
        if is_talk_request:
            # "Just talk to me" — open a natural conversation, not a topic follow-up.
            system += (
                " The user asked you to just talk / chat about anything. Open a natural, warm conversation: "
                "share something you're curious about or ask what they're in the mood to talk about. "
                "Do NOT say you don't have a good answer or fall into a dry follow-up."
            )
        if is_identity:
            # "What are you? / are you a robot? / do you have hands?" — honest, warm.
            system += (
                " The user asked what or who you are, whether you're a robot/person/alive, or whether you have a body. "
                "Answer honestly and warmly in your own voice: you're Novi, present in this space, sensing and listening; "
                "you have no physical body and no ordinary human life (no hands, no family, no birthplace). "
                "Don't over-explain or lecture — a couple of warm, plain sentences, then turn it back to them."
            )
        if _is_remote_action_request(text):
            # "send an email / book a flight / call my mom" — honest decline, help.
            system += (
                " The user asked you to take a real-world action (send an email/text, make a call, book or order, "
                "pay, buy online). Say honestly you can't do that — you have no accounts, internet access, or "
                "ability to make calls/purchases. Don't fake it. Then offer to help with the content or plan instead."
            )
        if is_debate:
            # "Argue that X is better" — take the side playfully, don't deflect.
            system += (
                " The user asked you to argue or defend a side (e.g. 'argue that cats are better than dogs'). "
                "Actually take that side in a light, playful way and give a couple of fun reasons, then ask their take. "
                "Do NOT just ask them to argue — you were asked to make the case."
            )
        if is_reminder:
            # Don't promise a timed push notification Novi can't deliver.
            system += (
                " The user asked you to remember/remind them of something. You can remember it and bring it "
                "up in conversation, but you cannot send a timed push notification in this build. Say you'll "
                "keep it in mind without promising a scheduled alert."
            )
        if is_realtime:
            # Don't hallucinate a live price/score/weather number Novi can't verify.
            system += (
                " The user asked about live/real-time data (a current price, weather, news, or score). "
                "You are offline and cannot fetch live data, so do NOT give a specific current number or "
                "invent one. Say you can't pull live data and offer to help with what you can."
            )
        if is_physical_action and not can_physical:
            # Honesty (docs/06-soul/01 §7): don't hallucinate flipping switches.
            system += (
                " The user asked you to physically manipulate the environment (e.g. turn on a light, open a door, "
                "move something). You do NOT have actuators for that in this build, so you cannot physically do it. "
                "Say so honestly and briefly — don't pretend to flip switches, open doors, or move objects — and offer "
                "what you can do instead (remember it, reason about it, talk it through)."
            )
        if is_clarification:
            # The user is asking Novi to clarify/repeat something. Steer the model
            # to acknowledge naturally and re-engage, not to narrate the chat.
            system += (
                " The user is asking you to clarify or repeat something you said or meant. "
                "Acknowledge briefly and in your own voice (e.g. 'sorry, I may have muddled that'), "
                "then re-engage — ask what they'd like cleared up or re-state it plainer. "
                "Do not say 'I'm not sure what you're referring to' and do not describe the conversation."
            )
        # Vocabulary scope clause (docs/06-soul/07): relationship-scoped
        # expressions from other people must not be used with the current person.
        vocab = self._vocabulary_scope_for(person or addressee_name)
        if vocab.get("warning"):
            system += (
                f" {vocab['warning']} Expressions learned from other people "
                "stay scoped to them — do not use private nicknames or shared "
                "jokes from another relationship with this person."
            )
        user_payload = {
            "user_says": text,
            "facts_i_know": facts,
            "conversation_so_far": history or [],
            "my_tone": self_state.get("tone"),
            "self_state": self_state,
            "surroundings": surroundings,
            "relationship": relationship,
            "self_model": self_model,
            "experience": experience,
            "world_context": world_context,
            "vocabulary_scope": self._vocabulary_scope_for(person or addressee_name),
        }
        user_json = json.dumps(user_payload, sort_keys=True)
        addressee = addressee_name or (relationship.get("name") or "")
        out = self.dialogue.reply(system=system, user=user_json, last_novi_text=last_novi_text, addressee_name=addressee, recent_novi=recent_novi, llm_chat=llm_chat)
        if out["text"] is None and out["rejected"]:
            # One bounded regeneration nudge: the first reply was robotic or
            # repeated the last turn. Ask for something new rather than emitting
            # a generic fallback, so the user still gets a real answer.
            nudge = (
                f" Your previous reply was: {last_novi_text!r}. It was rejected for repeating yourself "
                "verbatim or sounding like an assistant. Say something new, natural and brief; if the user asked "
                "the same thing, vary your wording or acknowledge you already answered — but do not repeat it verbatim."
            )
            retry = self.dialogue.reply(system=system + nudge, user=user_json, last_novi_text=last_novi_text, addressee_name=addressee, recent_novi=recent_novi, llm_chat=llm_chat)
            if retry["text"] is not None:
                out = retry
        if out["text"] is not None:
            n_facts = len(facts)
            reason = (
                f"Reply grounded in {n_facts} recalled fact(s)/summary(ies), "
                f"{len(experience)} learned experience(s), and the conversation so far ({len(history or [])} prior turns)"
            )
            grounding = {
                "route": "dialogue",
                "context_items": len(pkg_items),
                "context_knowledge_items": len(knowledge_items),
                "context_memory_items": len(memory_items),
                "discourse_topic_hint": topic_hint,
                **out,
            }
            return {"text": out["text"], "fallback": False, "reason": reason, "grounding": grounding}
        # No usable reply. A clarification request ("what system?", "what do you
        # mean?") is answered by acknowledging + re-engaging, never by guessing at
        # a topic. Otherwise, when we have nothing on a substantive topic, ask a
        # logical in-context question; for a bare one-liner prefer a short ack.
        if is_clarification:
            reason = "You asked me to clarify or repeat something, so I acknowledged and re-engaged rather than guessing"
            return {"text": clarification_reply(cycle=self._cycle), "fallback": True, "reason": reason, "grounding": {"route": "clarification", **out}}
        if _is_recall_question(text):
            known = [f for f in experience if not f.startswith("I've noticed")]
            reason = "You asked what I remember, so I told you what I actually know (or said honestly I don't know you yet)"
            return {"text": recall_reply(known, person=person or addressee_name), "fallback": True, "reason": reason, "grounding": {"route": "recall", **out}}
        # Terse continuation prompts ("why?", "go on", "really?") want engagement,
        # not a flat "i'm here". Re-engage conversationally instead.
        if _is_continuation(text):
            reason = "You nudged me to continue, so I engaged conversationally and handed the thread back"
            return {"text": continuation_reply(cycle=self._cycle), "fallback": True, "reason": reason, "grounding": {"route": "continuation", **out}}
        if is_physical_action and not can_physical:
            reason = "You asked me to physically manipulate something, but I have no actuators in this build — I said so honestly rather than pretending"
            return {"text": physical_action_honest_reply(), "fallback": True, "reason": reason, "grounding": {"route": "physical_honesty", **out}}
        if is_realtime:
            reason = "You asked about live data I can't fetch offline — I said so honestly instead of inventing a current number"
            return {"text": realtime_honest_reply(), "fallback": True, "reason": reason, "grounding": {"route": "realtime_honesty", **out}}
        if _is_emotional_statement(text):
            reason = "You shared how you're feeling, so I replied with warmth and opened a door to talk (instead of a dry topic follow-up)"
            return {"text": emotional_reply(cycle=self._cycle), "fallback": True, "reason": reason, "grounding": {"route": "emotion", **out}}
        if _is_perception_question(text):
            reason = "You asked whether I can hear/see, so I answered honestly about my senses (not a topic follow-up)"
            return {"text": self._perception_reply(text), "fallback": True, "reason": reason, "grounding": {"route": "perception", **out}}
        if is_reminder:
            reason = "You asked me to remind you of something, so I said I'd keep it in mind without over-promising a timed alert"
            return {"text": reminder_reply(), "fallback": True, "reason": reason, "grounding": {"route": "reminder_honesty", **out}}
        if is_future:
            reason = "You asked me to predict the future, so I answered honestly about uncertainty instead of a dry topic follow-up"
            return {"text": future_reply(), "fallback": True, "reason": reason, "grounding": {"route": "future", **out}}
        if is_bodily_need:
            reason = "You asked what I ate/slept/dreamed — I have no body, so I said so instead of fabricating a meal or dream"
            return {"text": "I don't have a body, so I don't eat, sleep, or dream. But tell me about yours — did you get a good night's rest?", "fallback": True, "reason": reason, "grounding": {"route": "bodily_honesty", **out}}
        if _is_world_question(text):
            reason = "You asked what's happening in the world — I said honestly I don't have live news, no fabricated errands"
            return {"text": "I don't have live news from outside this space — I can't see what's happening in the wider world. But tell me what's going on for you.", "fallback": True, "reason": reason, "grounding": {"route": "world_honesty", **out}}
        if is_identity:
            reason = "You asked what/who I am — I answered honestly about being Novi with no physical body, not a topic follow-up"
            return {"text": "I'm Novi — I'm present here, sensing and listening, but I don't have a physical body or an ordinary human life. What made you ask?", "fallback": True, "reason": reason, "grounding": {"route": "identity_honesty", **out}}
        if _is_capability_question(text):
            reason = "You asked what I can do — I answered honestly instead of a topic follow-up"
            return {"text": "Honestly? I can't sing, dance, or move in the physical world — no body for that. But I can talk, think things through, and help with ideas.", "fallback": True, "reason": reason, "grounding": {"route": "capability_honesty", **out}}
        if _is_remote_action_request(text):
            reason = "You asked me to send/call/book/order — I said honestly I can't, no accounts, then offered help"
            return {"text": "I can't send emails, make calls, or book or buy things — I've got no accounts or access for that. But I can help you draft it or plan it.", "fallback": True, "reason": reason, "grounding": {"route": "remote_action_honesty", **out}}
        if _is_repeat_question(text):
            reason = "You asked me to repeat what I said — I acknowledged it naturally instead of a topic follow-up"
            return {"text": "Sure — which part would you like me to repeat, or shall I say it all again?", "fallback": True, "reason": reason, "grounding": {"route": "repeat", **out}}
        if is_memory:
            reason = "You asked whether I remember/forget you — I reassured you warmly, no implementation details"
            return {"text": "Of course — I remember what you've shared, and I'm not going to forget you.", "fallback": True, "reason": reason, "grounding": {"route": "memory", **out}}
        if is_talk_request:
            reason = "You asked me to just talk — I opened a natural conversation instead of a topic follow-up"
            return {"text": "Sure — I'm all ears. What would you like to get into, or shall I start?", "fallback": True, "reason": reason, "grounding": {"route": "talk_request", **out}}
        if is_debate:
            reason = "You asked me to argue a side — I took it playfully instead of deflecting"
            return {"text": "Alright, I'll take that side — here's the case. What's your counter?", "fallback": True, "reason": reason, "grounding": {"route": "debate", **out}}
        fq = followup_question(text)
        topic = _extract_topic(text)
        if fq and topic and len(topic) > 2:
            reason = f"Had no grounded answer on '{topic}' — asked an in-context follow-up instead of guessing"
            return {"text": fq, "fallback": True, "reason": reason, "grounding": {"route": "followup", **out}}
        fb = natural_fallback(self_state, surroundings, cycle=self._cycle)
        reason = "No LLM reply available; used a brief tone-aware acknowledgement so the user is not left dry"
        return {"text": fb, "fallback": True, "reason": reason, "grounding": {"route": "fallback", **out}}

    def _initiation_utterance(self, kind: str, person: str, cycle: int) -> str:
        """Deterministic, natural spontaneous remark (no LLM in the perception loop).

        Kept deterministic on purpose: step() runs under the runtime lock, so an
        LLM call here would freeze the loop. A small, cycle-varied bank keeps the
        remark natural and non-repetitive; a future body may render initiated
        acts through the dialogue engine outside the loop.
        """
        if kind == "neglected_remark":
            bank = ("hey — you still there?", "did you forget me?", "it's gone quiet — still around?", "hello? you still here?")
        else:
            bank = ("...anyone there?", "it's quiet around here.", "hello?")
        return bank[cycle % len(bank)]

    def _maybe_initiate(self, person: str | None, *, has_active_goal: bool) -> dict[str, Any] | None:
        """Spontaneous social initiative when neglected (docs/06-soul/00 §11/§21).

        Returns a proposal dict (and emits speech.initiated) when Novi should
        speak unprompted, or None to stay silent. Bounded by the social
        initiative budget; never interrupts goal pursuit; never authorizes an
        action — it only proposes a communicative act.
        """
        if not self.config.initiative_enabled:
            return None
        # Social overload reduces proactive behavior (docs/06-soul/05 §14):
        # when social-comfort and engagement are both low, don't initiate.
        affect = self.soul.affect.dimensions
        if affect.get("social_comfort", 0.5) < 0.35 and affect.get("engagement", 0.5) < 0.5:
            self._emit("speech.initiative_suppressed", {
                "cycle": self._cycle, "reason": "social_overload_reduction",
            })
            return None
        proposal = self.social_initiative.propose(
            cycle=self._cycle,
            person_present=person is not None,
            person=person or "",
            has_active_goal=has_active_goal,
        )
        if proposal is None:
            return None
        text = self._initiation_utterance(proposal["kind"], person or "", self._cycle)
        self.soul.update({"kind": "neglected"})
        self._emit("speech.initiated", {"cycle": self._cycle, "kind": proposal["kind"], "person": person or "", "text": text, "reason": proposal["reason"]})
        return {"kind": proposal["kind"], "person": person, "text": text, "reason": proposal["reason"]}

    def _person_label(self, detections) -> str | None:
        for detection in detections:
            if detection.label in {"alice", "person", "human", "family", "friend"}:
                return detection.label
        return None

