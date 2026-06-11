from __future__ import annotations

import time
from pathlib import Path

from android_brain_memory.models import Episode, Fact, MemoryQuery, SourceType
from android_brain_memory.retrieval import retrieve_memory
from android_brain_memory.storage import MemoryStore


MIGRATION = Path(__file__).resolve().parents[1] / "storage" / "migrations" / "001_init.sql"


def test_store_trace_episode_and_fact_then_retrieve_bundle(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    store.apply_migration(MIGRATION)
    now = int(time.time())

    trace_id = store.store_raw_trace(
        summary="User asked Mneme to remember the memory architecture.",
        payload={"utterance": "remember the memory architecture"},
        source_type=SourceType.USER_CONFIRMED,
        confidence=0.95,
        salience=0.82,
        source_id="test_dialogue",
    )
    episode = Episode(
        episode_id="ep_test_architecture",
        start_ts=now,
        end_ts=now + 1,
        summary="User asked Mneme to remember the memory architecture.",
        context={"topic": "memory architecture", "trace_id": trace_id},
        salience=0.82,
        confidence=0.95,
        participants=["user"],
        provenance_refs=[trace_id],
    )
    store.store_episode(episode)
    store.upsert_fact(
        Fact(
            fact_id="fact_test_architecture",
            subject="mneme",
            predicate="project_focus",
            object_value={"value": "memory architecture"},
            confidence=0.95,
            source_type=SourceType.USER_CONFIRMED,
            supporting_episode_ids=[episode.episode_id],
        )
    )

    bundle = retrieve_memory(store, MemoryQuery(query_text="architecture", max_results=3))

    assert "found 1 fact(s)" in bundle.summary
    assert "found 1 episode(s)" in bundle.summary
    assert [fact.fact_id for fact in bundle.facts] == ["fact_test_architecture"]
    assert [episode.episode_id for episode in bundle.episodes] == ["ep_test_architecture"]
    assert "SQLite" in bundle.provenance_summary
    store.close()


def test_retrieve_memory_respects_fact_and_episode_include_flags(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    store.apply_migration(MIGRATION)
    now = int(time.time())
    store.store_episode(
        Episode(
            episode_id="ep_test_selective_memory",
            start_ts=now,
            end_ts=now + 1,
            summary="Mneme stores selective memory events.",
            context={"topic": "selective memory"},
            salience=0.7,
            confidence=0.8,
        )
    )
    store.upsert_fact(
        Fact(
            fact_id="fact_test_selective_memory",
            subject="mneme",
            predicate="memory_policy",
            object_value={"value": "selective memory"},
            confidence=0.8,
            source_type=SourceType.SYSTEM_GENERATED,
        )
    )

    facts_only = retrieve_memory(
        store,
        MemoryQuery(query_text="selective", include_episodes=False, max_results=3),
    )
    episodes_only = retrieve_memory(
        store,
        MemoryQuery(query_text="selective", include_facts=False, max_results=3),
    )

    assert [fact.fact_id for fact in facts_only.facts] == ["fact_test_selective_memory"]
    assert facts_only.episodes == []
    assert episodes_only.facts == []
    assert [episode.episode_id for episode in episodes_only.episodes] == ["ep_test_selective_memory"]
    store.close()
