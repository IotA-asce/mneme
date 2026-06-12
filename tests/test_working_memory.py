from __future__ import annotations

from pathlib import Path

from android_brain_memory import (
    EventBus,
    SensoryEchoBuffer,
    WorkingMemory,
    attention_update,
    executive_intent,
    perception_observation,
    safety_event,
    skill_goal,
    skill_status,
    world_state_update,
)
from android_brain_memory.runtime import RuntimeEventKind
from android_brain_memory.storage import MemoryStore


MIGRATIONS = Path(__file__).resolve().parents[1] / "storage" / "migrations"


class FixedClock:
    def __init__(self, now_ms: int) -> None:
        self.now_ms = now_ms

    def __call__(self) -> int:
        return self.now_ms


def test_sensory_echo_buffer_expires_fragments_and_respects_capacity():
    clock = FixedClock(1_000)
    echo = SensoryEchoBuffer(capacity=2, default_ttl_ms=100, clock=clock)

    old_event = perception_observation(
        source="vision_worker",
        observation_type="face_seen",
        payload={"person_id": "user"},
        confidence=0.8,
        timestamp=800,
    )
    assert echo.add_event(old_event) is None

    first = echo.add_event(
        perception_observation(
            source="vision_worker",
            observation_type="face_seen",
            payload={"person_id": "user"},
            confidence=0.8,
            timestamp=950,
            event_id="evt_001",
        )
    )
    second = echo.add_event(
        perception_observation(
            source="touch_worker",
            observation_type="tap",
            payload={"zone": "left_cheek"},
            confidence=0.9,
            timestamp=960,
            event_id="evt_002",
        )
    )
    third = echo.add_event(
        perception_observation(
            source="audio_worker",
            observation_type="speech",
            payload={"speaker": "user"},
            confidence=0.7,
            timestamp=970,
            event_id="evt_003",
        )
    )

    assert first is not None
    assert second is not None
    assert third is not None
    assert [fragment.event_id for fragment in echo.fragments()] == ["evt_002", "evt_003"]

    clock.now_ms = 1_071
    expired = echo.expire()
    assert [fragment.event_id for fragment in expired] == ["evt_002", "evt_003"]
    assert echo.fragments() == []


def test_sensory_echo_buffer_subscribes_to_event_bus_with_filters():
    clock = FixedClock(1_000)
    bus = EventBus(clock=clock)
    echo = SensoryEchoBuffer(capacity=5, default_ttl_ms=500, clock=clock)
    echo.attach_to_bus(bus, sources=["vision_worker"])

    bus.publish(
        perception_observation(
            source="vision_worker",
            observation_type="object_seen",
            payload={"object_id": "calibration_card"},
            confidence=0.7,
            timestamp=1_000,
            event_id="evt_visible",
        )
    )
    bus.publish(
        perception_observation(
            source="audio_worker",
            observation_type="speech",
            payload={"speaker": "user"},
            confidence=0.8,
            timestamp=1_001,
            event_id="evt_filtered",
        )
    )

    assert [fragment.event_id for fragment in echo.fragments()] == ["evt_visible"]
    assert echo.fragments(kinds=[RuntimeEventKind.PERCEPTION_OBSERVATION])[0].source == "vision_worker"


def test_working_memory_updates_from_runtime_events_and_stays_bounded():
    clock = FixedClock(2_000)
    bus = EventBus(clock=clock)
    memory = WorkingMemory(max_dialogue_turns=2, max_event_refs=3, clock=clock)
    memory.attach_to_bus(bus)

    bus.publish(
        perception_observation(
            source="speech_worker",
            observation_type="utterance",
            payload={"speaker": "user", "utterance": "hello mneme", "topic": "calibration"},
            confidence=0.95,
            timestamp=2_000,
            event_id="evt_dialogue_001",
        )
    )
    bus.publish(
        perception_observation(
            source="speech_worker",
            observation_type="utterance",
            payload={"speaker": "mneme", "utterance": "ready"},
            confidence=0.9,
            timestamp=2_001,
            event_id="evt_dialogue_002",
        )
    )
    bus.publish(
        perception_observation(
            source="speech_worker",
            observation_type="utterance",
            payload={"speaker": "user", "utterance": "start routine"},
            confidence=0.9,
            timestamp=2_002,
            event_id="evt_dialogue_003",
        )
    )
    bus.publish(
        attention_update(
            source="attention_manager",
            focus_id="user",
            payload={"reason": "active speaker"},
            confidence=0.9,
            timestamp=2_003,
            event_id="evt_attention",
        )
    )
    bus.publish(
        executive_intent(
            source="executive",
            intent_type="respond",
            payload={"active_goal": "guide_calibration", "response_style": "brief"},
            confidence=0.8,
            timestamp=2_004,
            event_id="evt_intent",
        )
    )
    bus.publish(
        safety_event(
            source="safety_supervisor",
            safety_level="normal",
            payload={"mode": "bench"},
            confidence=None,
            timestamp=2_005,
            event_id="evt_safety",
        )
    )

    snapshot = memory.snapshot(snapshot_id="ctx_test", created_ts=2_010).to_dict()

    assert snapshot["current_speaker"] == "user"
    assert snapshot["topic"] == "calibration"
    assert snapshot["attention_target"] == "user"
    assert [turn["event_id"] for turn in snapshot["recent_dialogue_turns"]] == [
        "evt_dialogue_002",
        "evt_dialogue_003",
    ]
    assert snapshot["active_goal"]["goal"] == "guide_calibration"
    assert snapshot["pending_response_intent"]["payload"]["intent_type"] == "respond"
    assert snapshot["safety_state"]["payload"]["safety_level"] == "normal"
    assert [event_ref["event_id"] for event_ref in snapshot["recent_event_refs"]] == [
        "evt_attention",
        "evt_intent",
        "evt_safety",
    ]


def test_working_memory_records_world_state_and_skill_goal_status():
    clock = FixedClock(3_000)
    bus = EventBus(clock=clock)
    memory = WorkingMemory(max_dialogue_turns=4, max_event_refs=8, clock=clock)
    memory.attach_to_bus(bus)

    bus.publish(
        world_state_update(
            source="state_builder",
            state_key="active_speaker",
            payload={"person_id": "user"},
            confidence=0.9,
            timestamp=3_000,
        )
    )
    bus.publish(
        world_state_update(
            source="state_builder",
            state_key="topic",
            payload={"value": "memory demo"},
            confidence=0.8,
            timestamp=3_001,
        )
    )
    bus.publish(
        skill_goal(
            source="executive",
            skill_id="gaze",
            goal_type="look_at",
            payload={"target": "user"},
            confidence=0.9,
            timestamp=3_002,
        )
    )
    bus.publish(
        skill_status(
            source="gaze_skill",
            skill_id="gaze",
            status="complete",
            payload={"target": "user"},
            confidence=0.9,
            timestamp=3_003,
        )
    )

    snapshot = memory.to_dict(created_ts=3_010)
    assert snapshot["current_speaker"] == "user"
    assert snapshot["topic"] == "memory demo"
    assert snapshot["active_goal"]["payload"]["goal_type"] == "look_at"
    assert snapshot["active_goal"]["last_skill_status"]["payload"]["status"] == "complete"


def test_working_memory_snapshot_persists_to_storage(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    store.run_migrations(MIGRATIONS)
    memory = WorkingMemory(clock=lambda: 4_000)
    memory.add_dialogue_turn(speaker="user", text="remember this", timestamp=3_990)
    memory.topic = "persistence"
    memory.attention_target = "user"

    stored = memory.persist_snapshot(
        store,
        snapshot_id="ctx_persisted",
        created_ts=4_000,
    )
    recent = store.get_recent_working_context_snapshots(limit=1)

    assert stored.snapshot_id == "ctx_persisted"
    assert stored.created_ts == 4_000
    assert recent[0].snapshot_id == "ctx_persisted"
    assert recent[0].context["topic"] == "persistence"
    assert recent[0].context["attention_target"] == "user"
    assert recent[0].context["recent_dialogue_turns"][0]["text"] == "remember this"
    store.close()
