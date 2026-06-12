from __future__ import annotations

import time
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .models import validate_timestamp
from .runtime import (
    EventBus,
    RuntimeEvent,
    RuntimeEventKind,
    Subscription,
    world_state_update,
)
from .storage import MemoryStore
from .working_memory import WorkingMemory

DEFAULT_IDLE_TIMEOUT_MS = 8_000
DEFAULT_WINDOW_HISTORY = 32
INTERACTION_OBSERVATION_TYPES = frozenset(
    {"speech_transcript", "speech", "utterance", "person_seen", "face_seen", "face", "person", "touch", "tap"}
)


@dataclass(slots=True)
class ContextWindow:
    window_id: str
    opened_ts: int
    trigger: str
    last_activity_ts: int
    event_count: int = 0
    closed_ts: int | None = None
    close_reason: str | None = None
    snapshot_id: str | None = None

    def __post_init__(self) -> None:
        self.window_id = _required_text(self.window_id, "window_id")
        self.opened_ts = validate_timestamp(self.opened_ts, "opened_ts")
        self.trigger = _required_text(self.trigger, "trigger")
        self.last_activity_ts = validate_timestamp(self.last_activity_ts, "last_activity_ts")
        if isinstance(self.event_count, bool) or not isinstance(self.event_count, int) or self.event_count < 0:
            raise ValueError("event_count must be a non-negative integer")
        if self.closed_ts is not None:
            self.closed_ts = validate_timestamp(self.closed_ts, "closed_ts")
        self.close_reason = _optional_text(self.close_reason, "close_reason")
        self.snapshot_id = _optional_text(self.snapshot_id, "snapshot_id")

    @property
    def is_open(self) -> bool:
        return self.closed_ts is None

    def to_dict(self) -> dict[str, Any]:
        return {
            "window_id": self.window_id,
            "opened_ts": self.opened_ts,
            "trigger": self.trigger,
            "last_activity_ts": self.last_activity_ts,
            "event_count": self.event_count,
            "closed_ts": self.closed_ts,
            "close_reason": self.close_reason,
            "snapshot_id": self.snapshot_id,
        }


class ContextWindowManager:
    """Bounds interactions into context windows with automatic snapshots.

    Opens a window when an interaction-relevant perception event arrives,
    keeps it alive while activity continues, and closes it after an idle
    timeout — persisting a working-memory snapshot at the close boundary.
    Owns window lifecycle only; WorkingMemory content updates are untouched.
    """

    def __init__(
        self,
        working_memory: WorkingMemory,
        *,
        store: MemoryStore | None = None,
        bus: EventBus | None = None,
        idle_timeout_ms: int = DEFAULT_IDLE_TIMEOUT_MS,
        max_history: int = DEFAULT_WINDOW_HISTORY,
        source: str = "context_windows",
        clock: Callable[[], int] | None = None,
    ) -> None:
        self.working_memory = working_memory
        self.store = store
        self.bus = bus
        self.idle_timeout_ms = _positive_int(idle_timeout_ms, "idle_timeout_ms")
        self.max_history = _positive_int(max_history, "max_history")
        self.source = _required_text(source, "source")
        self._clock = clock or _now_ms
        self._subscription: Subscription | None = None
        self._current: ContextWindow | None = None
        self._history: list[ContextWindow] = []
        self._window_counter = 0

    @property
    def current_window(self) -> ContextWindow | None:
        return self._current

    @property
    def history(self) -> list[ContextWindow]:
        return list(self._history)

    def attach_to_bus(self, bus: EventBus) -> Subscription:
        self.bus = bus
        self._subscription = bus.subscribe(
            self.handle_event,
            kinds=[RuntimeEventKind.PERCEPTION_OBSERVATION],
            subscription_id=f"{self.source}_perception",
        )
        return self._subscription

    def handle_event(self, event: RuntimeEvent) -> None:
        observation_type = _first_text(event.payload, ("observation_type", "type"))
        if observation_type not in INTERACTION_OBSERVATION_TYPES:
            return
        if self._current is None:
            self._open_window(trigger=observation_type, timestamp=event.timestamp)
        self._current.last_activity_ts = max(self._current.last_activity_ts, event.timestamp)
        self._current.event_count += 1

    def tick(self, now_ms: int | None = None) -> ContextWindow | None:
        now = self._clock() if now_ms is None else validate_timestamp(now_ms, "now_ms")
        if self._current is None:
            return None
        if now - self._current.last_activity_ts <= self.idle_timeout_ms:
            return None
        return self._close_window(reason="idle_timeout", now_ms=now)

    def close_now(self, *, reason: str, now_ms: int | None = None) -> ContextWindow | None:
        now = self._clock() if now_ms is None else validate_timestamp(now_ms, "now_ms")
        if self._current is None:
            return None
        return self._close_window(reason=reason, now_ms=now)

    def _open_window(self, *, trigger: str, timestamp: int) -> None:
        self._window_counter += 1
        self._current = ContextWindow(
            window_id=f"ctxwin_{self._window_counter:06d}_{uuid.uuid4().hex[:8]}",
            opened_ts=timestamp,
            trigger=trigger,
            last_activity_ts=timestamp,
        )
        self._publish_transition(status="opened", window=self._current, timestamp=timestamp)

    def _close_window(self, *, reason: str, now_ms: int) -> ContextWindow:
        window = self._current
        window.closed_ts = now_ms
        window.close_reason = reason
        if self.store is not None:
            snapshot = self.working_memory.persist_snapshot(self.store, created_ts=now_ms)
            window.snapshot_id = snapshot.snapshot_id
        self._current = None
        self._history.append(window)
        self._history = self._history[-self.max_history :]
        self._publish_transition(status="closed", window=window, timestamp=now_ms)
        return window

    def _publish_transition(self, *, status: str, window: ContextWindow, timestamp: int) -> None:
        if self.bus is None:
            return
        self.bus.publish(
            world_state_update(
                source=self.source,
                state_key="context_window",
                payload={"status": status, **window.to_dict()},
                confidence=None,
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
