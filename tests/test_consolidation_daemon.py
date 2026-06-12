from __future__ import annotations

from pathlib import Path

from android_brain_memory import MnemeMemory
from android_brain_memory.consolidation import ConsolidationOptions, ConsolidationReport
from android_brain_memory.consolidation_daemon import ConsolidationDaemon
from android_brain_memory.models import Episode
from android_brain_memory.runtime import EventBus, RuntimeEventKind


MIGRATIONS = Path(__file__).resolve().parents[1] / "storage" / "migrations"


class FixedClock:
    def __init__(self, now_ms: int) -> None:
        self.now_ms = now_ms

    def __call__(self) -> int:
        return self.now_ms


def open_engine(tmp_path) -> MnemeMemory:
    engine = MnemeMemory(tmp_path / "memory.sqlite3", migrations_dir=MIGRATIONS)
    engine.init_db()
    return engine


def add_repeated_episodes(engine: MnemeMemory, count: int = 3) -> None:
    for index in range(count):
        engine.add_episode(
            Episode(
                episode_id=f"ep_calibration_{index:03d}",
                start_ts=100 + index * 60,
                end_ts=110 + index * 60,
                summary="User practiced the calibration routine with Mneme.",
                context={"topic": "calibration routine", "tags": ["calibration"]},
                salience=0.7,
                confidence=0.9,
                participants=["user"],
            )
        )


def summary_count(engine: MnemeMemory) -> int:
    row = engine.store.conn.execute("SELECT COUNT(*) AS count FROM memory_summary").fetchone()
    return int(row["count"])


def test_first_tick_consolidates_and_publishes_lifecycle_event(tmp_path):
    engine = open_engine(tmp_path)
    add_repeated_episodes(engine)
    clock = FixedClock(1_000_000)
    bus = EventBus(clock=clock)
    daemon = ConsolidationDaemon(engine, min_interval_s=300, bus=bus, clock=clock)

    report = daemon.tick()

    assert isinstance(report, ConsolidationReport)
    assert report.groups_summarized >= 1
    assert summary_count(engine) >= 1

    events = bus.history(kinds=[RuntimeEventKind.MEMORY_LIFECYCLE])
    assert len(events) == 1
    payload = events[0].payload
    assert payload["lifecycle_stage"] == "consolidation"
    assert payload["groups_summarized"] == report.groups_summarized
    assert payload["summary_ids"] == report.summary_ids
    engine.close()


def test_ticks_inside_interval_are_skipped(tmp_path):
    engine = open_engine(tmp_path)
    add_repeated_episodes(engine)
    clock = FixedClock(1_000_000)
    daemon = ConsolidationDaemon(engine, min_interval_s=300, clock=clock)

    first = daemon.tick()
    clock.now_ms += 100_000  # 100s < 300s interval
    second = daemon.tick()

    assert first is not None
    assert second is None
    assert daemon.stats["passes"] == 1
    assert daemon.stats["skipped_ticks"] == 1
    engine.close()


def test_tick_after_interval_runs_and_updates_not_duplicates(tmp_path):
    engine = open_engine(tmp_path)
    add_repeated_episodes(engine)
    clock = FixedClock(1_000_000)
    daemon = ConsolidationDaemon(engine, min_interval_s=300, clock=clock)

    first = daemon.tick()
    count_after_first = summary_count(engine)
    clock.now_ms += 400_000  # 400s > 300s interval
    second = daemon.tick()

    assert first is not None and second is not None
    assert second.summaries_updated >= 1
    assert summary_count(engine) == count_after_first
    assert daemon.stats["passes"] == 2
    engine.close()


def test_run_once_forces_pass_ignoring_interval(tmp_path):
    engine = open_engine(tmp_path)
    add_repeated_episodes(engine)
    clock = FixedClock(1_000_000)
    daemon = ConsolidationDaemon(engine, min_interval_s=300, clock=clock)

    daemon.tick()
    forced = daemon.run_once()

    assert forced is not None
    assert daemon.stats["passes"] == 2
    engine.close()


def test_batch_limit_bounds_episodes_examined(tmp_path):
    engine = open_engine(tmp_path)
    add_repeated_episodes(engine, count=6)
    clock = FixedClock(1_000_000)
    daemon = ConsolidationDaemon(
        engine,
        min_interval_s=300,
        consolidation_options=ConsolidationOptions(max_episodes=2, min_repetition=2),
        clock=clock,
    )

    report = daemon.tick()

    assert report is not None
    assert report.episodes_examined <= 2
    engine.close()


def test_stats_accumulate_across_passes(tmp_path):
    engine = open_engine(tmp_path)
    add_repeated_episodes(engine)
    clock = FixedClock(1_000_000)
    daemon = ConsolidationDaemon(engine, min_interval_s=1, clock=clock)

    daemon.tick()
    clock.now_ms += 2_000
    daemon.tick()

    stats = daemon.stats
    assert stats["passes"] == 2
    assert stats["last_run_ms"] == clock.now_ms
    assert stats["summaries_created"] >= 1
    assert stats["summaries_updated"] >= 1
    engine.close()
