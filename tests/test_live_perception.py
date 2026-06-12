from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from android_brain_memory import (
    CommandFrameCaptureBackend,
    CommandSpeechRecognitionBackend,
    FakePeripheralBackend,
    LiveVisionWorker,
    MnemeRuntime,
    PerceptionRetentionPolicy,
    PeripheralDevice,
    PeripheralDiscoveryService,
    PeripheralKind,
    RuntimeClock,
    ScriptedCameraCaptureBackend,
    ScriptedSpeechRecognitionBackend,
)
MIGRATIONS = Path(__file__).resolve().parents[1] / "storage" / "migrations"


def devices() -> list[PeripheralDevice]:
    return [
        PeripheralDevice("cam-1", PeripheralKind.CAMERA, "Test Camera"),
        PeripheralDevice("mic-1", PeripheralKind.MICROPHONE, "Test Microphone"),
        PeripheralDevice("speaker-1", PeripheralKind.SPEAKER, "Test Speaker"),
    ]


def test_live_vision_worker_archives_frame_and_publishes_person_events(tmp_path):
    clock = RuntimeClock(1_000)
    discovery = PeripheralDiscoveryService(
        backend=FakePeripheralBackend(devices()),
        clock=clock,
    )
    discovery.scan_now(now_ms=1_000, publish=False)
    runtime = MnemeRuntime(
        db_path=tmp_path / "memory.sqlite3",
        migrations_dir=MIGRATIONS,
        clock=clock,
        discovery_service=discovery,
        live_camera_backend=ScriptedCameraCaptureBackend([
            {
                "content": b"frame-one",
                "detections": [
                    {"person_id": "alice", "label": "Alice", "confidence": 0.92},
                ],
            }
        ]),
        perception_retention=PerceptionRetentionPolicy(frame_archive_dir=tmp_path / "frames"),
    )
    try:
        runtime.start()
        result = runtime.tick(advance_ms=1_000)

        event_types = [event["payload"].get("observation_type") for event in result.events]
        assert "camera_frame" in event_types
        assert "person_seen" in event_types
        assert runtime.snapshot()["world"]["persons"][0]["person_id"] == "alice"

        traces = runtime.engine.store.get_recent_raw_traces(limit=5)
        assert any(trace.payload.get("frame", {}).get("device_label") == "Test Camera" for trace in traces)
        assert list((tmp_path / "frames").glob("*"))
    finally:
        runtime.close()


def test_live_speech_worker_publishes_transcript_and_memory_candidate(tmp_path):
    runtime = MnemeRuntime(
        db_path=tmp_path / "memory.sqlite3",
        migrations_dir=MIGRATIONS,
        clock=RuntimeClock(1_000),
        fake_devices=[device.to_dict() for device in devices()],
        live_speech_backend=ScriptedSpeechRecognitionBackend([
            {
                "speaker": "alice",
                "transcript": "remember that I like green tea",
                "confidence": 0.9,
            }
        ]),
        perception_retention=PerceptionRetentionPolicy(frame_archive_dir=tmp_path / "frames"),
        enable_perception_fusion=True,
    )
    try:
        runtime.start()
        result = runtime.tick(advance_ms=1_000)

        kinds = [event["kind"] for event in result.events]
        assert "perception_observation" in kinds
        assert "memory_candidate" in kinds
        assert "memory_lifecycle" in kinds
        assert runtime.snapshot()["world"]["active_speaker"] == "alice"

        facts = runtime.engine.store.search_facts("likes", limit=5)
        assert facts
        assert facts[0].object_value["value"] == "green tea"
    finally:
        runtime.close()


def test_live_perception_runtime_fuses_seen_person_and_speech(tmp_path):
    runtime = MnemeRuntime(
        db_path=tmp_path / "memory.sqlite3",
        migrations_dir=MIGRATIONS,
        clock=RuntimeClock(1_000),
        fake_devices=[device.to_dict() for device in devices()],
        live_camera_backend=ScriptedCameraCaptureBackend([
            {
                "content": b"frame-one",
                "detections": [
                    {"person_id": "alice", "label": "alice", "confidence": 0.95},
                ],
            }
        ]),
        live_speech_backend=ScriptedSpeechRecognitionBackend([
            {"speaker": "alice", "transcript": "hello Mneme", "confidence": 0.88},
        ]),
        perception_retention=PerceptionRetentionPolicy(frame_archive_dir=tmp_path / "frames"),
    )
    try:
        runtime.start()
        result = runtime.tick(advance_ms=1_000)

        fusion_events = [
            event for event in result.events
            if event["kind"] == "world_state_update"
            and event["payload"].get("state_key") == "perception_fusion"
        ]
        assert fusion_events
        assert fusion_events[-1]["payload"]["value"]["matched_person_id"] == "alice"
        assert runtime.snapshot()["perception"]["fusion"]["matches"] == 1
    finally:
        runtime.close()


def test_frame_archive_retention_limits_count(tmp_path):
    clock = RuntimeClock(1_000)
    discovery = PeripheralDiscoveryService(
        backend=FakePeripheralBackend(devices()),
        clock=clock,
    )
    discovery.scan_now(now_ms=1_000, publish=False)
    retention = PerceptionRetentionPolicy(
        frame_archive_dir=tmp_path / "frames",
        max_archived_frames=1,
        max_frame_archive_bytes=1024,
        max_frame_age_ms=60_000,
    )
    worker = LiveVisionWorker(
        discovery=discovery,
        backend=ScriptedCameraCaptureBackend([b"first", b"second"]),
        retention=retention,
        clock=clock,
    )

    first = worker.capture_once(now_ms=1_000)
    second = worker.capture_once(now_ms=2_000)

    assert first.status == "captured"
    assert second.status == "captured"
    archived = [path for path in (tmp_path / "frames").iterdir() if path.is_file()]
    assert len(archived) == 1


def test_command_backends_parse_frame_and_speech_outputs(tmp_path):
    def frame_runner(command: Sequence[str], timeout_ms: int) -> str:
        Path(command[-1]).write_bytes(b"image-bytes")
        return json.dumps({
            "detections": [
                {"person_id": "bob", "label": "Bob", "confidence": 0.81},
            ]
        })

    def speech_runner(command: Sequence[str], timeout_ms: int) -> str:
        return json.dumps({
            "speaker": "bob",
            "transcript": "hello from the microphone",
            "confidence": 0.82,
            "duration_ms": 500,
        })

    device = PeripheralDevice("cam-1", PeripheralKind.CAMERA, "Camera")
    frame_backend = CommandFrameCaptureBackend(
        ["capture", "{device_id}", "{output}"],
        command_runner=frame_runner,
    )
    frame = frame_backend.capture(
        device=device,
        output_path=tmp_path / "frame.jpg",
        timestamp=1_000,
    )
    assert frame is not None
    assert frame.detections[0]["person_id"] == "bob"

    mic = PeripheralDevice("mic-1", PeripheralKind.MICROPHONE, "Mic")
    speech_backend = CommandSpeechRecognitionBackend(
        ["asr", "{device_id}"],
        command_runner=speech_runner,
    )
    transcript = speech_backend.transcribe(device=mic, timestamp=1_000)
    assert transcript is not None
    assert transcript.speaker == "bob"
    assert transcript.transcript == "hello from the microphone"


def test_command_speech_backend_allows_json_literal_in_command_template():
    def runner(command: Sequence[str], timeout_ms: int) -> str:
        return command[1]

    backend = CommandSpeechRecognitionBackend(
        ["printf", '{"speaker":"alice","transcript":"hello","confidence":0.7}'],
        command_runner=runner,
    )
    mic = PeripheralDevice("mic-1", PeripheralKind.MICROPHONE, "Mic")

    transcript = backend.transcribe(device=mic, timestamp=1_000)

    assert transcript is not None
    assert transcript.speaker == "alice"
    assert transcript.transcript == "hello"
