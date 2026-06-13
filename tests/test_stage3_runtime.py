from __future__ import annotations

import json
from pathlib import Path

from android_brain_memory import (
    FakePeripheralBackend,
    FakeModelRuntime,
    ModelDialogueRealizer,
    ModelResponse,
    MnemeRuntime,
    PeripheralDevice,
    PeripheralDiscoveryService,
    PeripheralKind,
    RuntimeClock,
)
from android_brain_memory.runtime import RuntimeEventKind
from android_brain_memory.virtual_head import main as mneme_main


MIGRATIONS = Path(__file__).resolve().parents[1] / "storage" / "migrations"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "basic_conversation.yaml"


def make_runtime(tmp_path, *, devices=None) -> MnemeRuntime:
    return MnemeRuntime(
        db_path=tmp_path / "memory.sqlite3",
        migrations_dir=MIGRATIONS,
        clock=RuntimeClock(1_000),
        fake_devices=devices,
    )


def test_runtime_starts_with_fake_peripherals_and_publishes_inventory(tmp_path):
    runtime = make_runtime(tmp_path)
    try:
        snapshot = runtime.start()
        counts = snapshot.to_dict()["available_counts"]

        assert counts == {"camera": 1, "microphone": 1, "speaker": 1}
        updates = runtime.bus.history(kinds=[RuntimeEventKind.WORLD_STATE_UPDATE])
        assert updates[-1].payload["state_key"] == "peripheral_inventory"
        assert runtime.snapshot()["devices"]["available_counts"]["camera"] == 1
    finally:
        runtime.close()


def test_fake_peripheral_discovery_handles_appearance_removal_and_absence():
    clock = RuntimeClock(1_000)
    backend = FakePeripheralBackend([])
    service = PeripheralDiscoveryService(backend=backend, clock=clock, scan_interval_ms=100)

    absent = service.scan_now(now_ms=1_000, publish=False)
    assert absent.to_dict()["available_counts"] == {"camera": 0, "microphone": 0, "speaker": 0}

    backend.set_devices([
        PeripheralDevice(device_id="cam", kind=PeripheralKind.CAMERA, label="Camera")
    ])
    clock.set(1_100)
    appeared = service.tick(now_ms=1_100)
    assert appeared is not None
    assert appeared.to_dict()["available_counts"]["camera"] == 1

    backend.set_devices([])
    clock.set(1_200)
    removed = service.tick(now_ms=1_200)
    assert removed is not None
    assert removed.to_dict()["available_counts"]["camera"] == 0


def test_typed_virtual_head_remembers_and_answers_from_memory(tmp_path):
    runtime = make_runtime(tmp_path)
    try:
        runtime.start()
        first = runtime.process_user_utterance(
            "remember that I like tea",
            timestamp=1_000,
        )
        second = runtime.process_user_utterance(
            "what do I like",
            timestamp=2_000,
        )

        fact_rows = runtime.engine.store.search_facts("likes", limit=5)
        assert len(fact_rows) == 1
        assert fact_rows[0].object_value["value"] == "tea"

        utterance_text = " ".join(utterance.text for utterance in first.utterances + second.utterances)
        assert "remember" in utterance_text.lower()
        assert "tea" in utterance_text.lower()
        assert second.snapshot["executive"]["intent_type"] == "respond_to_user"
    finally:
        runtime.close()


def test_scenario_fixture_runs_through_runtime_stack(tmp_path):
    runtime = make_runtime(tmp_path)
    try:
        runtime.start()
        result = runtime.replay_scenario(FIXTURE)

        event_kinds = [event["kind"] for event in result.events]
        assert "perception_observation" in event_kinds
        assert "memory_lifecycle" in event_kinds
        assert "attention_update" in event_kinds
        assert "executive_intent" in event_kinds
        assert runtime.engine.store.search_episodes("calibration", limit=5)
        assert result.snapshot["world"]["active_speaker"] == "mneme"
    finally:
        runtime.close()


def test_tick_closes_context_window_and_snapshot_persists(tmp_path):
    runtime = make_runtime(tmp_path)
    try:
        runtime.start()
        runtime.process_user_utterance("hello Mneme", timestamp=1_000)
        result = runtime.tick(advance_ms=9_000)

        closed_events = [
            event for event in result.events
            if event["kind"] == "world_state_update"
            and event["payload"].get("state_key") == "context_window"
            and event["payload"].get("status") == "closed"
        ]
        assert closed_events
        assert runtime.engine.store.get_recent_working_context_snapshots(limit=1)
    finally:
        runtime.close()


def test_mneme_run_scripted_json_output(tmp_path, capsys):
    exit_code = mneme_main([
        "--db",
        str(tmp_path / "memory.sqlite3"),
        "--migrations",
        str(MIGRATIONS),
        "run",
        "--json",
        "--input",
        "hello Mneme",
    ])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output[0]["type"] == "startup"
    assert any(item["type"] == "turn" for item in output)


def test_runtime_can_realize_dialogue_with_injected_local_model(tmp_path):
    runtime = MnemeRuntime(
        db_path=tmp_path / "memory.sqlite3",
        migrations_dir=MIGRATIONS,
        clock=RuntimeClock(1_000),
        model_dialogue_realizer=ModelDialogueRealizer(
            FakeModelRuntime(response_text=json.dumps({
                "response_text": "Local model wording is active.",
                "memory_refs_used": [],
                "uncertainty": "low",
                "proposed_memory_candidates": [],
                "safety_notes": [],
            }))
        ),
    )
    try:
        runtime.start()
        result = runtime.process_user_utterance("hello Mneme", timestamp=1_000)

        assert result.utterances[0].text == "Local model wording is active."
        realization = result.utterances[0].plan.content_slots["model_realization"]
        assert realization["used_model"] is True
        assert result.snapshot["cognition"]["last_result"]["used_model"] is True
    finally:
        runtime.close()


def test_mneme_run_local_cognition_profile_uses_model_realizer(monkeypatch, tmp_path, capsys):
    class FakeOllama:
        backend = "ollama"

        def __init__(self, *, base_url: str) -> None:
            self.base_url = base_url

        def generate(self, request):
            return ModelResponse(
                ok=True,
                backend="ollama",
                model=request.model,
                text=json.dumps({
                    "response_text": "Hello from local cognition.",
                    "memory_refs_used": [],
                    "uncertainty": "low",
                    "proposed_memory_candidates": [],
                    "safety_notes": [],
                }),
                latency_ms=4,
            )

    monkeypatch.setattr("android_brain_memory.virtual_head.OllamaModelRuntime", FakeOllama)

    exit_code = mneme_main([
        "--db",
        str(tmp_path / "memory.sqlite3"),
        "--migrations",
        str(MIGRATIONS),
        "run",
        "--profile",
        "local-cognition",
        "--json",
        "--input",
        "hello Mneme",
    ])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    turn = next(item for item in output if item["type"] == "turn")
    assert turn["result"]["utterances"][0]["text"] == "Hello from local cognition."
    assert turn["result"]["snapshot"]["cognition"]["last_result"]["used_model"] is True
