from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
import time
import uuid
from typing import Any

from .models import validate_confidence, validate_timestamp
from .runtime import (
    EventBus,
    RuntimeEvent,
    RuntimeEventKind,
    Subscription,
)
from .storage import MemoryStore, WorkingContextSnapshot


DEFAULT_ECHO_TTL_MS = 5_000
DEFAULT_ECHO_CAPACITY = 128
DEFAULT_DIALOGUE_CAPACITY = 8
DEFAULT_EVENT_REF_CAPACITY = 16


@dataclass(slots=True)
class EchoFragment:
    fragment_id: str
    event_id: str
    kind: RuntimeEventKind | str
    timestamp: int
    source: str
    payload: dict[str, Any]
    confidence: float | None = None
    ttl_ms: int = DEFAULT_ECHO_TTL_MS
    sequence: int | None = None

    def __post_init__(self) -> None:
        self.fragment_id = _required_text(self.fragment_id, "fragment_id")
        self.event_id = _required_text(self.event_id, "event_id")
        self.kind = RuntimeEventKind(self.kind)
        self.timestamp = validate_timestamp(self.timestamp, "timestamp")
        self.source = _required_text(self.source, "source")
        self.payload = _json_mapping(self.payload, "payload")
        if self.confidence is not None:
            self.confidence = validate_confidence(self.confidence)
        self.ttl_ms = _positive_int(self.ttl_ms, "ttl_ms")
        if self.sequence is not None:
            self.sequence = _non_negative_int(self.sequence, "sequence")

    @property
    def expires_at(self) -> int:
        return self.timestamp + self.ttl_ms

    def is_expired(self, now_ms: int) -> bool:
        now = validate_timestamp(now_ms, "now_ms")
        return now >= self.expires_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "fragment_id": self.fragment_id,
            "event_id": self.event_id,
            "kind": self.kind.value,
            "timestamp": self.timestamp,
            "source": self.source,
            "confidence": self.confidence,
            "ttl_ms": self.ttl_ms,
            "expires_at": self.expires_at,
            "sequence": self.sequence,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_event(
        cls,
        event: RuntimeEvent,
        *,
        default_ttl_ms: int = DEFAULT_ECHO_TTL_MS,
    ) -> "EchoFragment":
        ttl_ms = event.ttl_ms if event.ttl_ms is not None else default_ttl_ms
        return cls(
            fragment_id=f"echo_{uuid.uuid4().hex[:12]}",
            event_id=event.event_id,
            kind=event.kind,
            timestamp=event.timestamp,
            source=event.source,
            confidence=event.confidence,
            ttl_ms=ttl_ms,
            sequence=event.sequence,
            payload=event.to_dict(),
        )


class SensoryEchoBuffer:
    """Bounded short-lived buffer for recent runtime event fragments."""

    def __init__(
        self,
        *,
        capacity: int = DEFAULT_ECHO_CAPACITY,
        default_ttl_ms: int = DEFAULT_ECHO_TTL_MS,
        clock: Callable[[], int] | None = None,
    ) -> None:
        self.capacity = _positive_int(capacity, "capacity")
        self.default_ttl_ms = _positive_int(default_ttl_ms, "default_ttl_ms")
        self._clock = clock or _now_ms
        self._fragments: list[EchoFragment] = []
        self._subscription: Subscription | None = None

    def add_event(self, event: RuntimeEvent) -> EchoFragment | None:
        now_ms = self._clock()
        self.expire(now_ms=now_ms)
        fragment = EchoFragment.from_event(event, default_ttl_ms=self.default_ttl_ms)
        if fragment.is_expired(now_ms):
            return None
        self._fragments.append(fragment)
        self._trim_to_capacity()
        return fragment

    def attach_to_bus(
        self,
        bus: EventBus,
        *,
        kinds: Sequence[RuntimeEventKind | str] | None = None,
        sources: Sequence[str] | None = None,
    ) -> Subscription:
        self._subscription = bus.subscribe(
            self.add_event,
            kinds=kinds,
            sources=sources,
        )
        return self._subscription

    def fragments(
        self,
        *,
        include_expired: bool = False,
        now_ms: int | None = None,
        kinds: Sequence[RuntimeEventKind | str] | None = None,
        sources: Sequence[str] | None = None,
    ) -> list[EchoFragment]:
        now = self._clock() if now_ms is None else validate_timestamp(now_ms, "now_ms")
        kind_filter = _kind_filter(kinds)
        source_filter = _source_filter(sources)
        results = []
        for fragment in self._ordered_fragments():
            if not include_expired and fragment.is_expired(now):
                continue
            if kind_filter is not None and fragment.kind not in kind_filter:
                continue
            if source_filter is not None and fragment.source not in source_filter:
                continue
            results.append(fragment)
        return results

    def expire(self, now_ms: int | None = None) -> list[EchoFragment]:
        now = self._clock() if now_ms is None else validate_timestamp(now_ms, "now_ms")
        expired = [fragment for fragment in self._fragments if fragment.is_expired(now)]
        self._fragments = [fragment for fragment in self._fragments if not fragment.is_expired(now)]
        return expired

    def to_dict(self, *, now_ms: int | None = None) -> dict[str, Any]:
        now = self._clock() if now_ms is None else validate_timestamp(now_ms, "now_ms")
        return {
            "capacity": self.capacity,
            "default_ttl_ms": self.default_ttl_ms,
            "fragments": [
                fragment.to_dict()
                for fragment in self.fragments(include_expired=False, now_ms=now)
            ],
        }

    def __len__(self) -> int:
        return len(self.fragments())

    def _trim_to_capacity(self) -> None:
        self._fragments = self._ordered_fragments()
        overflow = len(self._fragments) - self.capacity
        if overflow > 0:
            self._fragments = self._fragments[overflow:]

    def _ordered_fragments(self) -> list[EchoFragment]:
        return sorted(
            self._fragments,
            key=lambda fragment: (fragment.sequence if fragment.sequence is not None else 0, fragment.timestamp),
        )


@dataclass(slots=True)
class WorkingMemorySnapshot:
    snapshot_id: str
    created_ts: int
    current_speaker: str | None = None
    topic: str | None = None
    attention_target: str | None = None
    recent_dialogue_turns: list[dict[str, Any]] = field(default_factory=list)
    active_goal: dict[str, Any] | None = None
    safety_state: dict[str, Any] | None = None
    pending_response_intent: dict[str, Any] | None = None
    recent_event_refs: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.snapshot_id = _required_text(self.snapshot_id, "snapshot_id")
        self.created_ts = validate_timestamp(self.created_ts, "created_ts")
        self.current_speaker = _optional_text(self.current_speaker, "current_speaker")
        self.topic = _optional_text(self.topic, "topic")
        self.attention_target = _optional_text(self.attention_target, "attention_target")
        self.recent_dialogue_turns = _mapping_list(
            self.recent_dialogue_turns,
            "recent_dialogue_turns",
        )
        if self.active_goal is not None:
            self.active_goal = _json_mapping(self.active_goal, "active_goal")
        if self.safety_state is not None:
            self.safety_state = _json_mapping(self.safety_state, "safety_state")
        if self.pending_response_intent is not None:
            self.pending_response_intent = _json_mapping(
                self.pending_response_intent,
                "pending_response_intent",
            )
        self.recent_event_refs = _mapping_list(self.recent_event_refs, "recent_event_refs")

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "created_ts": self.created_ts,
            "current_speaker": self.current_speaker,
            "topic": self.topic,
            "attention_target": self.attention_target,
            "recent_dialogue_turns": [dict(turn) for turn in self.recent_dialogue_turns],
            "active_goal": dict(self.active_goal) if self.active_goal is not None else None,
            "safety_state": dict(self.safety_state) if self.safety_state is not None else None,
            "pending_response_intent": (
                dict(self.pending_response_intent)
                if self.pending_response_intent is not None
                else None
            ),
            "recent_event_refs": [dict(event_ref) for event_ref in self.recent_event_refs],
        }


class WorkingMemory:
    """Small explicit active context updated from runtime events."""

    def __init__(
        self,
        *,
        max_dialogue_turns: int = DEFAULT_DIALOGUE_CAPACITY,
        max_event_refs: int = DEFAULT_EVENT_REF_CAPACITY,
        clock: Callable[[], int] | None = None,
    ) -> None:
        self.max_dialogue_turns = _positive_int(max_dialogue_turns, "max_dialogue_turns")
        self.max_event_refs = _positive_int(max_event_refs, "max_event_refs")
        self._clock = clock or _now_ms
        self.current_speaker: str | None = None
        self.topic: str | None = None
        self.attention_target: str | None = None
        self.recent_dialogue_turns: list[dict[str, Any]] = []
        self.active_goal: dict[str, Any] | None = None
        self.safety_state: dict[str, Any] | None = None
        self.pending_response_intent: dict[str, Any] | None = None
        self.recent_event_refs: list[dict[str, Any]] = []
        self._subscription: Subscription | None = None

    def attach_to_bus(
        self,
        bus: EventBus,
        *,
        sources: Sequence[str] | None = None,
    ) -> Subscription:
        self._subscription = bus.subscribe(
            self.apply_event,
            kinds=[
                RuntimeEventKind.PERCEPTION_OBSERVATION,
                RuntimeEventKind.WORLD_STATE_UPDATE,
                RuntimeEventKind.ATTENTION_UPDATE,
                RuntimeEventKind.EXECUTIVE_INTENT,
                RuntimeEventKind.SKILL_GOAL,
                RuntimeEventKind.SKILL_STATUS,
                RuntimeEventKind.SAFETY_EVENT,
            ],
            sources=sources,
        )
        return self._subscription

    def apply_event(self, event: RuntimeEvent) -> None:
        self._remember_event_ref(event)
        payload = event.payload
        if event.kind == RuntimeEventKind.PERCEPTION_OBSERVATION:
            self._apply_perception(payload, event)
        elif event.kind == RuntimeEventKind.WORLD_STATE_UPDATE:
            self._apply_world_state(payload, event)
        elif event.kind == RuntimeEventKind.ATTENTION_UPDATE:
            self._apply_attention(payload, event)
        elif event.kind == RuntimeEventKind.EXECUTIVE_INTENT:
            self._apply_executive_intent(payload, event)
        elif event.kind == RuntimeEventKind.SKILL_GOAL:
            self._apply_skill_goal(payload, event)
        elif event.kind == RuntimeEventKind.SKILL_STATUS:
            self._apply_skill_status(payload, event)
        elif event.kind == RuntimeEventKind.SAFETY_EVENT:
            self._apply_safety(payload, event)

    def add_dialogue_turn(
        self,
        *,
        speaker: str,
        text: str,
        timestamp: int | None = None,
        source: str = "working_memory",
        event_id: str | None = None,
    ) -> None:
        turn = {
            "speaker": _required_text(speaker, "speaker"),
            "text": _required_text(text, "text"),
            "timestamp": timestamp if timestamp is not None else self._clock(),
            "source": _required_text(source, "source"),
        }
        if event_id is not None:
            turn["event_id"] = _required_text(event_id, "event_id")
        turn["timestamp"] = validate_timestamp(turn["timestamp"], "timestamp")
        self.recent_dialogue_turns.append(turn)
        self.recent_dialogue_turns = self.recent_dialogue_turns[-self.max_dialogue_turns :]
        self.current_speaker = turn["speaker"]

    def snapshot(
        self,
        *,
        snapshot_id: str | None = None,
        created_ts: int | None = None,
    ) -> WorkingMemorySnapshot:
        return WorkingMemorySnapshot(
            snapshot_id=snapshot_id or f"ctx_{uuid.uuid4().hex[:12]}",
            created_ts=created_ts if created_ts is not None else self._clock(),
            current_speaker=self.current_speaker,
            topic=self.topic,
            attention_target=self.attention_target,
            recent_dialogue_turns=[dict(turn) for turn in self.recent_dialogue_turns],
            active_goal=dict(self.active_goal) if self.active_goal is not None else None,
            safety_state=dict(self.safety_state) if self.safety_state is not None else None,
            pending_response_intent=(
                dict(self.pending_response_intent)
                if self.pending_response_intent is not None
                else None
            ),
            recent_event_refs=[dict(event_ref) for event_ref in self.recent_event_refs],
        )

    def to_dict(self, *, created_ts: int | None = None) -> dict[str, Any]:
        return self.snapshot(created_ts=created_ts).to_dict()

    def persist_snapshot(
        self,
        store: MemoryStore,
        *,
        snapshot_id: str | None = None,
        created_ts: int | None = None,
    ) -> WorkingContextSnapshot:
        snapshot = self.snapshot(snapshot_id=snapshot_id, created_ts=created_ts)
        return store.store_working_context_snapshot(
            snapshot.to_dict(),
            snapshot_id=snapshot.snapshot_id,
            created_ts=snapshot.created_ts,
        )

    def _apply_perception(self, payload: Mapping[str, Any], event: RuntimeEvent) -> None:
        speaker = _first_text(payload, ("speaker", "speaker_id", "person_id"))
        if speaker is not None:
            self.current_speaker = speaker
        topic = _first_text(payload, ("topic", "current_topic"))
        if topic is not None:
            self.topic = topic
        text = _first_text(payload, ("utterance", "text", "transcript"))
        if text is not None and speaker is not None:
            self.add_dialogue_turn(
                speaker=speaker,
                text=text,
                timestamp=event.timestamp,
                source=event.source,
                event_id=event.event_id,
            )

    def _apply_world_state(self, payload: Mapping[str, Any], event: RuntimeEvent) -> None:
        state_key = payload.get("state_key")
        if state_key in {"current_speaker", "active_speaker"}:
            speaker = _first_text(payload, ("value", "speaker", "person_id"))
            if speaker is not None:
                self.current_speaker = speaker
        elif state_key in {"topic", "current_topic"}:
            topic = _first_text(payload, ("value", "topic"))
            if topic is not None:
                self.topic = topic
        elif state_key in {"safety_state", "safety"}:
            self.safety_state = _event_context(event, payload)

    def _apply_attention(self, payload: Mapping[str, Any], event: RuntimeEvent) -> None:
        focus_id = _first_text(payload, ("focus_id", "attention_target", "target"))
        if focus_id is not None:
            self.attention_target = focus_id
        topic = _first_text(payload, ("topic", "current_topic"))
        if topic is not None:
            self.topic = topic

    def _apply_executive_intent(self, payload: Mapping[str, Any], event: RuntimeEvent) -> None:
        intent = _event_context(event, payload)
        self.pending_response_intent = intent
        goal = _first_text(payload, ("active_goal", "goal", "goal_type"))
        if goal is not None:
            self.active_goal = dict(intent, goal=goal)

    def _apply_skill_goal(self, payload: Mapping[str, Any], event: RuntimeEvent) -> None:
        self.active_goal = _event_context(event, payload)

    def _apply_skill_status(self, payload: Mapping[str, Any], event: RuntimeEvent) -> None:
        status_context = _event_context(event, payload)
        if self.active_goal is None:
            self.active_goal = status_context
            return
        active_goal = dict(self.active_goal)
        active_goal["last_skill_status"] = status_context
        self.active_goal = active_goal

    def _apply_safety(self, payload: Mapping[str, Any], event: RuntimeEvent) -> None:
        self.safety_state = _event_context(event, payload)

    def _remember_event_ref(self, event: RuntimeEvent) -> None:
        self.recent_event_refs.append(
            {
                "event_id": event.event_id,
                "kind": event.kind.value,
                "source": event.source,
                "timestamp": event.timestamp,
                "sequence": event.sequence,
            }
        )
        self.recent_event_refs = self.recent_event_refs[-self.max_event_refs :]


def _event_context(event: RuntimeEvent, payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "kind": event.kind.value,
        "source": event.source,
        "timestamp": event.timestamp,
        "confidence": event.confidence,
        "payload": dict(payload),
    }


def _first_text(payload: Mapping[str, Any], keys: Sequence[str]) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _now_ms() -> int:
    return int(time.time() * 1000)


def _kind_filter(kinds: Sequence[RuntimeEventKind | str] | None) -> frozenset[RuntimeEventKind] | None:
    if kinds is None:
        return None
    if isinstance(kinds, str):
        raise ValueError("kinds must be a sequence, not a string")
    return frozenset(RuntimeEventKind(kind) for kind in kinds)


def _source_filter(sources: Sequence[str] | None) -> frozenset[str] | None:
    if sources is None:
        return None
    if isinstance(sources, str):
        raise ValueError("sources must be a sequence, not a string")
    return frozenset(_required_text(source, "source") for source in sources)


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _optional_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string when provided")
    if not value.strip():
        raise ValueError(f"{field_name} must not be blank when provided")
    return value


def _json_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    return dict(value)


def _mapping_list(value: Any, field_name: str) -> list[dict[str, Any]]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ValueError(f"{field_name} must be a list of mappings")
    items = list(value)
    if not all(isinstance(item, Mapping) for item in items):
        raise ValueError(f"{field_name} must be a list of mappings")
    return [dict(item) for item in items]


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be a positive integer")
    if value < 1:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


def _non_negative_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be a non-negative integer")
    if value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")
    return value
