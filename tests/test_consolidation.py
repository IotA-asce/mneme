from __future__ import annotations

from pathlib import Path

from android_brain_memory.consolidation import ConsolidationOptions, consolidate_once
from android_brain_memory.models import Episode
from android_brain_memory.storage import MemoryStore


ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "storage" / "migrations"


def open_migrated_store(tmp_path) -> MemoryStore:
    store = MemoryStore(tmp_path / "memory.sqlite3")
    store.run_migrations(MIGRATIONS)
    return store


def test_consolidate_once_creates_summary_for_repeated_episodes(tmp_path):
    store = open_migrated_store(tmp_path)
    episodes = [
        Episode(
            episode_id="ep_calibration_001",
            start_ts=100,
            end_ts=110,
            summary="User practiced the calibration routine with Mneme.",
            context={"topic": "calibration routine", "tags": ["calibration"]},
            salience=0.7,
            confidence=0.9,
            participants=["user"],
        ),
        Episode(
            episode_id="ep_calibration_002",
            start_ts=160,
            end_ts=170,
            summary="User repeated the calibration routine at the bench.",
            context={"topic": "calibration routine", "tags": ["calibration"]},
            salience=0.8,
            confidence=0.9,
            participants=["user"],
        ),
        Episode(
            episode_id="ep_calibration_003",
            start_ts=220,
            end_ts=230,
            summary="User finished another calibration routine.",
            context={"topic": "calibration routine", "tags": ["calibration"]},
            salience=0.9,
            confidence=0.9,
            participants=["user"],
        ),
        Episode(
            episode_id="ep_unrelated",
            start_ts=900,
            end_ts=910,
            summary="User discussed unrelated storage notes.",
            context={"topic": "storage notes", "tags": ["storage"]},
            salience=0.6,
            confidence=0.8,
            participants=["user"],
        ),
    ]
    for episode in episodes:
        store.store_episode(episode)

    report = consolidate_once(
        store,
        ConsolidationOptions(min_repetition=3, close_time_window_s=600),
    )

    summaries = store.get_memory_summaries(summary_type="repeated_episode_group")
    assert report.episodes_examined == 4
    assert report.groups_summarized == 1
    assert report.summaries_created == 1
    assert report.decay_metadata_updates == 2
    assert len(report.summary_ids) == 1
    assert len(summaries) == 1
    assert summaries[0].summary_id == report.summary_ids[0]
    assert summaries[0].summary_type == "repeated_episode_group"
    assert "Observed 3 related episodes about calibration" in summaries[0].summary

    summary_meta = store.get_meta_memory(summaries[0].summary_id, "summary")
    assert summary_meta is not None
    assert summary_meta.provenance["supporting_memory_ids"] == [
        "ep_calibration_001",
        "ep_calibration_002",
        "ep_calibration_003",
    ]

    preserved_rows = store.conn.execute(
        "SELECT COUNT(*) AS count FROM episode WHERE status = 'active'"
    ).fetchone()
    assert preserved_rows["count"] == 4
    for episode in episodes:
        assert store.get_episode(episode.episode_id) is not None

    first_meta = store.get_meta_memory("ep_calibration_001", "episode")
    representative_meta = store.get_meta_memory("ep_calibration_003", "episode")
    assert first_meta is not None
    assert first_meta.provenance["decay"]["summary_id"] == summaries[0].summary_id
    assert first_meta.provenance["decay"]["accessibility"] == "downrank_candidate"
    assert representative_meta is not None
    assert "decay" not in representative_meta.provenance

    second_report = consolidate_once(
        store,
        ConsolidationOptions(min_repetition=3, close_time_window_s=600),
    )
    assert second_report.summaries_created == 0
    assert second_report.summaries_updated == 1
    assert len(store.get_memory_summaries(summary_type="repeated_episode_group")) == 1
    store.close()
