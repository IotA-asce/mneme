from __future__ import annotations

import json
import re
import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .executive import ExecutiveIntent, ExecutiveIntentType, ExecutiveMode
from .models import Fact, MemoryBundle, Speakability, validate_confidence, validate_timestamp
from .storage import MemoryStore

GREETING_PATTERN = re.compile(r"\b(hello|hi|hey|good (morning|afternoon|evening))\b")
CONFLICT_WARNING_PREFIX = "conflicting fact records exist for "
SPEAKABLE = {Speakability.NORMAL}
NON_SPEAKING_INTENTS = {
    ExecutiveIntentType.LISTEN,
    ExecutiveIntentType.LOOK_AT_TARGET,
    ExecutiveIntentType.IDLE_PRESENCE,
    ExecutiveIntentType.FREEZE_MOTION,
    ExecutiveIntentType.ENTER_DEGRADED_MODE,
}


class DialogueActType(StrEnum):
    ANSWER = "answer"
    CLARIFY = "clarify"
    ACKNOWLEDGE = "acknowledge"
    GREET = "greet"


@dataclass(slots=True)
class UtterancePlan:
    plan_id: str
    act_type: DialogueActType | str
    created_ts: int
    text: str
    content_slots: dict[str, Any] = field(default_factory=dict)
    memory_refs: list[dict[str, str]] = field(default_factory=list)
    confidence: float = 1.0
    intent_id: str | None = None

    def __post_init__(self) -> None:
        self.plan_id = _required_text(self.plan_id, "plan_id")
        self.act_type = (
            self.act_type
            if isinstance(self.act_type, DialogueActType)
            else DialogueActType(self.act_type)
        )
        self.created_ts = validate_timestamp(self.created_ts, "created_ts")
        self.text = _required_text(self.text, "text")
        if not isinstance(self.content_slots, Mapping):
            raise ValueError("content_slots must be a mapping")
        self.content_slots = dict(self.content_slots)
        self.memory_refs = [dict(ref) for ref in self.memory_refs]
        self.confidence = validate_confidence(self.confidence)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "act_type": self.act_type.value,
            "created_ts": self.created_ts,
            "text": self.text,
            "content_slots": dict(self.content_slots),
            "memory_refs": [dict(ref) for ref in self.memory_refs],
            "confidence": self.confidence,
            "intent_id": self.intent_id,
        }


class DialoguePlanner:
    """Deterministic intent-level utterance planning (no LLM, no TTS).

    Consumes executive intent and the retrieved memory bundle; produces a
    structured, speakability-filtered utterance plan, or None when speaking
    is inappropriate. It never generates intent and never owns the robot.
    """

    def __init__(
        self,
        *,
        store: MemoryStore | None = None,
        source: str = "dialogue_planner",
        clock: Callable[[], int] | None = None,
    ) -> None:
        self.store = store
        self.source = _required_text(source, "source")
        self._clock = clock or _now_ms
        self._plan_counter = 0

    def plan(
        self,
        intent: ExecutiveIntent,
        *,
        bundle: MemoryBundle | None = None,
        working: Mapping[str, Any] | None = None,
    ) -> UtterancePlan | None:
        if intent.mode != ExecutiveMode.NORMAL:
            return None
        if intent.intent_type in NON_SPEAKING_INTENTS:
            return None
        if intent.intent_type == ExecutiveIntentType.REMEMBER_EVENT:
            return self._acknowledge_memory(intent)
        if intent.intent_type != ExecutiveIntentType.RESPOND_TO_USER:
            return None

        memory_context = intent.payload.get("memory")
        if isinstance(memory_context, Mapping) and memory_context.get("needs_clarification"):
            return self._clarify(intent, memory_context)
        if "remember_event" in [
            str(item) for item in intent.payload.get("secondary_intents", [])
        ]:
            return self._acknowledge_memory(intent)

        speakable_facts = self._speakable_facts(bundle)
        if speakable_facts:
            return self._answer(intent, speakable_facts[0])

        turn_text = _turn_text(intent)
        if GREETING_PATTERN.search(turn_text.lower()):
            return self._build(
                intent,
                act_type=DialogueActType.GREET,
                text="Hello! I'm listening.",
                content_slots={},
            )
        return self._build(
            intent,
            act_type=DialogueActType.ACKNOWLEDGE,
            text="I heard you. I don't have a stored answer for that yet.",
            content_slots={},
        )

    def _answer(self, intent: ExecutiveIntent, fact: Fact) -> UtterancePlan:
        value = fact.object_value.get("value")
        value_text = (
            value
            if isinstance(value, str)
            else json.dumps(value, sort_keys=True, ensure_ascii=True)
        )
        return self._build(
            intent,
            act_type=DialogueActType.ANSWER,
            text=f"You mentioned that {fact.subject} {fact.predicate} {value_text}.",
            content_slots={
                "subject": fact.subject,
                "predicate": fact.predicate,
                "value": value if isinstance(value, (str, int, float, bool)) else value_text,
            },
            memory_refs=[{"memory_kind": "fact", "memory_id": fact.fact_id}],
            confidence=fact.confidence,
        )

    def _clarify(
        self,
        intent: ExecutiveIntent,
        memory_context: Mapping[str, Any],
    ) -> UtterancePlan:
        statement = None
        for warning in memory_context.get("warnings", []):
            if isinstance(warning, str) and warning.startswith(CONFLICT_WARNING_PREFIX):
                statement = warning[len(CONFLICT_WARNING_PREFIX):]
                break
        statement = statement or "that topic"
        return self._build(
            intent,
            act_type=DialogueActType.CLARIFY,
            text=f"I have conflicting memories about {statement}. Could you clarify?",
            content_slots={"statement": statement},
        )

    def _acknowledge_memory(self, intent: ExecutiveIntent) -> UtterancePlan:
        return self._build(
            intent,
            act_type=DialogueActType.ACKNOWLEDGE,
            text="Noted - I will remember that.",
            content_slots={},
        )

    def _speakable_facts(self, bundle: MemoryBundle | None) -> list[Fact]:
        if bundle is None:
            return []
        speakable = []
        for fact in bundle.facts:
            if self.store is not None:
                meta = self.store.get_meta_memory(fact.fact_id, "fact")
                if meta is not None and meta.speakability not in SPEAKABLE:
                    continue
            speakable.append(fact)
        return speakable

    def _build(
        self,
        intent: ExecutiveIntent,
        *,
        act_type: DialogueActType,
        text: str,
        content_slots: Mapping[str, Any],
        memory_refs: list[dict[str, str]] | None = None,
        confidence: float = 1.0,
    ) -> UtterancePlan:
        self._plan_counter += 1
        return UtterancePlan(
            plan_id=f"utt_plan_{self._plan_counter:06d}_{uuid.uuid4().hex[:8]}",
            act_type=act_type,
            created_ts=self._clock(),
            text=text,
            content_slots=dict(content_slots),
            memory_refs=memory_refs or [],
            confidence=confidence,
            intent_id=intent.intent_id,
        )


def _turn_text(intent: ExecutiveIntent) -> str:
    turn = intent.payload.get("dialogue_turn")
    if isinstance(turn, Mapping):
        text = turn.get("text")
        if isinstance(text, str):
            return text
    return ""


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _now_ms() -> int:
    return int(time.time() * 1000)
