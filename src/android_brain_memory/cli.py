from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .consolidation import ConsolidationOptions
from .engine import DEFAULT_DB, DEFAULT_MIGRATIONS, MnemeMemory, to_jsonable
from .models import MemoryQuery, MemoryStatus, SourceType, Speakability
from .storage import PROVENANCE_MEMORY_KINDS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mneme-memory",
        description="Mneme local memory API CLI.",
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite database path.")
    parser.add_argument(
        "--migrations",
        type=Path,
        default=DEFAULT_MIGRATIONS,
        help="Directory containing SQLite migrations.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db", help="Initialize or migrate the SQLite database.")

    remember = subparsers.add_parser(
        "remember-candidate",
        help="Score and optionally store a candidate.",
    )
    _add_json_input(remember, required=True)
    remember.add_argument("--config", type=Path, help="Optional salience config YAML path.")
    remember.add_argument("--no-store-trace", action="store_true", help="Score without storing a raw trace.")
    remember.add_argument("--episode", action="store_true", help="Also encode and store an episode.")
    remember.add_argument("--episode-id")
    remember.add_argument("--start-ts", type=int)
    remember.add_argument("--end-ts", type=int)
    remember.add_argument("--participant", action="append", dest="participants")
    remember.add_argument("--object", action="append", dest="objects")
    remember.add_argument("--context-json", help="Additional episode context JSON object.")
    remember.add_argument("--source-id")
    remember.add_argument(
        "--speakability",
        choices=_enum_values(Speakability),
        default=Speakability.NORMAL.value,
    )
    remember.add_argument("--notes")

    add_episode = subparsers.add_parser("add-episode", help="Store an episode from JSON.")
    _add_json_input(add_episode, required=True)
    add_episode.add_argument(
        "--source-type",
        choices=_enum_values(SourceType),
        default=SourceType.SYSTEM_GENERATED.value,
    )
    add_episode.add_argument("--source-id")
    add_episode.add_argument(
        "--speakability",
        choices=_enum_values(Speakability),
        default=Speakability.NORMAL.value,
    )
    add_episode.add_argument("--notes")

    add_fact = subparsers.add_parser("add-fact", help="Upsert a fact from JSON.")
    _add_json_input(add_fact, required=True)
    add_fact.add_argument("--source-id")
    add_fact.add_argument(
        "--speakability",
        choices=_enum_values(Speakability),
        default=Speakability.NORMAL.value,
    )
    add_fact.add_argument("--notes")

    retrieve = subparsers.add_parser("retrieve", help="Retrieve memory using text or structured filters.")
    _add_json_input(retrieve, required=False)
    retrieve.add_argument("--query-text", default="")
    retrieve.add_argument("--requester", default="cli")
    retrieve.add_argument("--query-type", default="general")
    retrieve.add_argument("--entity", action="append", dest="entities")
    retrieve.add_argument("--tag", action="append", dest="tags")
    retrieve.add_argument("--fact-subject", default="")
    retrieve.add_argument("--fact-predicate", default="")
    retrieve.add_argument("--fact-object-text", default="")
    retrieve.add_argument("--fact-source-type", choices=_enum_values(SourceType))
    retrieve.add_argument("--fact-status", choices=_enum_values(MemoryStatus))
    retrieve.add_argument("--max-results", type=int, default=5)
    retrieve.add_argument("--no-episodes", action="store_true")
    retrieve.add_argument("--no-facts", action="store_true")
    retrieve.add_argument("--no-summaries", action="store_true")
    retrieve.add_argument("--trusted-internal", action="store_true")
    retrieve.add_argument("--include-internal", action="store_true")

    consolidate = subparsers.add_parser("consolidate-once", help="Run one deterministic consolidation pass.")
    consolidate.add_argument("--max-episodes", type=int, default=100)
    consolidate.add_argument("--min-repetition", type=int, default=3)
    consolidate.add_argument("--close-time-window-s", type=int, default=3600)
    consolidate.add_argument("--no-decay-metadata", action="store_true")

    subparsers.add_parser("inspect-db", help="Return database counts and recent summary metadata.")

    inspect_provenance = subparsers.add_parser(
        "inspect-provenance",
        help="Return the stored provenance chain for a memory.",
    )
    inspect_provenance.add_argument("--memory-id", required=True)
    inspect_provenance.add_argument(
        "--memory-kind",
        required=True,
        choices=list(PROVENANCE_MEMORY_KINDS),
    )

    inspect_decay = subparsers.add_parser(
        "inspect-decay",
        help="List meta-memory records carrying decay metadata.",
    )
    inspect_decay.add_argument("--limit", type=int, default=50)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    with MnemeMemory(args.db, migrations_dir=args.migrations) as memory:
        if args.command == "init-db":
            applied = memory.init_db()
            _emit(
                {
                    "command": args.command,
                    "db_path": str(memory.db_path),
                    "applied_migrations": applied,
                }
            )
            return 0

        applied = memory.init_db()

        if args.command == "remember-candidate":
            result = memory.remember_candidate(
                _load_json_payload(args),
                config_path=args.config,
                store_trace=not args.no_store_trace,
                create_episode=args.episode,
                episode_id=args.episode_id,
                start_ts=args.start_ts,
                end_ts=args.end_ts,
                participants=args.participants,
                objects=args.objects,
                context=_parse_optional_json_object(args.context_json, "context-json"),
                source_id=args.source_id,
                speakability=args.speakability,
                notes=args.notes,
            )
            _emit({"command": args.command, "migrations_applied": applied, "result": result})
            return 0

        if args.command == "add-episode":
            episode = memory.add_episode(
                _load_json_payload(args),
                source_type=args.source_type,
                source_id=args.source_id,
                speakability=args.speakability,
                notes=args.notes,
            )
            _emit({"command": args.command, "migrations_applied": applied, "episode": episode})
            return 0

        if args.command == "add-fact":
            result = memory.add_fact(
                _load_json_payload(args),
                source_id=args.source_id,
                speakability=args.speakability,
                notes=args.notes,
            )
            _emit({"command": args.command, "migrations_applied": applied, "result": result})
            return 0

        if args.command == "retrieve":
            bundle = memory.retrieve(_query_from_args(args))
            _emit({"command": args.command, "migrations_applied": applied, "bundle": bundle})
            return 0

        if args.command == "consolidate-once":
            report = memory.consolidate_once(
                ConsolidationOptions(
                    max_episodes=args.max_episodes,
                    min_repetition=args.min_repetition,
                    close_time_window_s=args.close_time_window_s,
                    update_decay_metadata=not args.no_decay_metadata,
                )
            )
            _emit({"command": args.command, "migrations_applied": applied, "report": report})
            return 0

        if args.command == "inspect-db":
            _emit(
                {
                    "command": args.command,
                    "migrations_applied": applied,
                    "inspection": memory.inspect_db(),
                }
            )
            return 0

        if args.command == "inspect-provenance":
            chain = memory.store.get_provenance_chain(args.memory_id, args.memory_kind)
            _emit({"command": args.command, "migrations_applied": applied, "chain": chain})
            return 0

        if args.command == "inspect-decay":
            records = memory.store.get_meta_memory_with_decay(limit=args.limit)
            _emit({"command": args.command, "migrations_applied": applied, "records": records})
            return 0

    parser.error(f"unsupported command: {args.command}")
    return 2


def _add_json_input(parser: argparse.ArgumentParser, *, required: bool) -> None:
    group = parser.add_mutually_exclusive_group(required=required)
    group.add_argument("--data", help="JSON object payload.")
    group.add_argument("--file", type=Path, help="Path to a JSON object payload, or '-' for stdin.")


def _load_json_payload(args: argparse.Namespace) -> dict[str, Any]:
    if getattr(args, "data", None) is not None:
        raw = args.data
    elif getattr(args, "file", None) is not None:
        if str(args.file) == "-":
            raw = sys.stdin.read()
        else:
            raw = args.file.read_text(encoding="utf-8")
    else:
        raise ValueError("expected --data or --file")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("JSON payload must be an object")
    return value


def _query_from_args(args: argparse.Namespace) -> MemoryQuery:
    if getattr(args, "data", None) is not None or getattr(args, "file", None) is not None:
        return MemoryQuery.from_dict(_load_json_payload(args))
    return MemoryQuery(
        query_text=args.query_text,
        requester=args.requester,
        query_type=args.query_type,
        entities=args.entities or [],
        tags=args.tags or [],
        fact_subject=args.fact_subject,
        fact_predicate=args.fact_predicate,
        fact_object_text=args.fact_object_text,
        fact_source_type=args.fact_source_type,
        fact_status=args.fact_status,
        max_results=args.max_results,
        include_episodes=not args.no_episodes,
        include_facts=not args.no_facts,
        include_summaries=not args.no_summaries,
        trusted_internal=args.trusted_internal,
        include_internal=args.include_internal,
    )


def _parse_optional_json_object(value: str | None, label: str) -> dict[str, Any] | None:
    if value is None:
        return None
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError(f"{label} must be a JSON object")
    return parsed


def _emit(payload: Any) -> None:
    print(json.dumps(to_jsonable(payload), indent=2, sort_keys=True))


def _enum_values(enum_type: type[SourceType] | type[MemoryStatus] | type[Speakability]) -> list[str]:
    return [item.value for item in enum_type]


if __name__ == "__main__":
    raise SystemExit(main())
