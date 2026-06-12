from __future__ import annotations

import json
from pathlib import Path

from android_brain_memory import ScenarioReplayRunner
from android_brain_memory.runtime import (
    EventBus,
    RuntimeEventKind,
    RuntimeTopic,
    perception_observation,
    safety_event,
)
from android_brain_memory.world_model import WorldModel, WorldModelSnapshot


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "basic_conversation.yaml"


class FixedClock:
    def __init__(self, now_ms: int) -> None:
        self.now_ms = now_ms

    def __call__(self) -> int:
        return self.now_ms


def make_world(clock: FixedClock, bus: EventBus | None = None) -> WorldModel:
    world = WorldModel(clock=clock, person_ttl_ms=10_000, speaker_ttl_ms=6_000, sound_ttl_ms=3_000)
    if bus is not None:
        world.attach_to_bus(bus)
    return world


def face_event(person_id: str, timestamp: int, label: str | None = None):
    return perception_observation(
        source="face_worker",
        observation_type="person_seen",
        payload={"person_id": person_id, "label": label or person_id},
        confidence=0.9,
        timestamp=timestamp,
    )


def speech_event(speaker: str, text: str, timestamp: int):
    return perception_observation(
        source="speech_worker",
        observation_type="speech_transcript",
        payload={"speaker": speaker, "transcript": text, "topic": "test"},
        confidence=0.95,
        timestamp=timestamp,
    )


def test_person_seen_creates_presence_and_expires_after_ttl():
    clock = FixedClock(1_000)
    world = make_world(clock)

    world.process_event(face_event("user", 1_000, label="User"))

    snapshot = world.snapshot()
    assert [person.person_id for person in snapshot.persons] == ["user"]
    assert snapshot.persons[0].label == "User"

    clock.now_ms = 12_000  # > 10s person TTL
    assert world.snapshot().persons == []


def test_speech_sets_active_speaker_and_refreshes_person():
    clock = FixedClock(1_000)
    world = make_world(clock)

    world.process_event(speech_event("user", "hello Mneme", 1_000))

    snapshot = world.snapshot()
    assert snapshot.active_speaker == "user"
    assert snapshot.last_speech is not None
    assert snapshot.last_speech.transcript == "hello Mneme"
    assert [person.person_id for person in snapshot.persons] == ["user"]

    clock.now_ms = 8_000  # > 6s speaker TTL, < 10s person TTL
    snapshot = world.snapshot()
    assert snapshot.active_speaker is None
    assert [person.person_id for person in snapshot.persons] == ["user"]


def test_sound_touch_and_internal_state_updates():
    clock = FixedClock(1_000)
    world = make_world(clock)

    world.process_event(
        perception_observation(
            source="sound_worker",
            observation_type="sound_direction",
            payload={"direction_deg": 15, "source_label": "user"},
            confidence=0.8,
            timestamp=1_000,
        )
    )
    world.process_event(
        perception_observation(
            source="touch_worker",
            observation_type="touch",
            payload={"zone": "left_cheek", "gesture": "tap"},
            confidence=0.88,
            timestamp=1_010,
        )
    )
    world.process_event(
        perception_observation(
            source="health_worker",
            observation_type="body_health",
            payload={"status": "nominal", "battery_pct": 87, "safety_level": "normal"},
            confidence=0.99,
            timestamp=1_020,
        )
    )

    snapshot = world.snapshot()
    assert snapshot.ambient_sound.direction_deg == 15.0
    assert snapshot.ambient_sound.source_label == "user"
    assert snapshot.last_touch.zone == "left_cheek"
    assert snapshot.internal.status == "nominal"
    assert snapshot.internal.battery_pct == 87.0
    assert snapshot.safety_level == "normal"

    clock.now_ms = 5_000  # > 3s sound TTL
    assert world.snapshot().ambient_sound is None


def test_safety_event_updates_safety_level():
    clock = FixedClock(1_000)
    world = make_world(clock)

    world.process_event(
        safety_event(
            source="safety_supervisor",
            safety_level="emergency",
            payload={},
            confidence=1.0,
            timestamp=1_000,
        )
    )

    assert world.snapshot().safety_level == "emergency"


def test_world_state_updates_are_published_per_state_change():
    clock = FixedClock(1_000)
    bus = EventBus(clock=clock)
    make_world(clock, bus=bus)

    bus.publish(face_event("user", 1_000))
    bus.publish(speech_event("user", "hello", 1_010))

    updates = bus.history(kinds=[RuntimeEventKind.WORLD_STATE_UPDATE])
    state_keys = [event.payload["state_key"] for event in updates]
    assert "persons" in state_keys
    assert "active_speaker" in state_keys
    assert all(event.topic == RuntimeTopic.WORLD_STATE for event in updates)
    speaker_update = next(
        event for event in updates if event.payload["state_key"] == "active_speaker"
    )
    assert speaker_update.payload["value"] == "user"


def test_snapshot_is_json_friendly_and_deterministic():
    clock = FixedClock(1_000)
    world = make_world(clock)
    world.process_event(face_event("user", 1_000, label="User"))
    world.process_event(speech_event("user", "hello", 1_010))

    first = world.snapshot(snapshot_id="snap_1").to_dict()
    second = world.snapshot(snapshot_id="snap_1").to_dict()

    assert first == second
    assert isinstance(WorldModelSnapshot.from_dict(json.loads(json.dumps(first))), WorldModelSnapshot)


def test_replay_fixture_builds_expected_world_state():
    clock = FixedClock(1_000)
    bus = EventBus(clock=clock)
    world = make_world(clock, bus=bus)

    ScenarioReplayRunner(bus).replay_file(FIXTURE)

    snapshot = world.snapshot()
    person_ids = [person.person_id for person in snapshot.persons]
    assert "user" in person_ids
    assert "mneme" in person_ids  # speech refreshes presence for the robot speaker too
    assert snapshot.active_speaker == "mneme"  # last speech in the fixture
    assert snapshot.internal is not None
    assert snapshot.internal.status == "nominal"
    assert snapshot.safety_level == "normal"
