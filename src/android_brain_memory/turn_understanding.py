from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .models import validate_confidence


class TurnType(StrEnum):
    GREETING = "greeting"
    ORDINARY_CHAT = "ordinary_chat"
    EXPLICIT_REMEMBER_INSTRUCTION = "explicit_remember_instruction"
    RECALL_QUESTION = "recall_question"
    MEMORY_REVIEW_QUESTION = "memory_review_question"
    EXPLANATION_QUESTION = "explanation_question"
    CORRECTION = "correction"
    CONTRADICTION_CHALLENGE = "contradiction_challenge"
    FORGET_REQUEST = "forget_request"
    IDENTITY_SELF_QUESTION = "identity_self_question"
    CAPABILITY_QUESTION = "capability_question"
    DEVICE_STATUS_QUESTION = "device_status_question"


@dataclass(slots=True)
class TurnClassification:
    turn_type: TurnType | str
    confidence: float
    matched_rule: str
    normalized_text: str
    is_question: bool = False
    requires_review: bool = False
    should_create_memory_candidate: bool = False

    def __post_init__(self) -> None:
        self.turn_type = self.turn_type if isinstance(self.turn_type, TurnType) else TurnType(self.turn_type)
        self.confidence = validate_confidence(self.confidence)
        self.matched_rule = _required_text(self.matched_rule, "matched_rule")
        self.normalized_text = _required_text(self.normalized_text, "normalized_text")

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_type": self.turn_type.value,
            "confidence": self.confidence,
            "matched_rule": self.matched_rule,
            "normalized_text": self.normalized_text,
            "is_question": self.is_question,
            "requires_review": self.requires_review,
            "should_create_memory_candidate": self.should_create_memory_candidate,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TurnClassification":
        return cls(
            turn_type=data["turn_type"],
            confidence=data.get("confidence", 1.0),
            matched_rule=data.get("matched_rule", "unknown"),
            normalized_text=data.get("normalized_text", ""),
            is_question=bool(data.get("is_question", False)),
            requires_review=bool(data.get("requires_review", False)),
            should_create_memory_candidate=bool(data.get("should_create_memory_candidate", False)),
        )


QUESTION_PREFIX = re.compile(
    r"^(what|why|how|when|where|who|which|do|does|did|can|could|would|should|is|are|am)\b"
)


def classify_turn(text: str) -> TurnClassification:
    normalized = _normalize(text)
    is_question = normalized.endswith("?") or bool(QUESTION_PREFIX.search(normalized))

    if _matches(normalized, ("forget ", "delete ", "remove ", "purge ", "do not remember", "don't remember")):
        return _classification(
            TurnType.FORGET_REQUEST,
            normalized,
            "forget_request",
            is_question=is_question,
            requires_review=True,
        )
    if _matches(normalized, ("that is wrong", "that's wrong", "you are wrong", "you got that wrong", "actually ")):
        return _classification(
            TurnType.CORRECTION,
            normalized,
            "correction_phrase",
            is_question=is_question,
            requires_review=True,
        )
    if _matches(normalized, ("why did you say", "why do you think", "what did you base", "where did that come from")):
        return _classification(
            TurnType.EXPLANATION_QUESTION,
            normalized,
            "explanation_question",
            is_question=True,
            requires_review=True,
        )
    if _matches(normalized, ("what do you remember about me", "what do you know about me", "what have you remembered about me")):
        return _classification(
            TurnType.MEMORY_REVIEW_QUESTION,
            normalized,
            "memory_review_question",
            is_question=True,
            requires_review=True,
        )
    if _matches(normalized, ("remember", "do not forget", "don't forget", "note that", "save this", "keep this in mind")):
        return _classification(
            TurnType.EXPLICIT_REMEMBER_INSTRUCTION,
            normalized,
            "explicit_memory_phrase",
            is_question=is_question,
            should_create_memory_candidate=True,
        )
    if _matches(normalized, ("conflict", "contradict", "contradiction", "that conflicts", "but i said")):
        return _classification(
            TurnType.CONTRADICTION_CHALLENGE,
            normalized,
            "contradiction_phrase",
            is_question=is_question,
            requires_review=True,
        )
    if _matches(normalized, ("what do i", "what did i", "do you remember", "do you recall", "what is my", "what are my")):
        return _classification(
            TurnType.RECALL_QUESTION,
            normalized,
            "recall_question",
            is_question=True,
        )
    if _matches(normalized, ("what are you", "who are you", "what is your name", "who is mneme")):
        return _classification(
            TurnType.IDENTITY_SELF_QUESTION,
            normalized,
            "identity_question",
            is_question=True,
        )
    if _matches(normalized, ("what can you do", "what are you capable of", "what is implemented", "your capabilities", "your limitations")):
        return _classification(
            TurnType.CAPABILITY_QUESTION,
            normalized,
            "capability_question",
            is_question=True,
        )
    if _matches(normalized, ("what model", "which model", "model are you using", "devices are connected", "camera", "microphone", "speaker")):
        return _classification(
            TurnType.DEVICE_STATUS_QUESTION,
            normalized,
            "status_question",
            is_question=is_question,
        )
    if _matches(normalized, ("hello", "hi", "hey", "good morning", "good afternoon", "good evening")):
        return _classification(
            TurnType.GREETING,
            normalized,
            "greeting",
            is_question=is_question,
        )
    return _classification(
        TurnType.ORDINARY_CHAT,
        normalized,
        "fallback",
        confidence=0.72,
        is_question=is_question,
    )


def _classification(
    turn_type: TurnType,
    normalized_text: str,
    matched_rule: str,
    *,
    confidence: float = 0.95,
    is_question: bool = False,
    requires_review: bool = False,
    should_create_memory_candidate: bool = False,
) -> TurnClassification:
    return TurnClassification(
        turn_type=turn_type,
        confidence=confidence,
        matched_rule=matched_rule,
        normalized_text=normalized_text,
        is_question=is_question,
        requires_review=requires_review,
        should_create_memory_candidate=should_create_memory_candidate,
    )


def _matches(normalized: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in normalized for phrase in phrases)


def _normalize(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a non-empty string")
    return " ".join(text.strip().lower().split())


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()
