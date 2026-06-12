from __future__ import annotations

from android_brain_memory import (
    AttentionState,
    AttentionTarget,
    EventBus,
    Executive,
    ExecutiveIntent,
    ExecutiveIntentType,
    ExecutiveMode,
    WorkingMemory,
    attention_update,
    perception_observation,
    safety_event,
)
from android_brain_memory.runtime import RuntimeEventKind


class FixedClock:
    def __init__(self, now_ms: int) -> None:
        self.now_ms = now_ms

    def __call__(self) -> int:
        return self.now_ms


def test_active_user_interaction_priority_emits_respond_intent_only():
    clock = FixedClock(1_000)
    bus = EventBus(clock=clock)
    working = WorkingMemory(clock=clock)
    working.attach_to_bus(bus)
    executive = Executive(working_memory=working, clock=clock, bus=bus)

    bus.publish(
        perception_observation(
            source="speech_worker",
            observation_type="speech_transcript",
            payload={"speaker": "user", "transcript": "hello Mneme"},
            confidence=0.9,
            timestamp=1_000,
            event_id="evt_user",
        )
    )

    intent_events = bus.history(kinds=[RuntimeEventKind.EXECUTIVE_INTENT])
    skill_events = bus.history(kinds=[RuntimeEventKind.SKILL_GOAL, RuntimeEventKind.SKILL_STATUS])

    assert executive.last_intent is not None
    assert executive.last_intent.intent_type == ExecutiveIntentType.RESPOND_TO_USER
    assert executive.last_intent.priority == 70
    assert intent_events[-1].payload["intent_type"] == "respond_to_user"
    assert skill_events == []


def test_safety_preempts_active_user_interaction_with_freeze_motion():
    clock = FixedClock(2_000)
    bus = EventBus(clock=clock)
    working = WorkingMemory(clock=clock)
    working.attach_to_bus(bus)
    executive = Executive(working_memory=working, clock=clock, bus=bus)

    bus.publish(
        perception_observation(
            source="speech_worker",
            observation_type="speech_transcript",
            payload={"speaker": "user", "transcript": "can you respond?"},
            confidence=0.9,
            timestamp=2_000,
            event_id="evt_user",
        )
    )
    previous_intent = executive.last_intent
    assert previous_intent is not None
    assert previous_intent.intent_type == ExecutiveIntentType.RESPOND_TO_USER

    clock.now_ms = 2_100
    bus.publish(
        safety_event(
            source="safety_supervisor",
            safety_level="critical",
            payload={"reason": "bench motion limit exceeded"},
            confidence=1.0,
            timestamp=2_100,
            event_id="evt_safety",
        )
    )

    assert executive.last_intent is not None
    assert executive.last_intent.intent_type == ExecutiveIntentType.FREEZE_MOTION
    assert executive.last_intent.mode == ExecutiveMode.FROZEN
    assert executive.last_intent.priority == 100
    assert executive.last_intent.preempts_intent_id == previous_intent.intent_id


def test_degraded_safety_enters_degraded_mode():
    clock = FixedClock(3_000)
    executive = Executive(clock=clock)

    intent = executive.run_once(
        safety_state={
            "payload": {"safety_level": "degraded", "reason": "body health uncertainty"},
            "confidence": 0.8,
        },
        publish=False,
    )

    assert intent.intent_type == ExecutiveIntentType.ENTER_DEGRADED_MODE
    assert intent.mode == ExecutiveMode.DEGRADED
    assert intent.confidence == 0.8


def test_explicit_memory_instruction_after_active_window_emits_remember_event():
    clock = FixedClock(10_000)
    working = WorkingMemory(clock=clock)
    working.add_dialogue_turn(
        speaker="user",
        text="Remember that I prefer short calibration prompts.",
        timestamp=5_000,
        event_id="evt_memory_instruction",
    )
    executive = Executive(working_memory=working, clock=clock)

    intent = executive.run_once(publish=False)

    assert intent.intent_type == ExecutiveIntentType.REMEMBER_EVENT
    assert intent.priority == 55
    assert intent.payload["dialogue_turn"]["event_id"] == "evt_memory_instruction"


def test_attention_target_and_idle_presence_rules_are_deterministic():
    clock = FixedClock(11_000)
    target = AttentionTarget(
        target_id="object:calibration_card",
        target_type="object",
        label="calibration_card",
        source="vision_worker",
        last_event_id="evt_object",
        last_seen_ts=11_000,
        confidence=0.8,
        priority=0.2,
        factors={"confidence": 0.8},
        weighted_components={"confidence": 0.08},
        payload={"object_id": "calibration_card"},
    )
    attention = AttentionState(
        state_id="attn_state_test",
        created_ts=11_000,
        active_target_id=target.target_id,
        active_target=target,
        candidates=[target],
        reason="initial_target",
    )
    executive = Executive(clock=clock)

    look_intent = executive.run_once(attention_state=attention, publish=False)
    idle_intent = executive.run_once(
        working_memory={"created_ts": 11_000, "recent_dialogue_turns": []},
        attention_state=None,
        safety_state=None,
        world_state={},
        publish=False,
    )

    assert look_intent.intent_type == ExecutiveIntentType.LOOK_AT_TARGET
    assert look_intent.target_id == "object:calibration_card"
    assert idle_intent.intent_type == ExecutiveIntentType.IDLE_PRESENCE


def test_listen_rule_and_intent_serialization_round_trip():
    clock = FixedClock(12_000)
    working = WorkingMemory(clock=clock)
    working.current_speaker = "user"
    executive = Executive(working_memory=working, clock=clock)

    intent = executive.run_once(publish=False)
    round_tripped = ExecutiveIntent.from_dict(intent.to_dict())

    assert intent.intent_type == ExecutiveIntentType.LISTEN
    assert round_tripped.to_dict() == intent.to_dict()


def test_executive_consumes_attention_update_and_working_memory_receives_intent():
    clock = FixedClock(13_000)
    bus = EventBus(clock=clock)
    working = WorkingMemory(clock=clock)
    working.attach_to_bus(bus)
    executive = Executive(working_memory=working, clock=clock, bus=bus)

    bus.publish(
        attention_update(
            source="attention_manager",
            focus_id="person:user",
            payload={
                "attention_state": {
                    "state_id": "attn_state_event",
                    "created_ts": 13_000,
                    "active_target_id": "person:user",
                    "active_target": None,
                    "candidates": [],
                    "locked_until_ts": None,
                    "dwell_remaining_ms": 0,
                    "reason": "initial_target",
                }
            },
            confidence=0.9,
            timestamp=13_000,
            event_id="evt_attention",
        )
    )

    assert executive.last_intent is not None
    assert executive.last_intent.intent_type == ExecutiveIntentType.LOOK_AT_TARGET
    assert working.pending_response_intent is not None
    assert working.pending_response_intent["payload"]["intent_type"] == "look_at_target"
