from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from android_brain_memory.models import Episode, Fact, MemoryStatus, SourceType
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

    assert [record.migration_id for record in applied] == ["001_init"]
    assert applied_again == []
    assert [record.migration_id for record in records] == ["001_init"]
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
    assert updated.provenance == {"supporting_episode_ids": ["ep_001"], "source": "test"}
    assert updated.last_retrieved_ts == 120
    assert updated.retrieval_count == 2
    assert updated.contradiction_score == 0.4
    assert updated.speakability == "restricted"
    assert store.get_meta_memory("missing", "fact") is None
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
    assert loaded_fact.supporting_episode_ids == ["ep_001"]
    assert store.get_episode("missing") is None
    assert store.get_fact("missing") is None
    store.close()
