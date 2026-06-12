from __future__ import annotations

import time
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from .models import validate_confidence, validate_timestamp
from .runtime import (
    EventBus,
    RuntimeEvent,
    RuntimeEventKind,
    Subscription,
    world_state_update,
)

DEFAULT_PERSON_TTL_MS = 10_000
DEFAULT_SPEAKER_TTL_MS = 6_000
DEFAULT_SOUND_TTL_MS = 3_000


@dataclass(slots=True)
class PersonPresence:
    person_id: str
    label: str
    last_seen_ts: int
    confidence: float
    expression: str | None = None
    source: str = "unknown"

    def __post_init__(self) -> None:
        self.person_id = _required_text(self.person_id, "person_id")
        self.label = _required_text(self.label, "label")
        self.last_seen_ts = validate_timestamp(self.last_seen_ts, "last_seen_ts")
        self.confidence = validate_confidence(self.confidence)
        self.expression = _optional_text(self.expression, "expression")
        self.source = _required_text(self.source, "source")

    def to_dict(self) -> dict[str, Any]:
        return {
            "person_id": self.person_id,
            "label": self.label,
            "last_seen_ts": self.last_seen_ts,
            "confidence": self.confidence,
            "expression": self.expression,
            "source": self.source,
        }


@dataclass(slots=True)
class SpeechActivity:
    speaker: str
    transcript: str
    last_spoke_ts: int
    confidence: float
    topic: str | None = None

    def __post_init__(self) -> None:
        self.speaker = _required_text(self.speaker, "speaker")
        self.transcript = _required_text(self.transcript, "transcript")
        self.last_spoke_ts = validate_timestamp(self.last_spoke_ts, "last_spoke_ts")
        self.confidence = validate_confidence(self.confidence)
        self.topic = _optional_text(self.topic, "topic")

    def to_dict(self) -> dict[str, Any]:
        return {
            "speaker": self.speaker,
            "transcript": self.transcript,
            "last_spoke_ts": self.last_spoke_ts,
            "confidence": self.confidence,
            "topic": self.topic,
        }


@dataclass(slots=True)
class SoundState:
    source_label: str
    last_heard_ts: int
    confidence: float
    direction_deg: float | None = None

    def __post_init__(self) -> None:
        self.source_label = _required_text(self.source_label, "source_label")
        self.last_heard_ts = validate_timestamp(self.last_heard_ts, "last_heard_ts")
        self.confidence = validate_confidence(self.confidence)
        if self.direction_deg is not None:
            if isinstance(self.direction_deg, bool) or not isinstance(self.direction_deg, (int, float)):
                raise ValueError("direction_deg must be numeric when provided")
            self.direction_deg = float(self.direction_deg)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_label": self.source_label,
            "last_heard_ts": self.last_heard_ts,
            "confidence": self.confidence,
            "direction_deg": self.direction_deg,
        }


@dataclass(slots=True)
class TouchState:
    zone: str
    last_touched_ts: int
    confidence: float
    gesture: str | None = None

    def __post_init__(self) -> None:
        self.zone = _required_text(self.zone, "zone")
        self.last_touched_ts = validate_timestamp(self.last_touched_ts, "last_touched_ts")
        self.confidence = validate_confidence(self.confidence)
        self.gesture = _optional_text(self.gesture, "gesture")

    def to_dict(self) -> dict[str, Any]:
        return {
            "zone": self.zone,
            "last_touched_ts": self.last_touched_ts,
            "confidence": self.confidence,
            "gesture": self.gesture,
        }


@dataclass(slots=True)
class InternalState:
    status: str
    last_updated_ts: int
    confidence: float
    battery_pct: float | None = None
    safety_level: str | None = None

    def __post_init__(self) -> None:
        self.status = _required_text(self.status, "status")
        self.last_updated_ts = validate_timestamp(self.last_updated_ts, "last_updated_ts")
        self.confidence = validate_confidence(self.confidence)
        if self.battery_pct is not None:
            if isinstance(self.battery_pct, bool) or not isinstance(self.battery_pct, (int, float)):
                raise ValueError("battery_pct must be numeric when provided")
            self.battery_pct = float(self.battery_pct)
        self.safety_level = _optional_text(self.safety_level, "safety_level")

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "last_updated_ts": self.last_updated_ts,
            "confidence": self.confidence,
            "battery_pct": self.battery_pct,
            "safety_level": self.safety_level,
        }


@dataclass(slots=True)
class WorldModelSnapshot:
    snapshot_id: str
    created_ts: int
    persons: list[PersonPresence] = field(default_factory=list)
    active_speaker: str | None = None
    last_speech: SpeechActivity | None = None
    ambient_sound: SoundState | None = None
    last_touch: TouchState | None = None
    internal: InternalState | None = None
    safety_level: str | None = None

    def __post_init__(self) -> None:
        self.snapshot_id = _required_text(self.snapshot_id, "snapshot_id")
        self.created_ts = validate_timestamp(self.created_ts, "created_ts")
        self.persons = [
            person if isinstance(person, PersonPresence) else PersonPresence(**person)
            for person in self.persons
        ]
        self.active_speaker = _optional_text(self.active_speaker, "active_speaker")
        if self.last_speech is not None and not isinstance(self.last_speech, SpeechActivity):
            self.last_speech = SpeechActivity(**self.last_speech)
        if self.ambient_sound is not None and not isinstance(self.ambient_sound, SoundState):
            self.ambient_sound = SoundState(**self.ambient_sound)
        if self.last_touch is not None and not isinstance(self.last_touch, TouchState):
            self.last_touch = TouchState(**self.last_touch)
        if self.internal is not None and not isinstance(self.internal, InternalState):
            self.internal = InternalState(**self.internal)
        self.safety_level = _optional_text(self.safety_level, "safety_level")

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "created_ts": self.created_ts,
            "persons": [person.to_dict() for person in self.persons],
            "active_speaker": self.active_speaker,
            "last_speech": self.last_speech.to_dict() if self.last_speech else None,
            "ambient_sound": self.ambient_sound.to_dict() if self.ambient_sound else None,
            "last_touch": self.last_touch.to_dict() if self.last_touch else None,
            "internal": self.internal.to_dict() if self.internal else None,
            "safety_level": self.safety_level,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "WorldModelSnapshot":
        if not isinstance(data, Mapping):
            raise ValueError("data must be a mapping")
        return cls(
            snapshot_id=data["snapshot_id"],
            created_ts=data["created_ts"],
            persons=list(data.get("persons", [])),
            active_speaker=data.get("active_speaker"),
            last_speech=data.get("last_speech"),
            ambient_sound=data.get("ambient_sound"),
            last_touch=data.get("last_touch"),
            internal=data.get("internal"),
            safety_level=data.get("safety_level"),
        )


class WorldModel:
    """Fuses perception events into typed, TTL-bounded world state.

    State builder only: publishes world_state_update events and answers
    queries; it never publishes intent, skill goals, or safety overrides.
    """

    def __init__(
        self,
        *,
        bus: EventBus | None = None,
        source: str = "world_model",
        person_ttl_ms: int = DEFAULT_PERSON_TTL_MS,
        speaker_ttl_ms: int = DEFAULT_SPEAKER_TTL_MS,
        sound_ttl_ms: int = DEFAULT_SOUND_TTL_MS,
        clock: Callable[[], int] | None = None,
    ) -> None:
        self.source = _required_text(source, "source")
        self.person_ttl_ms = _positive_int(person_ttl_ms, "person_ttl_ms")
        self.speaker_ttl_ms = _positive_int(speaker_ttl_ms, "speaker_ttl_ms")
        self.sound_ttl_ms = _positive_int(sound_ttl_ms, "sound_ttl_ms")
        self._clock = clock or _now_ms
        self._bus: EventBus | None = None
        self._subscription: Subscription | None = None
        self._persons: dict[str, PersonPresence] = {}
        self._last_speech: SpeechActivity | None = None
        self._ambient_sound: SoundState | None = None
        self._last_touch: TouchState | None = None
        self._internal: InternalState | None = None
        self._safety_level: str | None = None
        if bus is not None:
            self.attach_to_bus(bus)

    def attach_to_bus(self, bus: EventBus) -> Subscription:
        self._bus = bus
        self._subscription = bus.subscribe(
            self.process_event,
            kinds=[
                RuntimeEventKind.PERCEPTION_OBSERVATION,
                RuntimeEventKind.SAFETY_EVENT,
            ],
            subscription_id=f"{self.source}_perception",
        )
        return self._subscription

    def process_event(self, event: RuntimeEvent) -> None:
        if event.kind == RuntimeEventKind.SAFETY_EVENT:
            self._apply_safety(event)
            return
        observation_type = _first_text(event.payload, ("observation_type", "type"))
        if observation_type in {"person_seen", "face_seen", "face", "person"}:
            self._apply_person(event)
        elif observation_type in {"speech_transcript", "speech", "utterance"}:
            self._apply_speech(event)
        elif observation_type in {"sound_direction", "sound"}:
            self._apply_sound(event)
        elif observation_type in {"touch", "tap"}:
            self._apply_touch(event)
        elif observation_type in {"body_health", "body_state", "internal_health"}:
            self._apply_internal(event)

    def expire(self, *, now_ms: int | None = None) -> None:
        now = self._clock() if now_ms is None else validate_timestamp(now_ms, "now_ms")
        self._persons = {
            person_id: person
            for person_id, person in self._persons.items()
            if now - person.last_seen_ts < self.person_ttl_ms
        }
        if (
            self._last_speech is not None
            and now - self._last_speech.last_spoke_ts >= self.speaker_ttl_ms
        ):
            self._last_speech = None
        if (
            self._ambient_sound is not None
            and now - self._ambient_sound.last_heard_ts >= self.sound_ttl_ms
        ):
            self._ambient_sound = None

    def snapshot(
        self,
        *,
        now_ms: int | None = None,
        snapshot_id: str | None = None,
    ) -> WorldModelSnapshot:
        now = self._clock() if now_ms is None else validate_timestamp(now_ms, "now_ms")
        self.expire(now_ms=now)
        return WorldModelSnapshot(
            snapshot_id=snapshot_id or f"world_{uuid.uuid4().hex[:12]}",
            created_ts=now,
            persons=sorted(self._persons.values(), key=lambda person: person.person_id),
            active_speaker=self._last_speech.speaker if self._last_speech else None,
            last_speech=self._last_speech,
            ambient_sound=self._ambient_sound,
            last_touch=self._last_touch,
            internal=self._internal,
            safety_level=self._safety_level,
        )

    def persons(self, *, now_ms: int | None = None) -> list[PersonPresence]:
        return self.snapshot(now_ms=now_ms).persons

    def active_speaker(self, *, now_ms: int | None = None) -> str | None:
        return self.snapshot(now_ms=now_ms).active_speaker

    def _apply_person(self, event: RuntimeEvent) -> None:
        payload = event.payload
        person_id = _first_text(payload, ("person_id", "speaker", "label"))
        if person_id is None:
            return
        self._upsert_person(
            person_id=person_id,
            label=_first_text(payload, ("label",)) or person_id,
            timestamp=event.timestamp,
            confidence=event.confidence if event.confidence is not None else 0.5,
            expression=_first_text(payload, ("expression",)),
            source=event.source,
        )
        self._publish_persons(event.timestamp)

    def _apply_speech(self, event: RuntimeEvent) -> None:
        payload = event.payload
        speaker = _first_text(payload, ("speaker", "speaker_id", "person_id"))
        transcript = _first_text(payload, ("transcript", "utterance", "text"))
        if speaker is None or transcript is None:
            return
        confidence = event.confidence if event.confidence is not None else 0.5
        self._last_speech = SpeechActivity(
            speaker=speaker,
            transcript=transcript,
            last_spoke_ts=event.timestamp,
            confidence=confidence,
            topic=_first_text(payload, ("topic", "current_topic")),
        )
        self._upsert_person(
            person_id=speaker,
            label=speaker,
            timestamp=event.timestamp,
            confidence=confidence,
            expression=None,
            source=event.source,
        )
        self._publish(
            state_key="active_speaker",
            payload={"value": speaker, "topic": self._last_speech.topic},
            confidence=confidence,
            timestamp=event.timestamp,
        )

    def _apply_sound(self, event: RuntimeEvent) -> None:
        payload = event.payload
        direction = payload.get("direction_deg", payload.get("azimuth_deg"))
        self._ambient_sound = SoundState(
            source_label=_first_text(payload, ("source_label", "label")) or "sound",
            last_heard_ts=event.timestamp,
            confidence=event.confidence if event.confidence is not None else 0.5,
            direction_deg=direction if isinstance(direction, (int, float)) else None,
        )
        self._publish(
            state_key="ambient_sound",
            payload=self._ambient_sound.to_dict(),
            confidence=self._ambient_sound.confidence,
            timestamp=event.timestamp,
        )

    def _apply_touch(self, event: RuntimeEvent) -> None:
        payload = event.payload
        zone = _first_text(payload, ("zone", "location", "label"))
        if zone is None:
            return
        self._last_touch = TouchState(
            zone=zone,
            last_touched_ts=event.timestamp,
            confidence=event.confidence if event.confidence is not None else 0.5,
            gesture=_first_text(payload, ("gesture",)),
        )
        self._publish(
            state_key="last_touch",
            payload=self._last_touch.to_dict(),
            confidence=self._last_touch.confidence,
            timestamp=event.timestamp,
        )

    def _apply_internal(self, event: RuntimeEvent) -> None:
        payload = event.payload
        status = _first_text(payload, ("status",))
        if status is None:
            return
        battery = payload.get("battery_pct")
        self._internal = InternalState(
            status=status,
            last_updated_ts=event.timestamp,
            confidence=event.confidence if event.confidence is not None else 0.5,
            battery_pct=battery if isinstance(battery, (int, float)) else None,
            safety_level=_first_text(payload, ("safety_level",)),
        )
        if self._internal.safety_level is not None:
            self._safety_level = self._internal.safety_level
        self._publish(
            state_key="internal_state",
            payload=self._internal.to_dict(),
            confidence=self._internal.confidence,
            timestamp=event.timestamp,
        )

    def _apply_safety(self, event: RuntimeEvent) -> None:
        level = _first_text(event.payload, ("safety_level", "level", "status"))
        if level is None:
            return
        self._safety_level = level
        self._publish(
            state_key="safety_state",
            payload={"safety_level": level, "source_event_id": event.event_id},
            confidence=event.confidence,
            timestamp=event.timestamp,
        )

    def _upsert_person(
        self,
        *,
        person_id: str,
        label: str,
        timestamp: int,
        confidence: float,
        expression: str | None,
        source: str,
    ) -> None:
        existing = self._persons.get(person_id)
        self._persons[person_id] = PersonPresence(
            person_id=person_id,
            label=label if label != person_id or existing is None else existing.label,
            last_seen_ts=timestamp,
            confidence=confidence,
            expression=expression if expression is not None else (existing.expression if existing else None),
            source=source,
        )

    def _publish_persons(self, timestamp: int) -> None:
        persons = sorted(self._persons.values(), key=lambda person: person.person_id)
        self._publish(
            state_key="persons",
            payload={
                "count": len(persons),
                "persons": [person.to_dict() for person in persons],
            },
            confidence=None,
            timestamp=timestamp,
        )

    def _publish(
        self,
        *,
        state_key: str,
        payload: Mapping[str, Any],
        confidence: float | None,
        timestamp: int,
    ) -> None:
        if self._bus is None:
            return
        self._bus.publish(
            world_state_update(
                source=self.source,
                state_key=state_key,
                payload=dict(payload),
                confidence=confidence,
                timestamp=timestamp,
            )
        )


def _first_text(payload: Mapping[str, Any], keys: Sequence[str]) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


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


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be a positive integer")
    if value < 1:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


def _now_ms() -> int:
    return int(time.time() * 1000)
