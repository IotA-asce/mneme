from __future__ import annotations

from pathlib import Path

from android_brain_memory import MnemeMemory, ScenarioReplayRunner
from android_brain_memory.models import MemoryCandidate, SourceType
from android_brain_memory.promotion import MemoryPromoter, PromotionOutcome
from android_brain_memory.runtime import (
    EventBus,
    RuntimeEvent,
    RuntimeEventKind,
    RuntimeTopic,
    memory_candidate_event,
    memory_lifecycle_event,
)


MIGRATIONS = Path(__file__).resolve().parents[1] / "storage" / "migrations"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "basic_conversation.yaml"


class FixedClock:
    def __init__(self, now_ms: int) -> None:
        self.now_ms = now_ms

    def __call__(self) -> int:
        return self.now_ms


def open_engine(tmp_path) -> MnemeMemory:
    engine = MnemeMemory(tmp_path / "memory.sqlite3", migrations_dir=MIGRATIONS)
    engine.init_db()
    return engine


def make_candidate(candidate_id: str, features: dict[str, float]) -> MemoryCandidate:
    return MemoryCandidate(
        candidate_id=candidate_id,
        candidate_type="observation",
        summary=f"candidate {candidate_id}",
        source_type=SourceType.SENSOR_OBSERVED,
        confidence=0.9,
        features=features,
    )


def table_count(engine: MnemeMemory, table: str) -> int:
    row = engine.store.conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()
    return int(row["count"])


def test_memory_lifecycle_event_kind_maps_to_memory_topic():
    event = memory_lifecycle_event(
        source="memory_promoter",
        lifecycle_stage="promotion",
        payload={"decision": "episode"},
        timestamp=1000,
    )
    assert event.kind == RuntimeEventKind.MEMORY_LIFECYCLE
    assert event.topic == RuntimeTopic.MEMORY
    assert event.payload["lifecycle_stage"] == "promotion"


def test_echo_only_candidate_is_not_stored(tmp_path):
    engine = open_engine(tmp_path)
    promoter = MemoryPromoter(engine)

    outcome = promoter.promote(make_candidate("cand_echo", {"novelty": 0.2}))

    assert isinstance(outcome, PromotionOutcome)
    assert outcome.decision == "echo_only"
    assert outcome.trace_id is None
    assert outcome.episode_id is None
    assert outcome.semantic_candidate is False
    assert table_count(engine, "raw_trace") == 0
    assert table_count(engine, "episode") == 0
    engine.close()


def test_working_memory_candidate_stores_trace_only(tmp_path):
    engine = open_engine(tmp_path)
    promoter = MemoryPromoter(engine)

    outcome = promoter.promote(
        make_candidate("cand_working", {"novelty": 0.7, "task_relevance": 0.9})
    )

    assert outcome.decision == "working_memory_candidate"
    assert outcome.trace_id is not None
    assert outcome.episode_id is None
    assert table_count(engine, "raw_trace") == 1
    assert table_count(engine, "episode") == 0
    engine.close()


def test_episode_candidate_stores_trace_and_episode(tmp_path):
    engine = open_engine(tmp_path)
    promoter = MemoryPromoter(engine)

    outcome = promoter.promote(
        make_candidate(
            "cand_episode",
            {"novelty": 1.0, "task_relevance": 1.0, "social_relevance": 1.0},
        )
    )

    assert outcome.decision == "episode"
    assert outcome.trace_id is not None
    assert outcome.episode_id is not None
    assert outcome.semantic_candidate is False
    episode = engine.store.get_episode(outcome.episode_id)
    assert episode is not None
    assert episode.summary == "candidate cand_episode"
    engine.close()


def test_explicit_remember_flags_semantic_candidate(tmp_path):
    engine = open_engine(tmp_path)
    promoter = MemoryPromoter(engine)

    outcome = promoter.promote(
        make_candidate("cand_semantic", {"explicit_remember_flag": 1.0})
    )

    assert outcome.decision == "episode_and_semantic_candidate"
    assert outcome.trace_id is not None
    assert outcome.episode_id is not None
    assert outcome.semantic_candidate is True
    engine.close()


def test_promoter_handles_bus_candidate_events_and_publishes_lifecycle(tmp_path):
    engine = open_engine(tmp_path)
    clock = FixedClock(1000)
    bus = EventBus(clock=clock)
    promoter = MemoryPromoter(engine, bus=bus)
    promoter.attach_to_bus(bus)

    bus.publish(
        memory_candidate_event(
            source="test_worker",
            candidate=make_candidate("cand_bus", {"explicit_remember_flag": 1.0}),
            timestamp=1000,
        )
    )

    assert promoter.stats["handled"] == 1
    assert table_count(engine, "episode") == 1

    lifecycle_events = bus.history(kinds=[RuntimeEventKind.MEMORY_LIFECYCLE])
    assert len(lifecycle_events) == 1
    payload = lifecycle_events[0].payload
    assert payload["lifecycle_stage"] == "promotion"
    assert payload["candidate_id"] == "cand_bus"
    assert payload["decision"] == "episode_and_semantic_candidate"
    assert payload["semantic_candidate"] is True
    assert payload["episode_id"] is not None
    assert payload["trace_id"] is not None
    engine.close()


def test_malformed_candidate_event_is_skipped_not_raised(tmp_path):
    engine = open_engine(tmp_path)
    bus = EventBus(clock=FixedClock(1000))
    promoter = MemoryPromoter(engine, bus=bus)
    promoter.attach_to_bus(bus)

    bus.publish(
        RuntimeEvent(
            event_id="evt_bad",
            kind=RuntimeEventKind.MEMORY_CANDIDATE,
            timestamp=1000,
            source="test_worker",
            payload={"unexpected": True},
        )
    )

    assert promoter.stats["handled"] == 0
    assert promoter.stats["skipped"] == 1
    assert table_count(engine, "raw_trace") == 0
    engine.close()


def test_scenario_replay_produces_durable_memory_without_manual_calls(tmp_path):
    engine = open_engine(tmp_path)
    clock = FixedClock(1000)
    bus = EventBus(clock=clock)
    promoter = MemoryPromoter(engine, bus=bus)
    promoter.attach_to_bus(bus)

    ScenarioReplayRunner(bus).replay_file(FIXTURE)

    episodes = engine.store.search_episodes("calibration", limit=5)
    assert len(episodes) == 1
    episode = episodes[0]
    assert episode.summary == "User prefers short calibration prompts."

    chain = engine.store.get_provenance_chain(episode.episode_id, "episode")
    trace_nodes = [
        node for node in chain["nodes"] if node["memory_kind"] == "raw_trace"
    ]
    assert len(trace_nodes) == 1

    lifecycle_events = bus.history(kinds=[RuntimeEventKind.MEMORY_LIFECYCLE])
    assert [event.payload["decision"] for event in lifecycle_events] == [
        "episode_and_semantic_candidate"
    ]
    engine.close()
