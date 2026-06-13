from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .attention import AttentionState
from .engine import to_jsonable
from .executive import ExecutiveIntent
from .models import Episode, Fact, MemoryBundle, Speakability, SourceType
from .storage import MemoryStore, MetaMemoryRecord


DEFAULT_CONTEXT_CHAR_BUDGET = 8_000
DEFAULT_STATE_CHAR_BUDGET = 1_200
RESTRICTED_PLACEHOLDER = "restricted memory exists"
INTERNAL_SPEAKABILITY = {Speakability.NEVER_SAY, Speakability.INTERNAL_ONLY}


@dataclass(slots=True)
class CognitiveMemoryRef:
    memory_kind: str
    memory_id: str
    text: str
    source_type: str | None = None
    confidence: float | None = None
    speakability: str = Speakability.NORMAL.value
    provenance: dict[str, Any] = field(default_factory=dict)
    ranking: dict[str, Any] = field(default_factory=dict)
    status: str | None = None
    redacted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_kind": self.memory_kind,
            "memory_id": self.memory_id,
            "text": self.text,
            "source_type": self.source_type,
            "confidence": self.confidence,
            "speakability": self.speakability,
            "provenance": dict(self.provenance),
            "ranking": dict(self.ranking),
            "status": self.status,
            "redacted": self.redacted,
        }


@dataclass(slots=True)
class OmittedMemoryRef:
    memory_kind: str
    memory_id: str
    reason: str
    speakability: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_kind": self.memory_kind,
            "memory_id": self.memory_id,
            "reason": self.reason,
            "speakability": self.speakability,
        }


@dataclass(slots=True)
class CognitiveContextPacket:
    user_utterance: str
    created_ts: int
    dialogue_intent: dict[str, Any]
    working_memory: dict[str, Any]
    attention: dict[str, Any]
    safety: dict[str, Any]
    avatar: dict[str, Any]
    memories: list[CognitiveMemoryRef] = field(default_factory=list)
    omitted_memories: list[OmittedMemoryRef] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    ranking_explanations: list[dict[str, Any]] = field(default_factory=list)
    provenance_summary: str = ""
    char_budget: int = DEFAULT_CONTEXT_CHAR_BUDGET
    truncated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_utterance": self.user_utterance,
            "created_ts": self.created_ts,
            "dialogue_intent": dict(self.dialogue_intent),
            "working_memory": dict(self.working_memory),
            "attention": dict(self.attention),
            "safety": dict(self.safety),
            "avatar": dict(self.avatar),
            "memories": [memory.to_dict() for memory in self.memories],
            "omitted_memories": [memory.to_dict() for memory in self.omitted_memories],
            "warnings": list(self.warnings),
            "ranking_explanations": [dict(item) for item in self.ranking_explanations],
            "provenance_summary": self.provenance_summary,
            "char_budget": self.char_budget,
            "serialized_chars": self.serialized_chars(),
            "truncated": self.truncated,
        }

    def serialized_chars(self) -> int:
        payload = self.to_dict_without_size()
        return len(json.dumps(payload, sort_keys=True, ensure_ascii=True))

    def to_dict_without_size(self) -> dict[str, Any]:
        return {
            "user_utterance": self.user_utterance,
            "created_ts": self.created_ts,
            "dialogue_intent": dict(self.dialogue_intent),
            "working_memory": dict(self.working_memory),
            "attention": dict(self.attention),
            "safety": dict(self.safety),
            "avatar": dict(self.avatar),
            "memories": [memory.to_dict() for memory in self.memories],
            "omitted_memories": [memory.to_dict() for memory in self.omitted_memories],
            "warnings": list(self.warnings),
            "ranking_explanations": [dict(item) for item in self.ranking_explanations],
            "provenance_summary": self.provenance_summary,
            "char_budget": self.char_budget,
            "truncated": self.truncated,
        }

    def allowed_memory_ids(self) -> set[tuple[str, str]]:
        return {
            (memory.memory_kind, memory.memory_id)
            for memory in self.memories
        }

    def memory_by_id(self, memory_kind: str, memory_id: str) -> CognitiveMemoryRef | None:
        for memory in self.memories:
            if memory.memory_kind == memory_kind and memory.memory_id == memory_id:
                return memory
        return None


def build_cognitive_context(
    *,
    user_utterance: str,
    intent: ExecutiveIntent | Mapping[str, Any] | None = None,
    bundle: MemoryBundle | None = None,
    working: Mapping[str, Any] | None = None,
    attention: AttentionState | Mapping[str, Any] | None = None,
    safety: Mapping[str, Any] | None = None,
    avatar: Mapping[str, Any] | None = None,
    store: MemoryStore | None = None,
    trusted_internal: bool = False,
    char_budget: int = DEFAULT_CONTEXT_CHAR_BUDGET,
) -> CognitiveContextPacket:
    if char_budget <= 0:
        raise ValueError("char_budget must be positive")
    intent_dict = _intent_dict(intent)
    created_ts = _created_ts(intent_dict, working)
    packet = CognitiveContextPacket(
        user_utterance=_shorten(_required_text(user_utterance, "user_utterance"), 1_000),
        created_ts=created_ts,
        dialogue_intent=_compact_mapping(intent_dict, DEFAULT_STATE_CHAR_BUDGET),
        working_memory=_compact_mapping(working or {}, DEFAULT_STATE_CHAR_BUDGET),
        attention=_compact_mapping(_attention_dict(attention), DEFAULT_STATE_CHAR_BUDGET),
        safety=_compact_mapping(safety or _safety_from_working(working), 600),
        avatar=_compact_mapping(avatar or {}, 600),
        warnings=list(bundle.warnings) if bundle else [],
        ranking_explanations=list(bundle.ranking_explanations) if bundle else [],
        provenance_summary=_shorten(bundle.provenance_summary if bundle else "", 1_200),
        char_budget=char_budget,
    )
    if bundle is not None:
        for fact in bundle.facts:
            _append_fact(packet, fact, store, trusted_internal)
        for episode in bundle.episodes:
            _append_episode(packet, episode, store, trusted_internal)
        for summary in bundle.summaries:
            _append_summary(packet, summary, store, trusted_internal)
    _enforce_budget(packet)
    return packet


def _append_fact(
    packet: CognitiveContextPacket,
    fact: Fact,
    store: MemoryStore | None,
    trusted_internal: bool,
) -> None:
    meta = _meta(store, fact.fact_id, "fact")
    speakability = _speakability(meta)
    if _is_withheld(speakability, trusted_internal):
        packet.omitted_memories.append(
            OmittedMemoryRef("fact", fact.fact_id, "withheld_by_speakability", speakability.value)
        )
        return
    value = fact.object_value.get("value", fact.object_value)
    text = f"{fact.subject} {fact.predicate} {_json_text(value)}"
    redacted = speakability == Speakability.RESTRICTED and not trusted_internal
    packet.memories.append(
        CognitiveMemoryRef(
            memory_kind="fact",
            memory_id=fact.fact_id,
            text=RESTRICTED_PLACEHOLDER if redacted else _shorten(text, 700),
            source_type=fact.source_type.value,
            confidence=fact.confidence,
            speakability=speakability.value,
            provenance=_provenance(meta),
            ranking=_ranking(packet, "fact", fact.fact_id),
            status=fact.status.value,
            redacted=redacted,
        )
    )


def _append_episode(
    packet: CognitiveContextPacket,
    episode: Episode,
    store: MemoryStore | None,
    trusted_internal: bool,
) -> None:
    meta = _meta(store, episode.episode_id, "episode")
    speakability = _speakability(meta)
    if _is_withheld(speakability, trusted_internal):
        packet.omitted_memories.append(
            OmittedMemoryRef("episode", episode.episode_id, "withheld_by_speakability", speakability.value)
        )
        return
    redacted = speakability == Speakability.RESTRICTED and not trusted_internal
    packet.memories.append(
        CognitiveMemoryRef(
            memory_kind="episode",
            memory_id=episode.episode_id,
            text=RESTRICTED_PLACEHOLDER if redacted else _shorten(episode.summary, 700),
            source_type=_source_type(meta),
            confidence=episode.confidence,
            speakability=speakability.value,
            provenance=_provenance(meta),
            ranking=_ranking(packet, "episode", episode.episode_id),
            redacted=redacted,
        )
    )


def _append_summary(
    packet: CognitiveContextPacket,
    summary: Mapping[str, Any],
    store: MemoryStore | None,
    trusted_internal: bool,
) -> None:
    summary_id = _required_text(summary.get("summary_id"), "summary_id")
    meta = _meta(store, summary_id, "summary")
    speakability = _speakability(meta)
    if _is_withheld(speakability, trusted_internal):
        packet.omitted_memories.append(
            OmittedMemoryRef("summary", summary_id, "withheld_by_speakability", speakability.value)
        )
        return
    redacted = speakability == Speakability.RESTRICTED and not trusted_internal
    packet.memories.append(
        CognitiveMemoryRef(
            memory_kind="summary",
            memory_id=summary_id,
            text=RESTRICTED_PLACEHOLDER if redacted else _shorten(str(summary.get("summary", "")), 700),
            source_type=_source_type(meta),
            confidence=_optional_float(summary.get("confidence")),
            speakability=speakability.value,
            provenance=_provenance(meta),
            ranking=_ranking(packet, "summary", summary_id),
            redacted=redacted,
        )
    )


def _enforce_budget(packet: CognitiveContextPacket) -> None:
    while packet.serialized_chars() > packet.char_budget and packet.memories:
        removed = packet.memories.pop()
        packet.omitted_memories.append(
            OmittedMemoryRef(
                removed.memory_kind,
                removed.memory_id,
                "omitted_due_to_context_budget",
                removed.speakability,
            )
        )
        packet.truncated = True
    if packet.serialized_chars() > packet.char_budget:
        packet.ranking_explanations = []
        packet.provenance_summary = _shorten(packet.provenance_summary, 200)
        packet.truncated = True


def _meta(store: MemoryStore | None, memory_id: str, memory_kind: str) -> MetaMemoryRecord | None:
    return store.get_meta_memory(memory_id, memory_kind) if store is not None else None


def _speakability(meta: MetaMemoryRecord | None) -> Speakability:
    return meta.speakability if meta is not None else Speakability.NORMAL


def _source_type(meta: MetaMemoryRecord | None) -> str | None:
    return meta.source_type.value if meta is not None else None


def _provenance(meta: MetaMemoryRecord | None) -> dict[str, Any]:
    return dict(meta.provenance) if meta is not None else {}


def _is_withheld(speakability: Speakability, trusted_internal: bool) -> bool:
    return speakability in INTERNAL_SPEAKABILITY and not trusted_internal


def _ranking(packet: CognitiveContextPacket, memory_kind: str, memory_id: str) -> dict[str, Any]:
    for item in packet.ranking_explanations:
        if item.get("memory_kind") == memory_kind and item.get("memory_id") == memory_id:
            return dict(item)
    return {}


def _intent_dict(intent: ExecutiveIntent | Mapping[str, Any] | None) -> dict[str, Any]:
    if intent is None:
        return {}
    if isinstance(intent, ExecutiveIntent):
        return intent.to_dict()
    return dict(intent)


def _attention_dict(attention: AttentionState | Mapping[str, Any] | None) -> dict[str, Any]:
    if attention is None:
        return {}
    if isinstance(attention, AttentionState):
        return attention.to_dict()
    return dict(attention)


def _safety_from_working(working: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(working, Mapping):
        return {}
    safety = working.get("safety_state")
    return dict(safety) if isinstance(safety, Mapping) else {}


def _created_ts(intent: Mapping[str, Any], working: Mapping[str, Any] | None) -> int:
    value = intent.get("created_ts")
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(working, Mapping):
        value = working.get("created_ts")
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    return 0


def _compact_mapping(value: Mapping[str, Any], max_chars: int) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    payload = to_jsonable(dict(value))
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    if len(encoded) <= max_chars:
        return payload
    return {
        "truncated": True,
        "summary": _shorten(encoded, max_chars),
    }


def _json_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(to_jsonable(value), sort_keys=True, ensure_ascii=True)


def _optional_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _shorten(text: str, limit: int) -> str:
    clean = " ".join(str(text).split())
    if len(clean) <= limit:
        return clean
    return clean[: max(0, limit - 3)].rstrip() + "..."
