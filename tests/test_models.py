from __future__ import annotations

import json

import pytest

from android_brain_memory.models import (
    Episode,
    Fact,
    MemoryBundle,
    MemoryCandidate,
    MemoryQuery,
    MemoryStatus,
    SalienceFeatures,
    Speakability,
    SourceType,
    parse_memory_status,
    parse_speakability,
    parse_source_type,
    validate_confidence,
    validate_salience,
    validate_timestamp,
)


def sample_candidate() -> MemoryCandidate:
    return MemoryCandidate(
        candidate_id="cand_001",
        candidate_type="dialogue",
        summary="User asked Mneme to remember a preference.",
        source_type=SourceType.USER_CONFIRMED,
        confidence=0.95,
        features=SalienceFeatures(novelty=0.7, explicit_remember_flag=1.0),
        entities=["user"],
        tags=["preference"],
        payload={"text": "remember this"},
        provenance_refs=["trace_001"],
    )


def sample_episode() -> Episode:
    return Episode(
        episode_id="ep_001",
        start_ts=10,
        end_ts=12,
        summary="User confirmed a memory preference.",
        context={"topic": "memory"},
        salience=0.8,
        confidence=0.9,
        participants=["user"],
        objects=["memory"],
        provenance_refs=["trace_001"],
    )


def sample_fact() -> Fact:
    return Fact(
        fact_id="fact_001",
        subject="user",
        predicate="prefers",
        object_value={"value": "selective memory"},
        confidence=0.9,
        source_type=SourceType.USER_CONFIRMED,
        status=MemoryStatus.ACTIVE,
        tags=["preference"],
        supporting_episode_ids=["ep_001"],
    )


def test_valid_domain_models_accept_expected_values():
    candidate = sample_candidate()
    episode = sample_episode()
    fact = sample_fact()
    query = MemoryQuery(query_text="memory", entities=["user"], tags=["preference"])
    bundle = MemoryBundle(
        query_id="query_001",
        summary="found memory",
        facts=[fact],
        episodes=[episode],
        provenance_summary="local test data",
    )

    assert candidate.source_type == SourceType.USER_CONFIRMED
    assert episode.salience == 0.8
    assert fact.status == MemoryStatus.ACTIVE
    assert query.max_results == 5
    assert bundle.facts == [fact]


@pytest.mark.parametrize("value", [-0.1, 1.1, float("nan"), "0.5", True])
def test_invalid_confidence_values_are_rejected(value):
    with pytest.raises(ValueError):
        validate_confidence(value)

    with pytest.raises(ValueError):
        Fact(
            fact_id="fact_bad_confidence",
            subject="user",
            predicate="prefers",
            object_value={"value": "memory"},
            confidence=value,
            source_type=SourceType.USER_CONFIRMED,
        )


@pytest.mark.parametrize("value", [-0.1, 1.1, float("inf"), "0.5", False])
def test_invalid_salience_values_are_rejected(value):
    with pytest.raises(ValueError):
        validate_salience(value)

    with pytest.raises(ValueError):
        SalienceFeatures(novelty=value)


@pytest.mark.parametrize("summary", ["", "   "])
def test_empty_summaries_are_rejected(summary):
    with pytest.raises(ValueError):
        MemoryCandidate(
            candidate_id="cand_bad_summary",
            candidate_type="dialogue",
            summary=summary,
            source_type=SourceType.USER_CONFIRMED,
            confidence=0.8,
            features=SalienceFeatures(),
        )

    with pytest.raises(ValueError):
        Episode(
            episode_id="ep_bad_summary",
            start_ts=1,
            end_ts=1,
            summary=summary,
            context={},
            salience=0.5,
            confidence=0.8,
        )


def test_timestamp_validation_and_ordering():
    assert validate_timestamp(0, "created_ts") == 0

    with pytest.raises(ValueError):
        validate_timestamp(-1, "created_ts")

    with pytest.raises(ValueError):
        validate_timestamp(1.5, "created_ts")

    with pytest.raises(ValueError):
        Episode(
            episode_id="ep_bad_time",
            start_ts=20,
            end_ts=19,
            summary="End timestamp is before start.",
            context={},
            salience=0.5,
            confidence=0.8,
        )


def test_enum_conversion_and_invalid_enum_values():
    assert parse_source_type("user_confirmed") == SourceType.USER_CONFIRMED
    assert parse_memory_status("conflicted") == MemoryStatus.CONFLICTED
    assert parse_speakability("never_say") == Speakability.NEVER_SAY

    fact = Fact(
        fact_id="fact_enum",
        subject="user",
        predicate="prefers",
        object_value={"value": "memory"},
        confidence=0.8,
        source_type="user_confirmed",
        status="superseded",
    )
    assert fact.source_type == SourceType.USER_CONFIRMED
    assert fact.status == MemoryStatus.SUPERSEDED

    with pytest.raises(ValueError):
        parse_source_type("untrusted_guess")

    with pytest.raises(ValueError):
        parse_memory_status("archived")

    with pytest.raises(ValueError):
        parse_speakability("public")


def assert_json_round_trip(model):
    payload = model.to_dict()
    json_payload = json.loads(json.dumps(payload))
    assert type(model).from_dict(json_payload) == model


def test_serialization_round_trips_for_domain_models():
    candidate = sample_candidate()
    episode = sample_episode()
    fact = sample_fact()
    query = MemoryQuery(
        query_text="memory",
        requester="executive",
        query_type="topic",
        entities=["user"],
        tags=["preference"],
        fact_subject="user",
        fact_predicate="prefers",
        fact_object_text="memory",
        fact_source_type=SourceType.USER_CONFIRMED,
        fact_status=MemoryStatus.ACTIVE,
        max_results=3,
        include_summaries=False,
        trusted_internal=True,
        include_internal=True,
    )
    bundle = MemoryBundle(
        query_id="query_001",
        summary="found 1 fact and 1 episode",
        facts=[fact],
        episodes=[episode],
        warnings=["low confidence nearby memory omitted"],
        ranking_explanations=[
            {
                "rank": 1,
                "memory_kind": "fact",
                "memory_id": fact.fact_id,
                "score": 0.9,
            }
        ],
        provenance_summary="fact fact_001 is supported by ep_001",
    )

    for model in (candidate, episode, fact, query, bundle):
        assert_json_round_trip(model)


def test_from_dict_applies_optional_defaults_without_hiding_invalid_required_data():
    query = MemoryQuery.from_dict({"query_text": "memory"})
    assert query.requester == "unknown"
    assert query.query_type == "general"
    assert query.max_results == 5
    assert query.include_episodes is True
    assert query.include_facts is True
    assert query.include_summaries is True

    with pytest.raises(ValueError):
        MemoryCandidate.from_dict(
            {
                "candidate_id": "cand_missing_summary",
                "candidate_type": "dialogue",
                "source_type": "user_confirmed",
                "confidence": 0.8,
                "features": {},
            }
        )

    with pytest.raises(ValueError):
        MemoryQuery.from_dict({"query_text": "memory", "max_results": 0})
