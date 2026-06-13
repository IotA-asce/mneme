from __future__ import annotations

import argparse
import json
import shlex
import sys
import time
from pathlib import Path
from typing import Any

from .capability_ladder import build_capability_report
from .cognitive_benchmarks import (
    DEFAULT_COGNITION_FIXTURE,
    DEFAULT_COGNITION_FIXTURES_DIR,
    run_cognitive_benchmark,
    run_cognitive_benchmark_suite,
)
from .engine import DEFAULT_DB, DEFAULT_MIGRATIONS, MnemeMemory, to_jsonable
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
from .model_runtime import (
    DEFAULT_MODEL_TIMEOUT_MS,
    DEFAULT_OLLAMA_BASE_URL,
    DEFAULT_OLLAMA_MODEL,
    OllamaModelRuntime,
)
from .model_dialogue import DEFAULT_MAX_RESPONSE_CHARS, DEFAULT_MODEL_DIALOGUE_TIMEOUT_MS, ModelDialogueRealizer
from .memory_review import apply_memory_review, explain_memory_refs, reject_memory_review
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
from .speech_benchmarks import (
    DEFAULT_SPEECH_FIXTURES_DIR,
    run_speech_soak,
    run_speech_soak_suite,
)


LOCAL_PROFILES = {"local-speech", "local-vision", "local-cognition", "local-lab"}
REAL_DEVICE_AUTO_PROFILES = {"local-speech", "local-vision", "local-lab"}
DEFAULT_STATUS_STREAM = object()


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
        choices=["default", "local-speech", "local-vision", "local-cognition", "local-lab"],
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
        "--live",
        action="store_true",
        help="Continuously tick live perception/runtime workers instead of waiting for typed input.",
    )
    run.add_argument(
        "--live-ticks",
        type=int,
        default=0,
        help="Run this many live ticks, then exit. Useful for tests and smoke checks.",
    )
    run.add_argument(
        "--live-sleep-ms",
        type=int,
        default=1_000,
        help="Wall-clock delay between live ticks when --live is unbounded.",
    )
    run.add_argument(
        "--quiet-live-status",
        action="store_true",
        help="Suppress human-readable live status lines. JSON output is unchanged.",
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
    run.add_argument(
        "--cognition-backend",
        choices=["auto", "none", "ollama"],
        default="auto",
        help="Optional local model wording backend. Auto enables Ollama for local-cognition only.",
    )
    run.add_argument("--cognition-base-url", default=DEFAULT_OLLAMA_BASE_URL)
    run.add_argument("--cognition-model", default=DEFAULT_OLLAMA_MODEL)
    run.add_argument("--cognition-timeout-ms", type=int, default=DEFAULT_MODEL_DIALOGUE_TIMEOUT_MS)
    run.add_argument("--cognition-max-response-chars", type=int, default=DEFAULT_MAX_RESPONSE_CHARS)

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
        default=5_000,
        help="Timeout for each real device inventory command.",
    )
    ui.add_argument(
        "--cognition-profile",
        choices=["none", "local"],
        default="none",
        help="Enable local model wording status and realization in the UI runtime.",
    )
    ui.add_argument(
        "--cognition-backend",
        choices=["ollama"],
        default="ollama",
        help="Local cognition backend for --cognition-profile local.",
    )
    ui.add_argument("--cognition-base-url", default=DEFAULT_OLLAMA_BASE_URL)
    ui.add_argument("--cognition-model", default=DEFAULT_OLLAMA_MODEL)
    ui.add_argument("--cognition-timeout-ms", type=int, default=DEFAULT_MODEL_DIALOGUE_TIMEOUT_MS)
    ui.add_argument("--cognition-max-response-chars", type=int, default=DEFAULT_MAX_RESPONSE_CHARS)

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

    cognition = subparsers.add_parser("cognition", help="Check local cognitive model backends.")
    cognition_subparsers = cognition.add_subparsers(dest="cognition_command", required=True)
    cognition_check = cognition_subparsers.add_parser("check", help="Check local model availability and latency.")
    cognition_check.add_argument("--backend", choices=["ollama"], default="ollama")
    cognition_check.add_argument("--base-url", default=DEFAULT_OLLAMA_BASE_URL)
    cognition_check.add_argument("--model", default=DEFAULT_OLLAMA_MODEL)
    cognition_check.add_argument("--timeout-ms", type=int, default=DEFAULT_MODEL_TIMEOUT_MS)
    cognition_check.add_argument("--no-probe", action="store_true")
    cognition_check.add_argument("--json", action="store_true")

    review = subparsers.add_parser("review", help="Inspect and apply supervised memory review records.")
    review_subparsers = review.add_subparsers(dest="review_command", required=True)
    review_list = review_subparsers.add_parser("list", help="List memory review records.")
    review_list.add_argument("--status", choices=["proposed", "applied", "rejected", "failed"])
    review_list.add_argument(
        "--proposal-type",
        choices=["correction", "forget_request", "confirm_memory", "contradiction_challenge"],
    )
    review_list.add_argument("--limit", type=int, default=50)
    review_list.add_argument("--json", action="store_true")
    review_show = review_subparsers.add_parser("show", help="Show one memory review record.")
    review_show.add_argument("--review-id", required=True)
    review_show.add_argument("--json", action="store_true")
    review_apply = review_subparsers.add_parser("apply", help="Apply one proposed memory review record.")
    review_apply.add_argument("--review-id", required=True)
    review_apply.add_argument("--reason", required=True)
    review_apply.add_argument("--fact-data", help="Optional JSON fact payload for correction reviews.")
    review_apply.add_argument("--json", action="store_true")
    review_reject = review_subparsers.add_parser("reject", help="Reject one proposed memory review record.")
    review_reject.add_argument("--review-id", required=True)
    review_reject.add_argument("--reason", required=True)
    review_reject.add_argument("--json", action="store_true")
    review_conflicts = review_subparsers.add_parser("conflicts", help="List unresolved fact conflict reports.")
    review_conflicts.add_argument("--subject", default="")
    review_conflicts.add_argument("--predicate", default="")
    review_conflicts.add_argument("--limit", type=int, default=50)
    review_conflicts.add_argument("--json", action="store_true")
    review_explain = review_subparsers.add_parser("explain", help="Explain one memory reference.")
    review_explain.add_argument("--memory-kind", required=True, choices=["fact", "episode", "summary"])
    review_explain.add_argument("--memory-id", required=True)
    review_explain.add_argument("--json", action="store_true")

    evaluation = subparsers.add_parser("eval", help="Inspect local living-lab evaluation logs.")
    eval_subparsers = evaluation.add_subparsers(dest="eval_command", required=True)
    eval_summary = eval_subparsers.add_parser("summarize", help="Summarize a JSONL evaluation log.")
    eval_summary.add_argument("--path", type=Path, default=DEFAULT_EVALUATION_LOG)
    eval_summary.add_argument("--json", action="store_true")
    eval_cognition = eval_subparsers.add_parser("cognition", help="Run cognitive benchmark fixtures.")
    eval_cognition.add_argument("--fixture", type=Path)
    eval_cognition.add_argument("--fixtures-dir", type=Path, default=DEFAULT_COGNITION_FIXTURES_DIR)
    eval_cognition.add_argument(
        "--benchmark-db",
        type=Path,
        help="Optional benchmark database path. Defaults to an isolated temporary database.",
    )
    eval_cognition.add_argument("--json", action="store_true")
    eval_speech = eval_subparsers.add_parser("speech", help="Run fake-backed live speech soak fixtures.")
    eval_speech.add_argument("--fixture", type=Path)
    eval_speech.add_argument("--fixtures-dir", type=Path, default=DEFAULT_SPEECH_FIXTURES_DIR)
    eval_speech.add_argument(
        "--benchmark-db",
        type=Path,
        help="Optional speech benchmark database path. Defaults to an isolated temporary database.",
    )
    eval_speech.add_argument("--json", action="store_true")
    eval_capability = eval_subparsers.add_parser("capability", help="Report conservative capability ladder evidence.")
    eval_capability.add_argument(
        "--fixture",
        type=Path,
        action="append",
        help="Optional benchmark fixture to run before building capability evidence.",
    )
    eval_capability.add_argument("--fixtures-dir", type=Path, default=DEFAULT_COGNITION_FIXTURES_DIR)
    eval_capability.add_argument(
        "--benchmark-db",
        type=Path,
        help="Optional benchmark database path. Defaults to an isolated temporary database.",
    )
    eval_capability.add_argument("--json", action="store_true")

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
    if args.command == "cognition":
        return _cognition(args)
    if args.command == "review":
        return _review(args)
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
        elif _should_run_live_loop(args):
            outputs.extend(_live_loop(
                runtime,
                max_ticks=args.live_ticks or None,
                step_ms=args.step_ms,
                sleep_ms=args.live_sleep_ms,
                evaluation_logger=evaluation_logger,
                status_stream=(
                    None
                    if args.quiet_live_status
                    else (sys.stderr if args.json else sys.stdout)
                ),
            ))
        else:
            outputs.extend(_interactive(
                runtime,
                evaluation_logger=evaluation_logger,
                terminal=not args.json,
            ))
        outputs.append({"type": "shutdown", "snapshot": runtime.snapshot()})
    finally:
        runtime.close()

    if args.json:
        print(json.dumps(to_jsonable(outputs), indent=2, sort_keys=True))
    elif args.inputs:
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
    model_dialogue_realizer = _model_dialogue_realizer(args)
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
        model_dialogue_realizer=model_dialogue_realizer,
    )


def _device_discovery(args: argparse.Namespace) -> tuple[PeripheralDiscoveryService | None, list[dict[str, Any]] | None]:
    device_backend = "none" if getattr(args, "no_fake_devices", False) else args.device_backend
    if (
        getattr(args, "profile", "default") in REAL_DEVICE_AUTO_PROFILES
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
        model_dialogue_realizer=_ui_model_dialogue_realizer(args),
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
                if item["error"] == "service_managed_use_backend_check":
                    status = "service-managed"
                else:
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


def _cognition(args: argparse.Namespace) -> int:
    if args.cognition_command == "check":
        try:
            adapter = _model_runtime_adapter(args)
            result = adapter.check_model(
                args.model,
                probe=not args.no_probe,
                timeout_ms=args.timeout_ms,
            )
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        payload = result.to_dict()
        if args.json:
            print(json.dumps(to_jsonable(payload), indent=2, sort_keys=True))
        else:
            if result.ok:
                probe = "probe skipped" if not result.probe_ran else "probe ok"
                print(f"{result.backend} {result.model}: ok ({probe}, {result.latency_ms} ms)")
            else:
                print(f"{result.backend} {result.model}: {result.error_code or 'failed'}")
                if result.error:
                    print(result.error)
                if result.suggestion:
                    print(result.suggestion)
        return 0 if result.ok else 1
    return 2


def _review(args: argparse.Namespace) -> int:
    try:
        with MnemeMemory(args.db, migrations_dir=args.migrations) as memory:
            memory.init_db()
            if args.review_command == "list":
                records = memory.store.list_memory_reviews(
                    status=args.status,
                    proposal_type=args.proposal_type,
                    limit=args.limit,
                )
                payload = {"records": [record.to_dict() for record in records]}
                _print_payload(payload, json_mode=args.json)
                return 0
            if args.review_command == "show":
                record = memory.store.get_memory_review(args.review_id)
                if record is None:
                    print(f"memory review not found: {args.review_id}", file=sys.stderr)
                    return 1
                _print_payload({"record": record.to_dict()}, json_mode=args.json)
                return 0
            if args.review_command == "apply":
                record = apply_memory_review(
                    memory.store,
                    args.review_id,
                    reason=args.reason,
                    fact_payload=_optional_json_object(args.fact_data, "fact-data"),
                )
                _print_payload({"record": record.to_dict()}, json_mode=args.json)
                return 0 if record.status == "applied" else 1
            if args.review_command == "reject":
                record = reject_memory_review(
                    memory.store,
                    args.review_id,
                    reason=args.reason,
                )
                _print_payload({"record": record.to_dict()}, json_mode=args.json)
                return 0
            if args.review_command == "conflicts":
                reports = memory.store.get_fact_conflict_reports(
                    subject=args.subject,
                    predicate=args.predicate,
                    limit=args.limit,
                )
                _print_payload({"reports": to_jsonable(reports)}, json_mode=args.json)
                return 0
            if args.review_command == "explain":
                explanations = explain_memory_refs(
                    memory.store,
                    [{"memory_kind": args.memory_kind, "memory_id": args.memory_id}],
                )
                _print_payload(
                    {"explanations": [item.to_dict() for item in explanations]},
                    json_mode=args.json,
                )
                return 0
    except (KeyError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 2


def _model_runtime_adapter(args: argparse.Namespace) -> OllamaModelRuntime:
    if args.backend == "ollama":
        return OllamaModelRuntime(base_url=args.base_url)
    raise ValueError(f"unsupported cognition backend: {args.backend}")


def _model_dialogue_realizer(args: argparse.Namespace) -> ModelDialogueRealizer | None:
    backend = args.cognition_backend
    if backend == "auto":
        backend = "ollama" if args.profile == "local-cognition" else "none"
    if backend == "none":
        return None
    if backend != "ollama":
        raise ValueError(f"unsupported cognition backend: {backend}")
    return ModelDialogueRealizer(
        OllamaModelRuntime(base_url=args.cognition_base_url),
        model=args.cognition_model,
        timeout_ms=args.cognition_timeout_ms,
        max_response_chars=args.cognition_max_response_chars,
    )


def _ui_model_dialogue_realizer(args: argparse.Namespace) -> ModelDialogueRealizer | None:
    if args.cognition_profile == "none":
        return None
    if args.cognition_backend != "ollama":
        raise ValueError(f"unsupported cognition backend: {args.cognition_backend}")
    return ModelDialogueRealizer(
        OllamaModelRuntime(base_url=args.cognition_base_url),
        model=args.cognition_model,
        timeout_ms=args.cognition_timeout_ms,
        max_response_chars=args.cognition_max_response_chars,
    )


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
    if args.eval_command == "cognition":
        if args.fixture is not None:
            report = run_cognitive_benchmark(
                args.fixture,
                db_path=args.benchmark_db,
                migrations_dir=args.migrations,
            )
            payload = report.to_dict()
            exit_ok = report.total_score >= 1.0
        else:
            report = run_cognitive_benchmark_suite(
                fixtures_dir=args.fixtures_dir,
                db_path=args.benchmark_db,
                migrations_dir=args.migrations,
            )
            payload = report.to_dict()
            exit_ok = payload["total_score"] >= 1.0
        if args.json:
            print(json.dumps(to_jsonable(payload), indent=2, sort_keys=True))
        else:
            if payload.get("suite"):
                print(
                    f"cognition suite: score={payload['total_score']} "
                    f"passed={payload['passed_fixtures']}/{payload['total_fixtures']}"
                )
            else:
                print(
                    f"{payload['fixture_name']}: score={payload['total_score']} "
                    f"passed={payload['passed_steps']}/{payload['total_steps']}"
                )
        return 0 if exit_ok else 1
    if args.eval_command == "speech":
        if args.fixture is not None:
            report = run_speech_soak(
                args.fixture,
                db_path=args.benchmark_db,
                migrations_dir=args.migrations,
            )
            payload = report.to_dict()
            exit_ok = report.total_score >= 1.0
        else:
            report = run_speech_soak_suite(
                fixtures_dir=args.fixtures_dir,
                db_path=args.benchmark_db,
                migrations_dir=args.migrations,
            )
            payload = report.to_dict()
            exit_ok = payload["total_score"] >= 1.0
        if args.json:
            print(json.dumps(to_jsonable(payload), indent=2, sort_keys=True))
        else:
            if payload.get("suite"):
                print(
                    f"speech suite: score={payload['total_score']} "
                    f"passed={payload['passed_fixtures']}/{payload['total_fixtures']}"
                )
            else:
                print(
                    f"{payload['fixture_name']}: score={payload['total_score']} "
                    f"passed={payload['passed_steps']}/{payload['total_steps']}"
                )
        return 0 if exit_ok else 1
    if args.eval_command == "capability":
        if args.fixture:
            reports = [
                run_cognitive_benchmark(
                    fixture,
                    db_path=args.benchmark_db,
                    migrations_dir=args.migrations,
                ).to_dict()
                for fixture in args.fixture
            ]
        else:
            reports = run_cognitive_benchmark_suite(
                fixtures_dir=args.fixtures_dir,
                db_path=args.benchmark_db,
                migrations_dir=args.migrations,
            ).to_dict()["fixture_reports"]
        report = build_capability_report(reports)
        payload = report.to_dict()
        if args.json:
            print(json.dumps(to_jsonable(payload), indent=2, sort_keys=True))
        else:
            print(f"{payload['current_level']}: {payload['summary']}")
        return 0
    return 2


def _interactive(
    runtime: MnemeRuntime,
    *,
    evaluation_logger: EvaluationLogger | None = None,
    terminal: bool = True,
) -> list[dict[str, Any]]:
    outputs = []
    if terminal:
        snapshot = runtime.snapshot()
        devices = snapshot.get("devices") or {}
        counts = devices.get("available_counts", {})
        print("Mneme virtual head. Type a message and press Enter. Type /quit to exit.", file=sys.stderr)
        print(
            "Mode: typed terminal input. For continuous mic/camera ticking use "
            "`mneme run --live` or `mneme run --profile local-lab --live`.",
            file=sys.stderr,
        )
        if isinstance(counts, dict):
            print(
                f"devices camera={counts.get('camera', 0)} "
                f"microphone={counts.get('microphone', 0)} "
                f"speaker={counts.get('speaker', 0)}",
                file=sys.stderr,
            )
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
        tick = runtime.tick()
        outputs.append({"type": "tick", "result": tick.to_dict()})
        if terminal:
            _print_turn(result_dict)
    return outputs


def _live_loop(
    runtime: MnemeRuntime,
    *,
    max_ticks: int | None,
    step_ms: int,
    sleep_ms: int,
    evaluation_logger: EvaluationLogger | None = None,
    status_stream: Any = DEFAULT_STATUS_STREAM,
) -> list[dict[str, Any]]:
    if max_ticks is not None and max_ticks < 1:
        raise ValueError("max_ticks must be positive when provided")
    if step_ms < 1:
        raise ValueError("step_ms must be positive")
    if sleep_ms < 0:
        raise ValueError("sleep_ms must be non-negative")
    if status_stream is DEFAULT_STATUS_STREAM:
        status_stream = sys.stdout
    outputs: list[dict[str, Any]] = []
    if status_stream is not None:
        print("Mneme live loop is running. Press Ctrl-C to stop.", file=status_stream, flush=True)
        print(
            "Live status shows perception, attention, speech, and generated responses as they happen.",
            file=status_stream,
            flush=True,
        )
    ticks = 0
    try:
        while max_ticks is None or ticks < max_ticks:
            result = runtime.tick(advance_ms=step_ms)
            result_dict = result.to_dict()
            outputs.append({"type": "live_tick", "result": result_dict})
            if evaluation_logger is not None:
                for utterance in result_dict.get("utterances", []):
                    if isinstance(utterance, dict):
                        evaluation_logger.record_turn(
                            input_text=_latest_user_turn_text(result_dict),
                            result=result_dict,
                        )
                        break
            if status_stream is not None:
                _print_live_tick(result_dict, stream=status_stream)
            ticks += 1
            if max_ticks is None and sleep_ms:
                time.sleep(sleep_ms / 1000)
    except KeyboardInterrupt:
        if status_stream is not None:
            print("\nMneme live loop stopped.", file=status_stream, flush=True)
    return outputs


def _should_run_live_loop(args: argparse.Namespace) -> bool:
    if args.live or args.live_ticks > 0:
        return True
    if args.profile in {"local-speech", "local-vision", "local-lab"}:
        return True
    if args.camera_command or args.speech_command:
        return True
    return False


def _print_payload(payload: dict[str, Any], *, json_mode: bool) -> None:
    if json_mode:
        print(json.dumps(to_jsonable(payload), indent=2, sort_keys=True))
        return
    print(json.dumps(to_jsonable(payload), indent=2, sort_keys=True))


def _optional_json_object(raw: str | None, field_name: str) -> dict[str, Any] | None:
    if raw is None:
        return None
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return value


def _print_terminal(outputs: list[dict[str, Any]]) -> None:
    for item in outputs:
        if item["type"] == "startup":
            counts = item["devices"]["available_counts"]
            print(f"devices camera={counts['camera']} microphone={counts['microphone']} speaker={counts['speaker']}")
        elif item["type"] == "turn":
            _print_turn(item["result"])
        elif item["type"] == "live_tick":
            _print_live_tick(item["result"])
        elif item["type"] == "shutdown":
            executive = item["snapshot"].get("executive") or {}
            print(f"state: {executive.get('intent_type', 'idle')}")


def _print_turn(result: dict[str, Any], *, stream: Any | None = None) -> None:
    stream = sys.stdout if stream is None else stream
    for utterance in result.get("utterances", []):
        if isinstance(utterance, dict):
            print(f"mneme: {utterance.get('text', '')}", file=stream, flush=True)


def _print_live_tick(result: dict[str, Any], *, stream: Any | None = None) -> None:
    stream = sys.stdout if stream is None else stream
    _print_turn(result, stream=stream)
    for line in _live_status_lines(result):
        print(line, file=stream, flush=True)


def _live_status_lines(result: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    events = result.get("events", [])
    if isinstance(events, list):
        lines.extend(_vision_status_lines(events))
        lines.extend(_speech_event_lines(events))
    snapshot = result.get("snapshot", {})
    if not isinstance(snapshot, dict):
        return lines
    lines.extend(_speech_loop_status_lines(snapshot))
    attention_line = _attention_status_line(snapshot)
    if attention_line is not None:
        lines.append(attention_line)
    presence_line = _presence_status_line(snapshot)
    if presence_line is not None:
        lines.append(presence_line)
    if not lines:
        lines.append("live: tick processed; no new perception or response")
    return _dedupe_preserve_order(lines)


def _vision_status_lines(events: list[Any]) -> list[str]:
    lines: list[str] = []
    for event in events:
        if not isinstance(event, dict) or event.get("kind") != "perception_observation":
            continue
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            continue
        observation_type = payload.get("observation_type")
        if observation_type == "camera_frame":
            detections = payload.get("detections", [])
            count = len(detections) if isinstance(detections, list) else 0
            label = payload.get("device_label") or payload.get("device_id") or "camera"
            metadata = payload.get("metadata", {})
            detector = metadata.get("face_detector") if isinstance(metadata, dict) else None
            if count:
                lines.append(f"vision: frame from {label}; detected {count} person candidate(s)")
            elif detector:
                lines.append(f"vision: frame from {label}; no person detected")
            else:
                lines.append(
                    f"vision: frame from {label}; person detection is off "
                    "(add --face-backend mediapipe)"
                )
        elif observation_type == "person_seen":
            label = payload.get("label") or payload.get("person_id") or "person"
            confidence = event.get("confidence")
            suffix = f" confidence={confidence:.2f}" if isinstance(confidence, (int, float)) else ""
            lines.append(f"vision: person seen: {label}{suffix}")
    return lines


def _speech_event_lines(events: list[Any]) -> list[str]:
    lines: list[str] = []
    for event in events:
        if not isinstance(event, dict) or event.get("kind") != "perception_observation":
            continue
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            continue
        if payload.get("observation_type") != "speech_transcript":
            continue
        speaker = payload.get("speaker", "speaker")
        text = str(payload.get("utterance") or payload.get("transcript") or "").strip()
        if text:
            lines.append(f"speech: heard {speaker}: {_short_console_text(text)}")
    return lines


def _speech_loop_status_lines(snapshot: dict[str, Any]) -> list[str]:
    speech_loop = snapshot.get("speech_loop", {})
    if not isinstance(speech_loop, dict):
        return []
    report = speech_loop.get("latest_capture_report")
    if not isinstance(report, dict):
        return []
    status = report.get("status")
    if status == "transcribed":
        latency = speech_loop.get("latest_asr_latency_ms")
        return [f"speech: transcribed in {latency} ms" if isinstance(latency, int) else "speech: transcribed"]
    if status == "no_speech":
        return ["speech: listening; no speech detected"]
    if status == "no_microphone":
        return ["speech: no microphone available"]
    if status == "capture_error":
        reason = str(speech_loop.get("latest_failure_reason") or "capture_error")
        return [f"speech: ASR/capture failed: {reason}{_speech_failure_hint(reason)}"]
    return []


def _attention_status_line(snapshot: dict[str, Any]) -> str | None:
    attention = snapshot.get("attention", {})
    if not isinstance(attention, dict):
        return None
    target = attention.get("active_target_id")
    reason = attention.get("reason")
    if isinstance(target, str) and target:
        return f"attention: {target} ({reason or 'active'})"
    return None


def _presence_status_line(snapshot: dict[str, Any]) -> str | None:
    world = snapshot.get("world", {})
    presence = snapshot.get("presence", {})
    avatar = presence.get("avatar", {}) if isinstance(presence, dict) else {}
    persons = world.get("persons", []) if isinstance(world, dict) else []
    mode = avatar.get("mode") if isinstance(avatar, dict) else None
    gaze = avatar.get("gaze_target") if isinstance(avatar, dict) else None
    if isinstance(persons, list) and persons:
        latest = persons[-1]
        if isinstance(latest, dict):
            label = latest.get("label") or latest.get("person_id") or "person"
            return f"presence: {mode or 'active'}; tracking {label}"
    if isinstance(mode, str) and mode:
        return f"presence: {mode}; gaze={gaze or 'none'}"
    return None


def _speech_failure_hint(reason: str) -> str:
    lowered = reason.lower()
    if "hfvalidationerror" in lowered or "repo id" in lowered:
        return " (check --asr-model path; run `mneme models verify --profile local-speech --json`)"
    if "importerror" in lowered or "optional dependency" in lowered:
        return " (install the local speech optional extras)"
    if "permission" in lowered:
        return " (check microphone permission)"
    return ""


def _dedupe_preserve_order(lines: list[str]) -> list[str]:
    seen: set[str] = set()
    results: list[str] = []
    for line in lines:
        if line in seen:
            continue
        seen.add(line)
        results.append(line)
    return results


def _short_console_text(text: str, *, limit: int = 96) -> str:
    clean = " ".join(text.split())
    if len(clean) <= limit:
        return clean
    return f"{clean[: limit - 3]}..."


def _latest_user_turn_text(result: dict[str, Any]) -> str:
    snapshot = result.get("snapshot", {})
    working = snapshot.get("working_memory", {}) if isinstance(snapshot, dict) else {}
    turns = working.get("recent_dialogue_turns", []) if isinstance(working, dict) else []
    if isinstance(turns, list) and turns:
        latest = turns[-1]
        if isinstance(latest, dict):
            text = latest.get("text")
            if isinstance(text, str):
                return text
    return ""


if __name__ == "__main__":
    raise SystemExit(main())
