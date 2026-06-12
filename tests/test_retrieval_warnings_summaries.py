from __future__ import annotations

import time
from pathlib import Path

from android_brain_memory.models import (
    Episode,
    Fact,
    MemoryBundle,
    MemoryQuery,
    MemoryStatus,
    SourceType,
    Speakability,
)
from android_brain_memory.retrieval import retrieve_memory
from android_brain_memory.storage import MemoryStore


MIGRATIONS = Path(__file__).resolve().parents[1] / "storage" / "migrations"


def open_migrated_store(tmp_path) -> MemoryStore:
    store = MemoryStore(tmp_path / "memory.sqlite3")
    store.run_migrations(MIGRATIONS)
    return store


def store_summary(store: MemoryStore, summary_id: str, text: str, **overrides):
    return store.store_memory_summary(
        summary_type=overrides.pop("summary_type", "repeated_episode"),
        scope_key=overrides.pop("scope_key", "topic:test"),
        summary=text,
        confidence=overrides.pop("confidence", 0.8),
        summary_id=summary_id,
        **overrides,
    )


def test_search_memory_summaries_matches_summary_and_scope_key(tmp_path):
    store = open_migrated_store(tmp_path)
    store_summary(store, "summary_tea", "User repeatedly asked about tea brewing.")
    store_summary(
        store,
        "summary_scope",
        "Routine morning greeting pattern.",
        scope_key="topic:tea-time",
    )
    store_summary(store, "summary_other", "Unrelated hardware note.")

    results = store.search_memory_summaries("tea", limit=10)

    assert [record.summary_id for record in results] == ["summary_scope", "summary_tea"] or [
        record.summary_id for record in results
    ] == ["summary_tea", "summary_scope"]
    assert all("summary_other" != record.summary_id for record in results)


def test_retrieve_includes_ranked_summaries_and_updates_history(tmp_path):
    store = open_migrated_store(tmp_path)
    store_summary(store, "summary_tea", "User repeatedly asked about tea brewing.")

    bundle = retrieve_memory(store, MemoryQuery(query_text="tea", max_results=3))

    assert [item["summary_id"] for item in bundle.summaries] == ["summary_tea"]
    assert "found 1 summary(ies)" in bundle.summary
    summary_explanations = [
        item for item in bundle.ranking_explanations if item["memory_kind"] == "summary"
    ]
    assert len(summary_explanations) == 1
    assert summary_explanations[0]["memory_id"] == "summary_tea"

    meta = store.get_meta_memory("summary_tea", "summary")
    assert meta is not None
    assert meta.retrieval_count == 1


def test_retrieve_respects_include_summaries_flag(tmp_path):
    store = open_migrated_store(tmp_path)
    store_summary(store, "summary_tea", "User repeatedly asked about tea brewing.")

    bundle = retrieve_memory(
        store,
        MemoryQuery(query_text="tea", include_summaries=False),
    )

    assert bundle.summaries == []


def test_retrieve_filters_internal_summaries_by_speakability(tmp_path):
    store = open_migrated_store(tmp_path)
    store_summary(
        store,
        "summary_internal",
        "Internal-only tea diagnostic pattern.",
        speakability=Speakability.INTERNAL_ONLY,
    )

    bundle = retrieve_memory(store, MemoryQuery(query_text="tea"))

    assert bundle.summaries == []
    assert any("withheld by speakability policy" in warning for warning in bundle.warnings)


def test_empty_retrieval_warns(tmp_path):
    store = open_migrated_store(tmp_path)

    bundle = retrieve_memory(store, MemoryQuery(query_text="nonexistent topic"))

    assert bundle.facts == []
    assert bundle.episodes == []
    assert bundle.summaries == []
    assert any("no matching memory found" in warning for warning in bundle.warnings)


def test_conflicting_fact_records_warn(tmp_path):
    store = open_migrated_store(tmp_path)
    store.upsert_fact(
        Fact(
            fact_id="fact_color_a",
            subject="user",
            predicate="favorite_color",
            object_value={"value": "blue"},
            confidence=0.9,
            source_type=SourceType.USER_CONFIRMED,
        )
    )
    store.upsert_fact(
        Fact(
            fact_id="fact_color_b",
            subject="user",
            predicate="favorite_color",
            object_value={"value": "green"},
            confidence=0.9,
            source_type=SourceType.USER_CONFIRMED,
        )
    )

    bundle = retrieve_memory(
        store,
        MemoryQuery(query_text="favorite_color", fact_status=MemoryStatus.CONFLICTED),
    )

    assert bundle.facts
    assert any(
        "conflicting fact records" in warning and "favorite_color" in warning
        for warning in bundle.warnings
    )


def test_provenance_summary_derived_from_support_links(tmp_path):
    store = open_migrated_store(tmp_path)
    now = int(time.time())
    trace_id = store.store_raw_trace(
        summary="User said they like tea.",
        payload={"utterance": "I like tea"},
        source_type=SourceType.USER_CONFIRMED,
        confidence=0.95,
        salience=0.8,
    )
    store.store_episode(
        Episode(
            episode_id="ep_tea",
            start_ts=now,
            end_ts=now + 1,
            summary="User stated a tea preference.",
            context={"topic": "tea"},
            salience=0.8,
            confidence=0.95,
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

    bundle = retrieve_memory(store, MemoryQuery(query_text="tea", max_results=5))

    assert "fact fact_tea supported_by episode ep_tea" in bundle.provenance_summary
    assert f"episode ep_tea derived_from raw_trace {trace_id}" in bundle.provenance_summary


def test_provenance_summary_states_when_no_links_exist(tmp_path):
    store = open_migrated_store(tmp_path)
    store.upsert_fact(
        Fact(
            fact_id="fact_plain",
            subject="user",
            predicate="nickname",
            object_value={"value": "Sam"},
            confidence=0.9,
            source_type=SourceType.USER_CONFIRMED,
        ),
        write_meta=False,
    )

    bundle = retrieve_memory(store, MemoryQuery(query_text="nickname"))

    assert bundle.facts
    assert "no stored provenance links" in bundle.provenance_summary


def test_memory_bundle_round_trips_summaries():
    bundle = MemoryBundle(
        query_id="query_test",
        summary="found 1 summary(ies)",
        summaries=[{"summary_id": "summary_x", "summary": "text", "confidence": 0.5}],
    )

    rebuilt = MemoryBundle.from_dict(bundle.to_dict())

    assert rebuilt.summaries == bundle.summaries
