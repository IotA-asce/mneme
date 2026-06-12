from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .engine import DEFAULT_DB, DEFAULT_MIGRATIONS, to_jsonable
from .peripherals import default_virtual_head_devices
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

    run = subparsers.add_parser("run", help="Run the Stage 3 terminal virtual head.")
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
        help="Start with no discovered fake peripherals.",
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
    fake_devices = [] if args.no_fake_devices else [device.to_dict() for device in default_virtual_head_devices()]
    runtime = MnemeRuntime(
        db_path=args.db,
        migrations_dir=args.migrations,
        clock=RuntimeClock(args.start_ms),
        fake_devices=fake_devices,
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
