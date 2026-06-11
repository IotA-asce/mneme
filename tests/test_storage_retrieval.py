from __future__ import annotations

import time
from pathlib import Path

from android_brain_memory.models import Episode, Fact, MemoryQuery, MemoryStatus, SourceType, Speakability
from android_brain_memory.retrieval import retrieve_memory
from android_brain_memory.storage import MemoryStore, MetaMemoryRecord


MIGRATIONS = Path(__file__).resolve().parents[1] / "storage" / "migrations"


def open_migrated_store(tmp_path) -> MemoryStore:
    store = MemoryStore(tmp_path / "memory.sqlite3")
    store.run_migrations(MIGRATIONS)
    return store


def test_store_trace_episode_and_fact_then_retrieve_bundle(tmp_path):
    store = open_migrated_store(tmp_path)
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
    store = open_migrated_store(tmp_path)
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


def test_structured_fact_retrieval_by_subject(tmp_path):
    store = open_migrated_store(tmp_path)
    store.upsert_fact(
        Fact(
            fact_id="fact_user_coffee",
            subject="user",
            predicate="prefers",
            object_value={"value": "black coffee"},
            confidence=0.9,
            source_type=SourceType.USER_CONFIRMED,
            tags=["preference"],
        )
    )
    store.upsert_fact(
        Fact(
            fact_id="fact_mneme_storage",
            subject="mneme",
            predicate="uses_storage",
            object_value={"value": "sqlite"},
            confidence=0.9,
            source_type=SourceType.SYSTEM_GENERATED,
        )
    )

    bundle = retrieve_memory(
        store,
        MemoryQuery(query_text="", fact_subject="us", include_episodes=True),
    )

    assert [fact.fact_id for fact in bundle.facts] == ["fact_user_coffee"]
    assert bundle.episodes == []
    store.close()


def test_structured_fact_retrieval_by_predicate(tmp_path):
    store = open_migrated_store(tmp_path)
    store.upsert_fact(
        Fact(
            fact_id="fact_user_color",
            subject="user",
            predicate="prefers_color",
            object_value={"value": "green"},
            confidence=0.8,
            source_type=SourceType.USER_CONFIRMED,
        )
    )
    store.upsert_fact(
        Fact(
            fact_id="fact_user_location",
            subject="user",
            predicate="lives_near",
            object_value={"value": "lab"},
            confidence=0.8,
            source_type=SourceType.USER_CONFIRMED,
        )
    )

    bundle = retrieve_memory(store, MemoryQuery(query_text="", fact_predicate="color"))

    assert [fact.fact_id for fact in bundle.facts] == ["fact_user_color"]
    store.close()


def test_structured_fact_retrieval_by_object_text_and_tags(tmp_path):
    store = open_migrated_store(tmp_path)
    store.upsert_fact(
        Fact(
            fact_id="fact_user_breakfast",
            subject="user",
            predicate="prefers_food",
            object_value={"value": "oatmeal with berries"},
            confidence=0.8,
            source_type=SourceType.USER_CONFIRMED,
            tags=["food", "preference"],
        )
    )
    store.upsert_fact(
        Fact(
            fact_id="fact_user_music",
            subject="user",
            predicate="prefers_music",
            object_value={"value": "jazz"},
            confidence=0.8,
            source_type=SourceType.USER_CONFIRMED,
            tags=["music", "preference"],
        )
    )

    bundle = retrieve_memory(
        store,
        MemoryQuery(query_text="", fact_object_text="berries", tags=["food"]),
    )

    assert [fact.fact_id for fact in bundle.facts] == ["fact_user_breakfast"]
    assert bundle.facts[0].tags == ["food", "preference"]
    store.close()


def test_user_confirmed_facts_outrank_inferred_facts_when_relevance_is_similar(tmp_path):
    store = open_migrated_store(tmp_path)
    store.upsert_fact(
        Fact(
            fact_id="fact_inferred_theme",
            subject="user",
            predicate="prefers_interface_theme",
            object_value={"value": "dark mode"},
            confidence=0.99,
            source_type=SourceType.MODEL_INFERRED,
        )
    )
    store.upsert_fact(
        Fact(
            fact_id="fact_confirmed_theme",
            subject="user",
            predicate="prefers_interface_theme",
            object_value={"value": "dark mode"},
            confidence=0.75,
            source_type=SourceType.USER_CONFIRMED,
        )
    )

    bundle = retrieve_memory(
        store,
        MemoryQuery(query_text="", fact_subject="user", fact_predicate="theme", max_results=2),
    )
    inferred_only = retrieve_memory(
        store,
        MemoryQuery(
            query_text="",
            fact_subject="user",
            fact_predicate="theme",
            fact_source_type=SourceType.MODEL_INFERRED,
        ),
    )

    assert [fact.fact_id for fact in bundle.facts] == [
        "fact_confirmed_theme",
        "fact_inferred_theme",
    ]
    assert [fact.fact_id for fact in inferred_only.facts] == ["fact_inferred_theme"]
    store.close()


def test_structured_fact_retrieval_filters_status_by_default_and_explicit_status(tmp_path):
    store = open_migrated_store(tmp_path)
    store.upsert_fact(
        Fact(
            fact_id="fact_active_preference",
            subject="user",
            predicate="prefers",
            object_value={"value": "tea"},
            confidence=0.8,
            source_type=SourceType.USER_CONFIRMED,
            status=MemoryStatus.ACTIVE,
        )
    )
    store.upsert_fact(
        Fact(
            fact_id="fact_conflicted_preference",
            subject="user",
            predicate="prefers",
            object_value={"value": "coffee"},
            confidence=0.8,
            source_type=SourceType.USER_CONFIRMED,
            status=MemoryStatus.CONFLICTED,
        )
    )
    store.upsert_fact(
        Fact(
            fact_id="fact_suppressed_preference",
            subject="user",
            predicate="prefers",
            object_value={"value": "private topic"},
            confidence=0.8,
            source_type=SourceType.USER_CONFIRMED,
            status=MemoryStatus.SUPPRESSED,
        )
    )
    store.upsert_fact(
        Fact(
            fact_id="fact_superseded_preference",
            subject="user",
            predicate="prefers",
            object_value={"value": "old preference"},
            confidence=0.8,
            source_type=SourceType.USER_CONFIRMED,
            status=MemoryStatus.SUPERSEDED,
        )
    )
    store.upsert_fact(
        Fact(
            fact_id="fact_purged_preference",
            subject="user",
            predicate="prefers",
            object_value={"value": "purged topic"},
            confidence=0.8,
            source_type=SourceType.USER_CONFIRMED,
            status=MemoryStatus.PURGED,
        )
    )

    default_bundle = retrieve_memory(store, MemoryQuery(query_text="", fact_predicate="prefers"))
    conflicted_bundle = retrieve_memory(
        store,
        MemoryQuery(query_text="", fact_predicate="prefers", fact_status=MemoryStatus.CONFLICTED),
    )

    assert [fact.fact_id for fact in default_bundle.facts] == ["fact_active_preference"]
    assert [fact.fact_id for fact in conflicted_bundle.facts] == ["fact_conflicted_preference"]
    assert conflicted_bundle.warnings == [
        "returned non-active fact status(es) due to explicit status filter: conflicted"
    ]
    store.close()


def test_reranking_orders_episodes_deterministically_and_explains_factors(tmp_path):
    store = open_migrated_store(tmp_path)
    user_episode = Episode(
        episode_id="ep_user_robot_memory",
        start_ts=10,
        end_ts=20,
        summary="Robot memory calibration with the user.",
        context={"topic": "robot memory", "place": "bench"},
        salience=0.6,
        confidence=0.9,
        participants=["user"],
        objects=["robot"],
    )
    recent_episode = Episode(
        episode_id="ep_recent_robot_memory",
        start_ts=30,
        end_ts=40,
        summary="Robot memory calibration without an entity cue.",
        context={"topic": "robot memory", "place": "bench"},
        salience=0.2,
        confidence=0.6,
        participants=["observer"],
        objects=["robot"],
    )
    store.store_episode(user_episode)
    store.store_episode(recent_episode)

    first_bundle = retrieve_memory(
        store,
        MemoryQuery(query_text="robot memory", entities=["user"], include_facts=False, max_results=2),
    )
    second_bundle = retrieve_memory(
        store,
        MemoryQuery(query_text="robot memory", entities=["user"], include_facts=False, max_results=2),
    )

    assert [episode.episode_id for episode in first_bundle.episodes] == [
        "ep_user_robot_memory",
        "ep_recent_robot_memory",
    ]
    assert [episode.episode_id for episode in second_bundle.episodes] == [
        "ep_user_robot_memory",
        "ep_recent_robot_memory",
    ]
    first_explanation = first_bundle.ranking_explanations[0]
    second_explanation = first_bundle.ranking_explanations[1]
    assert first_explanation["memory_kind"] == "episode"
    assert first_explanation["memory_id"] == "ep_user_robot_memory"
    assert first_explanation["rank"] == 1
    assert first_explanation["factors"]["context_match"] == 1.0
    assert first_explanation["factors"]["entity_match"] == 1.0
    assert first_explanation["factors"]["recency"] == 0.0
    assert second_explanation["factors"]["recency"] == 1.0
    assert first_explanation["score"] > second_explanation["score"]
    assert "entity_match" in first_explanation["components"]
    assert first_explanation["matched_entities"] == ["user"]
    store.close()


def test_retrieval_history_bonus_reranks_similar_facts_and_is_explained(tmp_path):
    store = open_migrated_store(tmp_path)
    store.upsert_fact(
        Fact(
            fact_id="fact_plain_memory_tool",
            subject="user",
            predicate="uses_memory_tool",
            object_value={"value": "memory notebook"},
            confidence=0.8,
            source_type=SourceType.USER_CONFIRMED,
        )
    )
    store.upsert_fact(
        Fact(
            fact_id="fact_history_memory_tool",
            subject="user",
            predicate="uses_memory_tool",
            object_value={"value": "memory notebook"},
            confidence=0.8,
            source_type=SourceType.USER_CONFIRMED,
        )
    )
    store.write_meta_memory(
        MetaMemoryRecord(
            memory_id="fact_history_memory_tool",
            memory_kind="fact",
            source_type=SourceType.USER_CONFIRMED,
            provenance={"source": "test"},
            last_retrieved_ts=100,
            retrieval_count=5,
        )
    )

    bundle = retrieve_memory(
        store,
        MemoryQuery(query_text="", fact_subject="user", fact_object_text="memory notebook", max_results=2),
    )

    assert [fact.fact_id for fact in bundle.facts] == [
        "fact_history_memory_tool",
        "fact_plain_memory_tool",
    ]
    first_explanation = bundle.ranking_explanations[0]
    second_explanation = bundle.ranking_explanations[1]
    assert first_explanation["memory_kind"] == "fact"
    assert first_explanation["memory_id"] == "fact_history_memory_tool"
    assert first_explanation["factors"]["retrieval_history_bonus"] == 0.5
    assert first_explanation["components"]["retrieval_history_bonus"] == 0.025
    assert first_explanation["meta_memory"]["retrieval_count"] == 5
    assert second_explanation["factors"]["retrieval_history_bonus"] == 0.0
    assert first_explanation["score"] > second_explanation["score"]
    store.close()


def test_retrieval_updates_meta_memory_counts_for_returned_items(tmp_path):
    store = open_migrated_store(tmp_path)
    episode = Episode(
        episode_id="ep_counter",
        start_ts=10,
        end_ts=20,
        summary="Counter memory episode.",
        context={"topic": "counter memory"},
        salience=0.7,
        confidence=0.9,
    )
    fact = Fact(
        fact_id="fact_counter",
        subject="mneme",
        predicate="tracks_counter",
        object_value={"value": "counter memory"},
        confidence=0.9,
        source_type=SourceType.SYSTEM_GENERATED,
    )
    store.store_episode(episode)
    store.upsert_fact(fact)

    first = retrieve_memory(store, MemoryQuery(query_text="counter memory", max_results=2))
    second = retrieve_memory(store, MemoryQuery(query_text="counter memory", max_results=2))

    assert [fact.fact_id for fact in first.facts] == ["fact_counter"]
    assert [episode.episode_id for episode in second.episodes] == ["ep_counter"]
    fact_meta = store.get_meta_memory("fact_counter", "fact")
    episode_meta = store.get_meta_memory("ep_counter", "episode")
    assert fact_meta is not None
    assert episode_meta is not None
    assert fact_meta.retrieval_count == 2
    assert episode_meta.retrieval_count == 2
    assert fact_meta.last_retrieved_ts is not None
    assert episode_meta.last_retrieved_ts is not None
    store.close()


def test_retrieval_filters_internal_speakability_without_trusted_override(tmp_path):
    store = open_migrated_store(tmp_path)
    store.upsert_fact(
        Fact(
            fact_id="fact_normal_policy",
            subject="mneme",
            predicate="policy",
            object_value={"value": "normal policy"},
            confidence=0.9,
            source_type=SourceType.SYSTEM_GENERATED,
        ),
        speakability=Speakability.NORMAL,
    )
    store.upsert_fact(
        Fact(
            fact_id="fact_restricted_policy",
            subject="mneme",
            predicate="policy",
            object_value={"value": "restricted policy"},
            confidence=0.9,
            source_type=SourceType.SYSTEM_GENERATED,
        ),
        speakability=Speakability.RESTRICTED,
    )
    store.upsert_fact(
        Fact(
            fact_id="fact_never_say_policy",
            subject="mneme",
            predicate="policy",
            object_value={"value": "never say policy"},
            confidence=0.9,
            source_type=SourceType.SYSTEM_GENERATED,
        ),
        speakability=Speakability.NEVER_SAY,
    )
    store.upsert_fact(
        Fact(
            fact_id="fact_internal_only_policy",
            subject="mneme",
            predicate="policy",
            object_value={"value": "internal only policy"},
            confidence=0.9,
            source_type=SourceType.SYSTEM_GENERATED,
        ),
        speakability=Speakability.INTERNAL_ONLY,
    )

    default_bundle = retrieve_memory(
        store,
        MemoryQuery(query_text="", fact_subject="mneme", fact_predicate="policy", max_results=10),
    )
    untrusted_internal_request = retrieve_memory(
        store,
        MemoryQuery(
            query_text="",
            fact_subject="mneme",
            fact_predicate="policy",
            max_results=10,
            include_internal=True,
        ),
    )
    trusted_internal_bundle = retrieve_memory(
        store,
        MemoryQuery(
            query_text="",
            fact_subject="mneme",
            fact_predicate="policy",
            max_results=10,
            trusted_internal=True,
            include_internal=True,
        ),
    )

    assert [fact.fact_id for fact in default_bundle.facts] == [
        "fact_normal_policy",
        "fact_restricted_policy",
    ]
    assert [fact.fact_id for fact in untrusted_internal_request.facts] == [
        "fact_normal_policy",
        "fact_restricted_policy",
    ]
    assert [fact.fact_id for fact in trusted_internal_bundle.facts] == [
        "fact_normal_policy",
        "fact_restricted_policy",
        "fact_internal_only_policy",
        "fact_never_say_policy",
    ]
    hidden_meta = store.get_meta_memory("fact_never_say_policy", "fact")
    assert hidden_meta is not None
    assert hidden_meta.retrieval_count == 1
    store.close()
