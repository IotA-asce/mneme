from __future__ import annotations

import json
import threading
import urllib.parse
import urllib.request
from http.server import HTTPServer
from pathlib import Path

from android_brain_memory import (
    AudioCapture,
    EvaluationLogger,
    EventBus,
    FasterWhisperSpeechRecognitionBackend,
    KokoroSpeechOutputBackend,
    LocalModelRecord,
    LocalModelRegistry,
    MnemeRuntime,
    OpenCVCameraCaptureBackend,
    PeripheralDevice,
    PeripheralKind,
    RuntimeClock,
    RuntimeDevicePreferences,
    RuntimePreferencesStore,
    VadDecision,
    VirtualSkillGoal,
    VirtualSkillRunner,
    VirtualSkillStatus,
    WebRtcVadEndpointDetector,
    make_ui_server,
    pcm16_frames,
    render_snapshot_html,
    write_silent_wav,
)
from android_brain_memory.local_ui import make_ui_handler
from android_brain_memory.virtual_head import main as mneme_main


MIGRATIONS = Path(__file__).resolve().parents[1] / "storage" / "migrations"


def _microphone() -> PeripheralDevice:
    return PeripheralDevice(
        device_id="mic_1",
        kind=PeripheralKind.MICROPHONE,
        label="Test Mic",
        metadata={"index": 0},
    )


def _camera() -> PeripheralDevice:
    return PeripheralDevice(
        device_id="camera_1",
        kind=PeripheralKind.CAMERA,
        label="Test Camera",
        metadata={"index": 0},
    )


def test_model_registry_verifies_existing_and_missing_models(tmp_path):
    model_file = tmp_path / "model.bin"
    model_file.write_bytes(b"mneme-model")
    import hashlib

    registry = LocalModelRegistry(
        [
            LocalModelRecord(
                model_id="present",
                backend="fake",
                path=model_file,
                license="Apache-2.0",
                sha256=hashlib.sha256(b"mneme-model").hexdigest(),
                profiles=["local-speech"],
            ),
            LocalModelRecord(
                model_id="missing",
                backend="fake",
                path=tmp_path / "missing.bin",
                license="Apache-2.0",
            ),
        ]
    )

    results = {item.model_id: item for item in registry.verify()}

    assert results["present"].exists is True
    assert results["present"].checksum_ok is True
    assert results["missing"].exists is False
    assert registry.list_models(profile="local-speech")[0].model_id == "present"


def test_model_registry_download_requires_configured_url(tmp_path):
    registry = LocalModelRegistry([
        LocalModelRecord(
            model_id="manual",
            backend="fake",
            path=tmp_path / "manual.bin",
            license="Apache-2.0",
        )
    ])

    try:
        registry.download("manual")
    except ValueError as exc:
        assert "download is not configured" in str(exc)
    else:
        raise AssertionError("download should require a configured URL")


def test_runtime_preferences_store_round_trips_and_clears_device_ids(tmp_path):
    store = RuntimePreferencesStore(tmp_path / "prefs.json")

    store.save(RuntimeDevicePreferences(
        camera_device_id="camera-a",
        microphone_device_id="mic-a",
        speaker_device_id="speaker-a",
    ))
    loaded = store.load()

    assert loaded.camera_device_id == "camera-a"
    assert loaded.microphone_device_id == "mic-a"
    assert loaded.speaker_device_id == "speaker-a"

    updated = store.update(camera_device_id=None, speaker_device_id="speaker-b")

    assert updated.camera_device_id is None
    assert updated.microphone_device_id == "mic-a"
    assert updated.speaker_device_id == "speaker-b"


def test_webrtc_vad_endpoint_detector_uses_injected_vad():
    class FakeVad:
        def __init__(self, aggressiveness: int) -> None:
            self.aggressiveness = aggressiveness

        def is_speech(self, frame: bytes, sample_rate: int) -> bool:
            return any(byte != 0 for byte in frame)

    detector = WebRtcVadEndpointDetector(vad_factory=FakeVad, min_speech_ratio=0.5)
    one_frame = [1000] * 480
    silence = [0] * 480
    decision = detector.classify(pcm16_frames(one_frame + silence))

    assert isinstance(decision, VadDecision)
    assert decision.total_frames == 2
    assert decision.speech_frames == 1
    assert decision.is_speech is True


def test_faster_whisper_backend_uses_injected_recorder_and_model(tmp_path):
    audio_path = write_silent_wav(tmp_path / "speech.wav", duration_ms=100)

    class FakeRecorder:
        def record(self, *, device: PeripheralDevice, timestamp: int) -> AudioCapture:
            return AudioCapture(
                capture_id="audio_1",
                captured_ts=timestamp,
                path=audio_path,
                duration_ms=100,
                metadata={"device": device.device_id},
            )

    class Segment:
        text = " hello Mneme "
        no_speech_prob = 0.1

    class Info:
        language = "en"
        language_probability = 0.9
        duration = 0.1

    class FakeModel:
        def transcribe(self, path: str, **kwargs):
            assert Path(path) == audio_path
            assert kwargs["beam_size"] == 5
            return iter([Segment()]), Info()

    backend = FasterWhisperSpeechRecognitionBackend(
        model_name_or_path="fake-model",
        recorder=FakeRecorder(),
        model_factory=lambda *args, **kwargs: FakeModel(),
    )

    observation = backend.transcribe(device=_microphone(), timestamp=1_000)

    assert observation is not None
    assert observation.transcript == "hello Mneme"
    assert observation.confidence == 0.9
    assert observation.metadata["backend"] == "faster_whisper"


def test_faster_whisper_backend_returns_none_for_empty_transcript(tmp_path):
    audio_path = write_silent_wav(tmp_path / "silence.wav", duration_ms=100)

    class FakeRecorder:
        def record(self, *, device: PeripheralDevice, timestamp: int) -> AudioCapture:
            return AudioCapture(
                capture_id="audio_silence",
                captured_ts=timestamp,
                path=audio_path,
                duration_ms=100,
            )

    class Segment:
        text = "   "
        no_speech_prob = 0.99

    class Info:
        language_probability = 0.1

    class FakeModel:
        def transcribe(self, path: str, **kwargs):
            return iter([Segment()]), Info()

    backend = FasterWhisperSpeechRecognitionBackend(
        model_name_or_path="fake-model",
        recorder=FakeRecorder(),
        model_factory=lambda *args, **kwargs: FakeModel(),
    )

    assert backend.transcribe(device=_microphone(), timestamp=1_000) is None


def test_faster_whisper_backend_surfaces_recorder_failure():
    class FailingRecorder:
        def record(self, *, device: PeripheralDevice, timestamp: int) -> AudioCapture:
            raise ValueError("microphone permission denied")

    backend = FasterWhisperSpeechRecognitionBackend(
        model_name_or_path="fake-model",
        recorder=FailingRecorder(),
        model_factory=lambda *args, **kwargs: object(),
    )

    try:
        backend.transcribe(device=_microphone(), timestamp=1_000)
    except ValueError as exc:
        assert "microphone permission denied" in str(exc)
    else:
        raise AssertionError("recorder failure should be visible to the speech worker")


def test_kokoro_backend_uses_injected_pipeline():
    calls = []

    class FakePipeline:
        def __call__(self, text: str, *, voice: str):
            calls.append((text, voice))
            yield ("graphemes", "phonemes", [0.0, 0.1])

    played = []
    backend = KokoroSpeechOutputBackend(
        voice="soft",
        pipeline_factory=lambda **kwargs: FakePipeline(),
        audio_player=lambda audio, sample_rate: played.append((audio, sample_rate)),
    )

    output = backend.speak(text="hello", voice=None, device_id=None, timestamp=1_000)

    assert output.status == "spoken"
    assert output.voice == "soft"
    assert output.metadata["backend"] == "kokoro"
    assert calls == [("hello", "soft")]
    assert played


def test_virtual_speech_runner_publishes_failed_status_for_tts_error():
    class FailingSpeechBackend:
        def speak(self, *, text: str, voice: str | None, device_id: str | None, timestamp: int):
            raise ValueError("tts timeout")

    clock = RuntimeClock(1_000)
    bus = EventBus(clock=clock)
    runner = VirtualSkillRunner(
        bus=bus,
        speech_backend=FailingSpeechBackend(),
        clock=clock,
    )
    goal = VirtualSkillGoal(
        goal_id="goal_speech",
        skill_id="virtual_speech",
        goal_type="speech",
        created_ts=1_000,
        payload={"text": "hello"},
    )

    record = runner.start_goal(goal, now_ms=1_000)

    assert record.status == VirtualSkillStatus.FAILED
    statuses = [event.payload["status"] for event in bus.history()]
    assert VirtualSkillStatus.FAILED.value in statuses
    assert runner.stats["failed"] == 1


def test_opencv_camera_backend_uses_injected_cv2_and_face_detector(tmp_path):
    class Capture:
        def isOpened(self) -> bool:
            return True

        def read(self):
            return True, b"frame"

        def release(self) -> None:
            pass

    class FakeCv2:
        def VideoCapture(self, camera_ref):
            assert camera_ref == 0
            return Capture()

        def imwrite(self, path: str, frame) -> bool:
            Path(path).write_bytes(b"jpeg")
            return True

    backend = OpenCVCameraCaptureBackend(
        cv2_module=FakeCv2(),
        face_detector=lambda path: [{
            "person_id": "session_person_1",
            "label": "person_1",
            "confidence": 0.88,
            "bbox": {"xmin": 0.1, "ymin": 0.2, "width": 0.3, "height": 0.4},
            "attention_facing_signal": True,
            "identity_status": "anonymous_session",
        }],
    )

    frame = backend.capture(
        device=_camera(),
        output_path=tmp_path / "frame.jpg",
        timestamp=1_000,
    )

    assert frame is not None
    assert frame.path.exists()
    assert frame.detections[0]["identity_status"] == "anonymous_session"
    assert frame.detections[0]["attention_facing_signal"] is True


def test_runtime_uses_preferred_microphone_and_speaker_devices(tmp_path):
    seen_microphones: list[str] = []

    class RecordingSpeechBackend:
        def transcribe(self, *, device: PeripheralDevice, timestamp: int):
            seen_microphones.append(device.device_id)
            return None

    runtime = MnemeRuntime(
        db_path=tmp_path / "memory.sqlite3",
        migrations_dir=MIGRATIONS,
        clock=RuntimeClock(1_000),
        fake_devices=[
            PeripheralDevice("mic-1", PeripheralKind.MICROPHONE, "Mic 1").to_dict(),
            PeripheralDevice("mic-2", PeripheralKind.MICROPHONE, "Mic 2").to_dict(),
            PeripheralDevice("speaker-1", PeripheralKind.SPEAKER, "Speaker 1").to_dict(),
            PeripheralDevice("speaker-2", PeripheralKind.SPEAKER, "Speaker 2").to_dict(),
        ],
        live_speech_backend=RecordingSpeechBackend(),
        device_preferences=RuntimeDevicePreferences(
            microphone_device_id="mic-2",
            speaker_device_id="speaker-2",
        ),
    )
    try:
        runtime.start()
        runtime.tick(advance_ms=1_000)
        result = runtime.process_user_utterance("hello Mneme", timestamp=2_500)
    finally:
        runtime.close()

    assert seen_microphones == ["mic-2"]
    outputs = result.snapshot["presence"]["skills"]["outputs"]
    assert outputs[-1]["device_id"] == "speaker-2"


def test_local_ui_renders_avatar_state():
    snapshot = {
        "timestamp": 1_000,
        "devices": {
            "devices": [
                {"device_id": "cam-1", "kind": "camera", "label": "Camera 1"},
                {"device_id": "mic-1", "kind": "microphone", "label": "Mic 1"},
                {"device_id": "speaker-1", "kind": "speaker", "label": "Speaker 1"},
            ],
        },
        "device_preferences": {
            "camera_device_id": "cam-1",
            "microphone_device_id": "mic-1",
            "speaker_device_id": "speaker-1",
        },
        "presence": {
            "voice": "default",
            "avatar": {
                "mode": "speaking",
                "gaze_target": "person:user",
                "expression": "speaking",
                "blink_pattern": "speaking",
                "mouth_state": "open",
            }
        },
        "last_utterance": {"text": "Hello!"},
    }

    html = render_snapshot_html(snapshot)

    assert 'data-mode="speaking"' in html
    assert "person:user" in html
    assert "Hello!" in html
    assert "mouth open" in html
    assert "Camera 1" in html
    assert "Mic 1" in html
    assert "Speaker 1" in html
    assert '<option value="cam-1" selected>' in html
    assert 'data-device-kind="camera"' in html
    assert "Refresh list" in html


def test_local_ui_refresh_action_rescans_devices():
    class RefreshingRuntime:
        def __init__(self):
            self.refreshed = False

        def snapshot(self):
            devices = []
            counts = {"camera": 0, "microphone": 0, "speaker": 0}
            if self.refreshed:
                devices = [{"device_id": "cam-1", "kind": "camera", "label": "Camera 1"}]
                counts["camera"] = 1
            return {
                "timestamp": 1_000,
                "devices": {"devices": devices, "available_counts": counts},
                "device_preferences": {},
                "presence": {"avatar": {"mode": "idle"}},
            }

        def process_user_utterance(self, text: str):
            return None

        def update_device_preferences(self, **kwargs):
            return None

        def refresh_devices(self):
            self.refreshed = True
            return None

    runtime = RefreshingRuntime()
    server = make_ui_server(runtime, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    base_url = f"http://{host}:{port}"
    try:
        first = urllib.request.urlopen(base_url, timeout=2).read().decode("utf-8")
        assert "No devices found yet" in first
        assert "Camera 1" not in first

        body = urllib.parse.urlencode({"action": "refresh"}).encode("utf-8")
        refreshed = urllib.request.urlopen(
            urllib.request.Request(base_url + "/devices", data=body, method="POST"),
            timeout=2,
        ).read().decode("utf-8")

        assert runtime.refreshed is True
        assert "Camera 1" in refreshed
        assert "Found 1 device option" in refreshed
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_make_ui_handler_returns_handler_class():
    class FakeRuntime:
        def snapshot(self):
            return {"presence": {"avatar": {"mode": "idle"}}}

        def process_user_utterance(self, text: str):
            return None

    handler = make_ui_handler(FakeRuntime())
    assert handler.__name__ == "MnemeUiHandler"


def test_local_ui_server_is_single_threaded_for_sqlite_runtime_safety():
    class FakeRuntime:
        def snapshot(self):
            return {"presence": {"avatar": {"mode": "idle"}}}

        def process_user_utterance(self, text: str):
            return None

    server = make_ui_server(FakeRuntime(), port=0)
    try:
        assert isinstance(server, HTTPServer)
        assert type(server) is HTTPServer
    finally:
        server.server_close()


def test_evaluation_logger_records_and_summarizes_turn(tmp_path):
    logger = EvaluationLogger(tmp_path / "eval.jsonl")
    record = logger.record_turn(
        input_text="hello",
        result={
            "timestamp": 1_000,
            "events": [{"kind": "skill_status"}, {"kind": "safety_event"}],
            "utterances": [{"text": "hi", "plan": {"memory_refs": ["fact_1"]}}],
            "snapshot": {
                "presence": {"coordinator": {"barge_ins": 1}},
                "memory": {"fact": 1},
            },
        },
    )

    assert record.metrics["response_generated"] is True
    assert record.metrics["memory_recall_signal"] is True
    summary = logger.summarize()
    assert summary["conversation_turns"] == 1
    assert summary["barge_ins_total"] == 1


def test_mneme_models_list_and_verify_cli(tmp_path, capsys):
    registry = tmp_path / "models.yaml"
    registry.write_text(
        """
models:
  - id: fake_model
    backend: fake
    path: missing.bin
    license: Apache-2.0
    profiles: [local-speech]
""",
        encoding="utf-8",
    )

    assert mneme_main(["models", "--registry", str(registry), "list", "--json"]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert listed["models"][0]["model_id"] == "fake_model"

    assert mneme_main(["models", "--registry", str(registry), "verify", "--json"]) == 0
    verified = json.loads(capsys.readouterr().out)
    assert verified[0]["exists"] is False


def test_mneme_eval_summarize_cli(tmp_path, capsys):
    path = tmp_path / "eval.jsonl"
    EvaluationLogger(path).record_turn(
        input_text="hello",
        result={"timestamp": 1_000, "events": [], "utterances": [], "snapshot": {}},
    )

    assert mneme_main(["eval", "summarize", "--path", str(path), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["conversation_turns"] == 1
