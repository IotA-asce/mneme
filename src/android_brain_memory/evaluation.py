from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .engine import to_jsonable
from .models import validate_timestamp


DEFAULT_EVALUATION_LOG = Path(".local/evaluation/daily_driver.jsonl")


@dataclass(slots=True)
class EvaluationRecord:
    timestamp: int
    event_type: str
    metrics: dict[str, Any] = field(default_factory=dict)
    notes: str | None = None

    def __post_init__(self) -> None:
        self.timestamp = validate_timestamp(self.timestamp, "timestamp")
        self.event_type = _required_text(self.event_type, "event_type")
        self.metrics = _json_mapping(self.metrics, "metrics")
        self.notes = _optional_text(self.notes, "notes")

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "metrics": dict(self.metrics),
            "notes": self.notes,
        }


class EvaluationLogger:
    def __init__(self, path: str | Path = DEFAULT_EVALUATION_LOG) -> None:
        self.path = Path(path)

    def record(self, record: EvaluationRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(to_jsonable(record.to_dict()), sort_keys=True) + "\n")

    def record_turn(self, *, input_text: str, result: Mapping[str, Any]) -> EvaluationRecord:
        timestamp = int(result.get("timestamp", 0))
        utterances = result.get("utterances", [])
        events = result.get("events", [])
        snapshot = result.get("snapshot", {})
        presence = snapshot.get("presence") if isinstance(snapshot, Mapping) else {}
        coordinator = presence.get("coordinator") if isinstance(presence, Mapping) else {}
        memory = snapshot.get("memory") if isinstance(snapshot, Mapping) else {}
        speech_loop = snapshot.get("speech_loop") if isinstance(snapshot, Mapping) else {}
        speech_counters = (
            speech_loop.get("counters", {})
            if isinstance(speech_loop, Mapping)
            else {}
        )
        response_text = ""
        if isinstance(utterances, list) and utterances:
            latest = utterances[-1]
            if isinstance(latest, Mapping):
                response_text = str(latest.get("text", ""))
        metrics = {
            "input_chars": len(input_text),
            "response_chars": len(response_text),
            "response_generated": bool(response_text),
            "event_count": len(events) if isinstance(events, list) else 0,
            "barge_ins_total": (
                coordinator.get("barge_ins", 0)
                if isinstance(coordinator, Mapping)
                else 0
            ),
            "memory_table_counts": dict(memory) if isinstance(memory, Mapping) else {},
            "memory_recall_signal": _memory_recall_signal(utterances),
            "skill_status_count": _count_events(events, "skill_status"),
            "safety_event_count": _count_events(events, "safety_event"),
            "speech_loop_state": (
                speech_loop.get("current_state")
                if isinstance(speech_loop, Mapping)
                else None
            ),
            "asr_latency_ms": (
                speech_loop.get("latest_asr_latency_ms")
                if isinstance(speech_loop, Mapping)
                else None
            ),
            "response_latency_ms": (
                speech_loop.get("latest_response_latency_ms")
                if isinstance(speech_loop, Mapping)
                else None
            ),
            "tts_latency_ms": (
                speech_loop.get("latest_tts_latency_ms")
                if isinstance(speech_loop, Mapping)
                else None
            ),
            "no_speech_total": _counter(speech_counters, "no_speech"),
            "capture_errors_total": _counter(speech_counters, "capture_errors"),
            "tts_failures_total": _counter(speech_counters, "tts_failures"),
            "duplicate_suppressions_total": _counter(speech_counters, "duplicate_suppressions"),
            "stuck_states_total": _counter(speech_counters, "stuck_states"),
        }
        record = EvaluationRecord(
            timestamp=timestamp,
            event_type="conversation_turn",
            metrics=metrics,
        )
        self.record(record)
        return record

    def summarize(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"path": str(self.path), "records": 0}
        records = [
            json.loads(line)
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        turns = [record for record in records if record.get("event_type") == "conversation_turn"]
        return {
            "path": str(self.path),
            "records": len(records),
            "conversation_turns": len(turns),
            "responses_generated": sum(1 for item in turns if item.get("metrics", {}).get("response_generated")),
            "skill_status_events": sum(int(item.get("metrics", {}).get("skill_status_count", 0)) for item in turns),
            "safety_events": sum(int(item.get("metrics", {}).get("safety_event_count", 0)) for item in turns),
            "barge_ins_total": max(
                [int(item.get("metrics", {}).get("barge_ins_total", 0)) for item in turns] or [0]
            ),
            "speech": {
                "no_speech_total": _max_metric(turns, "no_speech_total"),
                "capture_errors_total": _max_metric(turns, "capture_errors_total"),
                "tts_failures_total": _max_metric(turns, "tts_failures_total"),
                "duplicate_suppressions_total": _max_metric(turns, "duplicate_suppressions_total"),
                "stuck_states_total": _max_metric(turns, "stuck_states_total"),
                "max_asr_latency_ms": _max_metric(turns, "asr_latency_ms"),
                "max_response_latency_ms": _max_metric(turns, "response_latency_ms"),
                "max_tts_latency_ms": _max_metric(turns, "tts_latency_ms"),
            },
        }


def _memory_recall_signal(utterances: Any) -> bool:
    if not isinstance(utterances, list):
        return False
    for utterance in utterances:
        if not isinstance(utterance, Mapping):
            continue
        plan = utterance.get("plan")
        if isinstance(plan, Mapping) and plan.get("memory_refs"):
            return True
    return False


def _count_events(events: Any, kind: str) -> int:
    if not isinstance(events, list):
        return 0
    return sum(1 for event in events if isinstance(event, Mapping) and event.get("kind") == kind)


def _counter(counters: Any, name: str) -> int:
    if not isinstance(counters, Mapping):
        return 0
    value = counters.get(name, 0)
    return int(value) if isinstance(value, int) and not isinstance(value, bool) else 0


def _max_metric(records: list[dict[str, Any]], name: str) -> int:
    values = []
    for record in records:
        metrics = record.get("metrics", {})
        if not isinstance(metrics, Mapping):
            continue
        value = metrics.get(name)
        if isinstance(value, int) and not isinstance(value, bool):
            values.append(value)
    return max(values or [0])


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _optional_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    return value.strip() or None


def _json_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    return dict(value)
