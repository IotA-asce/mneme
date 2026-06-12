from __future__ import annotations

from pathlib import Path

from android_brain_memory import MnemeMemory
from android_brain_memory.models import MemoryQuery, MemoryStatus, SourceType
from android_brain_memory.self_model import ProceduralMemory, SelfModel


MIGRATIONS = Path(__file__).resolve().parents[1] / "storage" / "migrations"


def open_engine(tmp_path) -> MnemeMemory:
    engine = MnemeMemory(tmp_path / "memory.sqlite3", migrations_dir=MIGRATIONS)
    engine.init_db()
    return engine


def test_identity_fact_create_read_and_in_place_update(tmp_path):
    engine = open_engine(tmp_path)
    self_model = SelfModel(engine)

    self_model.set_identity_fact("name", "Mneme", source_type=SourceType.USER_CONFIRMED)
    fact = self_model.get_identity("name")
    assert fact is not None
    assert fact.subject == "self"
    assert fact.object_value["value"] == "Mneme"

    # deliberate update replaces in place: same fact id, no conflict
    self_model.set_identity_fact("name", "Mneme Mark II", source_type=SourceType.USER_CONFIRMED)
    updated = self_model.get_identity("name")
    assert updated.fact_id == fact.fact_id
    assert updated.object_value["value"] == "Mneme Mark II"
    assert updated.status == MemoryStatus.ACTIVE
    engine.close()


def test_identity_facts_listed_and_described_deterministically(tmp_path):
    engine = open_engine(tmp_path)
    self_model = SelfModel(engine)
    self_model.set_identity_fact("name", "Mneme")
    self_model.set_identity_fact("capability", "remembering conversations")
    self_model.set_identity_fact("limitation", "no actuators yet")

    facts = self_model.identity_facts()
    assert [fact.predicate for fact in facts] == ["capability", "limitation", "name"]

    description = self_model.describe()
    assert "name: Mneme" in description
    assert "capability: remembering conversations" in description
    assert self_model.describe() == description  # deterministic
    engine.close()


def test_self_facts_answerable_through_ordinary_retrieval(tmp_path):
    engine = open_engine(tmp_path)
    SelfModel(engine).set_identity_fact("name", "Mneme")

    bundle = engine.retrieve(MemoryQuery(query_text="", fact_subject="self"))

    assert [fact.predicate for fact in bundle.facts] == ["name"]
    engine.close()


def test_procedural_parameter_versioning_with_supersession_chain(tmp_path):
    engine = open_engine(tmp_path)
    procedures = ProceduralMemory(engine)

    first = procedures.set_parameter("gaze", "dwell_ms", 500, reason="initial default")
    second = procedures.set_parameter("gaze", "dwell_ms", 650, reason="user found gaze jumpy")

    assert procedures.get_parameter("gaze", "dwell_ms") == 650
    assert second.supersedes_fact_id == first.fact_id
    assert engine.store.get_fact(first.fact_id).status == MemoryStatus.SUPERSEDED
    assert engine.store.get_fact(second.fact_id).status == MemoryStatus.ACTIVE

    history = procedures.parameter_history("gaze", "dwell_ms")
    assert [fact.object_value["version"] for fact in history] == [1, 2]
    assert [fact.object_value["value"] for fact in history] == [500, 650]

    meta = engine.store.get_meta_memory(second.fact_id, "fact")
    assert meta.provenance["notes"] == "user found gaze jumpy"
    engine.close()


def test_get_parameter_default_when_unset(tmp_path):
    engine = open_engine(tmp_path)
    procedures = ProceduralMemory(engine)

    assert procedures.get_parameter("gaze", "dwell_ms") is None
    assert procedures.get_parameter("gaze", "dwell_ms", default=400) == 400
    engine.close()


def test_parameters_for_skill_returns_latest_values(tmp_path):
    engine = open_engine(tmp_path)
    procedures = ProceduralMemory(engine)
    procedures.set_parameter("gaze", "dwell_ms", 500)
    procedures.set_parameter("gaze", "saccade_speed", 0.8)
    procedures.set_parameter("gaze", "dwell_ms", 650)
    procedures.set_parameter("blink", "interval_ms", 4000)

    assert procedures.parameters_for_skill("gaze") == {
        "dwell_ms": 650,
        "saccade_speed": 0.8,
    }
    engine.close()


def test_superseded_parameter_versions_stay_queryable(tmp_path):
    engine = open_engine(tmp_path)
    procedures = ProceduralMemory(engine)
    first = procedures.set_parameter("gaze", "dwell_ms", 500)
    procedures.set_parameter("gaze", "dwell_ms", 650)

    chain = engine.store.get_provenance_chain(first.fact_id, "fact")
    assert chain["memory_id"] == first.fact_id
    old = engine.store.get_fact(first.fact_id)
    assert old is not None
    assert old.object_value["value"] == 500
    engine.close()
