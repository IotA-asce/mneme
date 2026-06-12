from __future__ import annotations

from android_brain_memory import (
    AttentionManager,
    AttentionState,
    AttentionTarget,
    EventBus,
    WorkingMemory,
    perception_observation,
    safety_event,
)
from android_brain_memory.runtime import RuntimeEventKind


class FixedClock:
    def __init__(self, now_ms: int) -> None:
        self.now_ms = now_ms

    def __call__(self) -> int:
        return self.now_ms


def test_active_speaker_wins_over_idle_object_and_updates_working_memory():
    clock = FixedClock(1_000)
    bus = EventBus(clock=clock)
    working = WorkingMemory(clock=clock)
    manager = AttentionManager(clock=clock, bus=bus)
    working.attach_to_bus(bus)

    bus.publish(
        perception_observation(
            source="vision_worker",
            observation_type="object_seen",
            payload={"object_id": "calibration_card"},
            confidence=0.8,
            timestamp=1_000,
            event_id="evt_object",
        )
    )
    clock.now_ms = 1_100
    state = bus.publish(
        perception_observation(
            source="speech_worker",
            observation_type="speech_transcript",
            payload={"speaker": "user", "transcript": "hello"},
            confidence=0.9,
            timestamp=1_100,
            event_id="evt_speech",
        )
    )

    attention_state = manager.state(now_ms=1_100)
    assert state.kind == RuntimeEventKind.PERCEPTION_OBSERVATION
    assert attention_state.active_target_id == "person:user"
    assert attention_state.active_target is not None
    assert attention_state.active_target.factors["active_speaker"] == 1.0
    assert working.attention_target == "person:user"


def test_safety_event_wins_over_normal_social_focus():
    clock = FixedClock(2_000)
    bus = EventBus(clock=clock)
    manager = AttentionManager(clock=clock, bus=bus)

    bus.publish(
        perception_observation(
            source="speech_worker",
            observation_type="speech_transcript",
            payload={"speaker": "user", "transcript": "Mneme, look here"},
            confidence=0.95,
            timestamp=2_000,
            event_id="evt_social",
        )
    )
    clock.now_ms = 2_100
    manager.process_event(
        safety_event(
            source="safety_supervisor",
            safety_level="degraded",
            payload={"reason": "body health uncertainty"},
            confidence=0.9,
            timestamp=2_100,
            event_id="evt_safety",
        )
    )

    state = manager.state(now_ms=2_100)
    assert state.active_target_id == "safety:degraded"
    assert state.reason == "current_state"
    assert state.active_target is not None
    assert state.active_target.factors["safety_relevance"] == 0.9


def test_target_lock_prevents_rapid_flicker_between_targets():
    clock = FixedClock(3_000)
    manager = AttentionManager(clock=clock, dwell_ms=1_000, switch_margin=0.0)

    first_state = manager.process_event(
        perception_observation(
            source="speech_worker",
            observation_type="speech_transcript",
            payload={"speaker": "user", "transcript": "Mneme, start"},
            confidence=0.9,
            timestamp=3_000,
            event_id="evt_user",
        )
    )
    clock.now_ms = 3_100
    second_state = manager.process_event(
        perception_observation(
            source="speech_worker",
            observation_type="speech_transcript",
            payload={"speaker": "guest", "transcript": "Mneme, over here"},
            confidence=0.9,
            timestamp=3_100,
            event_id="evt_guest",
        )
    )

    assert first_state.active_target_id == "person:user"
    assert second_state.active_target_id == "person:user"
    assert second_state.reason == "dwell_lock_active"
    assert second_state.dwell_remaining_ms == 900


def test_expired_target_is_released():
    clock = FixedClock(4_000)
    manager = AttentionManager(clock=clock, target_ttl_ms=100)

    manager.process_event(
        perception_observation(
            source="speech_worker",
            observation_type="speech_transcript",
            payload={"speaker": "user", "transcript": "hello"},
            confidence=0.9,
            timestamp=4_000,
            ttl_ms=100,
            event_id="evt_short",
        )
    )
    clock.now_ms = 4_101
    expired = manager.expire()
    state = manager.state(now_ms=4_101)

    assert [target.target_id for target in expired] == ["person:user"]
    assert state.active_target_id is None
    assert state.active_target is None
    assert state.candidates == []


def test_attention_state_serializes_cleanly():
    target = AttentionTarget(
        target_id="person:user",
        target_type="person",
        label="user",
        source="speech_worker",
        last_event_id="evt_speech",
        last_seen_ts=5_000,
        confidence=0.9,
        priority=0.63,
        factors={"active_speaker": 1.0, "confidence": 0.9},
        weighted_components={"active_speaker": 0.26, "confidence": 0.09},
        payload={"speaker": "user"},
        ttl_ms=3_000,
    )
    state = AttentionState(
        state_id="attn_state_test",
        created_ts=5_000,
        active_target_id="person:user",
        active_target=target,
        candidates=[target],
        locked_until_ts=5_500,
        dwell_remaining_ms=500,
        reason="initial_target",
    )

    round_tripped = AttentionState.from_dict(state.to_dict())

    assert round_tripped.to_dict() == state.to_dict()
