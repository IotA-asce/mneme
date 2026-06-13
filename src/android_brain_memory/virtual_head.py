from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any

from .engine import DEFAULT_DB, DEFAULT_MIGRATIONS, to_jsonable
from .evaluation import DEFAULT_EVALUATION_LOG, EvaluationLogger
from .live_perception import (
    CommandFrameCaptureBackend,
    CommandSpeechRecognitionBackend,
    PerceptionRetentionPolicy,
)
from .local_audio import (
    DEFAULT_AUDIO_DIR,
    FasterWhisperSpeechRecognitionBackend,
    KokoroSpeechOutputBackend,
    SoundDeviceMicrophoneRecorder,
)
from .local_models import DEFAULT_MODEL_REGISTRY, LocalModelRegistry
from .local_ui import serve_ui
from .local_vision import MediaPipeFaceDetectionBackend, OpenCVCameraCaptureBackend
from .peripherals import PeripheralDiscoveryService, RealPeripheralBackend, default_virtual_head_devices
from .presence import CommandSpeechOutputBackend
from .runtime_preferences import (
    DEFAULT_RUNTIME_PREFERENCES,
    RuntimeDevicePreferences,
    RuntimePreferencesStore,
)
from .runtime_loop import MnemeRuntime, RuntimeClock


LOCAL_PROFILES = {"local-speech", "local-vision", "local-lab"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mneme", description="Mneme virtual head runtime.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite database path.")
    parser.add_argument(
        "--migrations",
        type=Path,
        default=DEFAULT_MIGRATIONS,
        help="Directory containing SQLite migrations.",
    )
    parser.add_argument(
        "--preferences",
        type=Path,
        default=DEFAULT_RUNTIME_PREFERENCES,
        help="Runtime preference file for saved local device selections.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Run the terminal virtual head.")
    run.add_argument(
        "--profile",
        choices=["default", "local-speech", "local-vision", "local-lab"],
        default="default",
        help="Runtime profile. Local profiles use optional native backends when configured.",
    )
    run.add_argument("--json", action="store_true", help="Emit JSON instead of terminal text.")
    run.add_argument(
        "--input",
        action="append",
        dest="inputs",
        help="Scripted user input. May be passed more than once.",
    )
    run.add_argument(
        "--start-ms",
        type=int,
        default=1_000,
        help="Deterministic start timestamp for scripted input.",
    )
    run.add_argument(
        "--step-ms",
        type=int,
        default=1_000,
        help="Timestamp increment between scripted utterances.",
    )
    run.add_argument(
        "--no-fake-devices",
        action="store_true",
        help="Start with no discovered fake peripherals. Equivalent to --device-backend none.",
    )
    run.add_argument(
        "--device-backend",
        choices=["fake", "real", "none"],
        default="fake",
        help="Peripheral discovery backend. Real inventories host devices without opening sensors.",
    )
    run.add_argument(
        "--device-scan-timeout-ms",
        type=int,
        default=1_500,
        help="Timeout for each real device inventory command.",
    )
    run.add_argument(
        "--camera-command",
        help="Local command template that writes one camera frame to {output}. Enables live vision.",
    )
    run.add_argument(
        "--camera-backend",
        choices=["auto", "command", "opencv", "none"],
        default="auto",
        help="Camera backend. OpenCV requires the vision-local optional extra.",
    )
    run.add_argument("--camera-index", type=int, help="OpenCV camera index override.")
    run.add_argument("--camera-device-id", help="Preferred discovered camera device ID.")
    run.add_argument(
        "--face-backend",
        choices=["none", "mediapipe"],
        default="none",
        help="Optional face detector for OpenCV frames.",
    )
    run.add_argument(
        "--speech-command",
        help="Local command template that prints transcript text or JSON. Enables live speech.",
    )
    run.add_argument(
        "--asr-model",
        default=".local/models/faster-whisper-base",
        help="faster-whisper model name or local path for local-speech profile.",
    )
    run.add_argument("--asr-device", default="cpu", help="faster-whisper device name.")
    run.add_argument("--asr-compute-type", default="int8", help="faster-whisper compute type.")
    run.add_argument("--asr-language", help="Optional ASR language code.")
    run.add_argument("--microphone-device-id", help="Preferred discovered microphone device ID.")
    run.add_argument("--record-ms", type=int, default=3_000, help="Bounded microphone segment length.")
    run.add_argument("--audio-dir", type=Path, default=DEFAULT_AUDIO_DIR, help="Local audio segment directory.")
    run.add_argument(
        "--frame-archive-dir",
        type=Path,
        default=Path(".local/perception_frames"),
        help="Directory for bounded Stage 4 camera keyframe archive.",
    )
    run.add_argument("--live-camera-interval-ms", type=int, default=1_000)
    run.add_argument("--live-speech-interval-ms", type=int, default=1_000)
    run.add_argument("--max-archived-frames", type=int, default=1_000)
    run.add_argument("--max-frame-archive-bytes", type=int, default=512 * 1024 * 1024)
    run.add_argument("--max-frame-age-ms", type=int, default=7 * 24 * 60 * 60 * 1000)
    run.add_argument(
        "--tts-command",
        help="Local command template for spoken output. Supports {text}, {voice}, and {device_id}.",
    )
    run.add_argument(
        "--tts-backend",
        choices=["auto", "simulated", "command", "kokoro"],
        default="auto",
        help="Speech output backend. Kokoro requires the tts-local optional extra.",
    )
    run.add_argument(
        "--voice",
        help="Speech voice label to use and persist in procedural memory.",
    )
    run.add_argument(
        "--tts-timeout-ms",
        type=int,
        default=10_000,
        help="Timeout for local TTS command.",
    )
    run.add_argument("--speaker-device-id", help="Preferred discovered speaker device ID.")
    run.add_argument(
        "--virtual-speech-duration-ms",
        type=int,
        default=0,
        help="Simulated speech skill duration before completion.",
    )
    run.add_argument(
        "--no-virtual-presence",
        action="store_true",
        help="Disable virtual avatar, virtual skills, and speech-output simulation.",
    )
    run.add_argument(
        "--evaluation-log",
        type=Path,
        help="Append local living-lab conversation metrics to a JSONL file.",
    )

    ui = subparsers.add_parser("ui", help="Serve the local browser virtual-head UI.")
    ui.add_argument("--host", default="127.0.0.1")
    ui.add_argument("--port", type=int, default=8765)
    ui.add_argument(
        "--device-backend",
        choices=["fake", "real", "none"],
        default="real",
        help="Device inventory backend for UI device selectors.",
    )
    ui.add_argument(
        "--device-scan-timeout-ms",
        type=int,
        default=1_500,
        help="Timeout for each real device inventory command.",
    )

    models = subparsers.add_parser("models", help="Inspect local model registry.")
    models.add_argument("--registry", type=Path, default=DEFAULT_MODEL_REGISTRY)
    model_subparsers = models.add_subparsers(dest="models_command", required=True)
    models_list = model_subparsers.add_parser("list", help="List configured local models.")
    models_list.add_argument("--profile")
    models_list.add_argument("--json", action="store_true")
    models_verify = model_subparsers.add_parser("verify", help="Verify local model files/checksums.")
    models_verify.add_argument("model_id", nargs="?")
    models_verify.add_argument("--json", action="store_true")
    models_download = model_subparsers.add_parser("download", help="Download a configured model when allowed.")
    models_download.add_argument("model_id")
    models_download.add_argument("--overwrite", action="store_true")

    evaluation = subparsers.add_parser("eval", help="Inspect local living-lab evaluation logs.")
    eval_subparsers = evaluation.add_subparsers(dest="eval_command", required=True)
    eval_summary = eval_subparsers.add_parser("summarize", help="Summarize a JSONL evaluation log.")
    eval_summary.add_argument("--path", type=Path, default=DEFAULT_EVALUATION_LOG)
    eval_summary.add_argument("--json", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        return _run(args)
    if args.command == "ui":
        return _ui(args)
    if args.command == "models":
        return _models(args)
    if args.command == "eval":
        return _eval(args)
    parser.error(f"unsupported command: {args.command}")
    return 2


def _run(args: argparse.Namespace) -> int:
    try:
        runtime = _build_runtime(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    evaluation_logger = EvaluationLogger(args.evaluation_log) if args.evaluation_log else None
    outputs: list[dict[str, Any]] = []
    try:
        startup = runtime.start()
        outputs.append({"type": "startup", "devices": startup.to_dict()})
        if args.inputs:
            now = args.start_ms
            for text in args.inputs:
                result = runtime.process_user_utterance(text, timestamp=now)
                result_dict = result.to_dict()
                outputs.append({"type": "turn", "input": text, "result": result_dict})
                if evaluation_logger is not None:
                    evaluation_logger.record_turn(input_text=text, result=result_dict)
                now += args.step_ms
                outputs.append({"type": "tick", "result": runtime.tick(advance_ms=args.step_ms).to_dict()})
        else:
            outputs.extend(_interactive(runtime, evaluation_logger=evaluation_logger))
        outputs.append({"type": "shutdown", "snapshot": runtime.snapshot()})
    finally:
        runtime.close()

    if args.json:
        print(json.dumps(to_jsonable(outputs), indent=2, sort_keys=True))
    else:
        _print_terminal(outputs)
    return 0


def _build_runtime(args: argparse.Namespace) -> MnemeRuntime:
    preferences_store = RuntimePreferencesStore(args.preferences)
    preferences = _device_preferences_from_args(args, preferences_store.load())
    discovery_service, fake_devices = _device_discovery(args)
    retention = PerceptionRetentionPolicy(
        frame_archive_dir=args.frame_archive_dir,
        max_archived_frames=args.max_archived_frames,
        max_frame_archive_bytes=args.max_frame_archive_bytes,
        max_frame_age_ms=args.max_frame_age_ms,
    )
    camera_backend = _camera_backend(args)
    speech_backend = _speech_backend(args)
    speech_output_backend = _speech_output_backend(args)
    return MnemeRuntime(
        db_path=args.db,
        migrations_dir=args.migrations,
        clock=RuntimeClock(args.start_ms),
        discovery_service=discovery_service,
        fake_devices=fake_devices,
        live_camera_backend=camera_backend,
        live_speech_backend=speech_backend,
        perception_retention=retention,
        live_camera_interval_ms=args.live_camera_interval_ms,
        live_speech_interval_ms=args.live_speech_interval_ms,
        enable_perception_fusion=bool(camera_backend or speech_backend),
        speech_output_backend=speech_output_backend,
        speech_voice=args.voice,
        device_preferences=preferences,
        preferences_store=preferences_store,
        enable_virtual_presence=not args.no_virtual_presence,
        virtual_speech_duration_ms=args.virtual_speech_duration_ms,
    )


def _device_discovery(args: argparse.Namespace) -> tuple[PeripheralDiscoveryService | None, list[dict[str, Any]] | None]:
    device_backend = "none" if getattr(args, "no_fake_devices", False) else args.device_backend
    if (
        getattr(args, "profile", "default") in LOCAL_PROFILES
        and getattr(args, "device_backend", "fake") == "fake"
        and not getattr(args, "no_fake_devices", False)
    ):
        device_backend = "real"
    if device_backend == "real":
        return (
            PeripheralDiscoveryService(
                backend=RealPeripheralBackend(timeout_ms=args.device_scan_timeout_ms),
            ),
            None,
        )
    fake_devices = [] if device_backend == "none" else [
        device.to_dict() for device in default_virtual_head_devices()
    ]
    return None, fake_devices


def _device_preferences_from_args(
    args: argparse.Namespace,
    current: RuntimeDevicePreferences,
) -> RuntimeDevicePreferences:
    return RuntimeDevicePreferences(
        camera_device_id=getattr(args, "camera_device_id", None) or current.camera_device_id,
        microphone_device_id=getattr(args, "microphone_device_id", None) or current.microphone_device_id,
        speaker_device_id=getattr(args, "speaker_device_id", None) or current.speaker_device_id,
    )


def _camera_backend(args: argparse.Namespace) -> Any:
    if args.camera_command:
        return CommandFrameCaptureBackend(shlex.split(args.camera_command))
    wants_opencv = (
        args.camera_backend == "opencv"
        or (args.camera_backend == "auto" and args.profile in {"local-vision", "local-lab"})
    )
    if not wants_opencv:
        return None
    face_detector = MediaPipeFaceDetectionBackend() if args.face_backend == "mediapipe" else None
    return OpenCVCameraCaptureBackend(camera_index=args.camera_index, face_detector=face_detector)


def _speech_backend(args: argparse.Namespace) -> Any:
    if args.speech_command:
        return CommandSpeechRecognitionBackend(shlex.split(args.speech_command))
    if args.profile not in {"local-speech", "local-lab"}:
        return None
    recorder = SoundDeviceMicrophoneRecorder(
        audio_dir=args.audio_dir,
        duration_ms=args.record_ms,
    )
    return FasterWhisperSpeechRecognitionBackend(
        model_name_or_path=args.asr_model,
        recorder=recorder,
        language=args.asr_language,
        device_name=args.asr_device,
        compute_type=args.asr_compute_type,
    )


def _speech_output_backend(args: argparse.Namespace) -> Any:
    if args.tts_command:
        return CommandSpeechOutputBackend(
            shlex.split(args.tts_command),
            timeout_ms=args.tts_timeout_ms,
            default_voice=args.voice,
        )
    if args.tts_backend == "command":
        raise ValueError("--tts-backend command requires --tts-command")
    wants_kokoro = (
        args.tts_backend == "kokoro"
        or (args.tts_backend == "auto" and args.profile in {"local-speech", "local-lab"})
    )
    if wants_kokoro:
        return KokoroSpeechOutputBackend(voice=args.voice or "af_heart")
    return None


def _ui(args: argparse.Namespace) -> int:
    preferences_store = RuntimePreferencesStore(args.preferences)
    discovery_service, fake_devices = _device_discovery(args)
    runtime = MnemeRuntime(
        db_path=args.db,
        migrations_dir=args.migrations,
        discovery_service=discovery_service,
        fake_devices=fake_devices,
        preferences_store=preferences_store,
    )
    try:
        runtime.start()
        print(f"Mneme UI listening on http://{args.host}:{args.port}", file=sys.stderr)
        serve_ui(runtime, host=args.host, port=args.port)
    finally:
        runtime.close()
    return 0


def _models(args: argparse.Namespace) -> int:
    registry = LocalModelRegistry(registry_path=args.registry)
    if args.models_command == "list":
        payload = registry.to_dict(profile=args.profile)
        if args.json:
            print(json.dumps(to_jsonable(payload), indent=2, sort_keys=True))
        else:
            for record in registry.list_models(profile=args.profile):
                print(f"{record.model_id}\t{record.backend}\t{record.license}\t{record.path}")
        return 0
    if args.models_command == "verify":
        payload = [item.to_dict() for item in registry.verify(args.model_id)]
        if args.json:
            print(json.dumps(to_jsonable(payload), indent=2, sort_keys=True))
        else:
            for item in payload:
                status = "ok" if item["exists"] and item["checksum_ok"] is not False else "missing"
                print(f"{item['model_id']}\t{status}\t{item['path']}")
        return 0
    if args.models_command == "download":
        try:
            record = registry.download(args.model_id, overwrite=args.overwrite)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print(json.dumps(to_jsonable(record.to_dict()), indent=2, sort_keys=True))
        return 0
    return 2


def _eval(args: argparse.Namespace) -> int:
    if args.eval_command == "summarize":
        summary = EvaluationLogger(args.path).summarize()
        if args.json:
            print(json.dumps(to_jsonable(summary), indent=2, sort_keys=True))
        else:
            print(
                f"records={summary['records']} turns={summary.get('conversation_turns', 0)} "
                f"responses={summary.get('responses_generated', 0)}"
            )
        return 0
    return 2


def _interactive(
    runtime: MnemeRuntime,
    *,
    evaluation_logger: EvaluationLogger | None = None,
) -> list[dict[str, Any]]:
    outputs = []
    print("Mneme virtual head. Type /quit to exit.", file=sys.stderr)
    for raw in sys.stdin:
        text = raw.strip()
        if not text:
            continue
        if text in {"/quit", "/exit"}:
            break
        result = runtime.process_user_utterance(text)
        result_dict = result.to_dict()
        outputs.append({"type": "turn", "input": text, "result": result_dict})
        if evaluation_logger is not None:
            evaluation_logger.record_turn(input_text=text, result=result_dict)
        runtime.tick()
    return outputs

def _print_terminal(outputs: list[dict[str, Any]]) -> None:
    for item in outputs:
        if item["type"] == "startup":
            counts = item["devices"]["available_counts"]
            print(f"devices camera={counts['camera']} microphone={counts['microphone']} speaker={counts['speaker']}")
        elif item["type"] == "turn":
            for utterance in item["result"]["utterances"]:
                print(f"mneme: {utterance['text']}")
        elif item["type"] == "shutdown":
            executive = item["snapshot"].get("executive") or {}
            print(f"state: {executive.get('intent_type', 'idle')}")


if __name__ == "__main__":
    raise SystemExit(main())
