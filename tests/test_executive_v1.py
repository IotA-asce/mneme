from __future__ import annotations

from pathlib import Path

from android_brain_memory import MnemeMemory, WorkingMemory
from android_brain_memory.executive import (
    Executive,
    ExecutiveGoal,
    ExecutiveIntentType,
    ExecutiveMode,
)
from android_brain_memory.models import Fact, SourceType


MIGRATIONS = Path(__file__).resolve().parents[1] / "storage" / "migrations"


class FixedClock:
    def __init__(self, now_ms: int) -> None:
        self.now_ms = now_ms

    def __call__(self) -> int:
        return self.now_ms


def make_executive(clock, **kwargs) -> tuple[Executive, WorkingMemory]:
    working = WorkingMemory(clock=clock)
    executive = Executive(working_memory=working, clock=clock, **kwargs)
    return executive, working


def open_engine(tmp_path) -> MnemeMemory:
    engine = MnemeMemory(tmp_path / "memory.sqlite3", migrations_dir=MIGRATIONS)
    engine.init_db()
    return engine


def test_active_goal_context_attached_to_normal_intents():
    clock = FixedClock(10_000)
    executive, _ = make_executive(clock)

    goal = executive.push_goal("calibration_session", payload={"step": 1})
    intent = executive.run_once(publish=False)

    assert isinstance(goal, ExecutiveGoal)
    assert executive.current_goal.goal_id == goal.goal_id
    assert intent.payload["active_goal_id"] == goal.goal_id
    assert intent.payload["active_goal_type"] == "calibration_session"

    assert executive.complete_goal(goal.goal_id) is True
    after = executive.run_once(publish=False)
    assert "active_goal_id" not in after.payload


def test_safety_freeze_suspends_goal_and_recovery_resumes_it():
    clock = FixedClock(10_000)
    executive, _ = make_executive(clock)
    goal = executive.push_goal("calibration_session")

    frozen = executive.run_once(
        safety_state={"safety_level": "emergency"},
        publish=False,
    )
    assert frozen.intent_type == ExecutiveIntentType.FREEZE_MOTION
    assert frozen.mode == ExecutiveMode.FROZEN
    assert frozen.payload["suspended_goal_ids"] == [goal.goal_id]
    assert executive.current_goal.status == "suspended"

    resumed = executive.run_once(
        safety_state={"safety_level": "normal"},
        publish=False,
    )
    assert resumed.mode == ExecutiveMode.NORMAL
    assert resumed.payload["resumed_goal"]["goal_id"] == goal.goal_id
    assert executive.current_goal.status == "active"

    # resumption is reported once, then the goal is just active context
    following = executive.run_once(publish=False)
    assert "resumed_goal" not in following.payload
    assert following.payload["active_goal_id"] == goal.goal_id


def test_response_timing_waits_for_turn_completion():
    clock = FixedClock(10_000)
    executive, working = make_executive(clock, min_response_delay_ms=500)
    working.add_dialogue_turn(speaker="user", text="so what do you think", timestamp=10_000)

    clock.now_ms = 10_100  # 100ms after the turn, inside the delay window
    early = executive.run_once(publish=False)
    assert early.intent_type == ExecutiveIntentType.LISTEN
    assert early.reason == "awaiting_turn_completion"

    clock.now_ms = 10_600  # past the delay, inside the interaction TTL
    ready = executive.run_once(publish=False)
    assert ready.intent_type == ExecutiveIntentType.RESPOND_TO_USER


def test_memory_informed_response_carries_ids_and_bundle(tmp_path):
    engine = open_engine(tmp_path)
    engine.add_fact(
        Fact(
            fact_id="fact_beverage",
            subject="user",
            predicate="likes",
            object_value={"value": "tea"},
            confidence=0.95,
            source_type=SourceType.USER_CONFIRMED,
        )
    )
    clock = FixedClock(10_000)
    executive, working = make_executive(clock, engine=engine)
    working.add_dialogue_turn(
        speaker="user", text="do you remember what I like", timestamp=10_000
    )

    intent = executive.run_once(publish=False)

    assert intent.intent_type == ExecutiveIntentType.RESPOND_TO_USER
    memory = intent.payload["memory"]
    assert memory["fact_ids"] == ["fact_beverage"]
    assert memory["needs_clarification"] is False
    assert "tea" not in str(memory)  # IDs and warnings only, never content
    assert executive.last_memory_bundle is not None
    assert executive.last_memory_bundle.facts[0].fact_id == "fact_beverage"
    engine.close()


def test_conflicting_memory_sets_needs_clarification(tmp_path):
    engine = open_engine(tmp_path)
    # two inferred facts conflict (both become conflicted), then a confirmed one stays active
    for fact_id, value in (("fact_blue", "blue"), ("fact_green", "green")):
        engine.add_fact(
            Fact(
                fact_id=fact_id,
                subject="user",
                predicate="favorite_color",
                object_value={"value": value},
                confidence=0.6,
                source_type=SourceType.MODEL_INFERRED,
            )
        )
    engine.add_fact(
        Fact(
            fact_id="fact_red",
            subject="user",
            predicate="favorite_color",
            object_value={"value": "red"},
            confidence=0.95,
            source_type=SourceType.USER_CONFIRMED,
        )
    )
    clock = FixedClock(10_000)
    executive, working = make_executive(clock, engine=engine)
    working.add_dialogue_turn(
        speaker="user", text="what is my favorite_color", timestamp=10_000
    )

    intent = executive.run_once(publish=False)

    memory = intent.payload["memory"]
    assert memory["fact_ids"] == ["fact_red"]
    assert memory["needs_clarification"] is True
    assert any("conflicting fact records" in warning for warning in memory["warnings"])
    engine.close()


def test_idle_presence_rotates_behaviors_deterministically():
    clock = FixedClock(10_000)
    executive, _ = make_executive(clock)

    behaviors = [
        executive.run_once(publish=False).payload["idle_behavior"] for _ in range(4)
    ]

    assert behaviors == ["ambient_scan", "rest_pose", "micro_motion", "ambient_scan"]


def test_v0_defaults_preserved_without_engine_or_delay():
    clock = FixedClock(10_000)
    executive, working = make_executive(clock)
    working.add_dialogue_turn(speaker="user", text="hello there", timestamp=10_000)

    intent = executive.run_once(publish=False)

    assert intent.intent_type == ExecutiveIntentType.RESPOND_TO_USER
    assert intent.priority == 70
    assert "memory" not in intent.payload
