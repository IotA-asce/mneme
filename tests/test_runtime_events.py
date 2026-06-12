from __future__ import annotations

import pytest

from android_brain_memory.runtime import (
    EventBus,
    RuntimeEvent,
    RuntimeEventKind,
    RuntimeTopic,
    attention_update,
    executive_intent,
    memory_candidate_event,
    perception_observation,
    safety_event,
    skill_goal,
    skill_status,
    world_state_update,
)


def candidate_payload() -> dict:
    return {
        "candidate_id": "cand_runtime_001",
        "candidate_type": "perception_summary",
        "summary": "User waved near the robot head.",
        "source_type": "sensor_observed",
        "confidence": 0.8,
        "features": {
            "novelty": 0.5,
            "task_relevance": 0.6,
            "social_relevance": 0.8,
            "surprise": 0.3,
            "risk": 0.0,
            "contradiction": 0.0,
            "repetition_signal": 0.2,
            "explicit_remember_flag": 0.0,
        },
        "entities": ["user"],
        "tags": ["gesture"],
        "payload": {"gesture": "wave"},
    }


def test_event_publication_subscription_and_ordering():
    now = 1_000
    bus = EventBus(clock=lambda: now)
    received = []
    bus.subscribe(received.append)

    second = bus.publish(
        world_state_update(
            source="state_builder",
            state_key="active_speaker",
            payload={"person_id": "user"},
            confidence=0.9,
            timestamp=110,
        )
    )
    first = bus.publish(
        perception_observation(
            source="vision_worker",
            observation_type="face_seen",
            payload={"person_id": "user"},
            confidence=0.85,
            timestamp=100,
        )
    )

    assert [event.sequence for event in received] == [1, 2]
    assert [event.event_id for event in received] == [second.event_id, first.event_id]
    assert [event.event_id for event in bus.history()] == [second.event_id, first.event_id]
    assert first.topic == RuntimeTopic.PERCEPTION
    assert second.topic == RuntimeTopic.WORLD_STATE


def test_subscription_filters_by_kind_topic_and_source():
    bus = EventBus(clock=lambda: 1_000)
    attention_events = []
    safety_events = []
    vision_events = []

    bus.subscribe(attention_events.append, topics=[RuntimeTopic.ATTENTION])
    bus.subscribe(safety_events.append, kinds=[RuntimeEventKind.SAFETY_EVENT])
    bus.subscribe(vision_events.append, sources=["vision_worker"])

    perception = perception_observation(
        source="vision_worker",
        observation_type="object_seen",
        payload={"object_id": "calibration_card"},
        confidence=0.7,
        timestamp=100,
    )
    attention = attention_update(
        source="attention_manager",
        focus_id="user",
        payload={"reason": "active speaker"},
        confidence=0.9,
        timestamp=101,
    )
    safety = safety_event(
        source="safety_supervisor",
        safety_level="degraded",
        payload={"reason": "low confidence body state"},
        confidence=0.8,
        timestamp=102,
    )

    bus.publish(perception)
    bus.publish(attention)
    bus.publish(safety)

    assert [event.event_id for event in attention_events] == [attention.event_id]
    assert [event.event_id for event in safety_events] == [safety.event_id]
    assert [event.event_id for event in vision_events] == [perception.event_id]
    assert [event.kind for event in bus.history(sources=["vision_worker"])] == [
        RuntimeEventKind.PERCEPTION_OBSERVATION
    ]


def test_expired_events_are_not_delivered_and_can_be_pruned():
    bus = EventBus(clock=lambda: 1_000)
    received = []
    bus.subscribe(received.append)

    expired = bus.publish(
        perception_observation(
            source="touch_worker",
            observation_type="tap",
            payload={"zone": "left_cheek"},
            confidence=0.9,
            timestamp=900,
            ttl_ms=50,
        )
    )
    active = bus.publish(
        executive_intent(
            source="executive",
            intent_type="acknowledge_user",
            payload={"style": "brief"},
            confidence=0.8,
            timestamp=980,
            ttl_ms=100,
        )
    )

    assert [event.event_id for event in received] == [active.event_id]
    assert [event.event_id for event in bus.history(include_expired=False, now_ms=1_000)] == [
        active.event_id
    ]
    assert [event.event_id for event in bus.expire(now_ms=1_000)] == [expired.event_id]
    assert [event.event_id for event in bus.history()] == [active.event_id]


def test_all_required_runtime_event_types_are_json_friendly():
    events = [
        perception_observation(
            source="vision_worker",
            observation_type="face_seen",
            payload={"person_id": "user"},
            confidence=0.8,
            timestamp=100,
            event_id="evt_perception",
        ),
        world_state_update(
            source="state_builder",
            state_key="scene",
            payload={"description": "bench"},
            confidence=0.7,
            timestamp=101,
            event_id="evt_world",
        ),
        attention_update(
            source="attention_manager",
            focus_id="user",
            payload={"priority": 1},
            confidence=0.9,
            timestamp=102,
            event_id="evt_attention",
        ),
        memory_candidate_event(
            source="memory_gateway",
            candidate=candidate_payload(),
            timestamp=103,
            event_id="evt_memory",
        ),
        executive_intent(
            source="executive",
            intent_type="respond",
            payload={"response_policy": "concise"},
            confidence=0.8,
            timestamp=104,
            event_id="evt_intent",
        ),
        skill_goal(
            source="executive",
            skill_id="gaze",
            goal_type="look_at",
            payload={"target": "user"},
            confidence=0.9,
            timestamp=105,
            event_id="evt_skill_goal",
        ),
        skill_status(
            source="gaze_skill",
            skill_id="gaze",
            status="complete",
            payload={"target": "user"},
            confidence=0.9,
            timestamp=106,
            event_id="evt_skill_status",
        ),
        safety_event(
            source="safety_supervisor",
            safety_level="normal",
            payload={"mode": "bench"},
            confidence=None,
            timestamp=107,
            event_id="evt_safety",
        ),
    ]

    kinds = [event.kind for event in events]
    assert kinds == [
        RuntimeEventKind.PERCEPTION_OBSERVATION,
        RuntimeEventKind.WORLD_STATE_UPDATE,
        RuntimeEventKind.ATTENTION_UPDATE,
        RuntimeEventKind.MEMORY_CANDIDATE,
        RuntimeEventKind.EXECUTIVE_INTENT,
        RuntimeEventKind.SKILL_GOAL,
        RuntimeEventKind.SKILL_STATUS,
        RuntimeEventKind.SAFETY_EVENT,
    ]
    for event in events:
        round_tripped = RuntimeEvent.from_dict(event.to_dict())
        assert round_tripped.to_dict() == event.to_dict()


def test_event_validation_rejects_invalid_confidence_and_mismatched_topic():
    with pytest.raises(ValueError, match="confidence"):
        perception_observation(
            source="vision_worker",
            observation_type="face_seen",
            payload={},
            confidence=1.2,
            timestamp=100,
        )

    with pytest.raises(ValueError, match="topic"):
        RuntimeEvent(
            event_id="evt_bad_topic",
            kind=RuntimeEventKind.SAFETY_EVENT,
            topic=RuntimeTopic.PERCEPTION,
            timestamp=100,
            source="test",
            payload={},
        )
