from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .cognitive_context import CognitiveContextPacket
from .dialogue import UtterancePlan
from .model_runtime import (
    DEFAULT_OLLAMA_MODEL,
    ModelMessage,
    ModelRequest,
    ModelRuntimeAdapter,
)


DEFAULT_MAX_RESPONSE_CHARS = 500
DEFAULT_MODEL_DIALOGUE_TIMEOUT_MS = 15_000
VALID_UNCERTAINTY = {"low", "medium", "high"}
LOW_CONFIDENCE_THRESHOLD = 0.6
LOW_CONFIDENCE_MARKERS = (
    "i may be wrong",
    "i might be wrong",
    "i am not certain",
    "i'm not certain",
    "not certain",
)

MODEL_DIALOGUE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "response_text": {"type": "string"},
        "memory_refs_used": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "memory_kind": {"type": "string"},
                    "memory_id": {"type": "string"},
                },
                "required": ["memory_kind", "memory_id"],
            },
        },
        "uncertainty": {"type": "string", "enum": ["low", "medium", "high"]},
        "proposed_memory_candidates": {"type": "array", "maxItems": 0},
        "safety_notes": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "response_text",
        "memory_refs_used",
        "uncertainty",
        "proposed_memory_candidates",
        "safety_notes",
    ],
    "additionalProperties": False,
}


@dataclass(slots=True)
class ModelDialogueResult:
    text: str
    used_model: bool
    fallback_reason: str | None = None
    backend: str | None = None
    model: str | None = None
    latency_ms: int | None = None
    memory_refs_used: list[dict[str, str]] = field(default_factory=list)
    uncertainty: str = "low"
    proposed_memory_candidates: list[dict[str, Any]] = field(default_factory=list)
    safety_notes: list[str] = field(default_factory=list)
    raw_model_text: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "used_model": self.used_model,
            "fallback_reason": self.fallback_reason,
            "backend": self.backend,
            "model": self.model,
            "latency_ms": self.latency_ms,
            "memory_refs_used": [dict(item) for item in self.memory_refs_used],
            "uncertainty": self.uncertainty,
            "proposed_memory_candidates": [dict(item) for item in self.proposed_memory_candidates],
            "safety_notes": list(self.safety_notes),
            "raw_model_text": self.raw_model_text,
        }


class ModelDialogueRealizer:
    def __init__(
        self,
        adapter: ModelRuntimeAdapter,
        *,
        model: str = DEFAULT_OLLAMA_MODEL,
        timeout_ms: int = DEFAULT_MODEL_DIALOGUE_TIMEOUT_MS,
        max_response_chars: int = DEFAULT_MAX_RESPONSE_CHARS,
    ) -> None:
        self.adapter = adapter
        self.model = _required_text(model, "model")
        self.timeout_ms = _positive_int(timeout_ms, "timeout_ms")
        self.max_response_chars = _positive_int(max_response_chars, "max_response_chars")
        self.last_result: ModelDialogueResult | None = None

    @property
    def backend(self) -> str:
        return self.adapter.backend

    def realize(
        self,
        plan: UtterancePlan,
        context: CognitiveContextPacket,
    ) -> ModelDialogueResult:
        request = ModelRequest(
            model=self.model,
            messages=[
                ModelMessage(role="system", content=_system_prompt()),
                ModelMessage(role="user", content=_user_prompt(plan, context)),
            ],
            options={"temperature": 0, "num_predict": 384, "seed": 7},
            response_format=MODEL_DIALOGUE_SCHEMA,
            timeout_ms=self.timeout_ms,
        )
        response = self.adapter.generate(request)
        if not response.ok:
            return self._fallback(plan, response.error_code or "model_error", response=response.text)
        parsed = _parse_json_object(response.text)
        if parsed is None:
            return self._fallback(plan, "malformed_json", response=response.text, latency_ms=response.latency_ms)
        validation = self._validate_payload(parsed, plan, context)
        if validation is not None:
            return self._fallback(plan, validation, response=response.text, latency_ms=response.latency_ms)
        text = _required_text(parsed["response_text"], "response_text")
        refs = _memory_refs(parsed.get("memory_refs_used", []))
        uncertainty = str(parsed.get("uncertainty", "low"))
        notes = _string_list(parsed.get("safety_notes", []))
        if _uses_low_confidence_ref(refs, context) and not _has_low_confidence_marker(text):
            text = f"I may be wrong, but {text[:1].lower()}{text[1:]}"
            notes.append("added_low_confidence_hedge")
        result = ModelDialogueResult(
            text=text,
            used_model=True,
            backend=response.backend,
            model=response.model,
            latency_ms=response.latency_ms,
            memory_refs_used=refs,
            uncertainty=uncertainty,
            proposed_memory_candidates=_mapping_list(parsed.get("proposed_memory_candidates", [])),
            safety_notes=notes,
            raw_model_text=response.text,
        )
        self.last_result = result
        return result

    def _validate_payload(
        self,
        payload: Mapping[str, Any],
        plan: UtterancePlan,
        context: CognitiveContextPacket,
    ) -> str | None:
        text = payload.get("response_text")
        if not isinstance(text, str) or not text.strip():
            return "empty_response_text"
        if len(text.strip()) > self.max_response_chars:
            return "response_too_long"
        refs = _memory_refs(payload.get("memory_refs_used", []))
        if refs is None:
            return "invalid_memory_refs"
        allowed = context.allowed_memory_ids()
        for ref in refs:
            if (ref["memory_kind"], ref["memory_id"]) not in allowed:
                return "invented_memory_ref"
        uncertainty = payload.get("uncertainty")
        if uncertainty not in VALID_UNCERTAINTY:
            return "invalid_uncertainty"
        if _mentions_omitted_memory(text, context):
            return "withheld_memory_leak"
        if _claims_inferred_memory_was_user_confirmed(text, refs, context):
            return "source_status_misrepresented"
        if not isinstance(payload.get("proposed_memory_candidates"), list):
            return "invalid_memory_candidate_proposals"
        if not isinstance(payload.get("safety_notes"), list):
            return "invalid_safety_notes"
        return None

    def _fallback(
        self,
        plan: UtterancePlan,
        reason: str,
        *,
        response: str | None = None,
        latency_ms: int | None = None,
    ) -> ModelDialogueResult:
        result = ModelDialogueResult(
            text=plan.text,
            used_model=False,
            fallback_reason=reason,
            backend=self.backend,
            model=self.model,
            latency_ms=latency_ms,
            memory_refs_used=[dict(ref) for ref in plan.memory_refs],
            raw_model_text=response,
        )
        self.last_result = result
        return result

    def status(self) -> dict[str, Any]:
        return {
            "enabled": True,
            "backend": self.backend,
            "model": self.model,
            "last_result": self.last_result.to_dict() if self.last_result else None,
        }


def disabled_model_dialogue_status() -> dict[str, Any]:
    return {
        "enabled": False,
        "backend": None,
        "model": None,
        "last_result": None,
    }


def _system_prompt() -> str:
    return (
        "You are Mneme's local dialogue wording layer. "
        "Do not choose intent, do not invent memories, and do not add facts. "
        "Use only the allowed memory_refs in the provided context. "
        "proposed_memory_candidates must always be an empty array for now. "
        "Do not add fields outside the schema. "
        "Preserve provenance wording: user_confirmed means 'You told me', "
        "sensor_observed means 'I observed', model_inferred means 'I think'. "
        "Return only JSON matching the requested schema."
    )


def _user_prompt(plan: UtterancePlan, context: CognitiveContextPacket) -> str:
    payload = {
        "deterministic_plan": plan.to_dict(),
        "cognitive_context": _model_context_payload(context),
        "rules": [
            "Keep response_text concise and safe.",
            "Use memory_refs_used only from cognitive_context.memories.",
            "If no memory is needed, memory_refs_used must be empty.",
            "Do not expose omitted_memories.",
            "Do not store proposed_memory_candidates.",
        ],
    }
    return json.dumps(payload, sort_keys=True, ensure_ascii=True)


def _model_context_payload(context: CognitiveContextPacket) -> dict[str, Any]:
    return {
        "user_utterance": context.user_utterance,
        "created_ts": context.created_ts,
        "intent_type": context.dialogue_intent.get("intent_type"),
        "topic": context.working_memory.get("topic"),
        "current_speaker": context.working_memory.get("current_speaker"),
        "attention_target": context.working_memory.get("attention_target")
        or context.attention.get("active_target_id"),
        "safety": context.safety,
        "avatar": {
            key: context.avatar.get(key)
            for key in ("mode", "gaze_target", "expression", "mouth_state")
            if key in context.avatar
        },
        "memories": [
            {
                "memory_kind": memory.memory_kind,
                "memory_id": memory.memory_id,
                "text": memory.text,
                "source_type": memory.source_type,
                "confidence": memory.confidence,
                "speakability": memory.speakability,
                "redacted": memory.redacted,
            }
            for memory in context.memories
        ],
        "omitted_memories": [item.to_dict() for item in context.omitted_memories],
        "warnings": list(context.warnings),
        "provenance_summary": context.provenance_summary,
    }


def _parse_json_object(text: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return dict(parsed) if isinstance(parsed, Mapping) else None


def _memory_refs(value: Any) -> list[dict[str, str]] | None:
    if not isinstance(value, list):
        return None
    refs: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, Mapping):
            return None
        kind = item.get("memory_kind")
        memory_id = item.get("memory_id")
        if not isinstance(kind, str) or not kind.strip():
            return None
        if not isinstance(memory_id, str) or not memory_id.strip():
            return None
        refs.append({"memory_kind": kind.strip(), "memory_id": memory_id.strip()})
    return refs


def _mapping_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str)]


def _mentions_omitted_memory(text: str, context: CognitiveContextPacket) -> bool:
    lowered = text.lower()
    if "never_say" in lowered or "internal_only" in lowered:
        return True
    for omitted in context.omitted_memories:
        if omitted.memory_id.lower() in lowered:
            return True
    return False


def _claims_inferred_memory_was_user_confirmed(
    text: str,
    refs: list[dict[str, str]],
    context: CognitiveContextPacket,
) -> bool:
    lowered = text.lower()
    if "you told me" not in lowered:
        return False
    for ref in refs:
        memory = context.memory_by_id(ref["memory_kind"], ref["memory_id"])
        if memory is not None and memory.source_type == "model_inferred":
            return True
    return False


def _uses_low_confidence_ref(
    refs: list[dict[str, str]],
    context: CognitiveContextPacket,
) -> bool:
    for ref in refs:
        memory = context.memory_by_id(ref["memory_kind"], ref["memory_id"])
        if memory is not None and memory.confidence is not None and memory.confidence < LOW_CONFIDENCE_THRESHOLD:
            return True
    return False


def _has_low_confidence_marker(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in LOW_CONFIDENCE_MARKERS)


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer")
    return value
