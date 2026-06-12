from __future__ import annotations

import json
import time
from pathlib import Path

from android_brain_memory import MnemeMemory
from android_brain_memory.cli import main as cli_main
from android_brain_memory.models import Episode, Fact, MemoryQuery, SourceType
from android_brain_memory.runtime import EventBus, RuntimeEventKind


MIGRATIONS = Path(__file__).resolve().parents[1] / "storage" / "migrations"


class FixedClock:
    def __init__(self, now_ms: int) -> None:
        self.now_ms = now_ms

    def __call__(self) -> int:
        return self.now_ms


def open_engine(tmp_path, bus=None) -> MnemeMemory:
    engine = MnemeMemory(
        tmp_path / "memory.sqlite3",
        migrations_dir=MIGRATIONS,
        event_bus=bus,
    )
    engine.init_db()
    return engine


def seed_fact(engine: MnemeMemory, fact_id: str, value: str, source_type=SourceType.USER_CONFIRMED):
    return engine.add_fact(
        Fact(
            fact_id=fact_id,
            subject="user",
            predicate="likes",
            object_value={"value": value},
            confidence=0.9,
            source_type=source_type,
        )
    )


def test_retrieve_publishes_lifecycle_event_with_ids_not_content(tmp_path):
    bus = EventBus(clock=FixedClock(1000))
    engine = open_engine(tmp_path, bus=bus)
    seed_fact(engine, "fact_beverage", "tea")

    bundle = engine.retrieve(MemoryQuery(query_text="likes", requester="executive"))

    events = bus.history(kinds=[RuntimeEventKind.MEMORY_LIFECYCLE])
    retrieval_events = [
        event for event in events if event.payload["lifecycle_stage"] == "retrieval"
    ]
    assert len(retrieval_events) == 1
    payload = retrieval_events[0].payload
    assert payload["query_id"] == bundle.query_id
    assert payload["query_text"] == "likes"
    assert payload["requester"] == "executive"
    assert payload["fact_ids"] == ["fact_beverage"]
    assert payload["episode_ids"] == []
    assert payload["summary_ids"] == []
    assert payload["warnings"] == bundle.warnings
    assert "facts" not in payload
    assert "tea" not in json.dumps(payload)  # memory content never leaks into events
    engine.close()


def test_conflicting_fact_upsert_publishes_conflict_event(tmp_path):
    bus = EventBus(clock=FixedClock(1000))
    engine = open_engine(tmp_path, bus=bus)
    seed_fact(engine, "fact_a", "tea")

    result = seed_fact(engine, "fact_b", "coffee")

    assert result.conflict_report is not None
    conflict_events = [
        event
        for event in bus.history(kinds=[RuntimeEventKind.MEMORY_LIFECYCLE])
        if event.payload["lifecycle_stage"] == "conflict"
    ]
    assert len(conflict_events) == 1
    payload = conflict_events[0].payload
    assert payload["subject"] == "user"
    assert payload["predicate"] == "likes"
    assert set(payload["fact_ids"]) == {"fact_a", "fact_b"}
    engine.close()


def test_engine_without_bus_publishes_nothing_and_works(tmp_path):
    engine = open_engine(tmp_path)
    seed_fact(engine, "fact_tea", "tea")

    bundle = engine.retrieve(MemoryQuery(query_text="likes"))

    assert [fact.fact_id for fact in bundle.facts] == ["fact_tea"]
    engine.close()


def test_get_meta_memory_with_decay_lists_only_decay_records(tmp_path):
    engine = open_engine(tmp_path)
    now = int(time.time())
    engine.add_episode(
        Episode(
            episode_id="ep_decayed",
            start_ts=now,
            end_ts=now + 1,
            summary="decayed episode",
            context={},
            salience=0.5,
            confidence=0.9,
        )
    )
    engine.add_episode(
        Episode(
            episode_id="ep_fresh",
            start_ts=now,
            end_ts=now + 1,
            summary="fresh episode",
            context={},
            salience=0.5,
            confidence=0.9,
        )
    )
    engine.store.update_decay_metadata(
        "ep_decayed",
        "episode",
        {"policy": "covered_by_summary", "accessibility": "downrank_candidate"},
    )

    records = engine.store.get_meta_memory_with_decay(limit=10)

    assert [record.memory_id for record in records] == ["ep_decayed"]
    engine.close()


def run_cli(tmp_path, capsys, *argv: str) -> dict:
    db = str(tmp_path / "memory.sqlite3")
    code = cli_main(["--db", db, *argv])
    assert code == 0
    return json.loads(capsys.readouterr().out)


def test_cli_inspect_provenance_outputs_chain(tmp_path, capsys):
    engine = open_engine(tmp_path)
    now = int(time.time())
    trace_id = engine.store.store_raw_trace(
        summary="trace",
        payload={},
        source_type=SourceType.USER_CONFIRMED,
        confidence=0.9,
        salience=0.8,
    )
    engine.add_episode(
        Episode(
            episode_id="ep_chain",
            start_ts=now,
            end_ts=now + 1,
            summary="episode",
            context={},
            salience=0.8,
            confidence=0.9,
        ),
        supporting_memory_ids=[trace_id],
    )
    engine.close()

    output = run_cli(
        tmp_path,
        capsys,
        "inspect-provenance",
        "--memory-id",
        "ep_chain",
        "--memory-kind",
        "episode",
    )

    chain = output["chain"]
    assert chain["memory_id"] == "ep_chain"
    assert any(node["memory_kind"] == "raw_trace" for node in chain["nodes"])


def test_cli_inspect_decay_lists_decay_records(tmp_path, capsys):
    engine = open_engine(tmp_path)
    now = int(time.time())
    engine.add_episode(
        Episode(
            episode_id="ep_decayed",
            start_ts=now,
            end_ts=now + 1,
            summary="decayed episode",
            context={},
            salience=0.5,
            confidence=0.9,
        )
    )
    engine.store.update_decay_metadata(
        "ep_decayed",
        "episode",
        {"policy": "covered_by_summary", "accessibility": "downrank_candidate"},
    )
    engine.close()

    output = run_cli(tmp_path, capsys, "inspect-decay", "--limit", "10")

    records = output["records"]
    assert len(records) == 1
    assert records[0]["memory_id"] == "ep_decayed"
    assert records[0]["provenance"]["decay"]["policy"] == "covered_by_summary"
