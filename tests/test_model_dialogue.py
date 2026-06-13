from __future__ import annotations

import json

from android_brain_memory import CognitiveContextPacket, CognitiveMemoryRef, FakeModelRuntime, OmittedMemoryRef
from android_brain_memory.dialogue import DialogueActType, UtterancePlan
from android_brain_memory.model_dialogue import ModelDialogueRealizer


def plan() -> UtterancePlan:
    return UtterancePlan(
        plan_id="plan_001",
        act_type=DialogueActType.ANSWER,
        created_ts=10_000,
        text="You told me that you like tea.",
        content_slots={"value": "tea"},
        memory_refs=[{"memory_kind": "fact", "memory_id": "fact_tea"}],
        confidence=0.9,
        intent_id="intent_001",
    )


def context(*, confidence: float = 0.9, source_type: str = "user_confirmed") -> CognitiveContextPacket:
    return CognitiveContextPacket(
        user_utterance="what do I like",
        created_ts=10_000,
        dialogue_intent={"intent_type": "respond_to_user"},
        working_memory={},
        attention={},
        safety={},
        avatar={},
        memories=[
            CognitiveMemoryRef(
                memory_kind="fact",
                memory_id="fact_tea",
                text="user likes tea",
                source_type=source_type,
                confidence=confidence,
            )
        ],
        char_budget=8_000,
    )


def response_payload(**overrides) -> str:
    payload = {
        "response_text": "You told me you like tea.",
        "memory_refs_used": [{"memory_kind": "fact", "memory_id": "fact_tea"}],
        "uncertainty": "low",
        "proposed_memory_candidates": [],
        "safety_notes": [],
    }
    payload.update(overrides)
    return json.dumps(payload)


def test_model_dialogue_realizer_uses_valid_model_json():
    runtime = FakeModelRuntime(response_text=response_payload(response_text="You told me you like tea."))
    realizer = ModelDialogueRealizer(runtime)

    result = realizer.realize(plan(), context())

    assert result.used_model is True
    assert result.text == "You told me you like tea."
    assert result.memory_refs_used == [{"memory_kind": "fact", "memory_id": "fact_tea"}]
    assert result.fallback_reason is None
    assert realizer.status()["last_result"]["used_model"] is True


def test_model_dialogue_realizer_falls_back_on_malformed_json():
    runtime = FakeModelRuntime(response_text="not json")
    realizer = ModelDialogueRealizer(runtime)

    result = realizer.realize(plan(), context())

    assert result.used_model is False
    assert result.text == "You told me that you like tea."
    assert result.fallback_reason == "malformed_json"


def test_model_dialogue_realizer_falls_back_when_model_missing():
    runtime = FakeModelRuntime(available_models=[])
    realizer = ModelDialogueRealizer(runtime)

    result = realizer.realize(plan(), context())

    assert result.used_model is False
    assert result.fallback_reason == "model_missing"


def test_model_dialogue_realizer_rejects_invented_memory_refs():
    runtime = FakeModelRuntime(
        response_text=response_payload(
            memory_refs_used=[{"memory_kind": "fact", "memory_id": "fact_invented"}]
        )
    )
    realizer = ModelDialogueRealizer(runtime)

    result = realizer.realize(plan(), context())

    assert result.used_model is False
    assert result.fallback_reason == "invented_memory_ref"


def test_model_dialogue_realizer_rejects_withheld_memory_leak():
    ctx = context()
    ctx.omitted_memories.append(
        OmittedMemoryRef(
            memory_kind="fact",
            memory_id="fact_secret",
            reason="withheld_by_speakability",
            speakability="internal_only",
        )
    )
    runtime = FakeModelRuntime(
        response_text=response_payload(response_text="I should not mention fact_secret.")
    )
    realizer = ModelDialogueRealizer(runtime)

    result = realizer.realize(plan(), ctx)

    assert result.used_model is False
    assert result.fallback_reason == "withheld_memory_leak"


def test_model_dialogue_realizer_hedges_low_confidence_refs():
    runtime = FakeModelRuntime(
        response_text=response_payload(
            response_text="I think you like tea.",
            uncertainty="medium",
        )
    )
    realizer = ModelDialogueRealizer(runtime)

    result = realizer.realize(plan(), context(confidence=0.4))

    assert result.used_model is True
    assert result.text.startswith("I may be wrong, but")
    assert "added_low_confidence_hedge" in result.safety_notes


def test_model_dialogue_realizer_rejects_confirmed_claim_for_inferred_fact():
    runtime = FakeModelRuntime(response_text=response_payload(response_text="You told me you like tea."))
    realizer = ModelDialogueRealizer(runtime)

    result = realizer.realize(plan(), context(source_type="model_inferred"))

    assert result.used_model is False
    assert result.fallback_reason == "source_status_misrepresented"
