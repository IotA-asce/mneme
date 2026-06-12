from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
import time
import uuid
from typing import Any

from .models import MemoryCandidate, validate_confidence, validate_timestamp


class RuntimeEventKind(StrEnum):
    PERCEPTION_OBSERVATION = "perception_observation"
    WORLD_STATE_UPDATE = "world_state_update"
    ATTENTION_UPDATE = "attention_update"
    MEMORY_CANDIDATE = "memory_candidate"
    MEMORY_LIFECYCLE = "memory_lifecycle"
    EXECUTIVE_INTENT = "executive_intent"
    SKILL_GOAL = "skill_goal"
    SKILL_STATUS = "skill_status"
    SAFETY_EVENT = "safety_event"


class RuntimeTopic(StrEnum):
    PERCEPTION = "perception"
    WORLD_STATE = "world_state"
    ATTENTION = "attention"
    MEMORY = "memory"
    EXECUTIVE = "executive"
    SKILL = "skill"
    SAFETY = "safety"


EVENT_KIND_TOPICS = {
    RuntimeEventKind.PERCEPTION_OBSERVATION: RuntimeTopic.PERCEPTION,
    RuntimeEventKind.WORLD_STATE_UPDATE: RuntimeTopic.WORLD_STATE,
    RuntimeEventKind.ATTENTION_UPDATE: RuntimeTopic.ATTENTION,
    RuntimeEventKind.MEMORY_CANDIDATE: RuntimeTopic.MEMORY,
    RuntimeEventKind.MEMORY_LIFECYCLE: RuntimeTopic.MEMORY,
    RuntimeEventKind.EXECUTIVE_INTENT: RuntimeTopic.EXECUTIVE,
    RuntimeEventKind.SKILL_GOAL: RuntimeTopic.SKILL,
    RuntimeEventKind.SKILL_STATUS: RuntimeTopic.SKILL,
    RuntimeEventKind.SAFETY_EVENT: RuntimeTopic.SAFETY,
}


@dataclass(slots=True)
class RuntimeEvent:
    event_id: str
    kind: RuntimeEventKind | str
    timestamp: int
    source: str
    payload: dict[str, Any]
    confidence: float | None = None
    ttl_ms: int | None = None
    topic: RuntimeTopic | str | None = None
    sequence: int | None = None

    def __post_init__(self) -> None:
        self.event_id = _required_text(self.event_id, "event_id")
        self.kind = parse_runtime_event_kind(self.kind)
        self.timestamp = validate_timestamp(self.timestamp, "timestamp")
        self.source = _required_text(self.source, "source")
        self.payload = _json_mapping(self.payload, "payload")
        if self.confidence is not None:
            self.confidence = validate_confidence(self.confidence)
        if self.ttl_ms is not None:
            self.ttl_ms = _positive_int(self.ttl_ms, "ttl_ms")
        expected_topic = EVENT_KIND_TOPICS[self.kind]
        if self.topic is None:
            self.topic = expected_topic
        else:
            self.topic = parse_runtime_topic(self.topic)
            if self.topic != expected_topic:
                raise ValueError("topic must match the runtime event kind boundary")
        if self.sequence is not None:
            self.sequence = _non_negative_int(self.sequence, "sequence")

    @property
    def expires_at(self) -> int | None:
        if self.ttl_ms is None:
            return None
        return self.timestamp + self.ttl_ms

    def is_expired(self, now_ms: int) -> bool:
        now = validate_timestamp(now_ms, "now_ms")
        expires_at = self.expires_at
        return expires_at is not None and now >= expires_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "kind": self.kind.value,
            "topic": self.topic.value,
            "timestamp": self.timestamp,
            "source": self.source,
            "confidence": self.confidence,
            "ttl_ms": self.ttl_ms,
            "expires_at": self.expires_at,
            "sequence": self.sequence,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RuntimeEvent":
        data = _required_mapping(data)
        return cls(
            event_id=data.get("event_id", f"evt_{uuid.uuid4().hex[:12]}"),
            kind=_required(data, "kind"),
            topic=data.get("topic"),
            timestamp=_required(data, "timestamp"),
            source=_required(data, "source"),
            confidence=data.get("confidence"),
            ttl_ms=data.get("ttl_ms"),
            sequence=data.get("sequence"),
            payload=data.get("payload", {}),
        )


@dataclass(frozen=True, slots=True)
class Subscription:
    subscription_id: str
    callback: Callable[[RuntimeEvent], None]
    kinds: frozenset[RuntimeEventKind] | None = None
    topics: frozenset[RuntimeTopic] | None = None
    sources: frozenset[str] | None = None

    def matches(self, event: RuntimeEvent) -> bool:
        if self.kinds is not None and event.kind not in self.kinds:
            return False
        if self.topics is not None and event.topic not in self.topics:
            return False
        if self.sources is not None and event.source not in self.sources:
            return False
        return True


class EventBus:
    """Synchronous in-process dispatcher for local tests and demos."""

    def __init__(self, *, clock: Callable[[], int] | None = None) -> None:
        self._clock = clock or _now_ms
        self._sequence = 0
        self._subscriptions: dict[str, Subscription] = {}
        self._history: list[RuntimeEvent] = []

    def subscribe(
        self,
        callback: Callable[[RuntimeEvent], None],
        *,
        kinds: Sequence[RuntimeEventKind | str] | None = None,
        topics: Sequence[RuntimeTopic | str] | None = None,
        sources: Sequence[str] | None = None,
        subscription_id: str | None = None,
    ) -> Subscription:
        if not callable(callback):
            raise ValueError("callback must be callable")
        subscription = Subscription(
            subscription_id=subscription_id or f"sub_{uuid.uuid4().hex[:12]}",
            callback=callback,
            kinds=_kind_filter(kinds),
            topics=_topic_filter(topics),
            sources=_source_filter(sources),
        )
        self._subscriptions[subscription.subscription_id] = subscription
        return subscription

    def unsubscribe(self, subscription_id: str) -> bool:
        return self._subscriptions.pop(subscription_id, None) is not None

    def publish(self, event: RuntimeEvent | Mapping[str, Any]) -> RuntimeEvent:
        runtime_event = event if isinstance(event, RuntimeEvent) else RuntimeEvent.from_dict(event)
        if runtime_event.sequence is None:
            self._sequence += 1
            runtime_event.sequence = self._sequence
        else:
            self._sequence = max(self._sequence, runtime_event.sequence)
        self._history.append(runtime_event)

        now_ms = self._clock()
        if runtime_event.is_expired(now_ms):
            return runtime_event

        for subscription in list(self._subscriptions.values()):
            if subscription.matches(runtime_event):
                subscription.callback(runtime_event)
        return runtime_event

    def publish_perception_observation(
        self,
        *,
        source: str,
        observation_type: str,
        payload: Mapping[str, Any],
        confidence: float,
        timestamp: int | None = None,
        ttl_ms: int | None = None,
    ) -> RuntimeEvent:
        return self.publish(
            perception_observation(
                source=source,
                observation_type=observation_type,
                payload=payload,
                confidence=confidence,
                timestamp=timestamp if timestamp is not None else self._clock(),
                ttl_ms=ttl_ms,
            )
        )

    def history(
        self,
        *,
        kinds: Sequence[RuntimeEventKind | str] | None = None,
        topics: Sequence[RuntimeTopic | str] | None = None,
        sources: Sequence[str] | None = None,
        include_expired: bool = True,
        now_ms: int | None = None,
    ) -> list[RuntimeEvent]:
        kind_filter = _kind_filter(kinds)
        topic_filter = _topic_filter(topics)
        source_filter = _source_filter(sources)
        now = self._clock() if now_ms is None else validate_timestamp(now_ms, "now_ms")
        results = []
        for event in sorted(self._history, key=lambda item: (item.sequence or 0, item.event_id)):
            if kind_filter is not None and event.kind not in kind_filter:
                continue
            if topic_filter is not None and event.topic not in topic_filter:
                continue
            if source_filter is not None and event.source not in source_filter:
                continue
            if not include_expired and event.is_expired(now):
                continue
            results.append(event)
        return results

    def expire(self, now_ms: int | None = None) -> list[RuntimeEvent]:
        now = self._clock() if now_ms is None else validate_timestamp(now_ms, "now_ms")
        expired = [event for event in self._history if event.is_expired(now)]
        self._history = [event for event in self._history if not event.is_expired(now)]
        return expired


def perception_observation(
    *,
    source: str,
    observation_type: str,
    payload: Mapping[str, Any],
    confidence: float,
    timestamp: int,
    ttl_ms: int | None = None,
    event_id: str | None = None,
) -> RuntimeEvent:
    return RuntimeEvent(
        event_id=event_id or f"evt_{uuid.uuid4().hex[:12]}",
        kind=RuntimeEventKind.PERCEPTION_OBSERVATION,
        timestamp=timestamp,
        source=source,
        confidence=confidence,
        ttl_ms=ttl_ms,
        payload={"observation_type": _required_text(observation_type, "observation_type"), **dict(payload)},
    )


def world_state_update(
    *,
    source: str,
    state_key: str,
    payload: Mapping[str, Any],
    confidence: float | None,
    timestamp: int,
    ttl_ms: int | None = None,
    event_id: str | None = None,
) -> RuntimeEvent:
    return RuntimeEvent(
        event_id=event_id or f"evt_{uuid.uuid4().hex[:12]}",
        kind=RuntimeEventKind.WORLD_STATE_UPDATE,
        timestamp=timestamp,
        source=source,
        confidence=confidence,
        ttl_ms=ttl_ms,
        payload={"state_key": _required_text(state_key, "state_key"), **dict(payload)},
    )


def attention_update(
    *,
    source: str,
    focus_id: str,
    payload: Mapping[str, Any],
    confidence: float,
    timestamp: int,
    ttl_ms: int | None = None,
    event_id: str | None = None,
) -> RuntimeEvent:
    return RuntimeEvent(
        event_id=event_id or f"evt_{uuid.uuid4().hex[:12]}",
        kind=RuntimeEventKind.ATTENTION_UPDATE,
        timestamp=timestamp,
        source=source,
        confidence=confidence,
        ttl_ms=ttl_ms,
        payload={"focus_id": _required_text(focus_id, "focus_id"), **dict(payload)},
    )


def memory_candidate_event(
    *,
    source: str,
    candidate: MemoryCandidate | Mapping[str, Any],
    timestamp: int,
    ttl_ms: int | None = None,
    event_id: str | None = None,
) -> RuntimeEvent:
    memory_candidate = (
        candidate
        if isinstance(candidate, MemoryCandidate)
        else MemoryCandidate.from_dict(candidate)
    )
    return RuntimeEvent(
        event_id=event_id or f"evt_{uuid.uuid4().hex[:12]}",
        kind=RuntimeEventKind.MEMORY_CANDIDATE,
        timestamp=timestamp,
        source=source,
        confidence=memory_candidate.confidence,
        ttl_ms=ttl_ms,
        payload={"candidate": memory_candidate.to_dict()},
    )


def memory_lifecycle_event(
    *,
    source: str,
    lifecycle_stage: str,
    payload: Mapping[str, Any],
    timestamp: int,
    confidence: float | None = None,
    ttl_ms: int | None = None,
    event_id: str | None = None,
) -> RuntimeEvent:
    return RuntimeEvent(
        event_id=event_id or f"evt_{uuid.uuid4().hex[:12]}",
        kind=RuntimeEventKind.MEMORY_LIFECYCLE,
        timestamp=timestamp,
        source=source,
        confidence=confidence,
        ttl_ms=ttl_ms,
        payload={
            "lifecycle_stage": _required_text(lifecycle_stage, "lifecycle_stage"),
            **dict(payload),
        },
    )


def executive_intent(
    *,
    source: str,
    intent_type: str,
    payload: Mapping[str, Any],
    confidence: float | None,
    timestamp: int,
    ttl_ms: int | None = None,
    event_id: str | None = None,
) -> RuntimeEvent:
    return RuntimeEvent(
        event_id=event_id or f"evt_{uuid.uuid4().hex[:12]}",
        kind=RuntimeEventKind.EXECUTIVE_INTENT,
        timestamp=timestamp,
        source=source,
        confidence=confidence,
        ttl_ms=ttl_ms,
        payload={"intent_type": _required_text(intent_type, "intent_type"), **dict(payload)},
    )


def skill_goal(
    *,
    source: str,
    skill_id: str,
    goal_type: str,
    payload: Mapping[str, Any],
    confidence: float | None,
    timestamp: int,
    ttl_ms: int | None = None,
    event_id: str | None = None,
) -> RuntimeEvent:
    return RuntimeEvent(
        event_id=event_id or f"evt_{uuid.uuid4().hex[:12]}",
        kind=RuntimeEventKind.SKILL_GOAL,
        timestamp=timestamp,
        source=source,
        confidence=confidence,
        ttl_ms=ttl_ms,
        payload={
            "skill_id": _required_text(skill_id, "skill_id"),
            "goal_type": _required_text(goal_type, "goal_type"),
            **dict(payload),
        },
    )


def skill_status(
    *,
    source: str,
    skill_id: str,
    status: str,
    payload: Mapping[str, Any],
    confidence: float | None,
    timestamp: int,
    ttl_ms: int | None = None,
    event_id: str | None = None,
) -> RuntimeEvent:
    return RuntimeEvent(
        event_id=event_id or f"evt_{uuid.uuid4().hex[:12]}",
        kind=RuntimeEventKind.SKILL_STATUS,
        timestamp=timestamp,
        source=source,
        confidence=confidence,
        ttl_ms=ttl_ms,
        payload={
            "skill_id": _required_text(skill_id, "skill_id"),
            "status": _required_text(status, "status"),
            **dict(payload),
        },
    )


def safety_event(
    *,
    source: str,
    safety_level: str,
    payload: Mapping[str, Any],
    confidence: float | None,
    timestamp: int,
    ttl_ms: int | None = None,
    event_id: str | None = None,
) -> RuntimeEvent:
    return RuntimeEvent(
        event_id=event_id or f"evt_{uuid.uuid4().hex[:12]}",
        kind=RuntimeEventKind.SAFETY_EVENT,
        timestamp=timestamp,
        source=source,
        confidence=confidence,
        ttl_ms=ttl_ms,
        payload={
            "safety_level": _required_text(safety_level, "safety_level"),
            **dict(payload),
        },
    )


def parse_runtime_event_kind(value: RuntimeEventKind | str) -> RuntimeEventKind:
    if isinstance(value, RuntimeEventKind):
        return value
    try:
        return RuntimeEventKind(value)
    except (TypeError, ValueError) as exc:
        allowed = ", ".join(item.value for item in RuntimeEventKind)
        raise ValueError(f"kind must be one of: {allowed}") from exc


def parse_runtime_topic(value: RuntimeTopic | str) -> RuntimeTopic:
    if isinstance(value, RuntimeTopic):
        return value
    try:
        return RuntimeTopic(value)
    except (TypeError, ValueError) as exc:
        allowed = ", ".join(item.value for item in RuntimeTopic)
        raise ValueError(f"topic must be one of: {allowed}") from exc


def _now_ms() -> int:
    return int(time.time() * 1000)


def _kind_filter(kinds: Sequence[RuntimeEventKind | str] | None) -> frozenset[RuntimeEventKind] | None:
    if kinds is None:
        return None
    if isinstance(kinds, str):
        raise ValueError("kinds must be a sequence, not a string")
    return frozenset(parse_runtime_event_kind(kind) for kind in kinds)


def _topic_filter(topics: Sequence[RuntimeTopic | str] | None) -> frozenset[RuntimeTopic] | None:
    if topics is None:
        return None
    if isinstance(topics, str):
        raise ValueError("topics must be a sequence, not a string")
    return frozenset(parse_runtime_topic(topic) for topic in topics)


def _source_filter(sources: Sequence[str] | None) -> frozenset[str] | None:
    if sources is None:
        return None
    if isinstance(sources, str):
        raise ValueError("sources must be a sequence, not a string")
    return frozenset(_required_text(source, "source") for source in sources)


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


def _json_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    return dict(value)


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
