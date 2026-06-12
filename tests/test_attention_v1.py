from __future__ import annotations

from android_brain_memory import AttentionManager
from android_brain_memory.runtime import perception_observation, safety_event


class FixedClock:
    def __init__(self, now_ms: int) -> None:
        self.now_ms = now_ms

    def __call__(self) -> int:
        return self.now_ms


def face_event(person_id: str, timestamp: int, event_id: str):
    return perception_observation(
        source="vision_worker",
        observation_type="person_seen",
        payload={"person_id": person_id, "label": person_id},
        confidence=0.9,
        timestamp=timestamp,
        event_id=event_id,
    )


def speech(speaker: str, text: str, timestamp: int, event_id: str):
    return perception_observation(
        source="speech_worker",
        observation_type="speech_transcript",
        payload={"speaker": speaker, "transcript": text},
        confidence=0.9,
        timestamp=timestamp,
        event_id=event_id,
    )


def test_habituation_decays_novelty_over_repeated_sightings():
    clock = FixedClock(1_000)
    manager = AttentionManager(clock=clock, target_ttl_ms=60_000)

    novelties = []
    for index in range(4):
        clock.now_ms = 1_000 + index * 100
        manager.process_event(face_event("user", clock.now_ms, f"evt_{index}"))
        target = manager.targets(now_ms=clock.now_ms)[0]
        novelties.append(target.factors["novelty"])

    assert novelties[0] == 1.0
    assert novelties == sorted(novelties, reverse=True)
    assert novelties[1] == 0.5
    assert novelties[2] == 0.25
    assert novelties[3] < novelties[2]


def test_inhibition_of_return_penalizes_recently_dropped_target():
    clock = FixedClock(1_000)
    manager = AttentionManager(
        clock=clock,
        dwell_ms=1,
        switch_margin=0.0,
        target_ttl_ms=60_000,
        ior_ms=2_000,
        ior_penalty=0.15,
    )

    manager.process_event(face_event("alpha", 1_000, "evt_a1"))
    assert manager.state(now_ms=1_000).active_target_id == "person:alpha"

    # a speaker outranks a silent face -> focus switches, alpha becomes inhibited
    clock.now_ms = 1_100
    manager.process_event(speech("bravo", "hello", 1_100, "evt_b1"))
    assert manager.state(now_ms=1_100).active_target_id == "person:bravo"

    clock.now_ms = 1_200
    manager.process_event(face_event("alpha", 1_200, "evt_a2"))
    inhibited = next(
        target
        for target in manager.targets(now_ms=1_200)
        if target.target_id == "person:alpha"
    )
    assert inhibited.factors.get("inhibition_of_return") == 1.0

    # outside the inhibition window the penalty disappears
    clock.now_ms = 4_000
    manager.process_event(face_event("alpha", 4_000, "evt_a3"))
    recovered = next(
        target
        for target in manager.targets(now_ms=4_000)
        if target.target_id == "person:alpha"
    )
    assert "inhibition_of_return" not in recovered.factors or recovered.factors["inhibition_of_return"] == 0.0
    assert recovered.priority > inhibited.priority


def test_inhibition_never_blocks_safety_override():
    clock = FixedClock(1_000)
    manager = AttentionManager(clock=clock, dwell_ms=1, switch_margin=0.0, ior_ms=10_000)

    manager.process_event(
        safety_event(
            source="safety_supervisor",
            safety_level="degraded",
            payload={},
            confidence=0.9,
            timestamp=1_000,
            event_id="evt_safe1",
        )
    )
    clock.now_ms = 1_100
    manager.process_event(speech("user", "hello", 1_100, "evt_u1"))
    clock.now_ms = 1_200
    state = manager.process_event(
        safety_event(
            source="safety_supervisor",
            safety_level="emergency",
            payload={},
            confidence=1.0,
            timestamp=1_200,
            event_id="evt_safe2",
        )
    )

    assert state.active_target_id == "safety:emergency"


def test_curiosity_rotates_targets_when_idle_and_yields_to_real_targets():
    clock = FixedClock(1_000)
    manager = AttentionManager(clock=clock, enable_curiosity=True, target_ttl_ms=500)

    first = manager.idle_tick(now_ms=1_000)
    second = manager.idle_tick(now_ms=1_100)
    third = manager.idle_tick(now_ms=1_200)
    fourth = manager.idle_tick(now_ms=1_300)

    assert first.reason == "curiosity_idle"
    assert first.active_target.target_type == "curiosity"
    labels = [
        state.active_target.label for state in (first, second, third, fourth)
    ]
    assert labels == ["scan_left", "scan_center", "scan_right", "scan_left"]

    clock.now_ms = 1_400
    state = manager.process_event(speech("user", "hello", 1_400, "evt_real"))
    assert state.active_target_id == "person:user"


def test_curiosity_disabled_by_default_preserves_no_target():
    clock = FixedClock(1_000)
    manager = AttentionManager(clock=clock)

    state = manager.idle_tick(now_ms=1_000)

    assert state.active_target_id is None
    assert state.reason == "no_target"


def test_state_history_records_transitions_and_is_bounded():
    clock = FixedClock(1_000)
    manager = AttentionManager(clock=clock, max_history=3)

    manager.process_event(speech("user", "hello", 1_000, "evt_1"))
    clock.now_ms = 1_100
    manager.process_event(speech("user", "again", 1_100, "evt_2"))
    clock.now_ms = 1_200
    manager.process_event(speech("user", "more", 1_200, "evt_3"))
    clock.now_ms = 1_300
    manager.process_event(speech("user", "final", 1_300, "evt_4"))

    history = manager.state_history
    assert len(history) == 3  # bounded
    assert history[0]["active_target_id"] == "person:user"
    assert all(
        set(entry) == {"state_id", "created_ts", "active_target_id", "reason"}
        for entry in history
    )
    assert [entry["created_ts"] for entry in history] == sorted(
        entry["created_ts"] for entry in history
    )
