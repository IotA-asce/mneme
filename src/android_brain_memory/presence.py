from __future__ import annotations

import subprocess
import time
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .dialogue import UtterancePlan
from .executive import ExecutiveIntent, ExecutiveIntentType
from .models import validate_confidence, validate_timestamp
from .runtime import (
    EventBus,
    RuntimeEvent,
    RuntimeEventKind,
    Subscription,
    skill_goal,
    skill_status,
)
from .speech_loop import turn_id_from_dialogue_turn


DEFAULT_SKILL_TTL_MS = 5_000
DEFAULT_SPEECH_DURATION_MS = 900
SELF_SPEAKERS = {"mneme", "robot", "assistant"}


class VirtualSkillStatus(StrEnum):
    ACCEPTED = "accepted"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PREEMPTED = "preempted"
    CANCELED = "canceled"


class VirtualAvatarMode(StrEnum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    SAFETY = "safety"


@dataclass(slots=True)
class SpeechOutput:
    output_id: str
    text: str
    created_ts: int
    status: str = "spoken"
    voice: str | None = None
    device_id: str | None = None
    command: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.output_id = _required_text(self.output_id, "output_id")
        self.text = _required_text(self.text, "text")
        self.created_ts = validate_timestamp(self.created_ts, "created_ts")
        self.status = _required_text(self.status, "status")
        self.voice = _optional_text(self.voice, "voice")
        self.device_id = _optional_text(self.device_id, "device_id")
        self.command = _string_list(self.command, "command")
        self.metadata = _json_mapping(self.metadata, "metadata")

    def to_dict(self) -> dict[str, Any]:
        return {
            "output_id": self.output_id,
            "text": self.text,
            "created_ts": self.created_ts,
            "status": self.status,
            "voice": self.voice,
            "device_id": self.device_id,
            "command": list(self.command),
            "metadata": dict(self.metadata),
        }


class SpeechOutputBackend:
    def speak(
        self,
        *,
        text: str,
        voice: str | None,
        device_id: str | None,
        timestamp: int,
    ) -> SpeechOutput:
        raise NotImplementedError


class SimulatedSpeechOutputBackend(SpeechOutputBackend):
    """Deterministic speech backend that records text but plays no audio."""

    def __init__(self) -> None:
        self.outputs: list[SpeechOutput] = []

    def speak(
        self,
        *,
        text: str,
        voice: str | None,
        device_id: str | None,
        timestamp: int,
    ) -> SpeechOutput:
        output = SpeechOutput(
            output_id=f"speech_{uuid.uuid4().hex[:12]}",
            text=text,
            created_ts=timestamp,
            status="simulated",
            voice=voice,
            device_id=device_id,
            metadata={"backend": "simulated"},
        )
        self.outputs.append(output)
        return output


class CommandSpeechOutputBackend(SpeechOutputBackend):
    """Runs a configured local TTS command.

    Supported placeholders are `{text}`, `{voice}`, and `{device_id}`.
    The command is optional runtime integration, not a bundled TTS engine.
    """

    def __init__(
        self,
        command_template: Sequence[str],
        *,
        command_runner: Callable[[Sequence[str], int], str] | None = None,
        timeout_ms: int = 10_000,
        default_voice: str | None = None,
    ) -> None:
        self.command_template = [_required_text(part, "command_template item") for part in command_template]
        if not self.command_template:
            raise ValueError("command_template must not be empty")
        self.command_runner = command_runner or _run_command
        self.timeout_ms = _positive_int(timeout_ms, "timeout_ms")
        self.default_voice = _optional_text(default_voice, "default_voice")

    def speak(
        self,
        *,
        text: str,
        voice: str | None,
        device_id: str | None,
        timestamp: int,
    ) -> SpeechOutput:
        resolved_voice = voice or self.default_voice
        command = [
            _format_command_part(
                part,
                {
                    "text": text,
                    "voice": resolved_voice or "",
                    "device_id": device_id or "",
                },
            )
            for part in self.command_template
        ]
        stdout = self.command_runner(command, self.timeout_ms)
        return SpeechOutput(
            output_id=f"speech_{uuid.uuid4().hex[:12]}",
            text=text,
            created_ts=timestamp,
            status="spoken",
            voice=resolved_voice,
            device_id=device_id,
            command=command,
            metadata={"backend": "command", "stdout": stdout.strip()},
        )


@dataclass(slots=True)
class VirtualSkillGoal:
    goal_id: str
    skill_id: str
    goal_type: str
    created_ts: int
    payload: dict[str, Any] = field(default_factory=dict)
    source_event_id: str | None = None

    def __post_init__(self) -> None:
        self.goal_id = _required_text(self.goal_id, "goal_id")
        self.skill_id = _required_text(self.skill_id, "skill_id")
        self.goal_type = _required_text(self.goal_type, "goal_type")
        self.created_ts = validate_timestamp(self.created_ts, "created_ts")
        self.payload = _json_mapping(self.payload, "payload")
        self.source_event_id = _optional_text(self.source_event_id, "source_event_id")

    @classmethod
    def from_event(cls, event: RuntimeEvent) -> "VirtualSkillGoal":
        return cls(
            goal_id=str(event.payload.get("goal_id", f"goal_{event.event_id}")),
            skill_id=str(event.payload.get("skill_id", "virtual_skill")),
            goal_type=str(event.payload.get("goal_type", "unknown")),
            created_ts=event.timestamp,
            payload=dict(event.payload),
            source_event_id=event.event_id,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "skill_id": self.skill_id,
            "goal_type": self.goal_type,
            "created_ts": self.created_ts,
            "payload": dict(self.payload),
            "source_event_id": self.source_event_id,
        }


@dataclass(slots=True)
class VirtualSkillRecord:
    goal: VirtualSkillGoal
    status: VirtualSkillStatus
    started_ts: int
    due_ts: int
    output: SpeechOutput | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal.to_dict(),
            "status": self.status.value,
            "started_ts": self.started_ts,
            "due_ts": self.due_ts,
            "output": self.output.to_dict() if self.output else None,
        }


@dataclass(slots=True)
class VirtualAvatarState:
    updated_ts: int
    mode: VirtualAvatarMode | str = VirtualAvatarMode.IDLE
    gaze_target: str | None = None
    expression: str = "neutral"
    blink_pattern: str = "idle"
    mouth_state: str = "closed"
    safety_level: str | None = None
    speaking_text: str | None = None
    last_skill_status: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        self.updated_ts = validate_timestamp(self.updated_ts, "updated_ts")
        self.mode = self.mode if isinstance(self.mode, VirtualAvatarMode) else VirtualAvatarMode(self.mode)
        self.gaze_target = _optional_text(self.gaze_target, "gaze_target")
        self.expression = _required_text(self.expression, "expression")
        self.blink_pattern = _required_text(self.blink_pattern, "blink_pattern")
        self.mouth_state = _required_text(self.mouth_state, "mouth_state")
        self.safety_level = _optional_text(self.safety_level, "safety_level")
        self.speaking_text = _optional_text(self.speaking_text, "speaking_text")
        if self.last_skill_status is not None:
            self.last_skill_status = _json_mapping(self.last_skill_status, "last_skill_status")

    def to_dict(self) -> dict[str, Any]:
        return {
            "updated_ts": self.updated_ts,
            "mode": self.mode.value,
            "gaze_target": self.gaze_target,
            "expression": self.expression,
            "blink_pattern": self.blink_pattern,
            "mouth_state": self.mouth_state,
            "safety_level": self.safety_level,
            "speaking_text": self.speaking_text,
            "last_skill_status": dict(self.last_skill_status) if self.last_skill_status else None,
        }


class VirtualAvatarController:
    """Maintains on-screen expression state for the virtual head."""

    def __init__(
        self,
        *,
        clock: Callable[[], int] | None = None,
        source: str = "virtual_avatar",
    ) -> None:
        self._clock = clock or _now_ms
        self.source = _required_text(source, "source")
        self.state = VirtualAvatarState(updated_ts=self._clock())
        self._subscription: Subscription | None = None
        self._bus: EventBus | None = None

    def attach_to_bus(self, bus: EventBus) -> Subscription:
        self._bus = bus
        self._subscription = bus.subscribe(
            self.process_event,
            kinds=[
                RuntimeEventKind.ATTENTION_UPDATE,
                RuntimeEventKind.EXECUTIVE_INTENT,
                RuntimeEventKind.SKILL_GOAL,
                RuntimeEventKind.SKILL_STATUS,
                RuntimeEventKind.SAFETY_EVENT,
            ],
            subscription_id=f"{self.source}_events",
        )
        return self._subscription

    def process_event(self, event: RuntimeEvent) -> None:
        if event.kind == RuntimeEventKind.ATTENTION_UPDATE:
            self._apply_attention(event)
        elif event.kind == RuntimeEventKind.EXECUTIVE_INTENT:
            self._apply_intent(event)
        elif event.kind == RuntimeEventKind.SKILL_GOAL:
            self._apply_skill_goal(event)
        elif event.kind == RuntimeEventKind.SKILL_STATUS:
            self._apply_skill_status(event)
        elif event.kind == RuntimeEventKind.SAFETY_EVENT:
            self._set_state(
                event.timestamp,
                mode=VirtualAvatarMode.SAFETY,
                expression="concerned",
                blink_pattern="still",
                mouth_state="closed",
                safety_level=str(event.payload.get("safety_level", event.payload.get("level", "safety"))),
            )

    def _apply_attention(self, event: RuntimeEvent) -> None:
        target = event.payload.get("attention_target")
        target_id = None
        if isinstance(target, Mapping):
            target_id = target.get("target_id")
        target_id = target_id or event.payload.get("focus_id")
        if isinstance(target_id, str):
            self._set_state(event.timestamp, gaze_target=target_id)

    def _apply_intent(self, event: RuntimeEvent) -> None:
        intent_type = str(event.payload.get("intent_type", ""))
        if intent_type == ExecutiveIntentType.LISTEN.value:
            self._set_state(
                event.timestamp,
                mode=VirtualAvatarMode.LISTENING,
                expression="attentive",
                blink_pattern="attentive",
                mouth_state="closed",
            )
        elif intent_type == ExecutiveIntentType.RESPOND_TO_USER.value:
            if (
                self.state.mode == VirtualAvatarMode.SPEAKING
                or not isinstance(event.payload.get("dialogue_turn"), Mapping)
            ):
                return
            self._set_state(
                event.timestamp,
                mode=VirtualAvatarMode.THINKING,
                expression="engaged",
                blink_pattern="attentive",
                mouth_state="closed",
            )
        elif intent_type == ExecutiveIntentType.IDLE_PRESENCE.value:
            if self.state.mode == VirtualAvatarMode.SPEAKING:
                return
            self._set_state(
                event.timestamp,
                mode=VirtualAvatarMode.IDLE,
                expression="neutral",
                blink_pattern=str(event.payload.get("idle_behavior", "idle")),
                mouth_state="closed",
                speaking_text=None,
            )
        elif intent_type == ExecutiveIntentType.LOOK_AT_TARGET.value:
            self._set_state(
                event.timestamp,
                gaze_target=str(event.payload.get("target_id", event.payload.get("attention_target", ""))) or None,
                expression="attentive",
            )

    def _apply_skill_goal(self, event: RuntimeEvent) -> None:
        goal_type = str(event.payload.get("goal_type", ""))
        if goal_type == "speech":
            self._set_state(
                event.timestamp,
                mode=VirtualAvatarMode.SPEAKING,
                expression="speaking",
                blink_pattern="speaking",
                mouth_state="open",
                speaking_text=str(event.payload.get("text", "")) or None,
            )
        elif goal_type in {"gaze_on_screen", "gaze"}:
            self._set_state(
                event.timestamp,
                gaze_target=str(event.payload.get("target_id", event.payload.get("target", ""))) or None,
                expression="attentive",
            )
        elif goal_type == "idle_presence":
            self._set_state(
                event.timestamp,
                mode=VirtualAvatarMode.IDLE,
                expression="neutral",
                blink_pattern=str(event.payload.get("pattern", "idle")),
                mouth_state="closed",
                speaking_text=None,
            )

    def _apply_skill_status(self, event: RuntimeEvent) -> None:
        status = str(event.payload.get("status", ""))
        goal_type = str(event.payload.get("goal_type", ""))
        self.state.last_skill_status = dict(event.payload)
        if goal_type == "speech":
            if status == VirtualSkillStatus.RUNNING.value:
                self._set_state(
                    event.timestamp,
                    mode=VirtualAvatarMode.SPEAKING,
                    expression="speaking",
                    mouth_state="open",
                    speaking_text=str(event.payload.get("text", self.state.speaking_text or "")) or None,
                )
            elif status in {
                VirtualSkillStatus.COMPLETED.value,
                VirtualSkillStatus.PREEMPTED.value,
                VirtualSkillStatus.CANCELED.value,
                VirtualSkillStatus.FAILED.value,
            }:
                self._set_state(
                    event.timestamp,
                    mode=VirtualAvatarMode.LISTENING,
                    expression="attentive",
                    blink_pattern="attentive",
                    mouth_state="closed",
                    speaking_text=None,
                )

    def _set_state(self, timestamp: int, **updates: Any) -> None:
        current = self.state.to_dict()
        current.update(updates)
        current["updated_ts"] = timestamp
        self.state = VirtualAvatarState(**current)


class VirtualSkillRunner:
    """Simulated skill runner for speech, gaze, expression, and idle presence."""

    def __init__(
        self,
        *,
        bus: EventBus | None = None,
        speech_backend: SpeechOutputBackend | None = None,
        source: str = "virtual_skill_runner",
        clock: Callable[[], int] | None = None,
        speech_duration_ms: int = DEFAULT_SPEECH_DURATION_MS,
    ) -> None:
        self.bus = bus
        self.source = _required_text(source, "source")
        self._clock = clock or _now_ms
        self.speech_backend = speech_backend or SimulatedSpeechOutputBackend()
        self.speech_duration_ms = _non_negative_int(speech_duration_ms, "speech_duration_ms")
        self._subscription: Subscription | None = None
        self._active: VirtualSkillRecord | None = None
        self._completed: list[VirtualSkillRecord] = []
        self._outputs: list[SpeechOutput] = []
        self._stats = {
            "accepted": 0,
            "completed": 0,
            "failed": 0,
            "preempted": 0,
            "canceled": 0,
        }
        if bus is not None:
            self.attach_to_bus(bus)

    @property
    def active(self) -> VirtualSkillRecord | None:
        return self._active

    @property
    def outputs(self) -> list[SpeechOutput]:
        return list(self._outputs)

    @property
    def stats(self) -> dict[str, Any]:
        return {
            **dict(self._stats),
            "active": self._active.to_dict() if self._active else None,
            "outputs": [output.to_dict() for output in self._outputs[-10:]],
        }

    def attach_to_bus(self, bus: EventBus) -> Subscription:
        self.bus = bus
        self._subscription = bus.subscribe(
            self.handle_goal_event,
            kinds=[RuntimeEventKind.SKILL_GOAL],
            subscription_id=f"{self.source}_goals",
        )
        return self._subscription

    def handle_goal_event(self, event: RuntimeEvent) -> VirtualSkillRecord | None:
        try:
            goal = VirtualSkillGoal.from_event(event)
        except ValueError:
            return None
        return self.start_goal(goal, now_ms=event.timestamp)

    def start_goal(self, goal: VirtualSkillGoal, *, now_ms: int | None = None) -> VirtualSkillRecord:
        now = self._clock() if now_ms is None else validate_timestamp(now_ms, "now_ms")
        if self._active is not None:
            replaces_active = (
                goal.goal_type == "speech"
                or goal.goal_type == self._active.goal.goal_type
            )
            if replaces_active:
                self.preempt_active(reason="new_goal", now_ms=now)
            else:
                return self._complete_immediate_goal(goal, now)
        self._publish_status(goal, VirtualSkillStatus.ACCEPTED, now)
        self._publish_status(goal, VirtualSkillStatus.RUNNING, now)
        output = None
        tts_started = time.perf_counter()
        try:
            if goal.goal_type == "speech":
                output = self.speech_backend.speak(
                    text=str(goal.payload.get("text", "")),
                    voice=_optional_text(goal.payload.get("voice"), "voice"),
                    device_id=_optional_text(goal.payload.get("device_id"), "device_id"),
                    timestamp=now,
                )
                output.metadata = {
                    **dict(output.metadata),
                    "tts_latency_ms": int((time.perf_counter() - tts_started) * 1000),
                }
                self._outputs.append(output)
            duration = _non_negative_int(
                goal.payload.get(
                    "duration_ms",
                    self.speech_duration_ms if goal.goal_type == "speech" else 0,
                ),
                "duration_ms",
            )
            record = VirtualSkillRecord(
                goal=goal,
                status=VirtualSkillStatus.RUNNING,
                started_ts=now,
                due_ts=now + duration,
                output=output,
            )
            self._active = record
            self._stats["accepted"] += 1
            if duration == 0:
                self.complete_active(now_ms=now)
            return record
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            self._stats["failed"] += 1
            self._publish_status(
                goal,
                VirtualSkillStatus.FAILED,
                now,
                {
                    "error": type(exc).__name__,
                    "tts_latency_ms": int((time.perf_counter() - tts_started) * 1000),
                },
            )
            record = VirtualSkillRecord(
                goal=goal,
                status=VirtualSkillStatus.FAILED,
                started_ts=now,
                due_ts=now,
                output=None,
            )
            self._completed.append(record)
            return record

    def _complete_immediate_goal(self, goal: VirtualSkillGoal, timestamp: int) -> VirtualSkillRecord:
        self._publish_status(goal, VirtualSkillStatus.ACCEPTED, timestamp)
        self._publish_status(goal, VirtualSkillStatus.RUNNING, timestamp)
        self._publish_status(goal, VirtualSkillStatus.COMPLETED, timestamp)
        record = VirtualSkillRecord(
            goal=goal,
            status=VirtualSkillStatus.COMPLETED,
            started_ts=timestamp,
            due_ts=timestamp,
            output=None,
        )
        self._completed.append(record)
        self._stats["accepted"] += 1
        self._stats["completed"] += 1
        return record

    def tick(self, *, now_ms: int | None = None) -> VirtualSkillRecord | None:
        now = self._clock() if now_ms is None else validate_timestamp(now_ms, "now_ms")
        if self._active is not None and now >= self._active.due_ts:
            return self.complete_active(now_ms=now)
        return None

    def complete_active(self, *, now_ms: int | None = None) -> VirtualSkillRecord | None:
        if self._active is None:
            return None
        now = self._clock() if now_ms is None else validate_timestamp(now_ms, "now_ms")
        record = self._finish_active(VirtualSkillStatus.COMPLETED, now)
        self._stats["completed"] += 1
        return record

    def preempt_active(self, *, reason: str = "preempted", now_ms: int | None = None) -> VirtualSkillRecord | None:
        if self._active is None:
            return None
        now = self._clock() if now_ms is None else validate_timestamp(now_ms, "now_ms")
        record = self._finish_active(VirtualSkillStatus.PREEMPTED, now, {"reason": reason})
        self._stats["preempted"] += 1
        return record

    def cancel_active(self, *, reason: str = "canceled", now_ms: int | None = None) -> VirtualSkillRecord | None:
        if self._active is None:
            return None
        now = self._clock() if now_ms is None else validate_timestamp(now_ms, "now_ms")
        record = self._finish_active(VirtualSkillStatus.CANCELED, now, {"reason": reason})
        self._stats["canceled"] += 1
        return record

    def _finish_active(
        self,
        status: VirtualSkillStatus,
        timestamp: int,
        extra_payload: Mapping[str, Any] | None = None,
    ) -> VirtualSkillRecord:
        assert self._active is not None
        record = self._active
        record.status = status
        payload = dict(extra_payload or {})
        if record.output is not None:
            output = record.output.to_dict()
            payload.setdefault("output", output)
            latency = output.get("metadata", {}).get("tts_latency_ms")
            if latency is not None:
                payload.setdefault("tts_latency_ms", latency)
        self._publish_status(record.goal, status, timestamp, payload)
        self._completed.append(record)
        self._active = None
        return record

    def _publish_status(
        self,
        goal: VirtualSkillGoal,
        status: VirtualSkillStatus,
        timestamp: int,
        extra_payload: Mapping[str, Any] | None = None,
    ) -> None:
        if self.bus is None:
            return
        payload = {
            "goal_id": goal.goal_id,
            "goal_type": goal.goal_type,
            "source_event_id": goal.source_event_id,
            **goal.payload,
            **dict(extra_payload or {}),
        }
        self.bus.publish(
            skill_status(
                source=self.source,
                skill_id=goal.skill_id,
                status=status.value,
                payload=payload,
                confidence=1.0,
                timestamp=timestamp,
                ttl_ms=DEFAULT_SKILL_TTL_MS,
                event_id=f"evt_{goal.goal_id}_{status.value}",
            )
        )


class ConversationalPresenceCoordinator:
    """Maps executive/dialogue output into virtual skill goals and interruptions."""

    def __init__(
        self,
        *,
        bus: EventBus,
        skill_runner: VirtualSkillRunner,
        source: str = "conversational_presence",
        clock: Callable[[], int] | None = None,
        default_voice: str = "default",
        preferred_speaker_device_id: str | None = None,
        self_speakers: set[str] | None = None,
    ) -> None:
        self.bus = bus
        self.skill_runner = skill_runner
        self.source = _required_text(source, "source")
        self._clock = clock or _now_ms
        self.default_voice = _required_text(default_voice, "default_voice")
        self.preferred_speaker_device_id = _optional_text(
            preferred_speaker_device_id,
            "preferred_speaker_device_id",
        )
        self.self_speakers = {speaker.lower() for speaker in (self_speakers or SELF_SPEAKERS)}
        self._subscription = bus.subscribe(
            self.process_event,
            kinds=[RuntimeEventKind.PERCEPTION_OBSERVATION, RuntimeEventKind.SAFETY_EVENT],
            subscription_id=f"{self.source}_events",
        )
        self._stats = {"speech_goals": 0, "gaze_goals": 0, "idle_goals": 0, "barge_ins": 0}

    @property
    def stats(self) -> dict[str, int]:
        return dict(self._stats)

    def process_event(self, event: RuntimeEvent) -> None:
        if event.kind == RuntimeEventKind.SAFETY_EVENT:
            self.skill_runner.cancel_active(reason="safety_event", now_ms=event.timestamp)
            return
        observation_type = str(event.payload.get("observation_type", ""))
        if observation_type != "speech_transcript":
            return
        speaker = str(event.payload.get("speaker", ""))
        if speaker.lower() in self.self_speakers:
            return
        if self.skill_runner.active is not None and self.skill_runner.active.goal.goal_type == "speech":
            self.skill_runner.preempt_active(reason="barge_in", now_ms=event.timestamp)
            self._stats["barge_ins"] += 1

    def handle_intent(
        self,
        intent: ExecutiveIntent,
        *,
        plan: UtterancePlan | None = None,
        timestamp: int | None = None,
    ) -> None:
        now = self._clock() if timestamp is None else validate_timestamp(timestamp, "timestamp")
        if intent.intent_type == ExecutiveIntentType.LOOK_AT_TARGET and intent.target_id:
            self._publish_goal(
                skill_id="virtual_gaze",
                goal_type="gaze_on_screen",
                payload={
                    "goal_id": f"goal_gaze_{intent.intent_id}",
                    "target_id": intent.target_id,
                    "reason": intent.reason,
                },
                timestamp=now,
            )
            self._stats["gaze_goals"] += 1
        elif intent.intent_type == ExecutiveIntentType.IDLE_PRESENCE:
            self._publish_goal(
                skill_id="virtual_idle_presence",
                goal_type="idle_presence",
                payload={
                    "goal_id": f"goal_idle_{intent.intent_id}",
                    "pattern": str(intent.payload.get("idle_behavior", "idle")),
                    "reason": intent.reason,
                },
                timestamp=now,
            )
            self._stats["idle_goals"] += 1
        elif intent.intent_type == ExecutiveIntentType.LISTEN and intent.target_id:
            target_id = (
                intent.target_id
                if ":" in intent.target_id
                else f"person:{intent.target_id}"
            )
            self._publish_goal(
                skill_id="virtual_gaze",
                goal_type="gaze_on_screen",
                payload={
                    "goal_id": f"goal_listen_{intent.intent_id}",
                    "target_id": target_id,
                    "reason": intent.reason,
                },
                timestamp=now,
            )
            self._stats["gaze_goals"] += 1

        if plan is not None:
            dialogue_turn = intent.payload.get("dialogue_turn")
            turn_payload = {}
            if isinstance(dialogue_turn, Mapping):
                turn_payload = {
                    "turn_id": turn_id_from_dialogue_turn(dialogue_turn),
                    "turn_event_id": dialogue_turn.get("event_id"),
                    "turn_source": dialogue_turn.get("source"),
                    "turn_timestamp": dialogue_turn.get("timestamp"),
                }
            self._publish_goal(
                skill_id="virtual_speech",
                goal_type="speech",
                payload={
                    "goal_id": f"goal_speech_{plan.plan_id}",
                    "text": plan.text,
                    "plan_id": plan.plan_id,
                    "intent_id": intent.intent_id,
                    "voice": self.default_voice,
                    "device_id": self.preferred_speaker_device_id,
                    **turn_payload,
                },
                timestamp=now,
            )
            self._stats["speech_goals"] += 1

    def _publish_goal(
        self,
        *,
        skill_id: str,
        goal_type: str,
        payload: Mapping[str, Any],
        timestamp: int,
    ) -> None:
        self.bus.publish(
            skill_goal(
                source=self.source,
                skill_id=skill_id,
                goal_type=goal_type,
                payload=dict(payload),
                confidence=1.0,
                timestamp=timestamp,
                ttl_ms=DEFAULT_SKILL_TTL_MS,
                event_id=f"evt_{payload.get('goal_id', uuid.uuid4().hex[:12])}",
            )
        )


def _run_command(command: Sequence[str], timeout_ms: int) -> str:
    completed = subprocess.run(
        list(command),
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout_ms / 1000,
    )
    return completed.stdout


def _format_command_part(part: str, values: Mapping[str, str]) -> str:
    formatted = part
    for key, value in values.items():
        formatted = formatted.replace(f"{{{key}}}", value)
    return formatted


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _optional_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    return value.strip() or None


def _json_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    return dict(value)


def _string_list(value: Any, field_name: str) -> list[str]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ValueError(f"{field_name} must be a list of strings")
    items = list(value)
    if not all(isinstance(item, str) for item in items):
        raise ValueError(f"{field_name} must be a list of strings")
    return items


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


def _non_negative_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")
    return value


def _now_ms() -> int:
    return int(time.time() * 1000)
