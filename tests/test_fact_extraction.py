from __future__ import annotations

import time
from pathlib import Path

from android_brain_memory import MnemeMemory
from android_brain_memory.extraction import (
    FactExtractionReport,
    FactExtractor,
    statement_fact_id,
)
from android_brain_memory.models import Episode, Fact, MemoryCandidate, SourceType
from android_brain_memory.promotion import MemoryPromoter
from android_brain_memory.runtime import (
    EventBus,
    RuntimeEventKind,
    memory_candidate_event,
)


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


def store_episode_with_statements(engine: MnemeMemory, statements: list) -> Episode:
    now = int(time.time())
    episode = Episode(
        episode_id="ep_statements",
        start_ts=now,
        end_ts=now + 1,
        summary="User stated preferences.",
        context={"topic": "preferences", "statements": statements},
        salience=0.85,
        confidence=0.96,
        participants=["user"],
    )
    engine.add_episode(episode, source_type=SourceType.SENSOR_OBSERVED)
    return episode


def test_statement_fact_id_is_deterministic_and_content_derived():
    first = statement_fact_id("user", "likes", "tea")
    second = statement_fact_id("user", "likes", "tea")
    different = statement_fact_id("user", "likes", "coffee")

    assert first == second
    assert first != different
    assert first.startswith("fact_")


def test_extracts_model_inferred_facts_with_provenance(tmp_path):
    engine = open_engine(tmp_path)
    episode = store_episode_with_statements(
        engine,
        [
            {"subject": "user", "predicate": "likes", "value": "tea"},
            {"subject": "user", "predicate": "prefers_prompt_style", "value": "short"},
        ],
    )
    extractor = FactExtractor(engine)

    report = extractor.extract_from_episode(episode.episode_id)

    assert isinstance(report, FactExtractionReport)
    assert report.statements_found == 2
    assert report.facts_upserted == 2
    assert report.conflicts_flagged == 0
    for fact_id in report.fact_ids:
        fact = engine.store.get_fact(fact_id)
        assert fact is not None
        assert fact.source_type == SourceType.MODEL_INFERRED
        assert fact.confidence == 0.75  # capped below episode confidence 0.96
        assert fact.supporting_episode_ids == [episode.episode_id]
        chain = engine.store.get_provenance_chain(fact_id, "fact")
        node_kinds = {node["memory_kind"] for node in chain["nodes"]}
        assert "episode" in node_kinds
    engine.close()


def test_re_extraction_is_idempotent(tmp_path):
    engine = open_engine(tmp_path)
    episode = store_episode_with_statements(
        engine,
        [{"subject": "user", "predicate": "likes", "value": "tea"}],
    )
    extractor = FactExtractor(engine)

    first = extractor.extract_from_episode(episode.episode_id)
    second = extractor.extract_from_episode(episode.episode_id)

    assert first.fact_ids == second.fact_ids
    assert second.conflicts_flagged == 0
    rows = engine.store.conn.execute("SELECT COUNT(*) AS count FROM fact").fetchone()
    assert int(rows["count"]) == 1
    engine.close()


def test_malformed_statements_are_skipped_with_reasons(tmp_path):
    engine = open_engine(tmp_path)
    episode = store_episode_with_statements(
        engine,
        [
            {"subject": "user", "predicate": "likes", "value": "tea"},
            {"subject": "", "predicate": "likes", "value": "x"},
            {"predicate": "likes", "value": "x"},
            "not a mapping",
        ],
    )
    extractor = FactExtractor(engine)

    report = extractor.extract_from_episode(episode.episode_id)

    assert report.statements_found == 4
    assert report.facts_upserted == 1
    assert len(report.skipped) == 3
    engine.close()


def test_extracted_fact_conflicting_with_user_confirmed_is_flagged_not_overwritten(tmp_path):
    engine = open_engine(tmp_path)
    engine.add_fact(
        Fact(
            fact_id="fact_confirmed_tea",
            subject="user",
            predicate="likes",
            object_value={"value": "coffee"},
            confidence=0.95,
            source_type=SourceType.USER_CONFIRMED,
        )
    )
    episode = store_episode_with_statements(
        engine,
        [{"subject": "user", "predicate": "likes", "value": "tea"}],
    )
    extractor = FactExtractor(engine)

    report = extractor.extract_from_episode(episode.episode_id)

    assert report.conflicts_flagged == 1
    confirmed = engine.store.get_fact("fact_confirmed_tea")
    assert confirmed.status.value == "active"
    extracted = engine.store.get_fact(report.fact_ids[0])
    assert extracted.status.value == "conflicted"
    engine.close()


def test_bus_driven_promotion_to_extraction_end_to_end(tmp_path):
    engine = open_engine(tmp_path)
    clock = FixedClock(1000)
    bus = EventBus(clock=clock)
    promoter = MemoryPromoter(engine, bus=bus, clock=clock)
    promoter.attach_to_bus(bus)
    extractor = FactExtractor(engine, bus=bus, clock=clock)
    extractor.attach_to_bus(bus)

    candidate = MemoryCandidate(
        candidate_id="cand_pref",
        candidate_type="user_preference_observation",
        summary="User prefers short prompts.",
        source_type=SourceType.SENSOR_OBSERVED,
        confidence=0.96,
        features={"explicit_remember_flag": 1.0},
        entities=["user"],
        payload={
            "statements": [
                {"subject": "user", "predicate": "prefers_prompt_style", "value": "short"}
            ]
        },
    )
    bus.publish(memory_candidate_event(source="test_worker", candidate=candidate, timestamp=1000))

    facts = engine.store.search_facts("prefers_prompt_style", limit=5)
    assert len(facts) == 1
    assert facts[0].source_type == SourceType.MODEL_INFERRED

    stages = [
        event.payload["lifecycle_stage"]
        for event in bus.history(kinds=[RuntimeEventKind.MEMORY_LIFECYCLE])
    ]
    assert stages == ["promotion", "extraction"]

    extraction_event = bus.history(kinds=[RuntimeEventKind.MEMORY_LIFECYCLE])[-1]
    assert extraction_event.payload["facts_upserted"] == 1
    assert extraction_event.payload["episode_id"] == facts[0].supporting_episode_ids[0]
    engine.close()


def test_extractor_ignores_non_semantic_promotions(tmp_path):
    engine = open_engine(tmp_path)
    clock = FixedClock(1000)
    bus = EventBus(clock=clock)
    promoter = MemoryPromoter(engine, bus=bus, clock=clock)
    promoter.attach_to_bus(bus)
    extractor = FactExtractor(engine, bus=bus, clock=clock)
    extractor.attach_to_bus(bus)

    candidate = MemoryCandidate(
        candidate_id="cand_episode_only",
        candidate_type="observation",
        summary="An ordinary episode.",
        source_type=SourceType.SENSOR_OBSERVED,
        confidence=0.9,
        features={"novelty": 1.0, "task_relevance": 1.0, "social_relevance": 1.0},
        payload={"statements": [{"subject": "user", "predicate": "x", "value": "y"}]},
    )
    bus.publish(memory_candidate_event(source="test_worker", candidate=candidate, timestamp=1000))

    rows = engine.store.conn.execute("SELECT COUNT(*) AS count FROM fact").fetchone()
    assert int(rows["count"]) == 0
    assert extractor.stats["extractions"] == 0
    engine.close()
