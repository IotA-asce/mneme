from __future__ import annotations

import time
from pathlib import Path

import pytest

from android_brain_memory.models import Episode, Fact, MemoryStatus, SourceType
from android_brain_memory.storage import (
    FactSupportRecord,
    MemoryStore,
    RawTraceRecord,
)


MIGRATIONS = Path(__file__).resolve().parents[1] / "storage" / "migrations"


def open_migrated_store(tmp_path) -> MemoryStore:
    store = MemoryStore(tmp_path / "memory.sqlite3")
    store.run_migrations(MIGRATIONS)
    return store


def make_episode(episode_id: str, start_ts: int, end_ts: int, **overrides) -> Episode:
    payload = {
        "episode_id": episode_id,
        "start_ts": start_ts,
        "end_ts": end_ts,
        "summary": overrides.pop("summary", f"episode {episode_id}"),
        "context": overrides.pop("context", {}),
        "salience": overrides.pop("salience", 0.6),
        "confidence": overrides.pop("confidence", 0.9),
    }
    payload.update(overrides)
    return Episode(**payload)


def test_get_raw_trace_round_trip(tmp_path):
    store = open_migrated_store(tmp_path)
    trace_id = store.store_raw_trace(
        summary="User waved at the robot.",
        payload={"gesture": "wave"},
        source_type=SourceType.SENSOR_OBSERVED,
        confidence=0.8,
        salience=0.4,
        source_id="vision_worker",
    )

    record = store.get_raw_trace(trace_id)

    assert isinstance(record, RawTraceRecord)
    assert record.trace_id == trace_id
    assert record.summary == "User waved at the robot."
    assert record.payload == {"gesture": "wave"}
    assert record.source_type == SourceType.SENSOR_OBSERVED
    assert record.source_id == "vision_worker"
    assert record.confidence == 0.8
    assert record.salience == 0.4
    assert record.created_ts > 0


def test_get_raw_trace_missing_returns_none(tmp_path):
    store = open_migrated_store(tmp_path)
    assert store.get_raw_trace("trace_missing") is None


def test_get_recent_raw_traces_orders_newest_first_and_filters_source(tmp_path):
    store = open_migrated_store(tmp_path)
    base = int(time.time())
    first = store.store_raw_trace(
        summary="first",
        payload={},
        source_type=SourceType.SENSOR_OBSERVED,
        confidence=0.5,
        salience=0.1,
        created_ts=base - 20,
    )
    second = store.store_raw_trace(
        summary="second",
        payload={},
        source_type=SourceType.USER_CONFIRMED,
        confidence=0.5,
        salience=0.1,
        created_ts=base - 10,
    )
    third = store.store_raw_trace(
        summary="third",
        payload={},
        source_type=SourceType.SENSOR_OBSERVED,
        confidence=0.5,
        salience=0.1,
        created_ts=base,
    )

    traces = store.get_recent_raw_traces(limit=10)
    assert [trace.trace_id for trace in traces] == [third, second, first]

    limited = store.get_recent_raw_traces(limit=2)
    assert [trace.trace_id for trace in limited] == [third, second]

    sensor_only = store.get_recent_raw_traces(limit=10, source_type=SourceType.SENSOR_OBSERVED)
    assert [trace.trace_id for trace in sensor_only] == [third, first]


def test_get_fact_support_returns_links_directly(tmp_path):
    store = open_migrated_store(tmp_path)
    now = int(time.time())
    store.store_episode(make_episode("ep_a", now, now + 1))
    store.store_episode(make_episode("ep_b", now + 2, now + 3))
    store.upsert_fact(
        Fact(
            fact_id="fact_supported",
            subject="user",
            predicate="likes",
            object_value={"value": "tea"},
            confidence=0.9,
            source_type=SourceType.USER_CONFIRMED,
            supporting_episode_ids=["ep_b", "ep_a"],
        )
    )

    links = store.get_fact_support("fact_supported")

    assert all(isinstance(link, FactSupportRecord) for link in links)
    assert [(link.fact_id, link.episode_id, link.weight) for link in links] == [
        ("fact_supported", "ep_a", 1.0),
        ("fact_supported", "ep_b", 1.0),
    ]
    assert store.get_fact_support("fact_missing") == []


def test_get_facts_for_episode_reverse_lookup(tmp_path):
    store = open_migrated_store(tmp_path)
    now = int(time.time())
    store.store_episode(make_episode("ep_shared", now, now + 1))
    for fact_id in ("fact_b", "fact_a"):
        store.upsert_fact(
            Fact(
                fact_id=fact_id,
                subject="user",
                predicate=f"predicate_{fact_id}",
                object_value={"value": fact_id},
                confidence=0.7,
                source_type=SourceType.MODEL_INFERRED,
                supporting_episode_ids=["ep_shared"],
            )
        )

    facts = store.get_facts_for_episode("ep_shared")

    assert [fact.fact_id for fact in facts] == ["fact_a", "fact_b"]
    assert store.get_facts_for_episode("ep_missing") == []


def test_get_episodes_in_window_uses_overlap_semantics(tmp_path):
    store = open_migrated_store(tmp_path)
    store.store_episode(make_episode("ep_before", 100, 110))
    store.store_episode(make_episode("ep_overlap_start", 150, 210))
    store.store_episode(make_episode("ep_inside", 220, 230))
    store.store_episode(make_episode("ep_overlap_end", 290, 350))
    store.store_episode(make_episode("ep_after", 400, 410))

    episodes = store.get_episodes_in_window(200, 300)

    assert [episode.episode_id for episode in episodes] == [
        "ep_overlap_start",
        "ep_inside",
        "ep_overlap_end",
    ]


def test_get_episodes_in_window_validates_range_and_limit(tmp_path):
    store = open_migrated_store(tmp_path)
    with pytest.raises(ValueError):
        store.get_episodes_in_window(300, 200)
    with pytest.raises(ValueError):
        store.get_episodes_in_window(100, 200, limit=0)


def test_provenance_chain_traces_fact_to_episode_to_raw_trace(tmp_path):
    store = open_migrated_store(tmp_path)
    now = int(time.time())
    trace_id = store.store_raw_trace(
        summary="User said they like tea.",
        payload={"utterance": "I like tea"},
        source_type=SourceType.USER_CONFIRMED,
        confidence=0.95,
        salience=0.8,
        source_id="dialogue_worker",
    )
    store.store_episode(
        make_episode(
            "ep_tea",
            now,
            now + 1,
            summary="User stated a tea preference.",
            provenance_refs=[trace_id],
        ),
        source_type=SourceType.USER_CONFIRMED,
        supporting_memory_ids=[trace_id],
    )
    store.upsert_fact(
        Fact(
            fact_id="fact_tea",
            subject="user",
            predicate="likes",
            object_value={"value": "tea"},
            confidence=0.95,
            source_type=SourceType.USER_CONFIRMED,
            supporting_episode_ids=["ep_tea"],
        )
    )

    chain = store.get_provenance_chain("fact_tea", "fact")

    node_keys = {(node["memory_kind"], node["memory_id"]) for node in chain["nodes"]}
    assert ("fact", "fact_tea") in node_keys
    assert ("episode", "ep_tea") in node_keys
    assert ("raw_trace", trace_id) in node_keys

    edges = {
        (edge["from_kind"], edge["from_id"], edge["relation"], edge["to_kind"], edge["to_id"])
        for edge in chain["edges"]
    }
    assert ("fact", "fact_tea", "supported_by", "episode", "ep_tea") in edges
    assert ("episode", "ep_tea", "derived_from", "raw_trace", trace_id) in edges

    assert chain["missing"] == []
    assert "fact_tea" in chain["summary"]
    assert "ep_tea" in chain["summary"]
    assert trace_id in chain["summary"]


def test_provenance_chain_reports_missing_references(tmp_path):
    store = open_migrated_store(tmp_path)
    now = int(time.time())
    store.store_episode(
        make_episode("ep_orphan", now, now + 1),
        supporting_memory_ids=["trace_gone"],
    )

    chain = store.get_provenance_chain("ep_orphan", "episode")

    assert chain["missing"] == ["trace_gone"]
    node_keys = {(node["memory_kind"], node["memory_id"]) for node in chain["nodes"]}
    assert node_keys == {("episode", "ep_orphan")}


def test_provenance_chain_unknown_root_raises(tmp_path):
    store = open_migrated_store(tmp_path)
    with pytest.raises(KeyError):
        store.get_provenance_chain("fact_nope", "fact")
    with pytest.raises(ValueError):
        store.get_provenance_chain("fact_nope", "unsupported_kind")
