from __future__ import annotations

from pathlib import Path

from android_brain_memory import MnemeMemory, ScenarioReplayRunner, WorkingMemory
from android_brain_memory.context_windows import ContextWindow, ContextWindowManager
from android_brain_memory.runtime import (
    EventBus,
    RuntimeEventKind,
    perception_observation,
)


MIGRATIONS = Path(__file__).resolve().parents[1] / "storage" / "migrations"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "basic_conversation.yaml"


class FixedClock:
    def __init__(self, now_ms: int) -> None:
        self.now_ms = now_ms

    def __call__(self) -> int:
        return self.now_ms


def speech_event(speaker: str, text: str, timestamp: int):
    return perception_observation(
        source="speech_worker",
        observation_type="speech_transcript",
        payload={"speaker": speaker, "transcript": text},
        confidence=0.95,
        timestamp=timestamp,
    )


def health_event(timestamp: int):
    return perception_observation(
        source="health_worker",
        observation_type="body_health",
        payload={"status": "nominal"},
        confidence=0.99,
        timestamp=timestamp,
    )


def build_stack(tmp_path, clock):
    engine = MnemeMemory(tmp_path / "memory.sqlite3", migrations_dir=MIGRATIONS)
    engine.init_db()
    bus = EventBus(clock=clock)
    working = WorkingMemory(clock=clock)
    working.attach_to_bus(bus)
    manager = ContextWindowManager(
        working,
        store=engine.store,
        bus=bus,
        idle_timeout_ms=8_000,
        clock=clock,
    )
    manager.attach_to_bus(bus)
    return engine, bus, working, manager


def test_speech_opens_window_and_activity_extends_it(tmp_path):
    clock = FixedClock(1_000)
    engine, bus, _, manager = build_stack(tmp_path, clock)

    bus.publish(speech_event("user", "hello", 1_000))
    assert manager.current_window is not None
    assert manager.current_window.trigger == "speech_transcript"
    first_window_id = manager.current_window.window_id

    clock.now_ms = 7_000
    bus.publish(speech_event("user", "still here", 7_000))
    clock.now_ms = 14_000  # 7s after last activity, < 8s idle timeout
    manager.tick()
    assert manager.current_window is not None
    assert manager.current_window.window_id == first_window_id
    assert manager.current_window.event_count == 2
    engine.close()


def test_idle_timeout_closes_window_and_persists_snapshot(tmp_path):
    clock = FixedClock(1_000)
    engine, bus, _, manager = build_stack(tmp_path, clock)

    bus.publish(speech_event("user", "hello", 1_000))
    clock.now_ms = 10_000  # 9s idle > 8s timeout
    closed = manager.tick()

    assert isinstance(closed, ContextWindow)
    assert closed.closed_ts == 10_000
    assert closed.close_reason == "idle_timeout"
    assert closed.snapshot_id is not None
    assert manager.current_window is None
    assert manager.history[-1].window_id == closed.window_id

    snapshots = engine.store.get_recent_working_context_snapshots(limit=5)
    assert [snapshot.snapshot_id for snapshot in snapshots] == [closed.snapshot_id]
    assert snapshots[0].context["current_speaker"] == "user"
    engine.close()


def test_new_interaction_after_close_opens_new_window(tmp_path):
    clock = FixedClock(1_000)
    engine, bus, _, manager = build_stack(tmp_path, clock)

    bus.publish(speech_event("user", "hello", 1_000))
    first_id = manager.current_window.window_id
    clock.now_ms = 10_000
    manager.tick()

    clock.now_ms = 11_000
    bus.publish(speech_event("user", "back again", 11_000))
    assert manager.current_window is not None
    assert manager.current_window.window_id != first_id
    engine.close()


def test_window_transitions_publish_world_state_updates(tmp_path):
    clock = FixedClock(1_000)
    engine, bus, _, manager = build_stack(tmp_path, clock)

    bus.publish(speech_event("user", "hello", 1_000))
    clock.now_ms = 10_000
    manager.tick()

    updates = [
        event
        for event in bus.history(kinds=[RuntimeEventKind.WORLD_STATE_UPDATE])
        if event.payload.get("state_key") == "context_window"
    ]
    statuses = [event.payload["status"] for event in updates]
    assert statuses == ["opened", "closed"]
    assert updates[1].payload["snapshot_id"] is not None
    engine.close()


def test_non_interaction_events_do_not_open_windows(tmp_path):
    clock = FixedClock(1_000)
    engine, bus, _, manager = build_stack(tmp_path, clock)

    bus.publish(health_event(1_000))

    assert manager.current_window is None
    engine.close()


def test_manual_close_records_reason(tmp_path):
    clock = FixedClock(1_000)
    engine, bus, _, manager = build_stack(tmp_path, clock)

    bus.publish(speech_event("user", "hello", 1_000))
    closed = manager.close_now(reason="safety_freeze")

    assert closed is not None
    assert closed.close_reason == "safety_freeze"
    assert manager.current_window is None
    engine.close()


def test_replay_conversation_produces_window_and_snapshot(tmp_path):
    clock = FixedClock(1_000)
    engine, bus, _, manager = build_stack(tmp_path, clock)

    ScenarioReplayRunner(bus).replay_file(FIXTURE)
    assert manager.current_window is not None

    clock.now_ms = max(event.timestamp for event in bus.history()) + 9_000
    closed = manager.tick()

    assert closed is not None
    assert closed.event_count >= 3  # face, two speech turns, touch
    snapshots = engine.store.get_recent_working_context_snapshots(limit=5)
    assert len(snapshots) == 1
    context = snapshots[0].context
    assert context["current_speaker"] == "mneme"
    assert len(context["recent_dialogue_turns"]) == 2
    engine.close()
