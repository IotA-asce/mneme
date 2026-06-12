from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
import time
import uuid
from typing import Any

from .attention import AttentionState
from .models import validate_confidence, validate_timestamp
from .runtime import (
    EventBus,
    RuntimeEvent,
    RuntimeEventKind,
    Subscription,
    executive_intent,
)
from .working_memory import WorkingMemory, WorkingMemorySnapshot


DEFAULT_EXECUTIVE_INTENT_TTL_MS = 2_000
DEFAULT_USER_INTERACTION_TTL_MS = 3_000
DEFAULT_MEMORY_INSTRUCTION_TTL_MS = 15_000
DEFAULT_SELF_SPEAKERS = ("mneme", "robot", "assistant")


class ExecutiveMode(StrEnum):
    NORMAL = "normal"
    DEGRADED = "degraded"
    FROZEN = "frozen"


class ExecutiveIntentType(StrEnum):
    LOOK_AT_TARGET = "look_at_target"
    LISTEN = "listen"
    RESPOND_TO_USER = "respond_to_user"
    REMEMBER_EVENT = "remember_event"
    IDLE_PRESENCE = "idle_presence"
    FREEZE_MOTION = "freeze_motion"
    ENTER_DEGRADED_MODE = "enter_degraded_mode"


@dataclass(slots=True)
class ExecutiveIntent:
    intent_id: str
    intent_type: ExecutiveIntentType | str
    mode: ExecutiveMode | str
    priority: int
    created_ts: int
    source: str = "executive"
    confidence: float = 1.0
    reason: str = "rule_selected"
    target_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    preempts_intent_id: str | None = None

    def __post_init__(self) -> None:
        self.intent_id = _required_text(self.intent_id, "intent_id")
        self.intent_type = parse_executive_intent_type(self.intent_type)
        self.mode = parse_executive_mode(self.mode)
        self.priority = _priority(self.priority, "priority")
        self.created_ts = validate_timestamp(self.created_ts, "created_ts")
        self.source = _required_text(self.source, "source")
        self.confidence = validate_confidence(self.confidence)
        self.reason = _required_text(self.reason, "reason")
        self.target_id = _optional_text(self.target_id, "target_id")
        self.payload = _json_mapping(self.payload, "payload")
        self.preempts_intent_id = _optional_text(
            self.preempts_intent_id,
            "preempts_intent_id",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "intent_type": self.intent_type.value,
            "mode": self.mode.value,
            "priority": self.priority,
            "created_ts": self.created_ts,
            "source": self.source,
            "confidence": self.confidence,
            "reason": self.reason,
            "target_id": self.target_id,
            "payload": dict(self.payload),
            "preempts_intent_id": self.preempts_intent_id,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExecutiveIntent":
        data = _required_mapping(data)
        return cls(
            intent_id=data.get("intent_id", f"intent_{uuid.uuid4().hex[:12]}"),
            intent_type=_required(data, "intent_type"),
            mode=data.get("mode", ExecutiveMode.NORMAL),
            priority=data.get("priority", 0),
            created_ts=_required(data, "created_ts"),
            source=data.get("source", "executive"),
            confidence=data.get("confidence", 1.0),
            reason=data.get("reason", "rule_selected"),
            target_id=data.get("target_id"),
            payload=dict(data.get("payload", {})),
            preempts_intent_id=data.get("preempts_intent_id"),
        )


class Executive:
    """Deterministic executive intent generator and arbiter."""

    def __init__(
        self,
        *,
        working_memory: WorkingMemory | None = None,
        user_interaction_ttl_ms: int = DEFAULT_USER_INTERACTION_TTL_MS,
        memory_instruction_ttl_ms: int = DEFAULT_MEMORY_INSTRUCTION_TTL_MS,
        intent_ttl_ms: int = DEFAULT_EXECUTIVE_INTENT_TTL_MS,
        self_speakers: Sequence[str] = DEFAULT_SELF_SPEAKERS,
        source: str = "executive",
        clock: Callable[[], int] | None = None,
        bus: EventBus | None = None,
    ) -> None:
        self._clock = clock or _now_ms
        self.source = _required_text(source, "source")
        self.working_memory = working_memory or WorkingMemory(clock=self._clock)
        self._owns_working_memory = working_memory is None
        self.user_interaction_ttl_ms = _positive_int(
            user_interaction_ttl_ms,
            "user_interaction_ttl_ms",
        )
        self.memory_instruction_ttl_ms = _positive_int(
            memory_instruction_ttl_ms,
            "memory_instruction_ttl_ms",
        )
        self.intent_ttl_ms = _positive_int(intent_ttl_ms, "intent_ttl_ms")
        self.self_speakers = tuple(
            speaker.strip().lower()
            for speaker in self_speakers
            if _required_text(speaker, "self_speakers")
        )
        self._bus: EventBus | None = None
        self._subscription: Subscription | None = None
        self._attention_state: AttentionState | None = None
        self._world_state: dict[str, Any] = {}
        self._last_intent: ExecutiveIntent | None = None
        self._intent_counter = 0
        if bus is not None:
            self.attach_to_bus(bus)

    def attach_to_bus(self, bus: EventBus) -> Subscription:
        self._bus = bus
        self._subscription = bus.subscribe(
            self.process_event,
            kinds=[
                RuntimeEventKind.PERCEPTION_OBSERVATION,
                RuntimeEventKind.WORLD_STATE_UPDATE,
                RuntimeEventKind.ATTENTION_UPDATE,
                RuntimeEventKind.MEMORY_CANDIDATE,
                RuntimeEventKind.SAFETY_EVENT,
            ],
        )
        return self._subscription

    def process_event(self, event: RuntimeEvent) -> ExecutiveIntent:
        if self._owns_working_memory:
            self.working_memory.apply_event(event)
        self._apply_event_context(event)
        return self.run_once()

    def run_once(
        self,
        *,
        working_memory: WorkingMemory | WorkingMemorySnapshot | Mapping[str, Any] | None = None,
        attention_state: AttentionState | Mapping[str, Any] | None = None,
        safety_state: Mapping[str, Any] | None = None,
        world_state: Mapping[str, Any] | None = None,
        publish: bool = True,
        now_ms: int | None = None,
    ) -> ExecutiveIntent:
        now = self._clock() if now_ms is None else validate_timestamp(now_ms, "now_ms")
        context = _ExecutiveContext(
            working=_working_dict(working_memory or self.working_memory, now_ms=now),
            attention=_attention_dict(attention_state or self._attention_state),
            safety=dict(safety_state) if safety_state is not None else None,
            world=dict(world_state) if world_state is not None else dict(self._world_state),
            now_ms=now,
        )
        if context.safety is None:
            context.safety = _extract_safety_state(context.working)
        if context.safety is None:
            context.safety = _extract_world_safety_state(context.world)

        intent = self._select_intent(context)
        if publish:
            self._publish_intent(intent)
        self._last_intent = intent
        return intent

    @property
    def last_intent(self) -> ExecutiveIntent | None:
        return self._last_intent

    def _apply_event_context(self, event: RuntimeEvent) -> None:
        if event.kind == RuntimeEventKind.WORLD_STATE_UPDATE:
            state_key = _first_text(event.payload, ("state_key",))
            if state_key is not None:
                self._world_state[state_key] = dict(event.payload)
        elif event.kind == RuntimeEventKind.ATTENTION_UPDATE:
            state_data = event.payload.get("attention_state")
            if isinstance(state_data, Mapping):
                self._attention_state = AttentionState.from_dict(state_data)
        elif event.kind == RuntimeEventKind.SAFETY_EVENT:
            self._world_state["safety_state"] = {
                "event_id": event.event_id,
                "kind": event.kind.value,
                "source": event.source,
                "timestamp": event.timestamp,
                "confidence": event.confidence,
                "payload": dict(event.payload),
            }

    def _select_intent(self, context: "_ExecutiveContext") -> ExecutiveIntent:
        safety_level = _safety_level(context.safety)
        if safety_level in {"emergency", "critical", "estop", "stop", "unsafe"}:
            return self._intent(
                ExecutiveIntentType.FREEZE_MOTION,
                mode=ExecutiveMode.FROZEN,
                priority=100,
                reason="safety_freeze",
                confidence=_safety_confidence(context.safety),
                payload={"safety_state": context.safety},
                context=context,
            )
        if safety_level in {"degraded", "warning", "caution", "fault"}:
            return self._intent(
                ExecutiveIntentType.ENTER_DEGRADED_MODE,
                mode=ExecutiveMode.DEGRADED,
                priority=90,
                reason="safety_degraded",
                confidence=_safety_confidence(context.safety),
                payload={"safety_state": context.safety},
                context=context,
            )

        latest_user_turn = _latest_user_turn(context.working, self.self_speakers)
        if latest_user_turn is not None:
            age_ms = context.now_ms - int(latest_user_turn["timestamp"])
            if age_ms <= self.user_interaction_ttl_ms:
                payload = {
                    "dialogue_turn": dict(latest_user_turn),
                    "attention_target": _attention_target_id(context),
                }
                if _is_memory_instruction(str(latest_user_turn.get("text", ""))):
                    payload["secondary_intents"] = [ExecutiveIntentType.REMEMBER_EVENT.value]
                return self._intent(
                    ExecutiveIntentType.RESPOND_TO_USER,
                    mode=ExecutiveMode.NORMAL,
                    priority=70,
                    reason="active_user_interaction",
                    target_id=_attention_target_id(context) or str(latest_user_turn["speaker"]),
                    payload=payload,
                    context=context,
                )

        if latest_user_turn is not None:
            age_ms = context.now_ms - int(latest_user_turn["timestamp"])
            if (
                age_ms <= self.memory_instruction_ttl_ms
                and _is_memory_instruction(str(latest_user_turn.get("text", "")))
            ):
                return self._intent(
                    ExecutiveIntentType.REMEMBER_EVENT,
                    mode=ExecutiveMode.NORMAL,
                    priority=55,
                    reason="explicit_memory_instruction",
                    target_id=str(latest_user_turn["speaker"]),
                    payload={"dialogue_turn": dict(latest_user_turn)},
                    context=context,
                )

        active_speaker = _active_user_speaker(context.working, self.self_speakers)
        if active_speaker is not None:
            return self._intent(
                ExecutiveIntentType.LISTEN,
                mode=ExecutiveMode.NORMAL,
                priority=45,
                reason="active_speaker_without_pending_response",
                target_id=active_speaker,
                payload={"speaker": active_speaker},
                context=context,
            )

        attention_target = _attention_target_id(context)
        if attention_target is not None:
            return self._intent(
                ExecutiveIntentType.LOOK_AT_TARGET,
                mode=ExecutiveMode.NORMAL,
                priority=30,
                reason="attention_target_available",
                target_id=attention_target,
                payload={"attention_state": context.attention},
                context=context,
            )

        return self._intent(
            ExecutiveIntentType.IDLE_PRESENCE,
            mode=ExecutiveMode.NORMAL,
            priority=10,
            reason="idle_presence_default",
            payload={},
            context=context,
        )

    def _intent(
        self,
        intent_type: ExecutiveIntentType,
        *,
        mode: ExecutiveMode,
        priority: int,
        reason: str,
        context: "_ExecutiveContext",
        confidence: float = 1.0,
        target_id: str | None = None,
        payload: Mapping[str, Any] | None = None,
    ) -> ExecutiveIntent:
        self._intent_counter += 1
        preempts_intent_id = None
        if (
            self._last_intent is not None
            and priority > self._last_intent.priority
            and intent_type != self._last_intent.intent_type
        ):
            preempts_intent_id = self._last_intent.intent_id
        return ExecutiveIntent(
            intent_id=f"exec_intent_{self._intent_counter:06d}",
            intent_type=intent_type,
            mode=mode,
            priority=priority,
            created_ts=context.now_ms,
            source=self.source,
            confidence=confidence,
            reason=reason,
            target_id=target_id,
            payload=dict(payload or {}),
            preempts_intent_id=preempts_intent_id,
        )

    def _publish_intent(self, intent: ExecutiveIntent) -> RuntimeEvent | None:
        if self._bus is None:
            return None
        return self._bus.publish(
            executive_intent(
                source=self.source,
                intent_type=intent.intent_type.value,
                payload=intent.to_dict(),
                confidence=intent.confidence,
                timestamp=intent.created_ts,
                ttl_ms=self.intent_ttl_ms,
                event_id=f"evt_{intent.intent_id}",
            )
        )


@dataclass(slots=True)
class _ExecutiveContext:
    working: dict[str, Any]
    attention: dict[str, Any] | None
    safety: dict[str, Any] | None
    world: dict[str, Any]
    now_ms: int


def parse_executive_mode(value: ExecutiveMode | str) -> ExecutiveMode:
    if isinstance(value, ExecutiveMode):
        return value
    try:
        return ExecutiveMode(value)
    except (TypeError, ValueError) as exc:
        allowed = ", ".join(item.value for item in ExecutiveMode)
        raise ValueError(f"mode must be one of: {allowed}") from exc


def parse_executive_intent_type(value: ExecutiveIntentType | str) -> ExecutiveIntentType:
    if isinstance(value, ExecutiveIntentType):
        return value
    try:
        return ExecutiveIntentType(value)
    except (TypeError, ValueError) as exc:
        allowed = ", ".join(item.value for item in ExecutiveIntentType)
        raise ValueError(f"intent_type must be one of: {allowed}") from exc


def _working_dict(
    working: WorkingMemory | WorkingMemorySnapshot | Mapping[str, Any],
    *,
    now_ms: int,
) -> dict[str, Any]:
    if isinstance(working, WorkingMemory):
        return working.to_dict(created_ts=now_ms)
    if isinstance(working, WorkingMemorySnapshot):
        return working.to_dict()
    if isinstance(working, Mapping):
        return dict(working)
    raise ValueError("working_memory must be WorkingMemory, WorkingMemorySnapshot, or mapping")


def _attention_dict(attention_state: AttentionState | Mapping[str, Any] | None) -> dict[str, Any] | None:
    if attention_state is None:
        return None
    if isinstance(attention_state, AttentionState):
        return attention_state.to_dict()
    if isinstance(attention_state, Mapping):
        return dict(attention_state)
    raise ValueError("attention_state must be AttentionState, mapping, or None")


def _extract_safety_state(working: Mapping[str, Any]) -> dict[str, Any] | None:
    safety_state = working.get("safety_state")
    if isinstance(safety_state, Mapping):
        return dict(safety_state)
    return None


def _extract_world_safety_state(world: Mapping[str, Any]) -> dict[str, Any] | None:
    safety_state = world.get("safety_state") or world.get("safety")
    if isinstance(safety_state, Mapping):
        return dict(safety_state)
    return None


def _safety_level(safety_state: Mapping[str, Any] | None) -> str | None:
    if safety_state is None:
        return None
    direct = _first_text(safety_state, ("safety_level", "level", "status"))
    if direct is not None:
        return direct.strip().lower()
    payload = safety_state.get("payload")
    if isinstance(payload, Mapping):
        nested = _first_text(payload, ("safety_level", "level", "status"))
        if nested is not None:
            return nested.strip().lower()
    return None


def _safety_confidence(safety_state: Mapping[str, Any] | None) -> float:
    if safety_state is None:
        return 1.0
    confidence = safety_state.get("confidence")
    if confidence is None:
        return 1.0
    return validate_confidence(confidence)


def _latest_user_turn(
    working: Mapping[str, Any],
    self_speakers: Sequence[str],
) -> dict[str, Any] | None:
    turns = working.get("recent_dialogue_turns", [])
    if isinstance(turns, str) or not isinstance(turns, Sequence):
        return None
    for turn in reversed(list(turns)):
        if not isinstance(turn, Mapping):
            continue
        speaker = turn.get("speaker")
        timestamp = turn.get("timestamp")
        text = turn.get("text")
        if (
            isinstance(speaker, str)
            and speaker.strip().lower() not in self_speakers
            and isinstance(timestamp, int)
            and isinstance(text, str)
            and text.strip()
        ):
            return dict(turn)
    return None


def _active_user_speaker(
    working: Mapping[str, Any],
    self_speakers: Sequence[str],
) -> str | None:
    speaker = working.get("current_speaker")
    if isinstance(speaker, str) and speaker.strip().lower() not in self_speakers:
        return speaker
    return None


def _attention_target_id(context: _ExecutiveContext) -> str | None:
    if context.attention is not None:
        target_id = context.attention.get("active_target_id")
        if isinstance(target_id, str) and target_id.strip():
            return target_id
    attention_target = context.working.get("attention_target")
    if isinstance(attention_target, str) and attention_target.strip():
        return attention_target
    return None


def _is_memory_instruction(text: str) -> bool:
    normalized = " ".join(text.lower().split())
    return any(
        phrase in normalized
        for phrase in (
            "remember",
            "do not forget",
            "don't forget",
            "note that",
            "save this",
            "keep this in mind",
        )
    )


def _first_text(payload: Mapping[str, Any], keys: Sequence[str]) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _required_mapping(value: Any, field_name: str = "data") -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    return value


def _required(data: Mapping[str, Any], field_name: str) -> Any:
    data = _required_mapping(data)
    if field_name not in data:
        raise ValueError(f"missing required field: {field_name}")
    return data[field_name]


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _optional_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string when provided")
    return value


def _json_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    return dict(value)


def _priority(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer from 0 to 100")
    if value < 0 or value > 100:
        raise ValueError(f"{field_name} must be from 0 to 100")
    return value


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be a positive integer")
    if value < 1:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


def _now_ms() -> int:
    return int(time.time() * 1000)
