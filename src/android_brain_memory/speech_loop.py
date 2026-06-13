from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from .dialogue import UtterancePlan
from .live_perception import LivePerceptionReport
from .models import validate_timestamp
from .runtime import EventBus, RuntimeEvent, RuntimeEventKind, Subscription


DEFAULT_DUPLICATE_WINDOW_MS = 3_000
DEFAULT_MAX_RESPONSE_WAIT_MS = 5_000
DEFAULT_MAX_SPEAKING_MS = 30_000
SELF_SPEAKERS = {"mneme", "robot", "assistant"}
TERMINAL_SPEECH_STATUSES = {"completed", "failed", "preempted", "canceled"}


@dataclass(slots=True)
class SpeechTurnRecord:
    turn_id: str
    speaker: str
    text: str
    timestamp: int
    source: str
    event_id: str | None = None
    transcript_id: str | None = None
    confidence: float | None = None
    response_generated: bool = False
    response_ts: int | None = None
    response_latency_ms: int | None = None
    plan_id: str | None = None
    suppressed: bool = False
    suppression_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "speaker": self.speaker,
            "text": self.text,
            "timestamp": self.timestamp,
            "source": self.source,
            "event_id": self.event_id,
            "transcript_id": self.transcript_id,
            "confidence": self.confidence,
            "response_generated": self.response_generated,
            "response_ts": self.response_ts,
            "response_latency_ms": self.response_latency_ms,
            "plan_id": self.plan_id,
            "suppressed": self.suppressed,
            "suppression_reason": self.suppression_reason,
        }


@dataclass(slots=True)
class SpeechLoopDiagnostics:
    duplicate_window_ms: int = DEFAULT_DUPLICATE_WINDOW_MS
    max_response_wait_ms: int = DEFAULT_MAX_RESPONSE_WAIT_MS
    max_speaking_ms: int = DEFAULT_MAX_SPEAKING_MS
    self_speakers: set[str] = field(default_factory=lambda: set(SELF_SPEAKERS))
    _subscription: Subscription | None = field(default=None, init=False)
    _turns: dict[str, SpeechTurnRecord] = field(default_factory=dict, init=False)
    _turn_order: list[str] = field(default_factory=list, init=False)
    _responded_turn_ids: set[str] = field(default_factory=set, init=False)
    _responded_text_keys: dict[str, int] = field(default_factory=dict, init=False)
    _stuck_keys: set[str] = field(default_factory=set, init=False)
    _terminal_goal_ids: set[str] = field(default_factory=set, init=False)
    _active_speech_goal: dict[str, Any] | None = field(default=None, init=False)
    current_state: str = field(default="idle", init=False)
    latest_capture_report: dict[str, Any] | None = field(default=None, init=False)
    latest_failure_reason: str | None = field(default=None, init=False)
    latest_response: dict[str, Any] | None = field(default=None, init=False)
    latest_asr_latency_ms: int | None = field(default=None, init=False)
    latest_response_latency_ms: int | None = field(default=None, init=False)
    latest_tts_latency_ms: int | None = field(default=None, init=False)
    counters: dict[str, int] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self.duplicate_window_ms = _positive_int(
            self.duplicate_window_ms,
            "duplicate_window_ms",
        )
        self.max_response_wait_ms = _positive_int(
            self.max_response_wait_ms,
            "max_response_wait_ms",
        )
        self.max_speaking_ms = _positive_int(self.max_speaking_ms, "max_speaking_ms")
        self.self_speakers = {
            _required_text(speaker, "self_speakers").lower()
            for speaker in self.self_speakers
        }
        self.counters = {
            "capture_attempts": 0,
            "transcripts": 0,
            "no_speech": 0,
            "no_microphone": 0,
            "capture_errors": 0,
            "responses_generated": 0,
            "duplicate_suppressions": 0,
            "speech_goals": 0,
            "tts_completed": 0,
            "tts_failures": 0,
            "tts_preempted": 0,
            "tts_canceled": 0,
            "barge_ins": 0,
            "stuck_states": 0,
        }

    def attach_to_bus(self, bus: EventBus) -> Subscription:
        self._subscription = bus.subscribe(
            self.process_event,
            kinds=[
                RuntimeEventKind.PERCEPTION_OBSERVATION,
                RuntimeEventKind.SKILL_GOAL,
                RuntimeEventKind.SKILL_STATUS,
            ],
            subscription_id="speech_loop_diagnostics",
        )
        return self._subscription

    def process_event(self, event: RuntimeEvent) -> None:
        if event.kind == RuntimeEventKind.PERCEPTION_OBSERVATION:
            if str(event.payload.get("observation_type", "")) == "speech_transcript":
                self.record_transcript_event(event)
        elif event.kind == RuntimeEventKind.SKILL_GOAL:
            if str(event.payload.get("goal_type", "")) == "speech":
                self._record_speech_goal(event)
        elif event.kind == RuntimeEventKind.SKILL_STATUS:
            if str(event.payload.get("goal_type", "")) == "speech":
                self._record_speech_status(event)

    def record_capture_report(self, report: LivePerceptionReport | Mapping[str, Any]) -> None:
        data = report.to_dict() if isinstance(report, LivePerceptionReport) else dict(report)
        if data.get("worker") != "speech":
            return
        status = str(data.get("status", ""))
        details = data.get("details", {})
        details = details if isinstance(details, Mapping) else {}
        self.latest_capture_report = dict(data)
        self.counters["capture_attempts"] += 1
        latency = _optional_int(details.get("latency_ms"))
        if latency is not None:
            self.latest_asr_latency_ms = latency

        if status == "transcribed":
            self.counters["transcripts"] += 1
            latest_response_ts = (
                int(self.latest_response["timestamp"])
                if self.latest_response is not None
                else None
            )
            if latest_response_ts is None or latest_response_ts < int(data.get("timestamp", 0)):
                self.current_state = "thinking"
            if (
                self.latest_failure_reason == "no_microphone"
                or (
                    isinstance(self.latest_failure_reason, str)
                    and self.latest_failure_reason.startswith("capture_error")
                )
            ):
                self.latest_failure_reason = None
        elif status == "no_speech":
            self.counters["no_speech"] += 1
            if self._active_speech_goal is None:
                self.current_state = "listening"
        elif status == "no_microphone":
            self.counters["no_microphone"] += 1
            self.current_state = "degraded"
            self.latest_failure_reason = "no_microphone"
        elif status == "capture_error":
            self.counters["capture_errors"] += 1
            self.current_state = "degraded"
            error = details.get("error")
            self.latest_failure_reason = f"capture_error:{error}" if error else "capture_error"

    def record_transcript_event(self, event: RuntimeEvent) -> SpeechTurnRecord | None:
        speaker = _optional_text(event.payload.get("speaker"))
        text = _optional_text(
            event.payload.get("utterance")
            or event.payload.get("transcript")
            or event.payload.get("text")
        )
        if speaker is None or text is None:
            return None
        if speaker.lower() in self.self_speakers:
            return None
        turn_id = turn_id_from_dialogue_turn({
            "speaker": speaker,
            "text": text,
            "timestamp": event.timestamp,
            "source": event.source,
            "event_id": event.event_id,
            "transcript_id": event.payload.get("transcript_id"),
        })
        existing = self._turns.get(turn_id)
        if existing is not None:
            return existing
        record = SpeechTurnRecord(
            turn_id=turn_id,
            speaker=speaker,
            text=text,
            timestamp=event.timestamp,
            source=event.source,
            event_id=event.event_id,
            transcript_id=_optional_text(event.payload.get("transcript_id")),
            confidence=event.confidence,
        )
        self._turns[turn_id] = record
        self._turn_order.append(turn_id)
        self._turn_order = self._turn_order[-20:]
        self.current_state = "thinking"
        return record

    def should_suppress_response(
        self,
        dialogue_turn: Mapping[str, Any],
        *,
        timestamp: int,
    ) -> bool:
        turn_id = turn_id_from_dialogue_turn(dialogue_turn)
        source = _optional_text(dialogue_turn.get("source"))
        if source is None or source == "virtual_head.typed_input":
            return False
        if turn_id in self._responded_turn_ids:
            self._mark_suppressed(dialogue_turn, "same_turn_already_responded")
            return True
        text_key = _dialogue_text_key(dialogue_turn)
        last_response_ts = self._responded_text_keys.get(text_key)
        if last_response_ts is None:
            return False
        if timestamp - last_response_ts <= self.duplicate_window_ms:
            self._mark_suppressed(dialogue_turn, "duplicate_transcript_window")
            return True
        return False

    def record_response(
        self,
        dialogue_turn: Mapping[str, Any],
        plan: UtterancePlan,
        *,
        timestamp: int,
    ) -> None:
        turn_id = turn_id_from_dialogue_turn(dialogue_turn)
        record = self._turns.get(turn_id)
        if record is None:
            record = _record_from_dialogue_turn(dialogue_turn)
            self._turns[turn_id] = record
            self._turn_order.append(turn_id)
            self._turn_order = self._turn_order[-20:]
        latency = max(timestamp - int(record.timestamp), 0)
        record.response_generated = True
        record.response_ts = timestamp
        record.response_latency_ms = latency
        record.plan_id = plan.plan_id
        self._responded_turn_ids.add(turn_id)
        self._responded_text_keys[_dialogue_text_key(dialogue_turn)] = timestamp
        self.latest_response_latency_ms = latency
        self.latest_response = {
            "turn_id": turn_id,
            "plan_id": plan.plan_id,
            "timestamp": timestamp,
            "response_latency_ms": latency,
            "memory_refs": [dict(ref) for ref in plan.memory_refs],
        }
        self.counters["responses_generated"] += 1
        self.current_state = "speaking"

    def check_stuck_states(self, *, now_ms: int) -> None:
        now = validate_timestamp(now_ms, "now_ms")
        if self._active_speech_goal is not None:
            started_ts = int(self._active_speech_goal.get("started_ts", now))
            goal_id = str(self._active_speech_goal.get("goal_id", "speech"))
            if now - started_ts > self.max_speaking_ms:
                self._mark_stuck(f"speaking:{goal_id}", "speaking_timeout")
        for turn_id in list(self._turn_order):
            turn = self._turns.get(turn_id)
            if turn is None or turn.response_generated or turn.suppressed:
                continue
            if turn.source == "virtual_head.typed_input":
                continue
            if now - turn.timestamp > self.max_response_wait_ms:
                self._mark_stuck(f"response:{turn_id}", "response_timeout")

    def to_dict(self) -> dict[str, Any]:
        latest_turn = self._turns[self._turn_order[-1]].to_dict() if self._turn_order else None
        return {
            "current_state": self.current_state,
            "counters": dict(self.counters),
            "latest_capture_report": dict(self.latest_capture_report) if self.latest_capture_report else None,
            "latest_turn": latest_turn,
            "latest_response": dict(self.latest_response) if self.latest_response else None,
            "latest_failure_reason": self.latest_failure_reason,
            "latest_asr_latency_ms": self.latest_asr_latency_ms,
            "latest_response_latency_ms": self.latest_response_latency_ms,
            "latest_tts_latency_ms": self.latest_tts_latency_ms,
            "active_speech_goal": dict(self._active_speech_goal) if self._active_speech_goal else None,
            "recent_turns": [
                self._turns[turn_id].to_dict()
                for turn_id in self._turn_order[-5:]
                if turn_id in self._turns
            ],
            "config": {
                "duplicate_window_ms": self.duplicate_window_ms,
                "max_response_wait_ms": self.max_response_wait_ms,
                "max_speaking_ms": self.max_speaking_ms,
            },
        }

    def _record_speech_goal(self, event: RuntimeEvent) -> None:
        self.counters["speech_goals"] += 1
        goal_id = _optional_text(event.payload.get("goal_id"))
        if goal_id is not None and goal_id in self._terminal_goal_ids:
            return
        self.current_state = "speaking"
        self._active_speech_goal = {
            "goal_id": goal_id,
            "plan_id": event.payload.get("plan_id"),
            "turn_id": event.payload.get("turn_id"),
            "started_ts": event.timestamp,
            "text_chars": len(str(event.payload.get("text", ""))),
        }

    def _record_speech_status(self, event: RuntimeEvent) -> None:
        status = str(event.payload.get("status", ""))
        goal_id = _optional_text(event.payload.get("goal_id"))
        if status == "running":
            self.current_state = "speaking"
            if self._active_speech_goal is None:
                self._active_speech_goal = {
                    "goal_id": goal_id,
                    "plan_id": event.payload.get("plan_id"),
                    "turn_id": event.payload.get("turn_id"),
                    "started_ts": event.timestamp,
                    "text_chars": len(str(event.payload.get("text", ""))),
                }
            return

        if status == "completed":
            self.counters["tts_completed"] += 1
            self.latest_failure_reason = None
        elif status == "failed":
            self.counters["tts_failures"] += 1
            self.latest_failure_reason = _failure_reason(event.payload, "tts_failed")
            self.current_state = "degraded"
        elif status == "preempted":
            self.counters["tts_preempted"] += 1
            if event.payload.get("reason") == "barge_in":
                self.counters["barge_ins"] += 1
            self.current_state = "listening"
        elif status == "canceled":
            self.counters["tts_canceled"] += 1
            self.current_state = "listening"

        latency = _tts_latency_from_status(event.payload)
        if latency is not None:
            self.latest_tts_latency_ms = latency
        if status in TERMINAL_SPEECH_STATUSES:
            if goal_id is not None:
                self._terminal_goal_ids.add(goal_id)
            if status != "failed":
                self.current_state = "listening"
            self._active_speech_goal = None

    def _mark_suppressed(self, dialogue_turn: Mapping[str, Any], reason: str) -> None:
        turn_id = turn_id_from_dialogue_turn(dialogue_turn)
        record = self._turns.get(turn_id)
        if record is None:
            record = _record_from_dialogue_turn(dialogue_turn)
            self._turns[turn_id] = record
            self._turn_order.append(turn_id)
            self._turn_order = self._turn_order[-20:]
        if not record.suppressed:
            self.counters["duplicate_suppressions"] += 1
        record.suppressed = True
        record.suppression_reason = reason
        self.current_state = "listening"

    def _mark_stuck(self, key: str, reason: str) -> None:
        if key in self._stuck_keys:
            return
        self._stuck_keys.add(key)
        self.counters["stuck_states"] += 1
        self.latest_failure_reason = reason
        self.current_state = "degraded"


def turn_id_from_dialogue_turn(dialogue_turn: Mapping[str, Any]) -> str:
    event_id = _optional_text(dialogue_turn.get("event_id"))
    if event_id is not None:
        return f"turn_{event_id}"
    transcript_id = _optional_text(dialogue_turn.get("transcript_id"))
    if transcript_id is not None:
        return f"turn_{transcript_id}"
    speaker = _optional_text(dialogue_turn.get("speaker")) or "unknown"
    text = _optional_text(dialogue_turn.get("text")) or ""
    timestamp = dialogue_turn.get("timestamp", 0)
    digest = hashlib.sha256(
        f"{speaker.lower()}|{timestamp}|{' '.join(text.lower().split())}".encode("utf-8")
    ).hexdigest()[:12]
    return f"turn_{digest}"


def _record_from_dialogue_turn(dialogue_turn: Mapping[str, Any]) -> SpeechTurnRecord:
    return SpeechTurnRecord(
        turn_id=turn_id_from_dialogue_turn(dialogue_turn),
        speaker=_optional_text(dialogue_turn.get("speaker")) or "unknown",
        text=_optional_text(dialogue_turn.get("text")) or "",
        timestamp=validate_timestamp(int(dialogue_turn.get("timestamp", 0)), "timestamp"),
        source=_optional_text(dialogue_turn.get("source")) or "unknown",
        event_id=_optional_text(dialogue_turn.get("event_id")),
        transcript_id=_optional_text(dialogue_turn.get("transcript_id")),
    )


def _dialogue_text_key(dialogue_turn: Mapping[str, Any]) -> str:
    speaker = (_optional_text(dialogue_turn.get("speaker")) or "unknown").lower()
    text = " ".join((_optional_text(dialogue_turn.get("text")) or "").lower().split())
    return f"{speaker}:{text}"


def _tts_latency_from_status(payload: Mapping[str, Any]) -> int | None:
    latency = _optional_int(payload.get("tts_latency_ms"))
    if latency is not None:
        return latency
    output = payload.get("output")
    if isinstance(output, Mapping):
        metadata = output.get("metadata")
        if isinstance(metadata, Mapping):
            return _optional_int(metadata.get("tts_latency_ms"))
    return None


def _failure_reason(payload: Mapping[str, Any], default: str) -> str:
    error = _optional_text(payload.get("error"))
    reason = _optional_text(payload.get("reason"))
    if error:
        return f"{default}:{error}"
    return reason or default


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _optional_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return max(value, 0)
    if isinstance(value, float):
        return max(int(value), 0)
    return None


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()
