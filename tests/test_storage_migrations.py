from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from android_brain_memory.models import Episode, Fact, MemoryStatus, SourceType, Speakability
from android_brain_memory.storage import MetaMemoryRecord, MemoryStore


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "storage" / "migrations" / "001_init.sql"
MIGRATIONS = ROOT / "storage" / "migrations"


def open_migrated_store(tmp_path) -> MemoryStore:
    store = MemoryStore(tmp_path / "memory.sqlite3")
    store.run_migrations(MIGRATIONS)
    return store


def test_migrations_are_tracked_and_idempotent(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite3")

    applied = store.run_migrations(MIGRATIONS)
    applied_again = store.run_migrations(MIGRATIONS)
    records = store.get_applied_migrations()

    assert [record.migration_id for record in applied] == ["001_init", "002_fact_tags"]
    assert applied_again == []
    assert [record.migration_id for record in records] == ["001_init", "002_fact_tags"]
    assert records[0].filename == "001_init.sql"
    assert len(records[0].checksum_sha256) == 64
    assert records[0].applied_ts >= 0
    store.close()


def test_migration_checksum_mismatch_is_rejected(tmp_path):
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()
    migration_path = migrations_dir / "001_init.sql"
    shutil.copy(MIGRATION, migration_path)
    store = MemoryStore(tmp_path / "memory.sqlite3")
    store.apply_migration(migration_path)

    migration_path.write_text(
        migration_path.read_text(encoding="utf-8") + "\nCREATE TABLE changed_migration(id TEXT);\n",
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="different checksum"):
        store.apply_migration(migration_path)
    store.close()


def test_meta_memory_write_read_and_update_preserves_fields(tmp_path):
    store = open_migrated_store(tmp_path)
    record = MetaMemoryRecord(
        memory_id="fact_001",
        memory_kind="fact",
        source_type=SourceType.USER_CONFIRMED,
        provenance={"supporting_episode_ids": ["ep_001"], "source": "test"},
        last_retrieved_ts=100,
        retrieval_count=1,
        contradiction_score=0.2,
        speakability="normal",
    )

    store.write_meta_memory(record)
    loaded = store.get_meta_memory("fact_001", "fact")
    updated = store.update_meta_memory(
        "fact_001",
        "fact",
        last_retrieved_ts=120,
        retrieval_count=2,
        contradiction_score=0.4,
        speakability="restricted",
    )

    assert loaded == record
    assert updated.source_type == SourceType.USER_CONFIRMED
    assert updated.provenance == {
        "supporting_episode_ids": ["ep_001"],
        "source": "test",
        "source_type": "user_confirmed",
        "source_id": None,
        "derivation_path": [],
        "supporting_memory_ids": [],
        "notes": None,
    }
    assert updated.last_retrieved_ts == 120
    assert updated.retrieval_count == 2
    assert updated.contradiction_score == 0.4
    assert updated.speakability == Speakability.RESTRICTED
    assert store.get_meta_memory("missing", "fact") is None
    store.close()


def test_storage_writes_meta_memory_with_normalized_provenance(tmp_path):
    store = open_migrated_store(tmp_path)
    trace_id = store.store_raw_trace(
        summary="User asked Mneme to remember provenance.",
        payload={"utterance": "remember provenance"},
        source_type=SourceType.USER_CONFIRMED,
        confidence=0.9,
        salience=0.8,
        source_id="dialogue_001",
        derivation_path=["dialogue", "raw_trace"],
        notes="Raw trace provenance test.",
        speakability=Speakability.RESTRICTED,
    )
    episode = Episode(
        episode_id="ep_provenance",
        start_ts=10,
        end_ts=11,
        summary="User asked about provenance.",
        context={"trace_id": trace_id},
        salience=0.8,
        confidence=0.9,
        provenance_refs=[trace_id],
    )
    store.store_episode(
        episode,
        source_type=SourceType.USER_CONFIRMED,
        source_id="dialogue_001",
        derivation_path=["raw_trace", "episode"],
        notes="Episode derived from raw trace.",
    )
    fact = Fact(
        fact_id="fact_provenance",
        subject="mneme",
        predicate="tracks",
        object_value={"value": "provenance"},
        confidence=0.9,
        source_type=SourceType.USER_CONFIRMED,
        supporting_episode_ids=[episode.episode_id],
    )
    store.upsert_fact(
        fact,
        source_id="dialogue_001",
        derivation_path=["episode", "fact"],
        notes="Fact derived from episode.",
    )
    summary = store.store_memory_summary(
        summary_type="topic",
        scope_key="provenance",
        summary="Mneme tracks provenance for memory records.",
        confidence=0.85,
        summary_id="summary_provenance",
        source_type=SourceType.SYSTEM_GENERATED,
        derivation_path=["episode", "summary"],
        supporting_memory_ids=[episode.episode_id, fact.fact_id],
        notes="Summary derived from episode and fact.",
    )

    trace_meta = store.get_meta_memory(trace_id, "raw_trace")
    episode_meta = store.get_meta_memory(episode.episode_id, "episode")
    fact_meta = store.get_meta_memory(fact.fact_id, "fact")
    summary_meta = store.get_meta_memory(summary.summary_id, "summary")

    assert trace_meta is not None
    assert trace_meta.speakability == Speakability.RESTRICTED
    assert trace_meta.provenance == {
        "source_type": "user_confirmed",
        "source_id": "dialogue_001",
        "derivation_path": ["dialogue", "raw_trace"],
        "supporting_memory_ids": [],
        "notes": "Raw trace provenance test.",
    }
    assert episode_meta is not None
    assert episode_meta.provenance["supporting_memory_ids"] == [trace_id]
    assert episode_meta.provenance["derivation_path"] == ["raw_trace", "episode"]
    assert fact_meta is not None
    assert fact_meta.provenance["supporting_memory_ids"] == [episode.episode_id]
    assert fact_meta.provenance["notes"] == "Fact derived from episode."
    assert summary_meta is not None
    assert summary_meta.provenance["supporting_memory_ids"] == [episode.episode_id, fact.fact_id]
    assert summary_meta.provenance["derivation_path"] == ["episode", "summary"]
    store.close()


def test_meta_memory_rejects_secret_like_provenance_keys(tmp_path):
    store = open_migrated_store(tmp_path)

    with pytest.raises(ValueError, match="secret-bearing"):
        store.store_raw_trace(
            summary="Bad provenance.",
            payload={},
            source_type=SourceType.SYSTEM_GENERATED,
            confidence=0.5,
            salience=0.1,
            provenance={"api_token": "do-not-store"},
        )
    store.store_working_context_snapshot({"after": "rejection"})
    row = store.conn.execute(
        "SELECT COUNT(*) AS count FROM raw_trace WHERE summary = ?",
        ("Bad provenance.",),
    ).fetchone()
    assert row["count"] == 0
    store.close()


def test_working_context_snapshots_are_read_recent_first(tmp_path):
    store = open_migrated_store(tmp_path)
    first = store.store_working_context_snapshot(
        {"speaker": "user", "topic": "memory"},
        snapshot_id="ctx_001",
        created_ts=10,
    )
    second = store.store_working_context_snapshot(
        {"speaker": "user", "topic": "storage"},
        snapshot_id="ctx_002",
        created_ts=20,
    )

    recent = store.get_recent_working_context_snapshots(limit=2)

    assert first.context["topic"] == "memory"
    assert [snapshot.snapshot_id for snapshot in recent] == [second.snapshot_id, first.snapshot_id]
    assert recent[0].context == {"speaker": "user", "topic": "storage"}
    store.close()


def test_get_episode_and_fact_by_id_preserve_typed_fields(tmp_path):
    store = open_migrated_store(tmp_path)
    episode = Episode(
        episode_id="ep_001",
        start_ts=10,
        end_ts=12,
        summary="User confirmed a storage memory.",
        context={"topic": "storage"},
        salience=0.8,
        confidence=0.9,
        participants=["user"],
        objects=["sqlite"],
        provenance_refs=["trace_001"],
    )
    fact = Fact(
        fact_id="fact_001",
        subject="mneme",
        predicate="uses_storage",
        object_value={"value": "sqlite"},
        confidence=0.95,
        source_type=SourceType.USER_CONFIRMED,
        status=MemoryStatus.CONFLICTED,
        tags=["storage"],
        supporting_episode_ids=[episode.episode_id],
    )

    store.store_episode(episode)
    store.upsert_fact(fact)

    loaded_episode = store.get_episode("ep_001")
    loaded_fact = store.get_fact("fact_001")

    assert loaded_episode is not None
    assert loaded_episode.episode_id == episode.episode_id
    assert loaded_episode.participants == ["user"]
    assert loaded_episode.objects == ["sqlite"]
    assert loaded_episode.confidence == 0.9
    assert loaded_fact is not None
    assert loaded_fact.source_type == SourceType.USER_CONFIRMED
    assert loaded_fact.status == MemoryStatus.CONFLICTED
    assert loaded_fact.confidence == 0.95
    assert loaded_fact.tags == ["storage"]
    assert loaded_fact.supporting_episode_ids == ["ep_001"]
    assert loaded_fact.supersedes_fact_id is None
    assert store.get_episode("missing") is None
    assert store.get_fact("missing") is None
    store.close()


def test_user_confirmed_fact_supersedes_inferred_conflict(tmp_path):
    store = open_migrated_store(tmp_path)
    inferred = Fact(
        fact_id="fact_inferred_preference",
        subject="user",
        predicate="prefers",
        object_value={"value": "tea"},
        confidence=0.6,
        source_type=SourceType.MODEL_INFERRED,
    )
    confirmed = Fact(
        fact_id="fact_confirmed_preference",
        subject="user",
        predicate="prefers",
        object_value={"value": "coffee"},
        confidence=0.95,
        source_type=SourceType.USER_CONFIRMED,
    )

    assert store.upsert_fact(inferred) is None
    report = store.upsert_fact(confirmed)

    loaded_inferred = store.get_fact(inferred.fact_id)
    loaded_confirmed = store.get_fact(confirmed.fact_id)
    assert report is not None
    assert report.active_fact_ids == [confirmed.fact_id]
    assert report.superseded_fact_ids == [inferred.fact_id]
    assert report.supersession_edges == {confirmed.fact_id: inferred.fact_id}
    assert loaded_inferred is not None
    assert loaded_inferred.status == MemoryStatus.SUPERSEDED
    assert loaded_confirmed is not None
    assert loaded_confirmed.status == MemoryStatus.ACTIVE
    assert loaded_confirmed.supersedes_fact_id == inferred.fact_id

    active = store.search_facts_structured(subject="user", predicate="prefers", limit=10)
    reports = store.get_fact_conflict_reports(subject="user", predicate="prefers")
    assert [fact.fact_id for fact in active] == [confirmed.fact_id]
    assert len(reports) == 1
    assert reports[0].superseded_fact_ids == [inferred.fact_id]
    store.close()


def test_user_confirmed_fact_conflict_preserves_both_for_review(tmp_path):
    store = open_migrated_store(tmp_path)
    first = Fact(
        fact_id="fact_confirmed_tea",
        subject="user",
        predicate="prefers",
        object_value={"value": "tea"},
        confidence=0.95,
        source_type=SourceType.USER_CONFIRMED,
    )
    second = Fact(
        fact_id="fact_confirmed_coffee",
        subject="user",
        predicate="prefers",
        object_value={"value": "coffee"},
        confidence=0.95,
        source_type=SourceType.USER_CONFIRMED,
    )

    assert store.upsert_fact(first) is None
    report = store.upsert_fact(second)

    loaded_first = store.get_fact(first.fact_id)
    loaded_second = store.get_fact(second.fact_id)
    assert report is not None
    assert report.conflicted_fact_ids == [second.fact_id, first.fact_id]
    assert loaded_first is not None
    assert loaded_first.status == MemoryStatus.CONFLICTED
    assert loaded_second is not None
    assert loaded_second.status == MemoryStatus.CONFLICTED

    active = store.search_facts_structured(subject="user", predicate="prefers", limit=10)
    conflicted = store.search_facts_structured(
        subject="user",
        predicate="prefers",
        status=MemoryStatus.CONFLICTED,
        limit=10,
    )
    reports = store.get_fact_conflict_reports(subject="user", predicate="prefers")
    assert active == []
    assert {fact.fact_id for fact in conflicted} == {first.fact_id, second.fact_id}
    assert len(reports) == 1
    assert set(reports[0].conflicted_fact_ids) == {first.fact_id, second.fact_id}
    store.close()


def test_same_semantic_fact_duplicate_is_not_a_conflict(tmp_path):
    store = open_migrated_store(tmp_path)
    first = Fact(
        fact_id="fact_duplicate_a",
        subject="user",
        predicate="prefers",
        object_value={"value": "tea"},
        confidence=0.9,
        source_type=SourceType.USER_CONFIRMED,
    )
    second = Fact(
        fact_id="fact_duplicate_b",
        subject="user",
        predicate="prefers",
        object_value={"value": "tea"},
        confidence=0.8,
        source_type=SourceType.MODEL_INFERRED,
    )

    assert store.upsert_fact(first) is None
    assert store.upsert_fact(second) is None

    active = store.search_facts_structured(subject="user", predicate="prefers", limit=10)
    assert {fact.fact_id for fact in active} == {first.fact_id, second.fact_id}
    assert store.get_fact_conflict_reports(subject="user", predicate="prefers") == []
    store.close()


def test_context_preserving_fact_difference_is_not_a_conflict(tmp_path):
    store = open_migrated_store(tmp_path)
    morning = Fact(
        fact_id="fact_morning_preference",
        subject="user",
        predicate="prefers",
        object_value={"value": "tea", "context": "morning"},
        confidence=0.9,
        source_type=SourceType.USER_CONFIRMED,
    )
    evening = Fact(
        fact_id="fact_evening_preference",
        subject="user",
        predicate="prefers",
        object_value={"value": "coffee", "context": "evening"},
        confidence=0.9,
        source_type=SourceType.USER_CONFIRMED,
    )

    assert store.upsert_fact(morning) is None
    assert store.upsert_fact(evening) is None

    active = store.search_facts_structured(subject="user", predicate="prefers", limit=10)
    assert {fact.fact_id for fact in active} == {morning.fact_id, evening.fact_id}
    assert store.get_fact_conflict_reports(subject="user", predicate="prefers") == []
    store.close()
