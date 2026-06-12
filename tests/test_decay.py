from __future__ import annotations

import time
from pathlib import Path

import pytest

from android_brain_memory.decay import DecayOptions, DecayReport, purge_memory, run_decay_once
from android_brain_memory.models import Episode, Fact, MemoryQuery, MemoryStatus, SourceType
from android_brain_memory.retrieval import retrieve_memory
from android_brain_memory.runtime import EventBus, RuntimeEventKind
from android_brain_memory.storage import MemoryStore


MIGRATIONS = Path(__file__).resolve().parents[1] / "storage" / "migrations"
THIRTY_DAYS_S = 30 * 24 * 3600


class FixedClock:
    def __init__(self, now_ms: int) -> None:
        self.now_ms = now_ms

    def __call__(self) -> int:
        return self.now_ms


def open_migrated_store(tmp_path) -> MemoryStore:
    store = MemoryStore(tmp_path / "memory.sqlite3")
    store.run_migrations(MIGRATIONS)
    return store


def make_episode(episode_id: str, start_ts: int, **overrides) -> Episode:
    payload = {
        "episode_id": episode_id,
        "start_ts": start_ts,
        "end_ts": overrides.pop("end_ts", start_ts + 10),
        "summary": overrides.pop("summary", "User practiced the calibration routine."),
        "context": overrides.pop("context", {"topic": "calibration"}),
        "salience": overrides.pop("salience", 0.7),
        "confidence": overrides.pop("confidence", 0.9),
        "participants": overrides.pop("participants", ["user"]),
    }
    payload.update(overrides)
    return Episode(**payload)


def mark_covered_by_summary(store: MemoryStore, episode_id: str) -> None:
    store.update_decay_metadata(
        episode_id,
        "episode",
        {
            "policy": "covered_by_summary",
            "accessibility": "downrank_candidate",
            "summary_id": "summary_test",
        },
    )


def test_decay_metadata_downranks_retrieval_score(tmp_path):
    store = open_migrated_store(tmp_path)
    now = int(time.time())
    store.store_episode(make_episode("ep_fresh", now))
    store.store_episode(make_episode("ep_decayed", now))
    mark_covered_by_summary(store, "ep_decayed")

    bundle = retrieve_memory(store, MemoryQuery(query_text="calibration", max_results=5))

    assert [episode.episode_id for episode in bundle.episodes] == ["ep_fresh", "ep_decayed"]
    by_id = {item["memory_id"]: item for item in bundle.ranking_explanations}
    decayed = by_id["ep_decayed"]
    assert decayed["decay_penalty"] == 0.3
    assert decayed["score"] == pytest.approx(decayed["score_before_decay"] * 0.7, abs=1e-6)
    assert by_id["ep_fresh"]["decay_penalty"] == 0.0
    store.close()


def test_explicit_downrank_value_overrides_default(tmp_path):
    store = open_migrated_store(tmp_path)
    now = int(time.time())
    store.store_episode(make_episode("ep_half", now))
    store.update_decay_metadata("ep_half", "episode", {"downrank": 0.5})

    bundle = retrieve_memory(store, MemoryQuery(query_text="calibration"))

    explanation = bundle.ranking_explanations[0]
    assert explanation["decay_penalty"] == 0.5
    store.close()


def test_decay_pass_suppresses_old_summarized_unretrieved_episodes(tmp_path):
    store = open_migrated_store(tmp_path)
    base = int(time.time())
    now_s = base + THIRTY_DAYS_S + 1000

    store.store_episode(make_episode("ep_old_covered", base))
    mark_covered_by_summary(store, "ep_old_covered")

    store.store_episode(make_episode("ep_old_retrieved", base))
    mark_covered_by_summary(store, "ep_old_retrieved")
    store.record_retrieval("ep_old_retrieved", "episode", retrieved_ts=now_s - 100)

    store.store_episode(make_episode("ep_recent_covered", now_s - 50))
    mark_covered_by_summary(store, "ep_recent_covered")

    store.store_episode(make_episode("ep_old_uncovered", base))

    report = run_decay_once(store, now_s=now_s)

    assert isinstance(report, DecayReport)
    assert report.episodes_suppressed == 1
    assert report.suppressed_episode_ids == ["ep_old_covered"]
    suppressed = store.get_recent_episodes(status=MemoryStatus.SUPPRESSED)
    assert [episode.episode_id for episode in suppressed] == ["ep_old_covered"]
    store.close()


def test_decay_pass_suppresses_old_superseded_facts_but_never_user_confirmed(tmp_path):
    store = open_migrated_store(tmp_path)
    now_s = int(time.time()) + THIRTY_DAYS_S + 1000

    store.upsert_fact(
        Fact(
            fact_id="fact_superseded_inferred",
            subject="user",
            predicate="likes",
            object_value={"value": "old guess"},
            confidence=0.5,
            source_type=SourceType.MODEL_INFERRED,
        )
    )
    store.set_fact_status("fact_superseded_inferred", MemoryStatus.SUPERSEDED)

    store.upsert_fact(
        Fact(
            fact_id="fact_confirmed",
            subject="user",
            predicate="likes",
            object_value={"value": "tea"},
            confidence=0.95,
            source_type=SourceType.USER_CONFIRMED,
        )
    )

    report = run_decay_once(store, now_s=now_s)

    assert report.facts_suppressed == 1
    assert report.suppressed_fact_ids == ["fact_superseded_inferred"]
    assert store.get_fact("fact_confirmed").status == MemoryStatus.ACTIVE
    assert store.get_fact("fact_superseded_inferred").status == MemoryStatus.SUPPRESSED
    store.close()


def test_decay_pass_publishes_lifecycle_event(tmp_path):
    store = open_migrated_store(tmp_path)
    base = int(time.time())
    now_s = base + THIRTY_DAYS_S + 1000
    store.store_episode(make_episode("ep_old_covered", base))
    mark_covered_by_summary(store, "ep_old_covered")
    bus = EventBus(clock=FixedClock(now_s * 1000))

    report = run_decay_once(store, now_s=now_s, bus=bus)

    events = bus.history(kinds=[RuntimeEventKind.MEMORY_LIFECYCLE])
    assert len(events) == 1
    payload = events[0].payload
    assert payload["lifecycle_stage"] == "decay"
    assert payload["episodes_suppressed"] == report.episodes_suppressed
    assert payload["suppressed_episode_ids"] == ["ep_old_covered"]
    store.close()


def test_purge_memory_is_tombstone_with_reason(tmp_path):
    store = open_migrated_store(tmp_path)
    now = int(time.time())
    store.store_episode(make_episode("ep_purge", now))

    purge_memory(store, "ep_purge", "episode", reason="bench test data", now_s=now)

    suppressed = store.get_recent_episodes(status=MemoryStatus.PURGED)
    assert [episode.episode_id for episode in suppressed] == ["ep_purge"]
    meta = store.get_meta_memory("ep_purge", "episode")
    assert meta.provenance["purge"]["reason"] == "bench test data"
    assert meta.provenance["purge"]["purged_ts"] == now
    # tombstone: the row and its content are preserved
    assert store.get_episode("ep_purge") is not None
    store.close()


def test_purging_user_confirmed_fact_requires_force(tmp_path):
    store = open_migrated_store(tmp_path)
    store.upsert_fact(
        Fact(
            fact_id="fact_keep",
            subject="user",
            predicate="likes",
            object_value={"value": "tea"},
            confidence=0.95,
            source_type=SourceType.USER_CONFIRMED,
        )
    )

    with pytest.raises(ValueError):
        purge_memory(store, "fact_keep", "fact", reason="cleanup")
    assert store.get_fact("fact_keep").status == MemoryStatus.ACTIVE

    purge_memory(store, "fact_keep", "fact", reason="user requested deletion", force=True)
    assert store.get_fact("fact_keep").status == MemoryStatus.PURGED
    store.close()


def test_status_setters_validate_ids(tmp_path):
    store = open_migrated_store(tmp_path)
    with pytest.raises(KeyError):
        store.set_episode_status("ep_missing", MemoryStatus.SUPPRESSED)
    with pytest.raises(KeyError):
        store.set_fact_status("fact_missing", MemoryStatus.SUPPRESSED)
    with pytest.raises(KeyError):
        purge_memory(store, "ep_missing", "episode", reason="x")
    store.close()


def test_decay_options_validate():
    with pytest.raises(ValueError):
        DecayOptions(suppress_after_s=0)
    with pytest.raises(ValueError):
        DecayOptions(min_retrievals_to_keep=-1)
