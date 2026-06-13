from __future__ import annotations

from pathlib import Path

from android_brain_memory import MnemeMemory, WorkingMemory
from android_brain_memory.dialogue import DialogueActType, DialoguePlanner, UtterancePlan
from android_brain_memory.executive import Executive, ExecutiveIntent, ExecutiveMode
from android_brain_memory.models import Episode, Fact, MemoryBundle, SourceType, Speakability


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


def make_fact(fact_id="fact_beverage", value="tea") -> Fact:
    return Fact(
        fact_id=fact_id,
        subject="user",
        predicate="likes",
        object_value={"value": value},
        confidence=0.95,
        source_type=SourceType.USER_CONFIRMED,
    )


def make_bundle(facts=None, warnings=None) -> MemoryBundle:
    return MemoryBundle(
        query_id="query_test",
        summary="test bundle",
        facts=facts or [],
        warnings=warnings or [],
    )


def make_episode(episode_id="ep_calibration") -> Episode:
    return Episode(
        episode_id=episode_id,
        start_ts=9_000,
        end_ts=10_000,
        summary="User discussed calibration timing with Mneme.",
        context={"topic": "calibration"},
        salience=0.7,
        confidence=0.88,
        participants=["user"],
    )


def respond_intent(payload=None, mode=ExecutiveMode.NORMAL) -> ExecutiveIntent:
    return ExecutiveIntent(
        intent_id="exec_intent_000001",
        intent_type="respond_to_user",
        mode=mode,
        priority=70,
        created_ts=10_000,
        payload=payload
        or {"dialogue_turn": {"speaker": "user", "text": "what do I like", "timestamp": 10_000}},
    )


def intent_of(intent_type: str, payload=None, mode=ExecutiveMode.NORMAL) -> ExecutiveIntent:
    return ExecutiveIntent(
        intent_id="exec_intent_000002",
        intent_type=intent_type,
        mode=mode,
        priority=50,
        created_ts=10_000,
        payload=payload or {},
    )


def test_answer_plan_uses_top_fact_with_slots_and_refs():
    planner = DialoguePlanner(clock=FixedClock(10_000))

    plan = planner.plan(respond_intent(), bundle=make_bundle(facts=[make_fact()]))

    assert isinstance(plan, UtterancePlan)
    assert plan.act_type == DialogueActType.ANSWER
    assert plan.content_slots == {"subject": "user", "predicate": "likes", "value": "tea"}
    assert "tea" in plan.text
    assert "you like tea" in plan.text
    assert plan.memory_refs == [{"memory_kind": "fact", "memory_id": "fact_beverage"}]
    assert plan.intent_id == "exec_intent_000001"


def test_answer_plan_can_use_top_episode_when_no_fact_matches():
    planner = DialoguePlanner(clock=FixedClock(10_000))
    bundle = MemoryBundle(
        query_id="query_test",
        summary="test bundle",
        episodes=[make_episode()],
    )

    plan = planner.plan(respond_intent(), bundle=bundle)

    assert plan.act_type == DialogueActType.ANSWER
    assert "calibration timing" in plan.text
    assert plan.memory_refs == [{"memory_kind": "episode", "memory_id": "ep_calibration"}]


def test_clarify_plan_when_memory_conflicts():
    planner = DialoguePlanner(clock=FixedClock(10_000))
    intent = respond_intent(
        payload={
            "dialogue_turn": {"speaker": "user", "text": "what is my color", "timestamp": 10_000},
            "memory": {"needs_clarification": True, "warnings": [
                "conflicting fact records exist for user favorite_color"
            ]},
        }
    )

    plan = planner.plan(intent, bundle=make_bundle(
        facts=[make_fact("fact_red", "red")],
        warnings=["conflicting fact records exist for user favorite_color"],
    ))

    assert plan.act_type == DialogueActType.CLARIFY
    assert "user favorite_color" in plan.text
    assert plan.memory_refs == []


def test_memory_instruction_yields_acknowledge():
    planner = DialoguePlanner(clock=FixedClock(10_000))
    intent = respond_intent(
        payload={
            "dialogue_turn": {
                "speaker": "user",
                "text": "remember that I prefer short prompts",
                "timestamp": 10_000,
            },
            "secondary_intents": ["remember_event"],
        }
    )

    plan = planner.plan(intent, bundle=make_bundle())

    assert plan.act_type == DialogueActType.ACKNOWLEDGE
    assert "remember" in plan.text.lower()
    assert "you prefer short prompts" in plan.text


def test_greeting_without_memory_yields_greet():
    planner = DialoguePlanner(clock=FixedClock(10_000))
    intent = respond_intent(
        payload={
            "dialogue_turn": {"speaker": "user", "text": "hello Mneme", "timestamp": 10_000}
        }
    )

    plan = planner.plan(intent, bundle=make_bundle())

    assert plan.act_type == DialogueActType.GREET
    assert "I'm here" in plan.text


def test_unknown_response_uses_current_user_text():
    planner = DialoguePlanner(clock=FixedClock(10_000))
    intent = respond_intent(
        payload={
            "dialogue_turn": {
                "speaker": "user",
                "text": "I am tuning the attention loop",
                "timestamp": 10_000,
            }
        }
    )

    plan = planner.plan(intent, bundle=make_bundle())

    assert plan.act_type == DialogueActType.ACKNOWLEDGE
    assert "I am tuning the attention loop" in plan.text
    assert "current context" in plan.text


def test_no_plan_for_safety_listen_or_idle_intents():
    planner = DialoguePlanner(clock=FixedClock(10_000))

    assert planner.plan(intent_of("freeze_motion", mode=ExecutiveMode.FROZEN)) is None
    assert planner.plan(intent_of("enter_degraded_mode", mode=ExecutiveMode.DEGRADED)) is None
    assert planner.plan(intent_of("listen")) is None
    assert planner.plan(intent_of("look_at_target")) is None
    assert planner.plan(intent_of("idle_presence")) is None
    # a respond intent in a degraded mode is also silent
    assert planner.plan(respond_intent(mode=ExecutiveMode.DEGRADED)) is None


def test_remember_event_intent_yields_acknowledge():
    planner = DialoguePlanner(clock=FixedClock(10_000))

    plan = planner.plan(intent_of("remember_event"))

    assert plan.act_type == DialogueActType.ACKNOWLEDGE


def test_restricted_facts_are_not_spoken(tmp_path):
    engine = open_engine(tmp_path)
    engine.add_fact(make_fact("fact_secretive", "medical detail"), speakability=Speakability.RESTRICTED)
    engine.add_fact(
        Fact(
            fact_id="fact_open",
            subject="user",
            predicate="enjoys",
            object_value={"value": "gardening"},
            confidence=0.9,
            source_type=SourceType.USER_CONFIRMED,
        )
    )
    restricted = engine.store.get_fact("fact_secretive")
    open_fact = engine.store.get_fact("fact_open")
    planner = DialoguePlanner(store=engine.store, clock=FixedClock(10_000))

    plan = planner.plan(respond_intent(), bundle=make_bundle(facts=[restricted, open_fact]))

    assert plan.act_type == DialogueActType.ANSWER
    assert plan.memory_refs == [{"memory_kind": "fact", "memory_id": "fact_open"}]
    assert "medical detail" not in plan.text
    engine.close()


def test_executive_integration_produces_answer_plan(tmp_path):
    engine = open_engine(tmp_path)
    engine.add_fact(make_fact())
    clock = FixedClock(10_000)
    working = WorkingMemory(clock=clock)
    executive = Executive(working_memory=working, clock=clock, engine=engine)
    working.add_dialogue_turn(speaker="user", text="do you recall what I like", timestamp=10_000)
    planner = DialoguePlanner(store=engine.store, clock=clock)

    intent = executive.run_once(publish=False)
    plan = planner.plan(intent, bundle=executive.last_memory_bundle)

    assert plan is not None
    assert plan.act_type == DialogueActType.ANSWER
    assert plan.memory_refs[0]["memory_id"] == "fact_beverage"
    engine.close()


def test_plans_are_json_friendly_and_deterministic():
    planner = DialoguePlanner(clock=FixedClock(10_000))
    bundle = make_bundle(facts=[make_fact()])

    first = planner.plan(respond_intent(), bundle=bundle)
    second = planner.plan(respond_intent(), bundle=bundle)

    assert first.to_dict()["text"] == second.to_dict()["text"]
    assert first.to_dict()["content_slots"] == second.to_dict()["content_slots"]
