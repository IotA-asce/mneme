from __future__ import annotations

import re
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .attention import AttentionManager
from .capability_ladder import current_runtime_capability_evidence
from .consolidation_daemon import ConsolidationDaemon
from .context_windows import ContextWindowManager
from .cognitive_context import build_cognitive_context
from .dialogue import DialoguePlanner, UtterancePlan
from .engine import DEFAULT_DB, DEFAULT_MIGRATIONS, MnemeMemory, to_jsonable
from .executive import Executive, ExecutiveIntent
from .extraction import FactExtractor
from .live_perception import (
    CameraCaptureBackend,
    LiveSpeechWorker,
    LiveVisionWorker,
    PerceptionFusionCalibrator,
    PerceptionRetentionPolicy,
    SpeechRecognitionBackend,
)
from .models import MemoryCandidate, SalienceFeatures, SourceType
from .model_dialogue import ModelDialogueRealizer, disabled_model_dialogue_status
from .memory_review import (
    apply_memory_review,
    create_memory_review_record,
    explain_last_response,
    reject_memory_review,
)
from .peripherals import (
    FakePeripheralBackend,
    PeripheralDiscoveryService,
    PeripheralSnapshot,
    RealPeripheralBackend,
    default_virtual_head_devices,
)
from .presence import (
    ConversationalPresenceCoordinator,
    SimulatedSpeechOutputBackend,
    SpeechOutputBackend,
    VirtualAvatarController,
    VirtualSkillRunner,
)
from .promotion import MemoryPromoter
from .runtime import (
    EventBus,
    RuntimeEvent,
    RuntimeEventKind,
    Subscription,
    memory_candidate_event,
    perception_observation,
)
from .runtime_preferences import RuntimeDevicePreferences, RuntimePreferencesStore
from .self_model import ProceduralMemory
from .simulation import ScenarioReplayRunner
from .turn_understanding import TurnClassification, TurnType, classify_turn
from .working_memory import SensoryEchoBuffer, WorkingMemory
from .world_model import WorldModel


DEFAULT_TICK_MS = 100
DEFAULT_USER_TTL_MS = 5_000
DEFAULT_SPEECH_VOICE = "default"


class RuntimeClock:
    def __init__(self, now_ms: int | None = None) -> None:
        self.now_ms = int(time.time() * 1000) if now_ms is None else _timestamp(now_ms, "now_ms")

    def __call__(self) -> int:
        return self.now_ms

    def advance(self, delta_ms: int) -> int:
        if isinstance(delta_ms, bool) or not isinstance(delta_ms, int) or delta_ms < 0:
            raise ValueError("delta_ms must be a non-negative integer")
        self.now_ms += delta_ms
        return self.now_ms

    def set(self, now_ms: int) -> int:
        self.now_ms = _timestamp(now_ms, "now_ms")
        return self.now_ms


@dataclass(slots=True)
class VirtualHeadOutput:
    timestamp: int
    text: str
    plan: UtterancePlan

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "text": self.text,
            "plan": self.plan.to_dict(),
        }


@dataclass(slots=True)
class RuntimeStepResult:
    timestamp: int
    events: list[dict[str, Any]] = field(default_factory=list)
    utterances: list[VirtualHeadOutput] = field(default_factory=list)
    snapshot: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "events": [dict(event) for event in self.events],
            "utterances": [utterance.to_dict() for utterance in self.utterances],
            "snapshot": dict(self.snapshot),
        }


class MnemeRuntime:
    """One-process deterministic runtime for the Stage 3 virtual head."""

    def __init__(
        self,
        *,
        db_path: str | Path = DEFAULT_DB,
        migrations_dir: str | Path = DEFAULT_MIGRATIONS,
        clock: RuntimeClock | Callable[[], int] | None = None,
        discovery_service: PeripheralDiscoveryService | None = None,
        peripheral_backend: FakePeripheralBackend | RealPeripheralBackend | None = None,
        fake_devices: Sequence[Mapping[str, Any]] | None = None,
        live_camera_backend: CameraCaptureBackend | None = None,
        live_speech_backend: SpeechRecognitionBackend | None = None,
        perception_retention: PerceptionRetentionPolicy | None = None,
        live_camera_interval_ms: int = DEFAULT_TICK_MS * 10,
        live_speech_interval_ms: int = DEFAULT_TICK_MS * 10,
        enable_perception_fusion: bool = False,
        speech_output_backend: SpeechOutputBackend | None = None,
        speech_voice: str | None = None,
        device_preferences: RuntimeDevicePreferences | Mapping[str, Any] | None = None,
        preferences_store: RuntimePreferencesStore | None = None,
        persist_speech_voice: bool = True,
        enable_virtual_presence: bool = True,
        virtual_speech_duration_ms: int = 0,
        model_dialogue_realizer: ModelDialogueRealizer | None = None,
        cognitive_context_char_budget: int = 8_000,
        source: str = "mneme_runtime",
        initialize_db: bool = True,
    ) -> None:
        self.source = _required_text(source, "source")
        self.clock = clock if clock is not None else RuntimeClock(0)
        self.preferences_store = preferences_store
        if device_preferences is None and preferences_store is not None:
            device_preferences = preferences_store.load()
        self.device_preferences = (
            device_preferences
            if isinstance(device_preferences, RuntimeDevicePreferences)
            else RuntimeDevicePreferences.from_dict(device_preferences)
        )
        self.bus = EventBus(clock=self.clock)
        self.engine = MnemeMemory(
            db_path,
            migrations_dir=migrations_dir,
            event_bus=self.bus,
            event_source="memory_engine",
            clock=self.clock,
        )
        if initialize_db:
            self.engine.init_db()
        self.speech_voice = (
            _resolve_speech_voice(
                self.engine,
                speech_voice=speech_voice,
                persist=persist_speech_voice,
            )
            if initialize_db
            else _optional_text(speech_voice, "speech_voice") or DEFAULT_SPEECH_VOICE
        )

        self.echo = SensoryEchoBuffer(clock=self.clock)
        self.working_memory = WorkingMemory(clock=self.clock)
        self.world_model = WorldModel(clock=self.clock)
        self.context_windows = ContextWindowManager(
            self.working_memory,
            store=self.engine.store,
            bus=self.bus,
            clock=self.clock,
        )
        self.attention = AttentionManager(clock=self.clock, enable_curiosity=True)
        self.executive = Executive(
            working_memory=self.working_memory,
            clock=self.clock,
            engine=self.engine,
        )
        self.dialogue = DialoguePlanner(store=self.engine.store, clock=self.clock)
        self.model_dialogue_realizer = model_dialogue_realizer
        self.cognitive_context_char_budget = cognitive_context_char_budget
        self.promoter = MemoryPromoter(self.engine, bus=self.bus, clock=self.clock)
        self.extractor = FactExtractor(self.engine, bus=self.bus, clock=self.clock)
        self.consolidation_daemon = ConsolidationDaemon(
            self.engine,
            min_interval_s=300,
            bus=self.bus,
            clock=self.clock,
        )
        if discovery_service is None:
            devices = fake_devices if fake_devices is not None else [
                device.to_dict() for device in default_virtual_head_devices()
            ]
            discovery_service = PeripheralDiscoveryService(
                backend=peripheral_backend or FakePeripheralBackend(devices),
                bus=self.bus,
                clock=self.clock,
            )
        else:
            discovery_service.bus = self.bus
        self.discovery = discovery_service
        self.vision_worker = (
            LiveVisionWorker(
                discovery=self.discovery,
                backend=live_camera_backend,
                bus=self.bus,
                store=self.engine.store,
                retention=perception_retention,
                capture_interval_ms=live_camera_interval_ms,
                preferred_device_id=self.device_preferences.camera_device_id,
                clock=self.clock,
            )
            if live_camera_backend is not None
            else None
        )
        self.speech_worker = (
            LiveSpeechWorker(
                discovery=self.discovery,
                backend=live_speech_backend,
                bus=self.bus,
                store=self.engine.store,
                retention=perception_retention,
                capture_interval_ms=live_speech_interval_ms,
                preferred_device_id=self.device_preferences.microphone_device_id,
                clock=self.clock,
            )
            if live_speech_backend is not None
            else None
        )
        self.perception_fusion = (
            PerceptionFusionCalibrator(clock=self.clock)
            if enable_perception_fusion or live_camera_backend is not None or live_speech_backend is not None
            else None
        )
        self.avatar = VirtualAvatarController(clock=self.clock) if enable_virtual_presence else None
        self.virtual_skill_runner = (
            VirtualSkillRunner(
                bus=None,
                speech_backend=speech_output_backend or SimulatedSpeechOutputBackend(),
                clock=self.clock,
                speech_duration_ms=virtual_speech_duration_ms,
            )
            if enable_virtual_presence
            else None
        )
        self.presence = (
            ConversationalPresenceCoordinator(
                bus=self.bus,
                skill_runner=self.virtual_skill_runner,
                clock=self.clock,
                default_voice=self.speech_voice,
                preferred_speaker_device_id=self.device_preferences.speaker_device_id,
            )
            if enable_virtual_presence and self.virtual_skill_runner is not None
            else None
        )

        self._event_cursor = 0
        self._utterance_cursor = 0
        self._utterances: list[VirtualHeadOutput] = []
        self._handled_dialogue_keys: set[str] = set()
        self._last_turn_classification: TurnClassification | None = None
        self._last_memory_review: dict[str, Any] | None = None
        self._last_correction_proposal: dict[str, Any] | None = None
        self._subscriptions: list[Subscription] = []
        self._attach_components()

    def start(self) -> PeripheralSnapshot:
        return self.discovery.scan_now(now_ms=self._now_ms())

    def refresh_devices(self) -> PeripheralSnapshot:
        return self.discovery.scan_now(now_ms=self._now_ms())

    def tick(self, *, advance_ms: int = DEFAULT_TICK_MS) -> RuntimeStepResult:
        if isinstance(self.clock, RuntimeClock):
            now = self.clock.advance(advance_ms)
        else:
            now = self._now_ms()
        self.discovery.tick(now_ms=now)
        if self.vision_worker is not None:
            self.vision_worker.tick(now_ms=now)
        if self.speech_worker is not None:
            self.speech_worker.tick(now_ms=now)
        if self.virtual_skill_runner is not None:
            self.virtual_skill_runner.tick(now_ms=now)
        self.context_windows.tick(now_ms=now)
        self.attention.idle_tick(now_ms=now)
        self.consolidation_daemon.tick(now_ms=now)
        return self._step_result(now)

    def process_user_utterance(
        self,
        text: str,
        *,
        speaker: str = "user",
        timestamp: int | None = None,
    ) -> RuntimeStepResult:
        clean_text = _required_text(text, "text")
        now = self._set_time(timestamp)
        turn_classification = classify_turn(clean_text)
        self._last_turn_classification = turn_classification
        event = perception_observation(
            source="virtual_head.typed_input",
            observation_type="speech_transcript",
            payload={
                "speaker": _required_text(speaker, "speaker"),
                "transcript": clean_text,
                "utterance": clean_text,
                "topic": _topic_for_text(clean_text),
                "turn_classification": turn_classification.to_dict(),
            },
            confidence=1.0,
            timestamp=now,
            ttl_ms=DEFAULT_USER_TTL_MS,
            event_id=f"evt_typed_{_stable_text_id(clean_text)}_{now}",
        )
        self.bus.publish(event)
        candidate = candidate_from_user_utterance(clean_text, speaker=speaker, timestamp=now)
        if candidate is not None:
            self.bus.publish(
                memory_candidate_event(
                    source="virtual_head.typed_input",
                    candidate=candidate,
                    timestamp=now,
                    ttl_ms=DEFAULT_USER_TTL_MS,
                    event_id=f"evt_{candidate.candidate_id}",
                )
            )
        return self._step_result(now)

    def replay_scenario(self, path: str | Path) -> RuntimeStepResult:
        before = len(self.bus.history())
        result = ScenarioReplayRunner(self.bus).replay_file(path)
        if result.events:
            latest = max(event.timestamp for event in result.events)
            self._set_time(latest)
        now = self._now_ms()
        events = self.bus.history()[before:]
        return RuntimeStepResult(
            timestamp=now,
            events=[event.to_dict() for event in events],
            utterances=self._new_utterances(),
            snapshot=self.snapshot(),
        )

    def snapshot(self) -> dict[str, Any]:
        attention_state = self.attention.state(now_ms=self._now_ms())
        return {
            "timestamp": self._now_ms(),
            "devices": (
                self.discovery.last_snapshot.to_dict()
                if self.discovery.last_snapshot is not None
                else None
            ),
            "device_preferences": self.device_preferences.to_dict(),
            "world": self.world_model.snapshot().to_dict(),
            "working_memory": self.working_memory.to_dict(created_ts=self._now_ms()),
            "attention": attention_state.to_dict(),
            "executive": (
                self.executive.last_intent.to_dict()
                if self.executive.last_intent is not None
                else None
            ),
            "last_utterance": (
                self._utterances[-1].to_dict()
                if self._utterances
                else None
            ),
            "memory": self.engine.inspect_db()["table_counts"],
            "promoter": self.promoter.stats,
            "extractor": self.extractor.stats,
            "consolidation": self.consolidation_daemon.stats,
            "perception": {
                "vision": self.vision_worker.stats if self.vision_worker is not None else None,
                "speech": self.speech_worker.stats if self.speech_worker is not None else None,
                "fusion": self.perception_fusion.stats if self.perception_fusion is not None else None,
            },
            "presence": {
                "voice": self.speech_voice,
                "avatar": self.avatar.state.to_dict() if self.avatar is not None else None,
                "skills": self.virtual_skill_runner.stats if self.virtual_skill_runner is not None else None,
                "coordinator": self.presence.stats if self.presence is not None else None,
            },
            "cognition": (
                self.model_dialogue_realizer.status()
                if self.model_dialogue_realizer is not None
                else disabled_model_dialogue_status()
            ),
            "turn_understanding": (
                self._last_turn_classification.to_dict()
                if self._last_turn_classification is not None
                else None
            ),
            "memory_review": {
                "last_explanation": self._last_memory_review,
                "last_correction_proposal": self._last_correction_proposal,
            },
            "capability": current_runtime_capability_evidence().to_dict(),
        }

    def update_device_preferences(
        self,
        *,
        camera_device_id: str | None = None,
        microphone_device_id: str | None = None,
        speaker_device_id: str | None = None,
        save: bool = True,
    ) -> RuntimeDevicePreferences:
        preferences = RuntimeDevicePreferences(
            camera_device_id=camera_device_id,
            microphone_device_id=microphone_device_id,
            speaker_device_id=speaker_device_id,
        )
        self.device_preferences = preferences
        if self.vision_worker is not None:
            self.vision_worker.preferred_device_id = preferences.camera_device_id
        if self.speech_worker is not None:
            self.speech_worker.preferred_device_id = preferences.microphone_device_id
        if self.presence is not None:
            self.presence.preferred_speaker_device_id = preferences.speaker_device_id
        if save and self.preferences_store is not None:
            self.preferences_store.save(preferences)
        return preferences

    def apply_review(self, review_id: str, *, reason: str) -> dict[str, Any]:
        record = apply_memory_review(self.engine.store, review_id, reason=reason)
        self._last_correction_proposal = record.to_dict()
        return self._last_correction_proposal

    def reject_review(self, review_id: str, *, reason: str) -> dict[str, Any]:
        record = reject_memory_review(self.engine.store, review_id, reason=reason)
        self._last_correction_proposal = record.to_dict()
        return self._last_correction_proposal

    def close(self) -> None:
        if self.virtual_skill_runner is not None:
            self.virtual_skill_runner.cancel_active(reason="runtime_shutdown", now_ms=self._now_ms())
        self.context_windows.close_now(reason="runtime_shutdown", now_ms=self._now_ms())
        self.engine.close()

    def _attach_components(self) -> None:
        self.echo.attach_to_bus(self.bus)
        self.working_memory.attach_to_bus(self.bus)
        self.world_model.attach_to_bus(self.bus)
        self.context_windows.attach_to_bus(self.bus)
        self.attention.attach_to_bus(
            self.bus,
            kinds=[
                RuntimeEventKind.PERCEPTION_OBSERVATION,
                RuntimeEventKind.WORLD_STATE_UPDATE,
                RuntimeEventKind.SAFETY_EVENT,
            ],
        )
        self.promoter.attach_to_bus(self.bus)
        self.extractor.attach_to_bus(self.bus)
        if self.perception_fusion is not None:
            self.perception_fusion.attach_to_bus(self.bus)
        if self.avatar is not None:
            self.avatar.attach_to_bus(self.bus)
        if self.virtual_skill_runner is not None:
            self.virtual_skill_runner.attach_to_bus(self.bus)
        self.executive.attach_to_bus(self.bus)
        self._subscriptions.append(
            self.bus.subscribe(
                self._handle_executive_intent,
                kinds=[RuntimeEventKind.EXECUTIVE_INTENT],
                subscription_id=f"{self.source}_dialogue",
            )
        )

    def _handle_executive_intent(self, event: RuntimeEvent) -> None:
        try:
            intent = ExecutiveIntent.from_dict(event.payload)
        except ValueError:
            return
        self._enrich_review_intent(intent, event.timestamp)
        plan = self.dialogue.plan(
            intent,
            bundle=self.executive.last_memory_bundle,
            working=self.working_memory.to_dict(created_ts=event.timestamp),
        )
        if plan is None:
            if self.presence is not None:
                self.presence.handle_intent(intent, plan=None, timestamp=event.timestamp)
            return
        dialogue_key = _dialogue_key(intent)
        if dialogue_key is not None:
            if dialogue_key in self._handled_dialogue_keys:
                return
            self._handled_dialogue_keys.add(dialogue_key)
        if self.model_dialogue_realizer is not None:
            context = build_cognitive_context(
                user_utterance=_intent_turn_text(intent),
                intent=intent,
                bundle=self.executive.last_memory_bundle,
                working=self.working_memory.to_dict(created_ts=event.timestamp),
                attention=self.attention.state(now_ms=event.timestamp),
                safety=self.working_memory.to_dict(created_ts=event.timestamp).get("safety_state", {}),
                avatar=self.avatar.state.to_dict() if self.avatar is not None else {},
                store=self.engine.store,
                char_budget=self.cognitive_context_char_budget,
            )
            realized = self.model_dialogue_realizer.realize(plan, context)
            plan.text = realized.text
            plan.memory_refs = realized.memory_refs_used
            plan.content_slots = dict(
                plan.content_slots,
                model_realization=realized.to_dict(),
                cognitive_context={
                    "memory_refs_available": [
                        {
                            "memory_kind": memory.memory_kind,
                            "memory_id": memory.memory_id,
                            "source_type": memory.source_type,
                            "confidence": memory.confidence,
                        }
                        for memory in context.memories
                    ],
                    "omitted_memories": [
                        omitted.to_dict() for omitted in context.omitted_memories
                    ],
                    "truncated": context.truncated,
                    "serialized_chars": context.serialized_chars(),
                },
            )
        self._utterances.append(
            VirtualHeadOutput(timestamp=event.timestamp, text=plan.text, plan=plan)
        )
        if self.presence is not None:
            self.presence.handle_intent(intent, plan=plan, timestamp=event.timestamp)

    def _enrich_review_intent(self, intent: ExecutiveIntent, timestamp: int) -> None:
        turn_classification = _turn_classification_from_intent(intent)
        if turn_classification is None:
            return
        turn_text = _intent_turn_text(intent)
        if turn_classification.turn_type == TurnType.EXPLANATION_QUESTION:
            review = explain_last_response(
                self.engine.store,
                self._utterances[-1] if self._utterances else None,
                created_ts=timestamp,
            )
            self._last_memory_review = review.to_dict()
            intent.payload["memory_review"] = review.to_dict()
        elif turn_classification.turn_type in {
            TurnType.CORRECTION,
            TurnType.CONTRADICTION_CHALLENGE,
            TurnType.FORGET_REQUEST,
            TurnType.CONFIRM_MEMORY_REQUEST,
        }:
            related_refs = (
                self._utterances[-1].plan.memory_refs
                if self._utterances
                else []
            )
            proposal = create_memory_review_record(
                self.engine.store,
                turn_text,
                turn_type=turn_classification.turn_type,
                created_ts=timestamp,
                related_memory_refs=related_refs,
            )
            self._last_correction_proposal = proposal.to_dict()
            intent.payload["correction_proposal"] = proposal.to_dict()
        elif turn_classification.turn_type in {
            TurnType.CAPABILITY_QUESTION,
            TurnType.DEVICE_STATUS_QUESTION,
            TurnType.IDENTITY_SELF_QUESTION,
        }:
            intent.payload["runtime_status"] = {
                "devices": (
                    self.discovery.last_snapshot.to_dict()
                    if self.discovery.last_snapshot is not None
                    else None
                ),
                "cognition": (
                    self.model_dialogue_realizer.status()
                    if self.model_dialogue_realizer is not None
                    else disabled_model_dialogue_status()
                ),
                "capability": current_runtime_capability_evidence().to_dict(),
                "memory_counts": self.engine.inspect_db()["table_counts"],
            }

    def _step_result(self, now: int) -> RuntimeStepResult:
        return RuntimeStepResult(
            timestamp=now,
            events=self._new_events(),
            utterances=self._new_utterances(),
            snapshot=self.snapshot(),
        )

    def _new_events(self) -> list[dict[str, Any]]:
        history = self.bus.history()
        new_events = history[self._event_cursor :]
        self._event_cursor = len(history)
        return [event.to_dict() for event in new_events]

    def _new_utterances(self) -> list[VirtualHeadOutput]:
        new_utterances = self._utterances[self._utterance_cursor :]
        self._utterance_cursor = len(self._utterances)
        return list(new_utterances)

    def _set_time(self, timestamp: int | None) -> int:
        if timestamp is None:
            return self._now_ms()
        now = _timestamp(timestamp, "timestamp")
        if isinstance(self.clock, RuntimeClock):
            self.clock.set(now)
        return now

    def _now_ms(self) -> int:
        return self.clock()


def candidate_from_user_utterance(
    text: str,
    *,
    speaker: str = "user",
    timestamp: int = 0,
) -> MemoryCandidate | None:
    if not _is_memory_instruction(text):
        return None
    statement = _statement_from_memory_text(text)
    payload: dict[str, Any] = {
        "utterance": text,
        "speaker": speaker,
        "timestamp": timestamp,
    }
    tags = ["virtual_head", "typed_input"]
    if statement is not None:
        payload["statements"] = [statement]
        tags.append("preference")
    return MemoryCandidate(
        candidate_id=f"cand_typed_{_stable_text_id(text)}",
        candidate_type="typed_user_memory_instruction",
        summary=_summary_for_memory_instruction(text, statement),
        source_type=SourceType.SENSOR_OBSERVED,
        confidence=0.96,
        features=SalienceFeatures(explicit_remember_flag=1.0),
        entities=[speaker],
        tags=tags,
        payload=payload,
        provenance_refs=[],
    )


def _dialogue_key(intent: ExecutiveIntent) -> str | None:
    turn = intent.payload.get("dialogue_turn")
    if not isinstance(turn, Mapping):
        return None
    speaker = turn.get("speaker")
    text = turn.get("text")
    timestamp = turn.get("timestamp")
    if not isinstance(speaker, str) or not isinstance(text, str):
        return None
    return f"{intent.intent_type.value}:{speaker}:{timestamp}:{_stable_text_id(text)}"


def _intent_turn_text(intent: ExecutiveIntent) -> str:
    turn = intent.payload.get("dialogue_turn")
    if isinstance(turn, Mapping):
        text = turn.get("text")
        if isinstance(text, str):
            return text
    return ""


def _turn_classification_from_intent(intent: ExecutiveIntent) -> TurnClassification | None:
    turn = intent.payload.get("dialogue_turn")
    if not isinstance(turn, Mapping):
        return None
    classification = turn.get("turn_classification")
    if not isinstance(classification, Mapping):
        return None
    try:
        return TurnClassification.from_dict(dict(classification))
    except (KeyError, ValueError):
        return None


def _resolve_speech_voice(
    engine: MnemeMemory,
    *,
    speech_voice: str | None,
    persist: bool,
) -> str:
    requested = _optional_text(speech_voice, "speech_voice")
    procedures = ProceduralMemory(engine)
    stored = procedures.get_parameter("speech", "voice")
    stored_voice = stored.strip() if isinstance(stored, str) and stored.strip() else None
    if requested is None:
        return stored_voice or DEFAULT_SPEECH_VOICE
    if persist and stored_voice != requested:
        procedures.set_parameter(
            "speech",
            "voice",
            requested,
            reason="Stage 5 virtual speech voice selection",
        )
    return requested


def _statement_from_memory_text(text: str) -> dict[str, Any] | None:
    normalized = " ".join(text.strip().split())
    lowered = normalized.lower()
    for prefix in ("mneme, remember that ", "remember that ", "remember "):
        if lowered.startswith(prefix):
            statement = normalized[len(prefix) :]
            return _parse_user_statement(statement)
    marker = " remember that "
    if marker in lowered:
        start = lowered.index(marker) + len(marker)
        return _parse_user_statement(normalized[start:])
    return None


def _parse_user_statement(statement: str) -> dict[str, Any] | None:
    patterns = (
        (r"^i like (.+)$", "likes"),
        (r"^i prefer (.+)$", "prefers"),
        (r"^my favorite ([a-z0-9_ -]+) is (.+)$", "favorite"),
    )
    cleaned = statement.strip().rstrip(".")
    lowered = cleaned.lower()
    for pattern, predicate in patterns:
        match = re.match(pattern, lowered)
        if not match:
            continue
        if predicate == "favorite":
            return {
                "subject": "user",
                "predicate": f"favorite_{match.group(1).strip().replace(' ', '_')}",
                "value": match.group(2).strip(),
                "confidence": 0.9,
            }
        return {
            "subject": "user",
            "predicate": predicate,
            "value": match.group(1).strip(),
            "confidence": 0.9,
        }
    return None


def _summary_for_memory_instruction(text: str, statement: Mapping[str, Any] | None) -> str:
    if statement is None:
        return f"User asked Mneme to remember: {text}"
    return f"User {statement['predicate']} {statement['value']}."


def _topic_for_text(text: str) -> str:
    lowered = text.lower()
    if "remember" in lowered:
        return "memory"
    if "like" in lowered or "prefer" in lowered or "favorite" in lowered:
        return "preference"
    return "conversation"


def _is_memory_instruction(text: str) -> bool:
    normalized = " ".join(text.lower().split())
    return any(
        phrase in normalized
        for phrase in ("remember", "do not forget", "don't forget", "note that", "save this")
    )


def _stable_text_id(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.strip().lower().encode("utf-8")).hexdigest()[:12]


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _optional_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    return value.strip() or None


def _timestamp(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer timestamp")
    return value
