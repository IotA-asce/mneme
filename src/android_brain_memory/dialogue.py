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
from .memory_review import explain_memory_refs, user_memory_review
from .models import Episode, Fact, MemoryBundle, SourceType, Speakability, validate_confidence, validate_timestamp
from .storage import MemoryStore
from .turn_understanding import TurnType

GREETING_PATTERN = re.compile(r"\b(hello|hi|hey|good (morning|afternoon|evening))\b")
QUESTION_PATTERN = re.compile(
    r"^\s*(what|why|how|when|where|who|which|do|does|did|can|could|would|should|is|are|am)\b",
    re.IGNORECASE,
)
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

        turn_type = _turn_type(intent)
        memory_context = intent.payload.get("memory")
        if isinstance(memory_context, Mapping) and memory_context.get("needs_clarification"):
            return self._clarify(intent, memory_context)
        if turn_type == TurnType.EXPLICIT_REMEMBER_INSTRUCTION:
            return self._acknowledge_memory(intent)
        if turn_type == TurnType.EXPLANATION_QUESTION:
            return self._explain_previous_response(intent)
        if turn_type == TurnType.MEMORY_REVIEW_QUESTION:
            return self._review_user_memory(intent)
        if turn_type in {
            TurnType.CORRECTION,
            TurnType.CONTRADICTION_CHALLENGE,
            TurnType.FORGET_REQUEST,
        }:
            return self._acknowledge_review_proposal(intent, turn_type)
        if turn_type == TurnType.IDENTITY_SELF_QUESTION:
            return self._identity_response(intent)
        if turn_type == TurnType.CAPABILITY_QUESTION:
            return self._capability_response(intent)
        if turn_type == TurnType.DEVICE_STATUS_QUESTION:
            return self._status_response(intent)
        if "remember_event" in [
            str(item) for item in intent.payload.get("secondary_intents", [])
        ]:
            return self._acknowledge_memory(intent)

        speakable_facts = self._speakable_facts(bundle)
        if speakable_facts:
            return self._answer(intent, speakable_facts[0])

        speakable_episodes = self._speakable_episodes(bundle)
        if speakable_episodes:
            return self._answer_episode(intent, speakable_episodes[0])

        turn_text = _turn_text(intent)
        if GREETING_PATTERN.search(turn_text.lower()):
            return self._build(
                intent,
                act_type=DialogueActType.GREET,
                text=_greeting_text(working),
                content_slots={"grounding": "current_session"},
            )
        return self._build(
            intent,
            act_type=DialogueActType.ACKNOWLEDGE,
            text=_unknown_response(turn_text),
            content_slots={"turn_text": turn_text},
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
            text=_fact_response_text(fact, value_text),
            content_slots={
                "subject": fact.subject,
                "predicate": fact.predicate,
                "value": value if isinstance(value, (str, int, float, bool)) else value_text,
            },
            memory_refs=[{"memory_kind": "fact", "memory_id": fact.fact_id}],
            confidence=fact.confidence,
        )

    def _answer_episode(self, intent: ExecutiveIntent, episode: Episode) -> UtterancePlan:
        summary = _clean_sentence(episode.summary)
        return self._build(
            intent,
            act_type=DialogueActType.ANSWER,
            text=_episode_response_text(episode, summary),
            content_slots={"summary": summary},
            memory_refs=[{"memory_kind": "episode", "memory_id": episode.episode_id}],
            confidence=episode.confidence,
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
        statement = _remember_statement_text(_turn_text(intent))
        text = (
            f"I will remember that {statement}."
            if statement
            else "I will remember that."
        )
        return self._build(
            intent,
            act_type=DialogueActType.ACKNOWLEDGE,
            text=text,
            content_slots={"remembered_statement": statement} if statement else {},
        )

    def _explain_previous_response(self, intent: ExecutiveIntent) -> UtterancePlan:
        review = intent.payload.get("memory_review")
        if not isinstance(review, Mapping):
            return self._build(
                intent,
                act_type=DialogueActType.ANSWER,
                text="I do not have a previous response to explain yet.",
                content_slots={"grounding": "memory_review_unavailable"},
            )
        refs = [
            {
                "memory_kind": str(item.get("memory_kind")),
                "memory_id": str(item.get("memory_id")),
            }
            for item in review.get("memory_refs", [])
            if isinstance(item, Mapping) and item.get("memory_kind") and item.get("memory_id")
        ]
        if not refs:
            text = "I answered from the current conversation and deterministic dialogue rules, not from a durable memory."
        else:
            pieces = []
            for item in review.get("memory_refs", []):
                if not isinstance(item, Mapping):
                    continue
                source = item.get("source_type") or "unknown source"
                confidence = item.get("confidence")
                confidence_text = f" with confidence {confidence:.2f}" if isinstance(confidence, float) else ""
                pieces.append(f"{item.get('memory_kind')} {item.get('memory_id')} from {source}{confidence_text}")
            text = "I said that because I used " + "; ".join(pieces) + "."
        return self._build(
            intent,
            act_type=DialogueActType.ANSWER,
            text=text,
            content_slots={"memory_review": dict(review)},
            memory_refs=refs,
        )

    def _review_user_memory(self, intent: ExecutiveIntent) -> UtterancePlan:
        if self.store is None:
            return self._build(
                intent,
                act_type=DialogueActType.ANSWER,
                text="I cannot inspect durable memory in this runtime.",
                content_slots={"grounding": "store_unavailable"},
            )
        facts = user_memory_review(self.store, limit=5)
        if not facts:
            return self._build(
                intent,
                act_type=DialogueActType.ANSWER,
                text="I do not have speakable durable facts about you yet.",
                content_slots={"grounding": "no_user_facts"},
            )
        refs = [{"memory_kind": "fact", "memory_id": fact.fact_id} for fact in facts]
        explanations = [item.to_dict() for item in explain_memory_refs(self.store, refs)]
        fact_text = "; ".join(_brief_fact_text(fact) for fact in facts)
        return self._build(
            intent,
            act_type=DialogueActType.ANSWER,
            text=f"I have these speakable memories about you: {fact_text}.",
            content_slots={"memory_review": {"memory_refs": explanations}},
            memory_refs=refs,
            confidence=min(fact.confidence for fact in facts),
        )

    def _acknowledge_review_proposal(
        self,
        intent: ExecutiveIntent,
        turn_type: TurnType,
    ) -> UtterancePlan:
        proposal = intent.payload.get("correction_proposal")
        proposal_dict = dict(proposal) if isinstance(proposal, Mapping) else {}
        if turn_type == TurnType.FORGET_REQUEST:
            text = "I marked that as a forget request for review. I have not purged any memory yet."
        elif turn_type == TurnType.CONTRADICTION_CHALLENGE:
            text = "I marked that as a contradiction challenge for review. I have not changed confirmed memory yet."
        else:
            text = "I marked that as a correction proposal for review. I have not changed memory yet."
        return self._build(
            intent,
            act_type=DialogueActType.ACKNOWLEDGE,
            text=text,
            content_slots={"correction_proposal": proposal_dict},
            memory_refs=[
                dict(ref)
                for ref in proposal_dict.get("related_memory_refs", [])
                if isinstance(ref, Mapping)
            ],
        )

    def _identity_response(self, intent: ExecutiveIntent) -> UtterancePlan:
        return self._build(
            intent,
            act_type=DialogueActType.ANSWER,
            text="I am Mneme, a local memory-centered cognition prototype for a future lifelike robot head.",
            content_slots={"grounding": "self_model_static_runtime"},
        )

    def _capability_response(self, intent: ExecutiveIntent) -> UtterancePlan:
        status = intent.payload.get("runtime_status")
        capability = status.get("capability") if isinstance(status, Mapping) else {}
        level = capability.get("current_level") if isinstance(capability, Mapping) else "L1"
        text = (
            "Right now I can run a local brain loop with working memory, durable memory, "
            "attention, executive intent, virtual speech, local model wording, and reviewable memory refs. "
            f"My current conservative capability evidence is {level}; that is benchmark evidence, not animal or human equivalence."
        )
        return self._build(
            intent,
            act_type=DialogueActType.ANSWER,
            text=text,
            content_slots={"runtime_status": dict(status) if isinstance(status, Mapping) else {}},
        )

    def _status_response(self, intent: ExecutiveIntent) -> UtterancePlan:
        status = intent.payload.get("runtime_status")
        status_dict = dict(status) if isinstance(status, Mapping) else {}
        cognition = status_dict.get("cognition") if isinstance(status_dict.get("cognition"), Mapping) else {}
        devices = status_dict.get("devices") if isinstance(status_dict.get("devices"), Mapping) else {}
        counts = devices.get("available_counts") if isinstance(devices.get("available_counts"), Mapping) else {}
        model = (
            f"{cognition.get('backend')} / {cognition.get('model')}"
            if cognition.get("enabled")
            else "deterministic fallback"
        )
        text = (
            f"I am using {model}. "
            f"Device inventory currently shows {counts.get('camera', 0)} camera, "
            f"{counts.get('microphone', 0)} microphone, and {counts.get('speaker', 0)} speaker option(s)."
        )
        return self._build(
            intent,
            act_type=DialogueActType.ANSWER,
            text=text,
            content_slots={"runtime_status": status_dict},
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

    def _speakable_episodes(self, bundle: MemoryBundle | None) -> list[Episode]:
        if bundle is None:
            return []
        speakable = []
        for episode in bundle.episodes:
            if self.store is not None:
                meta = self.store.get_meta_memory(episode.episode_id, "episode")
                if meta is not None and meta.speakability not in SPEAKABLE:
                    continue
            speakable.append(episode)
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


def _turn_type(intent: ExecutiveIntent) -> TurnType | None:
    turn = intent.payload.get("dialogue_turn")
    if not isinstance(turn, Mapping):
        return None
    classification = turn.get("turn_classification")
    if not isinstance(classification, Mapping):
        return None
    raw = classification.get("turn_type")
    if not isinstance(raw, str):
        return None
    try:
        return TurnType(raw)
    except ValueError:
        return None


def _fact_response_text(fact: Fact, value_text: str) -> str:
    relation = _fact_relation(fact, value_text)
    if fact.source_type == SourceType.USER_CONFIRMED:
        base = f"You told me that {relation}."
    elif fact.source_type == SourceType.SENSOR_OBSERVED:
        base = f"I observed that {relation}."
    elif fact.source_type == SourceType.MODEL_INFERRED:
        base = f"I think {relation}."
    else:
        base = f"I have a memory that {relation}."
    if fact.confidence < 0.6:
        return f"I may be wrong, but {base[0].lower()}{base[1:]}"
    return base


def _episode_response_text(episode: Episode, summary: str) -> str:
    text = f"I remember this from our context: {summary}."
    if episode.confidence < 0.6:
        return f"I may be wrong, but {text[0].lower()}{text[1:]}"
    return text


def _greeting_text(working: Mapping[str, Any] | None) -> str:
    if isinstance(working, Mapping):
        topic = working.get("topic")
        attention = working.get("attention_target")
        if topic:
            return f"I'm here. I still have the current topic as {topic}."
        if attention:
            return f"I'm here, and my attention is on {attention}."
    return "I'm here. I can listen, remember, and use the context we build."


def _unknown_response(turn_text: str) -> str:
    clean = _clean_sentence(turn_text)
    if not clean:
        return "I don't have enough context to answer that yet."
    topic = _topic_label(clean)
    if _looks_like_question(clean):
        return (
            f"I don't know that yet. I'm treating it as a {topic} question, "
            "and I can answer better once I have a relevant memory or observation."
        )
    return (
        f"I heard you say: \"{_shorten(clean)}\". "
        "I can use it as current context; ask me to remember it if it should persist."
    )


def _remember_statement_text(turn_text: str) -> str | None:
    normalized = " ".join(turn_text.strip().split())
    lowered = normalized.lower()
    statement = None
    for prefix in ("mneme, remember that ", "remember that ", "remember "):
        if lowered.startswith(prefix):
            statement = normalized[len(prefix) :]
            break
    if statement is None:
        marker = " remember that "
        if marker in lowered:
            statement = normalized[lowered.index(marker) + len(marker) :]
    if not statement:
        return None
    statement = statement.strip().rstrip(".")
    patterns = (
        (r"^i like (.+)$", "you like {value}"),
        (r"^i prefer (.+)$", "you prefer {value}"),
        (r"^my favorite ([a-z0-9_ -]+) is (.+)$", "your favorite {field} is {value}"),
    )
    for pattern, template in patterns:
        match = re.match(pattern, statement, flags=re.IGNORECASE)
        if not match:
            continue
        if "{field}" in template:
            return template.format(
                field=match.group(1).strip().lower(),
                value=match.group(2).strip(),
            )
        return template.format(value=match.group(1).strip())
    return _first_person_to_second_person(statement)


def _first_person_to_second_person(text: str) -> str:
    replacements = (
        (r"\bI am\b", "you are"),
        (r"\bI'm\b", "you are"),
        (r"\bI\b", "you"),
        (r"\bmy\b", "your"),
        (r"\bme\b", "you"),
    )
    result = text.strip()
    for pattern, replacement in replacements:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result[:1].lower() + result[1:] if result else result


def _topic_label(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ("camera", "microphone", "speaker", "device")):
        return "local setup"
    if any(word in lowered for word in ("remember", "memory", "recall")):
        return "memory"
    if any(word in lowered for word in ("like", "prefer", "favorite")):
        return "preference"
    return "conversation"


def _looks_like_question(text: str) -> bool:
    return text.strip().endswith("?") or bool(QUESTION_PATTERN.search(text))


def _humanize_predicate(predicate: str) -> str:
    return predicate.replace("_", " ")


def _fact_relation(fact: Fact, value_text: str) -> str:
    subject = fact.subject.strip()
    predicate = fact.predicate.strip()
    if subject.lower() == "user":
        if predicate.startswith("favorite_"):
            field = predicate[len("favorite_") :].replace("_", " ")
            return f"your favorite {field} is {value_text}"
        verb = _humanize_predicate(predicate)
        if verb in {"likes", "prefers", "enjoys", "needs", "wants"}:
            verb = verb[:-1]
        return f"you {verb} {value_text}"
    return f"{subject} {_humanize_predicate(predicate)} {value_text}"


def _brief_fact_text(fact: Fact) -> str:
    value = fact.object_value.get("value")
    value_text = value if isinstance(value, str) else json.dumps(value, sort_keys=True, ensure_ascii=True)
    return _fact_relation(fact, value_text)


def _clean_sentence(text: str) -> str:
    return " ".join(text.strip().split()).rstrip(".")


def _shorten(text: str, *, limit: int = 120) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _now_ms() -> int:
    return int(time.time() * 1000)
