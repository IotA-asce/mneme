from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from android_brain_memory import ConsolidationOptions, MemoryStore, consolidate_once


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / ".local" / "android_brain_memory.sqlite3"
DEFAULT_MIGRATIONS = ROOT / "storage" / "migrations"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one deterministic memory consolidation pass.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite database path.")
    parser.add_argument(
        "--migrations",
        type=Path,
        default=DEFAULT_MIGRATIONS,
        help="Migration directory.",
    )
    parser.add_argument("--max-episodes", type=int, default=100)
    parser.add_argument("--min-repetition", type=int, default=3)
    parser.add_argument("--close-time-window-s", type=int, default=3600)
    parser.add_argument(
        "--no-decay-metadata",
        action="store_true",
        help="Do not write meta-memory decay/downranking metadata.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    store = MemoryStore(args.db)
    store.run_migrations(args.migrations)
    report = consolidate_once(
        store,
        ConsolidationOptions(
            max_episodes=args.max_episodes,
            min_repetition=args.min_repetition,
            close_time_window_s=args.close_time_window_s,
            update_decay_metadata=not args.no_decay_metadata,
        ),
    )
    store.close()
    print(json.dumps(asdict(report), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
