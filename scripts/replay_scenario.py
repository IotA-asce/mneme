from __future__ import annotations

import argparse
import json
from pathlib import Path

from android_brain_memory import EventBus, ScenarioReplayRunner, SensoryEchoBuffer, WorkingMemory


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay a deterministic Mneme scenario fixture.")
    parser.add_argument("scenario", type=Path, help="Path to a YAML or JSON scenario file.")
    parser.add_argument("--echo-capacity", type=int, default=128)
    parser.add_argument("--echo-ttl-ms", type=int, default=5_000)
    parser.add_argument("--max-dialogue-turns", type=int, default=8)
    parser.add_argument("--max-event-refs", type=int, default=16)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    clock = {"now": 0}
    bus = EventBus(clock=lambda: clock["now"])
    echo = SensoryEchoBuffer(
        capacity=args.echo_capacity,
        default_ttl_ms=args.echo_ttl_ms,
        clock=lambda: clock["now"],
    )
    working = WorkingMemory(
        max_dialogue_turns=args.max_dialogue_turns,
        max_event_refs=args.max_event_refs,
        clock=lambda: clock["now"],
    )
    echo.attach_to_bus(bus)
    working.attach_to_bus(bus)
    result = ScenarioReplayRunner(bus).replay_file(args.scenario)
    if result.events:
        clock["now"] = max(event.timestamp for event in result.events)
    output = {
        "replay": result.to_dict(),
        "echo": echo.to_dict(now_ms=clock["now"]),
        "working_memory": working.to_dict(created_ts=clock["now"]),
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
