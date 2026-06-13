from __future__ import annotations

import io
import json
from pathlib import Path
import sys
from typing import Sequence

from android_brain_memory import (
    CommandSpeechOutputBackend,
    MnemeRuntime,
    RuntimeClock,
    SimulatedSpeechOutputBackend,
    VirtualSkillGoal,
    VirtualSkillRunner,
    VirtualSkillStatus,
)
from android_brain_memory.runtime import EventBus, RuntimeEventKind, perception_observation
from android_brain_memory.virtual_head import main as mneme_main


MIGRATIONS = Path(__file__).resolve().parents[1] / "storage" / "migrations"


def test_command_speech_output_backend_substitutes_known_placeholders_only():
    calls: list[list[str]] = []

    def runner(command: Sequence[str], timeout_ms: int) -> str:
        calls.append(list(command))
        return "ok"

    backend = CommandSpeechOutputBackend(
        ["printf", '{"text":"{text}","literal":"{ignored}"}'],
        command_runner=runner,
    )

    output = backend.speak(
        text="hello Mneme",
        voice="soft",
        device_id="speaker-1",
        timestamp=1_000,
    )

    assert output.status == "spoken"
    assert calls == [["printf", '{"text":"hello Mneme","literal":"{ignored}"}']]


def test_virtual_skill_runner_emits_speech_statuses_and_records_output():
    clock = RuntimeClock(1_000)
    bus = EventBus(clock=clock)
    runner = VirtualSkillRunner(
        bus=bus,
        speech_backend=SimulatedSpeechOutputBackend(),
        clock=clock,
        speech_duration_ms=200,
    )
    goal = VirtualSkillGoal(
        goal_id="goal_speech",
        skill_id="virtual_speech",
        goal_type="speech",
        created_ts=1_000,
        payload={"text": "hello"},
    )

    runner.start_goal(goal, now_ms=1_000)
    assert runner.active is not None
    clock.set(1_200)
    runner.tick(now_ms=1_200)

    statuses = [
        event.payload["status"]
        for event in bus.history(kinds=[RuntimeEventKind.SKILL_STATUS])
    ]
    assert statuses == [
        VirtualSkillStatus.ACCEPTED.value,
        VirtualSkillStatus.RUNNING.value,
        VirtualSkillStatus.COMPLETED.value,
    ]
    assert runner.outputs[-1].text == "hello"


def test_virtual_gaze_goal_does_not_preempt_active_speech():
    clock = RuntimeClock(1_000)
    bus = EventBus(clock=clock)
    runner = VirtualSkillRunner(
        bus=bus,
        speech_backend=SimulatedSpeechOutputBackend(),
        clock=clock,
        speech_duration_ms=5_000,
    )
    speech = VirtualSkillGoal(
        goal_id="goal_speech",
        skill_id="virtual_speech",
        goal_type="speech",
        created_ts=1_000,
        payload={"text": "hello"},
    )
    gaze = VirtualSkillGoal(
        goal_id="goal_gaze",
        skill_id="virtual_gaze",
        goal_type="gaze_on_screen",
        created_ts=1_000,
        payload={"target_id": "person:user"},
    )

    runner.start_goal(speech, now_ms=1_000)
    runner.start_goal(gaze, now_ms=1_100)

    assert runner.active is not None
    assert runner.active.goal.goal_type == "speech"
    statuses = [
        (event.payload["goal_type"], event.payload["status"])
        for event in bus.history(kinds=[RuntimeEventKind.SKILL_STATUS])
    ]
    assert ("gaze_on_screen", VirtualSkillStatus.COMPLETED.value) in statuses
    assert ("speech", VirtualSkillStatus.PREEMPTED.value) not in statuses


def test_runtime_speaks_dialogue_plan_and_updates_avatar(tmp_path):
    runtime = MnemeRuntime(
        db_path=tmp_path / "memory.sqlite3",
        migrations_dir=MIGRATIONS,
        clock=RuntimeClock(1_000),
        virtual_speech_duration_ms=500,
    )
    try:
        runtime.start()
        first = runtime.process_user_utterance("hello Mneme", timestamp=1_000)

        assert first.utterances
        assert first.snapshot["presence"]["avatar"]["mode"] == "speaking"
        assert first.snapshot["presence"]["voice"] == "default"
        assert first.snapshot["presence"]["skills"]["active"]["goal"]["goal_type"] == "speech"

        done = runtime.tick(advance_ms=500)
        statuses = [
            event["payload"]["status"]
            for event in done.events
            if event["kind"] == "skill_status"
        ]
        assert VirtualSkillStatus.COMPLETED.value in statuses
        assert done.snapshot["presence"]["avatar"]["mode"] == "listening"
    finally:
        runtime.close()


def test_runtime_persists_speech_voice_in_procedural_memory(tmp_path):
    db_path = tmp_path / "memory.sqlite3"
    runtime = MnemeRuntime(
        db_path=db_path,
        migrations_dir=MIGRATIONS,
        clock=RuntimeClock(1_000),
        speech_voice="soft",
    )
    try:
        runtime.start()
        result = runtime.process_user_utterance("hello Mneme", timestamp=1_000)
        outputs = result.snapshot["presence"]["skills"]["outputs"]
        assert outputs[-1]["voice"] == "soft"
    finally:
        runtime.close()

    restored = MnemeRuntime(
        db_path=db_path,
        migrations_dir=MIGRATIONS,
        clock=RuntimeClock(2_000),
    )
    try:
        restored.start()
        assert restored.snapshot()["presence"]["voice"] == "soft"
    finally:
        restored.close()


def test_runtime_barge_in_preempts_active_speech(tmp_path):
    runtime = MnemeRuntime(
        db_path=tmp_path / "memory.sqlite3",
        migrations_dir=MIGRATIONS,
        clock=RuntimeClock(1_000),
        virtual_speech_duration_ms=5_000,
    )
    try:
        runtime.start()
        runtime.process_user_utterance("hello Mneme", timestamp=1_000)
        result = runtime.process_user_utterance("wait, one more thing", timestamp=1_500)

        status_events = [
            event for event in result.events
            if event["kind"] == "skill_status"
        ]
        assert any(event["payload"]["status"] == "preempted" for event in status_events)
        assert result.snapshot["presence"]["coordinator"]["barge_ins"] == 1
    finally:
        runtime.close()


def test_virtual_avatar_tracks_attention_and_safety(tmp_path):
    runtime = MnemeRuntime(
        db_path=tmp_path / "memory.sqlite3",
        migrations_dir=MIGRATIONS,
        clock=RuntimeClock(1_000),
    )
    try:
        runtime.start()
        runtime.bus.publish(
            perception_observation(
                source="test",
                observation_type="person_seen",
                payload={"person_id": "alice", "label": "Alice"},
                confidence=0.9,
                timestamp=1_000,
            )
        )

        avatar = runtime.snapshot()["presence"]["avatar"]
        assert avatar["gaze_target"] == "person:alice"
        assert avatar["expression"] == "attentive"
    finally:
        runtime.close()


def test_mneme_run_tts_command_json_output(tmp_path, capsys):
    exit_code = mneme_main([
        "--db",
        str(tmp_path / "memory.sqlite3"),
        "--migrations",
        str(MIGRATIONS),
        "run",
        "--json",
        "--tts-command",
        "printf {text}",
        "--voice",
        "soft",
        "--input",
        "hello Mneme",
    ])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    turn = next(item for item in output if item["type"] == "turn")
    outputs = turn["result"]["snapshot"]["presence"]["skills"]["outputs"]
    assert outputs
    assert outputs[-1]["status"] == "spoken"
    assert outputs[-1]["voice"] == "soft"


def test_mneme_run_interactive_prints_typed_response(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO("hello Mneme\n/quit\n"))

    exit_code = mneme_main([
        "--db",
        str(tmp_path / "memory.sqlite3"),
        "--migrations",
        str(MIGRATIONS),
        "run",
    ])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "mneme:" in captured.out
    assert "state:" not in captured.out
    assert "typed terminal input" in captured.err


def test_mneme_run_live_ticks_speech_without_stdin(tmp_path, capsys):
    exit_code = mneme_main([
        "--db",
        str(tmp_path / "memory.sqlite3"),
        "--migrations",
        str(MIGRATIONS),
        "run",
        "--json",
        "--live-ticks",
        "1",
        "--speech-command",
        "printf hello",
    ])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    live_tick = next(item for item in output if item["type"] == "live_tick")
    assert live_tick["result"]["utterances"]
    assert live_tick["result"]["snapshot"]["speech_loop"]["counters"]["transcripts"] == 1
