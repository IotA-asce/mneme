from __future__ import annotations

import json
from pathlib import Path

from android_brain_memory import (
    EventBus,
    ScenarioReplayRunner,
    SensoryEchoBuffer,
    WorkingMemory,
    load_scenario,
)
from android_brain_memory.runtime import RuntimeEventKind


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "basic_conversation.yaml"


class FixedClock:
    def __init__(self, now_ms: int) -> None:
        self.now_ms = now_ms

    def __call__(self) -> int:
        return self.now_ms


def test_loads_basic_conversation_scenario():
    scenario = load_scenario(FIXTURE)

    assert scenario.name == "basic_conversation"
    assert scenario.start_ts == 1000
    assert [step.step_id for step in scenario.steps] == [
        "face_user",
        "sound_user",
        "user_speech",
        "touch_ack",
        "health_nominal",
        "mneme_speech",
    ]


def test_replay_basic_conversation_updates_echo_working_memory_and_candidates():
    clock = FixedClock(1000)
    bus = EventBus(clock=clock)
    echo = SensoryEchoBuffer(capacity=16, default_ttl_ms=5_000, clock=clock)
    working = WorkingMemory(max_dialogue_turns=4, max_event_refs=8, clock=clock)
    echo.attach_to_bus(bus)
    working.attach_to_bus(bus)

    result = ScenarioReplayRunner(bus).replay_file(FIXTURE)
    clock.now_ms = max(event.timestamp for event in result.events)

    history = bus.history()
    kinds = [event.kind for event in history]
    assert len(result.events) == 8
    assert kinds == [
        RuntimeEventKind.PERCEPTION_OBSERVATION,
        RuntimeEventKind.PERCEPTION_OBSERVATION,
        RuntimeEventKind.PERCEPTION_OBSERVATION,
        RuntimeEventKind.MEMORY_CANDIDATE,
        RuntimeEventKind.PERCEPTION_OBSERVATION,
        RuntimeEventKind.PERCEPTION_OBSERVATION,
        RuntimeEventKind.SAFETY_EVENT,
        RuntimeEventKind.PERCEPTION_OBSERVATION,
    ]
    assert [event.sequence for event in history] == list(range(1, 9))

    snapshot = working.snapshot(snapshot_id="ctx_replay", created_ts=1100).to_dict()
    assert snapshot["current_speaker"] == "mneme"
    assert snapshot["topic"] == "calibration"
    assert snapshot["safety_state"]["payload"]["safety_level"] == "normal"
    assert [turn["speaker"] for turn in snapshot["recent_dialogue_turns"]] == ["user", "mneme"]
    assert snapshot["recent_dialogue_turns"][0]["text"] == (
        "Mneme, remember that I prefer short calibration prompts."
    )
    assert snapshot["recent_dialogue_turns"][1]["text"] == (
        "I will keep calibration prompts short."
    )

    fragments = echo.fragments(now_ms=clock.now_ms)
    assert len(fragments) == 8
    assert fragments[0].source == "sim.face_person_worker"
    assert any(fragment.kind == RuntimeEventKind.MEMORY_CANDIDATE for fragment in fragments)

    assert [candidate.candidate_id for candidate in result.memory_candidates] == [
        "cand_user_short_calibration_prompts"
    ]
    candidate = result.memory_candidates[0]
    assert candidate.summary == "User prefers short calibration prompts."
    assert candidate.features.explicit_remember_flag == 1.0
    assert candidate.provenance_refs == ["evt_user_speech"]


def test_json_scenario_replay_matches_yaml_shape(tmp_path):
    scenario = load_scenario(FIXTURE)
    json_path = tmp_path / "scenario.json"
    json_path.write_text(
        json.dumps(
            {
                "name": scenario.name,
                "start_ts": scenario.start_ts,
                "default_ttl_ms": scenario.default_ttl_ms,
                "steps": [
                    {
                        "id": step.step_id,
                        "worker": step.worker,
                        "at_ms": step.at_ms,
                        "payload": step.payload,
                        "confidence": step.confidence,
                        "ttl_ms": step.ttl_ms,
                        "source": step.source,
                        "important": step.important,
                        "memory_candidate": step.memory_candidate,
                    }
                    for step in scenario.steps
                ],
            }
        ),
        encoding="utf-8",
    )

    bus = EventBus(clock=lambda: 1000)
    result = ScenarioReplayRunner(bus).replay_file(json_path)

    assert result.scenario_name == "basic_conversation"
    assert len(result.events) == 8
    assert result.memory_candidates[0].candidate_id == "cand_user_short_calibration_prompts"
