from __future__ import annotations

import json
from pathlib import Path

from android_brain_memory.models import (
    Episode,
    Fact,
    MemoryBundle,
    MemoryCandidate,
    MemoryQuery,
    SalienceFeatures,
    SourceType,
)
from android_brain_memory.runtime import RuntimeEvent, RuntimeEventKind
from android_brain_memory.storage import MemorySummaryRecord


INTERFACES = Path(__file__).resolve().parents[1] / "interfaces"


def msg_field_names(relative_path: str) -> list[str]:
    text = (INTERFACES / relative_path).read_text(encoding="utf-8")
    fields = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or line == "---":
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        fields.append(parts[1])
    return [field for field in fields if field != "header"]


def sample_features() -> SalienceFeatures:
    return SalienceFeatures(novelty=0.5, task_relevance=0.4, explicit_remember_flag=1.0)


def sample_candidate() -> MemoryCandidate:
    return MemoryCandidate(
        candidate_id="cand_1",
        candidate_type="speech",
        summary="User asked to be remembered.",
        source_type=SourceType.USER_CONFIRMED,
        confidence=0.9,
        features=sample_features(),
        entities=["user"],
        tags=["dialogue"],
        payload={"utterance": "remember this"},
        provenance_refs=["trace_1"],
    )


def sample_episode() -> Episode:
    return Episode(
        episode_id="ep_1",
        start_ts=100,
        end_ts=110,
        summary="A short exchange.",
        context={"topic": "greeting"},
        salience=0.7,
        confidence=0.9,
        participants=["user"],
        objects=["mug"],
        provenance_refs=["trace_1"],
    )


def sample_fact() -> Fact:
    return Fact(
        fact_id="fact_1",
        subject="user",
        predicate="likes",
        object_value={"value": "tea"},
        confidence=0.95,
        source_type=SourceType.USER_CONFIRMED,
        tags=["preference"],
        supporting_episode_ids=["ep_1"],
        supersedes_fact_id="fact_0",
    )


def sample_query() -> MemoryQuery:
    return MemoryQuery(query_text="tea", entities=["user"], tags=["preference"])


def sample_summary_record() -> MemorySummaryRecord:
    return MemorySummaryRecord(
        summary_id="summary_1",
        summary_type="repeated_episode",
        scope_key="topic:tea",
        summary="User repeatedly mentions tea.",
        confidence=0.8,
        start_ts=100,
        end_ts=200,
        created_ts=300,
    )


def sample_bundle() -> MemoryBundle:
    return MemoryBundle(
        query_id="query_1",
        summary="found 1 fact(s)",
        facts=[sample_fact()],
        episodes=[sample_episode()],
        summaries=[sample_summary_record().to_dict()],
        warnings=["example warning"],
        ranking_explanations=[{"memory_kind": "fact", "memory_id": "fact_1"}],
        provenance_summary="fact fact_1 supported_by episode ep_1",
    )


def sample_runtime_event() -> RuntimeEvent:
    return RuntimeEvent(
        event_id="evt_1",
        kind=RuntimeEventKind.PERCEPTION_OBSERVATION,
        timestamp=1000,
        source="vision_worker",
        payload={"observation_type": "face"},
        confidence=0.9,
        ttl_ms=500,
        sequence=1,
    )


# msg field -> model to_dict key, where the names differ.
# Dict-valued model fields map to "*_json" string fields in the drafts.
# Derived keys are produced by to_dict() but intentionally absent from messages.
INTERFACE_CONTRACTS = [
    (
        "msg/SalienceFeatures.msg",
        sample_features().to_dict(),
        {},
        set(),
    ),
    (
        "msg/MemoryCandidate.msg",
        sample_candidate().to_dict(),
        {"payload_json": "payload"},
        set(),
    ),
    (
        "msg/Episode.msg",
        sample_episode().to_dict(),
        {"start_time": "start_ts", "end_time": "end_ts", "context_json": "context"},
        set(),
    ),
    (
        "msg/Fact.msg",
        sample_fact().to_dict(),
        {"object_json": "object_value"},
        set(),
    ),
    (
        "msg/MemoryQuery.msg",
        sample_query().to_dict(),
        {},
        set(),
    ),
    (
        "msg/MemorySummary.msg",
        sample_summary_record().to_dict(),
        {"start_time": "start_ts", "end_time": "end_ts", "created_time": "created_ts"},
        set(),
    ),
    (
        "msg/MemoryBundle.msg",
        sample_bundle().to_dict(),
        {"ranking_explanations_json": "ranking_explanations"},
        set(),
    ),
    (
        "msg/RuntimeEvent.msg",
        sample_runtime_event().to_dict(),
        {"payload_json": "payload"},
        {"expires_at"},
    ),
]


def test_interface_drafts_align_with_domain_models():
    for relative_path, model_dict, overrides, derived_keys in INTERFACE_CONTRACTS:
        fields = msg_field_names(relative_path)
        assert fields, f"{relative_path} declares no fields"
        mapped_keys = [overrides.get(field, field) for field in fields]

        unknown = [key for key in mapped_keys if key not in model_dict]
        assert not unknown, f"{relative_path} has fields without model keys: {unknown}"

        expected_keys = set(model_dict) - derived_keys
        missing = sorted(expected_keys - set(mapped_keys))
        assert not missing, f"{relative_path} is missing model fields: {missing}"

        assert len(mapped_keys) == len(set(mapped_keys)), f"{relative_path} maps a key twice"


def test_upsert_fact_service_reports_conflicts():
    fields = msg_field_names("srv/UpsertFact.srv")
    assert "conflict_report_json" in fields


def test_models_round_trip_through_json():
    samples = [
        (MemoryCandidate, sample_candidate()),
        (Episode, sample_episode()),
        (Fact, sample_fact()),
        (MemoryQuery, sample_query()),
        (MemoryBundle, sample_bundle()),
        (RuntimeEvent, sample_runtime_event()),
    ]
    for model_type, instance in samples:
        encoded = json.dumps(instance.to_dict(), sort_keys=True)
        rebuilt = model_type.from_dict(json.loads(encoded))
        assert rebuilt.to_dict() == instance.to_dict(), model_type.__name__
