from __future__ import annotations

from pathlib import Path

from android_brain_memory import (
    Episode,
    Fact,
    MemoryBundle,
    MemoryStore,
    SourceType,
    Speakability,
    build_cognitive_context,
)
from android_brain_memory.executive import ExecutiveIntent, ExecutiveMode


MIGRATIONS = Path(__file__).resolve().parents[1] / "storage" / "migrations"


def open_store(tmp_path) -> MemoryStore:
    store = MemoryStore(tmp_path / "memory.sqlite3")
    store.run_migrations(MIGRATIONS)
    return store


def respond_intent() -> ExecutiveIntent:
    return ExecutiveIntent(
        intent_id="intent_001",
        intent_type="respond_to_user",
        mode=ExecutiveMode.NORMAL,
        priority=70,
        created_ts=10_000,
        payload={"dialogue_turn": {"speaker": "user", "text": "what do I like", "timestamp": 10_000}},
    )


def fact(fact_id: str, value: str, *, source_type: SourceType = SourceType.USER_CONFIRMED) -> Fact:
    return Fact(
        fact_id=fact_id,
        subject="user",
        predicate="likes",
        object_value={"value": value},
        confidence=0.9,
        source_type=source_type,
    )


def test_cognitive_context_orders_memories_and_includes_provenance(tmp_path):
    store = open_store(tmp_path)
    first = fact("fact_tea", "tea")
    second = fact("fact_coffee", "coffee", source_type=SourceType.MODEL_INFERRED)
    store.upsert_fact(first, provenance={"source_id": "trace_1"}, notes="user statement")
    store.upsert_fact(second, provenance={"source_id": "trace_2"}, notes="model inference")
    episode = Episode(
        episode_id="ep_tea",
        start_ts=9_000,
        end_ts=9_100,
        summary="User discussed tea with Mneme.",
        context={"topic": "tea"},
        salience=0.8,
        confidence=0.85,
        participants=["user"],
    )
    store.store_episode(episode, source_type=SourceType.SENSOR_OBSERVED)
    summary = store.store_memory_summary(
        summary_id="summary_tea",
        summary_type="preference",
        scope_key="topic:tea",
        summary="User has a recurring tea preference.",
        confidence=0.8,
    )

    bundle = MemoryBundle(
        query_id="query_001",
        summary="found memories",
        facts=[first, second],
        episodes=[episode],
        summaries=[summary.to_dict()],
        ranking_explanations=[
            {"memory_kind": "fact", "memory_id": "fact_tea", "rank": 1, "score": 0.9},
            {"memory_kind": "episode", "memory_id": "ep_tea", "rank": 3, "score": 0.7},
        ],
        provenance_summary="fact fact_tea supported_by raw_trace trace_1",
    )

    packet = build_cognitive_context(
        user_utterance="what do I like",
        intent=respond_intent(),
        bundle=bundle,
        working={"topic": "tea", "created_ts": 10_000},
        attention={"selected_target_id": "speaker:user"},
        avatar={"mode": "listening"},
        store=store,
    )

    assert [(memory.memory_kind, memory.memory_id) for memory in packet.memories] == [
        ("fact", "fact_tea"),
        ("fact", "fact_coffee"),
        ("episode", "ep_tea"),
        ("summary", "summary_tea"),
    ]
    assert packet.memories[0].source_type == "user_confirmed"
    assert packet.memories[0].provenance
    assert packet.memories[0].ranking["score"] == 0.9
    assert packet.provenance_summary == "fact fact_tea supported_by raw_trace trace_1"


def test_cognitive_context_filters_internal_and_redacts_restricted(tmp_path):
    store = open_store(tmp_path)
    open_fact = fact("fact_open", "tea")
    restricted_fact = fact("fact_restricted", "medical detail")
    internal_fact = fact("fact_internal", "private diagnostic")
    never_fact = fact("fact_never", "never say this")
    store.upsert_fact(open_fact)
    store.upsert_fact(restricted_fact, speakability=Speakability.RESTRICTED)
    store.upsert_fact(internal_fact, speakability=Speakability.INTERNAL_ONLY)
    store.upsert_fact(never_fact, speakability=Speakability.NEVER_SAY)
    bundle = MemoryBundle(
        query_id="query_001",
        summary="found memories",
        facts=[open_fact, restricted_fact, internal_fact, never_fact],
    )

    packet = build_cognitive_context(
        user_utterance="what do I like",
        intent=respond_intent(),
        bundle=bundle,
        store=store,
    )

    visible = {memory.memory_id: memory for memory in packet.memories}
    omitted = {memory.memory_id: memory for memory in packet.omitted_memories}
    assert visible["fact_open"].text.endswith("tea")
    assert visible["fact_restricted"].text == "restricted memory exists"
    assert visible["fact_restricted"].redacted is True
    assert "medical detail" not in packet.to_dict()["memories"][1]["text"]
    assert omitted["fact_internal"].reason == "withheld_by_speakability"
    assert omitted["fact_never"].reason == "withheld_by_speakability"


def test_cognitive_context_trusted_internal_can_include_internal_memory(tmp_path):
    store = open_store(tmp_path)
    internal_fact = fact("fact_internal", "private diagnostic")
    store.upsert_fact(internal_fact, speakability=Speakability.INTERNAL_ONLY)
    bundle = MemoryBundle(query_id="query_001", summary="found", facts=[internal_fact])

    packet = build_cognitive_context(
        user_utterance="internal check",
        intent=respond_intent(),
        bundle=bundle,
        store=store,
        trusted_internal=True,
    )

    assert packet.memories[0].memory_id == "fact_internal"
    assert packet.memories[0].text.endswith("private diagnostic")
    assert packet.omitted_memories == []


def test_cognitive_context_enforces_budget_deterministically(tmp_path):
    store = open_store(tmp_path)
    facts = [fact(f"fact_{index}", "x" * 200) for index in range(5)]
    for item in facts:
        store.upsert_fact(item)
    bundle = MemoryBundle(query_id="query_001", summary="found", facts=facts)

    first = build_cognitive_context(
        user_utterance="what do I like",
        intent=respond_intent(),
        bundle=bundle,
        store=store,
        char_budget=1_400,
    )
    second = build_cognitive_context(
        user_utterance="what do I like",
        intent=respond_intent(),
        bundle=bundle,
        store=store,
        char_budget=1_400,
    )

    assert first.truncated is True
    assert first.to_dict() == second.to_dict()
    assert first.serialized_chars() <= first.char_budget or first.memories == []
    assert any(item.reason == "omitted_due_to_context_budget" for item in first.omitted_memories)
