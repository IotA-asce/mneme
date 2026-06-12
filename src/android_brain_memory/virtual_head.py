from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any

from .engine import DEFAULT_DB, DEFAULT_MIGRATIONS, to_jsonable
from .live_perception import (
    CommandFrameCaptureBackend,
    CommandSpeechRecognitionBackend,
    PerceptionRetentionPolicy,
)
from .peripherals import PeripheralDiscoveryService, RealPeripheralBackend, default_virtual_head_devices
from .presence import CommandSpeechOutputBackend
from .runtime_loop import MnemeRuntime, RuntimeClock


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mneme", description="Mneme virtual head runtime.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite database path.")
    parser.add_argument(
        "--migrations",
        type=Path,
        default=DEFAULT_MIGRATIONS,
        help="Directory containing SQLite migrations.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Run the terminal virtual head.")
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
        "--speech-command",
        help="Local command template that prints transcript text or JSON. Enables live speech.",
    )
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
        "--voice",
        help="Speech voice label to use and persist in procedural memory.",
    )
    run.add_argument(
        "--tts-timeout-ms",
        type=int,
        default=10_000,
        help="Timeout for local TTS command.",
    )
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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        return _run(args)
    parser.error(f"unsupported command: {args.command}")
    return 2


def _run(args: argparse.Namespace) -> int:
    device_backend = "none" if args.no_fake_devices else args.device_backend
    discovery_service = None
    fake_devices = None
    if device_backend == "real":
        discovery_service = PeripheralDiscoveryService(
            backend=RealPeripheralBackend(timeout_ms=args.device_scan_timeout_ms),
        )
    else:
        fake_devices = [] if device_backend == "none" else [
            device.to_dict() for device in default_virtual_head_devices()
        ]
    retention = PerceptionRetentionPolicy(
        frame_archive_dir=args.frame_archive_dir,
        max_archived_frames=args.max_archived_frames,
        max_frame_archive_bytes=args.max_frame_archive_bytes,
        max_frame_age_ms=args.max_frame_age_ms,
    )
    camera_backend = (
        CommandFrameCaptureBackend(shlex.split(args.camera_command))
        if args.camera_command
        else None
    )
    speech_backend = (
        CommandSpeechRecognitionBackend(shlex.split(args.speech_command))
        if args.speech_command
        else None
    )
    speech_output_backend = (
        CommandSpeechOutputBackend(
            shlex.split(args.tts_command),
            timeout_ms=args.tts_timeout_ms,
            default_voice=args.voice,
        )
        if args.tts_command
        else None
    )
    runtime = MnemeRuntime(
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
        enable_virtual_presence=not args.no_virtual_presence,
        virtual_speech_duration_ms=args.virtual_speech_duration_ms,
    )
    outputs: list[dict[str, Any]] = []
    try:
        startup = runtime.start()
        outputs.append({"type": "startup", "devices": startup.to_dict()})
        if args.inputs:
            now = args.start_ms
            for text in args.inputs:
                result = runtime.process_user_utterance(text, timestamp=now)
                outputs.append({"type": "turn", "input": text, "result": result.to_dict()})
                now += args.step_ms
                outputs.append({"type": "tick", "result": runtime.tick(advance_ms=args.step_ms).to_dict()})
        else:
            outputs.extend(_interactive(runtime))
        outputs.append({"type": "shutdown", "snapshot": runtime.snapshot()})
    finally:
        runtime.close()

    if args.json:
        print(json.dumps(to_jsonable(outputs), indent=2, sort_keys=True))
    else:
        _print_terminal(outputs)
    return 0


def _interactive(runtime: MnemeRuntime) -> list[dict[str, Any]]:
    outputs = []
    print("Mneme virtual head. Type /quit to exit.", file=sys.stderr)
    for raw in sys.stdin:
        text = raw.strip()
        if not text:
            continue
        if text in {"/quit", "/exit"}:
            break
        result = runtime.process_user_utterance(text)
        outputs.append({"type": "turn", "input": text, "result": result.to_dict()})
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
