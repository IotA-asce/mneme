from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
import time
import uuid
from typing import Any

from .models import validate_confidence, validate_salience, validate_timestamp
from .runtime import (
    EventBus,
    RuntimeEvent,
    RuntimeEventKind,
    Subscription,
    attention_update,
)


DEFAULT_ATTENTION_TARGET_TTL_MS = 3_000
DEFAULT_ATTENTION_DWELL_MS = 500
DEFAULT_SWITCH_MARGIN = 0.12
DEFAULT_SELF_NAMES = ("mneme", "robot")

ATTENTION_WEIGHTS = {
    "safety_relevance": 0.50,
    "active_speaker": 0.26,
    "explicit_user_address": 0.20,
    "current_goal": 0.14,
    "sound_event": 0.12,
    "face_person_presence": 0.10,
    "novelty": 0.08,
    "confidence": 0.10,
}


@dataclass(slots=True)
class AttentionTarget:
    target_id: str
    target_type: str
    label: str
    source: str
    last_event_id: str
    last_seen_ts: int
    confidence: float
    priority: float
    factors: dict[str, float] = field(default_factory=dict)
    weighted_components: dict[str, float] = field(default_factory=dict)
    payload: dict[str, Any] = field(default_factory=dict)
    ttl_ms: int = DEFAULT_ATTENTION_TARGET_TTL_MS

    def __post_init__(self) -> None:
        self.target_id = _required_text(self.target_id, "target_id")
        self.target_type = _required_text(self.target_type, "target_type")
        self.label = _required_text(self.label, "label")
        self.source = _required_text(self.source, "source")
        self.last_event_id = _required_text(self.last_event_id, "last_event_id")
        self.last_seen_ts = validate_timestamp(self.last_seen_ts, "last_seen_ts")
        self.confidence = validate_confidence(self.confidence)
        self.priority = validate_salience(self.priority, "priority")
        self.factors = _float_mapping(self.factors, "factors")
        self.weighted_components = _float_mapping(
            self.weighted_components,
            "weighted_components",
        )
        self.payload = _json_mapping(self.payload, "payload")
        self.ttl_ms = _positive_int(self.ttl_ms, "ttl_ms")

    @property
    def expires_at(self) -> int:
        return self.last_seen_ts + self.ttl_ms

    def is_expired(self, now_ms: int) -> bool:
        now = validate_timestamp(now_ms, "now_ms")
        return now >= self.expires_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_id": self.target_id,
            "target_type": self.target_type,
            "label": self.label,
            "source": self.source,
            "last_event_id": self.last_event_id,
            "last_seen_ts": self.last_seen_ts,
            "confidence": self.confidence,
            "priority": self.priority,
            "factors": dict(self.factors),
            "weighted_components": dict(self.weighted_components),
            "payload": dict(self.payload),
            "ttl_ms": self.ttl_ms,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "AttentionTarget":
        data = _required_mapping(data)
        return cls(
            target_id=_required(data, "target_id"),
            target_type=_required(data, "target_type"),
            label=_required(data, "label"),
            source=_required(data, "source"),
            last_event_id=_required(data, "last_event_id"),
            last_seen_ts=_required(data, "last_seen_ts"),
            confidence=_required(data, "confidence"),
            priority=_required(data, "priority"),
            factors=dict(data.get("factors", {})),
            weighted_components=dict(data.get("weighted_components", {})),
            payload=dict(data.get("payload", {})),
            ttl_ms=data.get("ttl_ms", DEFAULT_ATTENTION_TARGET_TTL_MS),
        )


@dataclass(slots=True)
class AttentionState:
    state_id: str
    created_ts: int
    active_target_id: str | None = None
    active_target: AttentionTarget | None = None
    candidates: list[AttentionTarget] = field(default_factory=list)
    locked_until_ts: int | None = None
    dwell_remaining_ms: int = 0
    reason: str = "no_target"

    def __post_init__(self) -> None:
        self.state_id = _required_text(self.state_id, "state_id")
        self.created_ts = validate_timestamp(self.created_ts, "created_ts")
        self.active_target_id = _optional_text(self.active_target_id, "active_target_id")
        if self.active_target is not None and not isinstance(self.active_target, AttentionTarget):
            self.active_target = AttentionTarget.from_dict(self.active_target)
        self.candidates = [
            candidate
            if isinstance(candidate, AttentionTarget)
            else AttentionTarget.from_dict(candidate)
            for candidate in self.candidates
        ]
        if self.locked_until_ts is not None:
            self.locked_until_ts = validate_timestamp(self.locked_until_ts, "locked_until_ts")
        self.dwell_remaining_ms = _non_negative_int(
            self.dwell_remaining_ms,
            "dwell_remaining_ms",
        )
        self.reason = _required_text(self.reason, "reason")

    def to_dict(self) -> dict[str, Any]:
        return {
            "state_id": self.state_id,
            "created_ts": self.created_ts,
            "active_target_id": self.active_target_id,
            "active_target": (
                self.active_target.to_dict() if self.active_target is not None else None
            ),
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "locked_until_ts": self.locked_until_ts,
            "dwell_remaining_ms": self.dwell_remaining_ms,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "AttentionState":
        data = _required_mapping(data)
        active_target = data.get("active_target")
        return cls(
            state_id=_required(data, "state_id"),
            created_ts=_required(data, "created_ts"),
            active_target_id=data.get("active_target_id"),
            active_target=(
                AttentionTarget.from_dict(active_target)
                if active_target is not None
                else None
            ),
            candidates=[
                AttentionTarget.from_dict(candidate)
                for candidate in data.get("candidates", [])
            ],
            locked_until_ts=data.get("locked_until_ts"),
            dwell_remaining_ms=data.get("dwell_remaining_ms", 0),
            reason=data.get("reason", "no_target"),
        )


class AttentionManager:
    """Computes and publishes attention state without commanding motion."""

    def __init__(
        self,
        *,
        dwell_ms: int = DEFAULT_ATTENTION_DWELL_MS,
        target_ttl_ms: int = DEFAULT_ATTENTION_TARGET_TTL_MS,
        switch_margin: float = DEFAULT_SWITCH_MARGIN,
        self_names: Sequence[str] = DEFAULT_SELF_NAMES,
        source: str = "attention_manager",
        clock: Callable[[], int] | None = None,
        bus: EventBus | None = None,
    ) -> None:
        self.dwell_ms = _positive_int(dwell_ms, "dwell_ms")
        self.target_ttl_ms = _positive_int(target_ttl_ms, "target_ttl_ms")
        self.switch_margin = validate_salience(switch_margin, "switch_margin")
        self.self_names = tuple(_required_text(name, "self_names") for name in self_names)
        self.source = _required_text(source, "source")
        self._clock = clock or _now_ms
        self._targets: dict[str, AttentionTarget] = {}
        self._active_target_id: str | None = None
        self._locked_until_ts: int | None = None
        self._state_counter = 0
        self._subscription: Subscription | None = None
        self._bus: EventBus | None = None
        self._current_goal_text: str | None = None
        if bus is not None:
            self.attach_to_bus(bus)

    def attach_to_bus(self, bus: EventBus) -> Subscription:
        self._bus = bus
        self._subscription = bus.subscribe(
            self.process_event,
            kinds=[
                RuntimeEventKind.PERCEPTION_OBSERVATION,
                RuntimeEventKind.WORLD_STATE_UPDATE,
                RuntimeEventKind.EXECUTIVE_INTENT,
                RuntimeEventKind.SKILL_GOAL,
                RuntimeEventKind.SAFETY_EVENT,
            ],
        )
        return self._subscription

    def process_event(self, event: RuntimeEvent) -> AttentionState:
        now_ms = self._clock()
        self.expire(now_ms=now_ms)
        target = self._target_from_event(event)
        if target is not None and not target.is_expired(now_ms):
            self._targets[target.target_id] = target
        state = self._select_state(now_ms=now_ms)
        self._publish_state(state)
        return state

    def expire(self, *, now_ms: int | None = None) -> list[AttentionTarget]:
        now = self._clock() if now_ms is None else validate_timestamp(now_ms, "now_ms")
        expired = [target for target in self._targets.values() if target.is_expired(now)]
        for target in expired:
            self._targets.pop(target.target_id, None)
        if self._active_target_id not in self._targets:
            self._active_target_id = None
            self._locked_until_ts = None
        return sorted(expired, key=lambda target: (target.last_seen_ts, target.target_id))

    def state(self, *, now_ms: int | None = None) -> AttentionState:
        now = self._clock() if now_ms is None else validate_timestamp(now_ms, "now_ms")
        self.expire(now_ms=now)
        return self._build_state(now_ms=now, reason="current_state")

    def targets(self, *, now_ms: int | None = None) -> list[AttentionTarget]:
        now = self._clock() if now_ms is None else validate_timestamp(now_ms, "now_ms")
        self.expire(now_ms=now)
        return self._ordered_targets()

    def _target_from_event(self, event: RuntimeEvent) -> AttentionTarget | None:
        if event.kind == RuntimeEventKind.PERCEPTION_OBSERVATION:
            return self._perception_target(event)
        if event.kind == RuntimeEventKind.SAFETY_EVENT:
            return self._safety_target(event)
        if event.kind in {RuntimeEventKind.EXECUTIVE_INTENT, RuntimeEventKind.SKILL_GOAL}:
            return self._goal_target(event)
        if event.kind == RuntimeEventKind.WORLD_STATE_UPDATE:
            return self._world_state_target(event)
        return None

    def _perception_target(self, event: RuntimeEvent) -> AttentionTarget | None:
        payload = event.payload
        observation_type = _first_text(payload, ("observation_type", "type")) or "observation"
        confidence = event.confidence if event.confidence is not None else 0.5
        factors = _empty_factors(confidence)

        if observation_type in {"speech_transcript", "speech", "utterance"}:
            speaker = _first_text(payload, ("speaker", "speaker_id", "person_id"))
            if speaker is None:
                return None
            target_id = f"person:{speaker}"
            label = speaker
            target_type = "person"
            factors["active_speaker"] = 1.0
            text = _first_text(payload, ("transcript", "utterance", "text")) or ""
            if self._mentions_self(text):
                factors["explicit_user_address"] = 1.0
        elif observation_type in {"person_seen", "face_seen", "face", "person"}:
            person_id = _first_text(payload, ("person_id", "speaker", "label"))
            if person_id is None:
                return None
            target_id = f"person:{person_id}"
            label = _first_text(payload, ("label", "person_id")) or person_id
            target_type = "person"
            factors["face_person_presence"] = 1.0
        elif observation_type in {"sound_direction", "sound"}:
            label = _first_text(payload, ("source_label", "label")) or "sound"
            direction = payload.get("direction_deg", payload.get("azimuth_deg"))
            direction_part = str(int(direction)) if isinstance(direction, (int, float)) else label
            target_id = f"sound:{label}:{direction_part}"
            target_type = "sound"
            factors["sound_event"] = 1.0
        elif observation_type in {"touch", "tap"}:
            zone = _first_text(payload, ("zone", "location", "label")) or "touch"
            target_id = f"touch:{zone}"
            label = zone
            target_type = "touch"
            factors["novelty"] = 1.0
        else:
            object_id = _first_text(payload, ("object_id", "target_id", "label", "name"))
            if object_id is None:
                return None
            target_id = f"object:{object_id}"
            label = object_id
            target_type = "object"

        if target_id not in self._targets:
            factors["novelty"] = max(factors["novelty"], 1.0)
        else:
            factors["novelty"] = max(factors["novelty"], 0.25)
        factors["current_goal"] = self._goal_match_factor(payload, label)
        return self._build_target(
            event=event,
            target_id=target_id,
            target_type=target_type,
            label=label,
            factors=factors,
        )

    def _safety_target(self, event: RuntimeEvent) -> AttentionTarget:
        payload = event.payload
        safety_level = _first_text(payload, ("safety_level", "level", "status")) or "safety"
        confidence = event.confidence if event.confidence is not None else 1.0
        factors = _empty_factors(confidence)
        factors["safety_relevance"] = _safety_relevance(safety_level)
        if factors["safety_relevance"] > 0:
            factors["novelty"] = 1.0 if f"safety:{safety_level}" not in self._targets else 0.25
        return self._build_target(
            event=event,
            target_id=f"safety:{safety_level}",
            target_type="safety",
            label=safety_level,
            factors=factors,
        )

    def _goal_target(self, event: RuntimeEvent) -> AttentionTarget | None:
        payload = event.payload
        goal = _first_text(payload, ("active_goal", "goal", "goal_type", "intent_type", "skill_id"))
        if goal is None:
            return None
        self._current_goal_text = goal
        confidence = event.confidence if event.confidence is not None else 0.7
        factors = _empty_factors(confidence)
        factors["current_goal"] = 1.0
        factors["novelty"] = 1.0 if f"goal:{goal}" not in self._targets else 0.25
        return self._build_target(
            event=event,
            target_id=f"goal:{goal}",
            target_type="goal",
            label=goal,
            factors=factors,
        )

    def _world_state_target(self, event: RuntimeEvent) -> AttentionTarget | None:
        payload = event.payload
        state_key = _first_text(payload, ("state_key",))
        if state_key == "active_speaker":
            speaker = _first_text(payload, ("value", "speaker", "person_id"))
            if speaker is None:
                return None
            confidence = event.confidence if event.confidence is not None else 0.7
            factors = _empty_factors(confidence)
            factors["active_speaker"] = 1.0
            factors["novelty"] = 1.0 if f"person:{speaker}" not in self._targets else 0.25
            return self._build_target(
                event=event,
                target_id=f"person:{speaker}",
                target_type="person",
                label=speaker,
                factors=factors,
            )
        if state_key in {"active_goal", "goal", "current_goal"}:
            goal = _first_text(payload, ("value", "goal", "active_goal"))
            if goal is not None:
                self._current_goal_text = goal
        return None

    def _build_target(
        self,
        *,
        event: RuntimeEvent,
        target_id: str,
        target_type: str,
        label: str,
        factors: Mapping[str, float],
    ) -> AttentionTarget:
        normalized_factors = {
            name: validate_salience(value, name)
            for name, value in factors.items()
        }
        components = {
            name: round(normalized_factors.get(name, 0.0) * weight, 6)
            for name, weight in ATTENTION_WEIGHTS.items()
        }
        priority = validate_salience(sum(components.values()), "priority")
        ttl_ms = event.ttl_ms if event.ttl_ms is not None else self.target_ttl_ms
        return AttentionTarget(
            target_id=target_id,
            target_type=target_type,
            label=label,
            source=event.source,
            last_event_id=event.event_id,
            last_seen_ts=event.timestamp,
            confidence=normalized_factors["confidence"],
            priority=priority,
            factors=normalized_factors,
            weighted_components=components,
            payload=dict(event.payload),
            ttl_ms=ttl_ms,
        )

    def _select_state(self, *, now_ms: int) -> AttentionState:
        best = self._ordered_targets()[0] if self._targets else None
        current = self._targets.get(self._active_target_id) if self._active_target_id else None
        safety_candidate = self._safety_candidate(current)
        if safety_candidate is not None:
            best = safety_candidate

        if best is None:
            self._active_target_id = None
            self._locked_until_ts = None
            return self._build_state(now_ms=now_ms, reason="no_target")

        if current is None:
            self._activate(best, now_ms=now_ms)
            return self._build_state(now_ms=now_ms, reason="initial_target")

        if (
            self._locked_until_ts is not None
            and now_ms < self._locked_until_ts
            and best.target_id != current.target_id
            and not _safety_override(best, current)
            and best.priority <= current.priority + self.switch_margin
        ):
            return self._build_state(now_ms=now_ms, reason="dwell_lock_active")

        if best.target_id == current.target_id:
            return self._build_state(now_ms=now_ms, reason="target_refreshed")

        if _safety_override(best, current):
            self._activate(best, now_ms=now_ms)
            return self._build_state(now_ms=now_ms, reason="safety_override")

        if best.priority > current.priority + self.switch_margin:
            self._activate(best, now_ms=now_ms)
            return self._build_state(now_ms=now_ms, reason="higher_priority")

        return self._build_state(now_ms=now_ms, reason="current_target_retained")

    def _activate(self, target: AttentionTarget, *, now_ms: int) -> None:
        self._active_target_id = target.target_id
        self._locked_until_ts = now_ms + self.dwell_ms

    def _build_state(self, *, now_ms: int, reason: str) -> AttentionState:
        self._state_counter += 1
        candidates = self._ordered_targets()
        active_target = (
            self._targets.get(self._active_target_id)
            if self._active_target_id is not None
            else None
        )
        dwell_remaining = 0
        if self._locked_until_ts is not None:
            dwell_remaining = max(0, self._locked_until_ts - now_ms)
        return AttentionState(
            state_id=f"attn_state_{self._state_counter:06d}",
            created_ts=now_ms,
            active_target_id=self._active_target_id,
            active_target=active_target,
            candidates=candidates,
            locked_until_ts=self._locked_until_ts,
            dwell_remaining_ms=dwell_remaining,
            reason=reason,
        )

    def _publish_state(self, state: AttentionState) -> None:
        if self._bus is None or state.active_target is None:
            return
        self._bus.publish(
            attention_update(
                source=self.source,
                focus_id=state.active_target.target_id,
                payload={
                    "attention_state": state.to_dict(),
                    "attention_target": state.active_target.to_dict(),
                    "reason": state.reason,
                    "priority": state.active_target.priority,
                },
                confidence=state.active_target.confidence,
                timestamp=state.created_ts,
                ttl_ms=state.active_target.ttl_ms,
                event_id=f"evt_{state.state_id}",
            )
        )

    def _ordered_targets(self) -> list[AttentionTarget]:
        return sorted(
            self._targets.values(),
            key=lambda target: (
                -target.priority,
                -target.last_seen_ts,
                target.target_id,
            ),
        )

    def _safety_candidate(self, current: AttentionTarget | None) -> AttentionTarget | None:
        current_safety = (
            current.factors.get("safety_relevance", 0.0)
            if current is not None
            else 0.0
        )
        candidates = [
            target
            for target in self._targets.values()
            if target.factors.get("safety_relevance", 0.0) > current_safety
        ]
        if not candidates:
            return None
        return sorted(
            candidates,
            key=lambda target: (
                -target.factors.get("safety_relevance", 0.0),
                -target.priority,
                -target.last_seen_ts,
                target.target_id,
            ),
        )[0]

    def _mentions_self(self, text: str) -> bool:
        lower_text = text.lower()
        return any(name.lower() in lower_text for name in self.self_names)

    def _goal_match_factor(self, payload: Mapping[str, Any], label: str) -> float:
        if self._current_goal_text is None:
            return 0.0
        goal_text = self._current_goal_text.lower()
        haystack = " ".join(
            str(value).lower()
            for value in [label, *payload.values()]
            if isinstance(value, (str, int, float))
        )
        return 1.0 if goal_text in haystack else 0.0


def _empty_factors(confidence: float) -> dict[str, float]:
    return {
        "active_speaker": 0.0,
        "sound_event": 0.0,
        "face_person_presence": 0.0,
        "explicit_user_address": 0.0,
        "safety_relevance": 0.0,
        "novelty": 0.0,
        "current_goal": 0.0,
        "confidence": validate_confidence(confidence),
    }


def _safety_relevance(level: str) -> float:
    normalized = level.strip().lower()
    if normalized in {"emergency", "critical", "estop", "stop", "unsafe"}:
        return 1.0
    if normalized in {"degraded", "warning", "caution", "fault"}:
        return 0.9
    if normalized in {"normal", "nominal", "ok", "safe"}:
        return 0.0
    return 0.6


def _safety_override(best: AttentionTarget, current: AttentionTarget) -> bool:
    return (
        best.factors.get("safety_relevance", 0.0) > 0.0
        and best.factors.get("safety_relevance", 0.0)
        > current.factors.get("safety_relevance", 0.0)
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


def _float_mapping(value: Any, field_name: str) -> dict[str, float]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    result = {}
    for key, item in value.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError(f"{field_name} keys must be non-empty strings")
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ValueError(f"{field_name}.{key} must be numeric")
        result[key] = float(item)
    return result


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


def _now_ms() -> int:
    return int(time.time() * 1000)
