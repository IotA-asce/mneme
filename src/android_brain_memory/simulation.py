from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

import yaml

from .models import MemoryCandidate, SalienceFeatures, SourceType, validate_confidence, validate_timestamp
from .runtime import (
    EventBus,
    RuntimeEvent,
    memory_candidate_event,
    perception_observation,
    safety_event,
)


DEFAULT_SCENARIO_TTL_MS = 5_000


@dataclass(slots=True)
class ScenarioStep:
    step_id: str
    worker: str
    at_ms: int
    payload: dict[str, Any]
    confidence: float = 0.8
    ttl_ms: int | None = None
    source: str | None = None
    important: bool = False
    memory_candidate: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        self.step_id = _required_text(self.step_id, "step_id")
        self.worker = _required_text(self.worker, "worker")
        self.at_ms = validate_timestamp(self.at_ms, "at_ms")
        self.payload = _json_mapping(self.payload, "payload")
        self.confidence = validate_confidence(self.confidence)
        if self.ttl_ms is not None:
            self.ttl_ms = _positive_int(self.ttl_ms, "ttl_ms")
        if self.source is not None:
            self.source = _required_text(self.source, "source")
        if not isinstance(self.important, bool):
            raise ValueError("important must be a boolean")
        if self.memory_candidate is not None:
            self.memory_candidate = _json_mapping(self.memory_candidate, "memory_candidate")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ScenarioStep":
        data = _required_mapping(data)
        worker = data.get("worker", data.get("type"))
        if worker is None:
            raise ValueError("scenario step requires worker or type")
        payload = data.get("payload", data.get("data", {}))
        if not isinstance(payload, Mapping):
            reserved = {
                "id",
                "step_id",
                "worker",
                "type",
                "at",
                "at_ms",
                "time_ms",
                "timestamp",
                "confidence",
                "ttl_ms",
                "source",
                "important",
                "memory_candidate",
                "summary",
            }
            payload = {key: value for key, value in data.items() if key not in reserved}
        return cls(
            step_id=data.get("id", data.get("step_id", f"step_{data.get('at_ms', 0)}")),
            worker=worker,
            at_ms=data.get("at_ms", data.get("at", data.get("time_ms", data.get("timestamp", 0)))),
            payload=dict(payload),
            confidence=data.get("confidence", 0.8),
            ttl_ms=data.get("ttl_ms"),
            source=data.get("source"),
            important=data.get("important", False),
            memory_candidate=data.get("memory_candidate"),
        )


@dataclass(slots=True)
class Scenario:
    name: str
    start_ts: int = 0
    default_ttl_ms: int = DEFAULT_SCENARIO_TTL_MS
    steps: list[ScenarioStep] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.name = _required_text(self.name, "name")
        self.start_ts = validate_timestamp(self.start_ts, "start_ts")
        self.default_ttl_ms = _positive_int(self.default_ttl_ms, "default_ttl_ms")
        self.steps = [
            step if isinstance(step, ScenarioStep) else ScenarioStep.from_dict(step)
            for step in self.steps
        ]
        self.steps = sorted(self.steps, key=lambda step: (step.at_ms, step.step_id))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Scenario":
        data = _required_mapping(data)
        return cls(
            name=data.get("name", "unnamed_scenario"),
            start_ts=data.get("start_ts", data.get("start_time_ms", 0)),
            default_ttl_ms=data.get("default_ttl_ms", DEFAULT_SCENARIO_TTL_MS),
            steps=list(data.get("steps", [])),
        )


@dataclass(slots=True)
class ReplayResult:
    scenario_name: str
    events: list[RuntimeEvent] = field(default_factory=list)
    memory_candidates: list[MemoryCandidate] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_name": self.scenario_name,
            "events": [event.to_dict() for event in self.events],
            "memory_candidates": [
                candidate.to_dict()
                for candidate in self.memory_candidates
            ],
        }


class FacePersonWorker:
    source = "sim.face_person_worker"

    def event(self, step: ScenarioStep, timestamp: int, ttl_ms: int, event_id: str) -> RuntimeEvent:
        person_id = _required_text(step.payload.get("person_id", step.payload.get("label")), "person_id")
        payload = {
            "person_id": person_id,
            "label": step.payload.get("label", person_id),
            "observation_type": "person_seen",
            **step.payload,
        }
        return perception_observation(
            source=step.source or self.source,
            observation_type="person_seen",
            payload=payload,
            confidence=step.confidence,
            timestamp=timestamp,
            ttl_ms=ttl_ms,
            event_id=event_id,
        )


class SpeechTranscriptWorker:
    source = "sim.speech_transcript_worker"

    def event(self, step: ScenarioStep, timestamp: int, ttl_ms: int, event_id: str) -> RuntimeEvent:
        speaker = _required_text(step.payload.get("speaker"), "speaker")
        transcript = _required_text(
            step.payload.get("transcript", step.payload.get("utterance", step.payload.get("text"))),
            "transcript",
        )
        payload = {
            "speaker": speaker,
            "transcript": transcript,
            "utterance": transcript,
            **step.payload,
        }
        return perception_observation(
            source=step.source or self.source,
            observation_type="speech_transcript",
            payload=payload,
            confidence=step.confidence,
            timestamp=timestamp,
            ttl_ms=ttl_ms,
            event_id=event_id,
        )


class SoundDirectionWorker:
    source = "sim.sound_direction_worker"

    def event(self, step: ScenarioStep, timestamp: int, ttl_ms: int, event_id: str) -> RuntimeEvent:
        direction_deg = step.payload.get("direction_deg", step.payload.get("azimuth_deg"))
        if isinstance(direction_deg, bool) or not isinstance(direction_deg, (int, float)):
            raise ValueError("direction_deg must be a number")
        payload = {
            "direction_deg": float(direction_deg),
            "source_label": step.payload.get("source_label", "unknown"),
            **step.payload,
        }
        return perception_observation(
            source=step.source or self.source,
            observation_type="sound_direction",
            payload=payload,
            confidence=step.confidence,
            timestamp=timestamp,
            ttl_ms=ttl_ms,
            event_id=event_id,
        )


class TouchWorker:
    source = "sim.touch_worker"

    def event(self, step: ScenarioStep, timestamp: int, ttl_ms: int, event_id: str) -> RuntimeEvent:
        zone = _required_text(step.payload.get("zone", step.payload.get("location")), "zone")
        payload = {
            "zone": zone,
            "gesture": step.payload.get("gesture", "touch"),
            **step.payload,
        }
        return perception_observation(
            source=step.source or self.source,
            observation_type="touch",
            payload=payload,
            confidence=step.confidence,
            timestamp=timestamp,
            ttl_ms=ttl_ms,
            event_id=event_id,
        )


class BodyHealthWorker:
    source = "sim.body_health_worker"

    def event(self, step: ScenarioStep, timestamp: int, ttl_ms: int, event_id: str) -> RuntimeEvent:
        status = _required_text(step.payload.get("status", step.payload.get("health_status")), "status")
        payload = {
            "status": status,
            "health_status": status,
            **step.payload,
        }
        return perception_observation(
            source=step.source or self.source,
            observation_type="body_health",
            payload=payload,
            confidence=step.confidence,
            timestamp=timestamp,
            ttl_ms=ttl_ms,
            event_id=event_id,
        )

    def safety_event(
        self,
        step: ScenarioStep,
        timestamp: int,
        ttl_ms: int,
        event_id: str,
    ) -> RuntimeEvent | None:
        level = step.payload.get("safety_level")
        if level is None:
            return None
        return safety_event(
            source=step.source or self.source,
            safety_level=_required_text(level, "safety_level"),
            payload=dict(step.payload),
            confidence=step.confidence,
            timestamp=timestamp,
            ttl_ms=ttl_ms,
            event_id=f"{event_id}_safety",
        )


SIMULATED_WORKERS = {
    "face_person": FacePersonWorker(),
    "person": FacePersonWorker(),
    "speech_transcript": SpeechTranscriptWorker(),
    "speech": SpeechTranscriptWorker(),
    "sound_direction": SoundDirectionWorker(),
    "sound": SoundDirectionWorker(),
    "touch": TouchWorker(),
    "body_health": BodyHealthWorker(),
    "health": BodyHealthWorker(),
}


class ScenarioReplayRunner:
    def __init__(
        self,
        bus: EventBus,
        *,
        workers: Mapping[str, Any] | None = None,
    ) -> None:
        self.bus = bus
        self.workers = dict(workers or SIMULATED_WORKERS)

    def replay(self, scenario: Scenario | Mapping[str, Any]) -> ReplayResult:
        loaded = scenario if isinstance(scenario, Scenario) else Scenario.from_dict(scenario)
        result = ReplayResult(scenario_name=loaded.name)
        for step in loaded.steps:
            result.events.extend(self._publish_step(loaded, step, result))
        return result

    def replay_file(self, path: str | Path) -> ReplayResult:
        return self.replay(load_scenario(path))

    def _publish_step(
        self,
        scenario: Scenario,
        step: ScenarioStep,
        result: ReplayResult,
    ) -> list[RuntimeEvent]:
        worker = self.workers.get(step.worker)
        if worker is None:
            raise ValueError(f"unknown simulated worker: {step.worker}")
        timestamp = scenario.start_ts + step.at_ms
        ttl_ms = step.ttl_ms if step.ttl_ms is not None else scenario.default_ttl_ms
        event_id = f"evt_{_stable_id(step.step_id)}"
        event = worker.event(step, timestamp, ttl_ms, event_id)
        published = [self.bus.publish(event)]

        if isinstance(worker, BodyHealthWorker):
            maybe_safety = worker.safety_event(step, timestamp, ttl_ms, event_id)
            if maybe_safety is not None:
                published.append(self.bus.publish(maybe_safety))

        if step.important or step.memory_candidate is not None:
            candidate = _candidate_from_step(step, event)
            result.memory_candidates.append(candidate)
            candidate_event = memory_candidate_event(
                source="scenario_replay",
                candidate=candidate,
                timestamp=timestamp,
                ttl_ms=ttl_ms,
                event_id=f"{event_id}_memory_candidate",
            )
            published.append(self.bus.publish(candidate_event))

        return published


def load_scenario(path: str | Path) -> Scenario:
    scenario_path = Path(path)
    raw = scenario_path.read_text(encoding="utf-8")
    if scenario_path.suffix.lower() == ".json":
        data = json.loads(raw)
    else:
        data = yaml.safe_load(raw)
    if not isinstance(data, Mapping):
        raise ValueError("scenario file must contain a mapping")
    return Scenario.from_dict(data)


def _candidate_from_step(step: ScenarioStep, event: RuntimeEvent) -> MemoryCandidate:
    if step.memory_candidate is not None:
        payload = dict(step.memory_candidate)
        payload.setdefault("candidate_id", f"cand_{_stable_id(step.step_id)}")
        payload.setdefault("candidate_type", f"{step.worker}_event")
        payload.setdefault("summary", _summary_for_step(step, event))
        payload.setdefault("source_type", SourceType.SENSOR_OBSERVED.value)
        payload.setdefault("confidence", event.confidence if event.confidence is not None else 0.5)
        payload.setdefault("features", _default_features(explicit_remember=step.important))
        payload.setdefault("entities", _entities_for_event(event))
        payload.setdefault("tags", ["scenario", step.worker])
        payload.setdefault("payload", {"event": event.to_dict()})
        payload.setdefault("provenance_refs", [event.event_id])
        return MemoryCandidate.from_dict(payload)

    return MemoryCandidate(
        candidate_id=f"cand_{_stable_id(step.step_id)}",
        candidate_type=f"{step.worker}_event",
        summary=_summary_for_step(step, event),
        source_type=SourceType.SENSOR_OBSERVED,
        confidence=event.confidence if event.confidence is not None else 0.5,
        features=SalienceFeatures.from_dict(_default_features(explicit_remember=True)),
        entities=_entities_for_event(event),
        tags=["scenario", step.worker],
        payload={"event": event.to_dict()},
        provenance_refs=[event.event_id],
    )


def _summary_for_step(step: ScenarioStep, event: RuntimeEvent) -> str:
    if step.memory_candidate and isinstance(step.memory_candidate.get("summary"), str):
        return step.memory_candidate["summary"]
    for key in ("summary", "transcript", "utterance", "text"):
        value = event.payload.get(key, step.payload.get(key))
        if isinstance(value, str) and value.strip():
            return value
    return f"Simulated {step.worker} event from {event.source}"


def _entities_for_event(event: RuntimeEvent) -> list[str]:
    entities = []
    for key in ("person_id", "speaker", "source_label", "zone"):
        value = event.payload.get(key)
        if isinstance(value, str) and value.strip():
            entities.append(value)
    return sorted(set(entities))


def _default_features(*, explicit_remember: bool) -> dict[str, float]:
    return {
        "novelty": 0.5,
        "task_relevance": 0.6,
        "social_relevance": 0.6,
        "surprise": 0.2,
        "risk": 0.0,
        "contradiction": 0.0,
        "repetition_signal": 0.1,
        "explicit_remember_flag": 1.0 if explicit_remember else 0.0,
    }


def _stable_id(value: str) -> str:
    return "".join(char if char.isalnum() or char == "_" else "_" for char in value.strip())


def _required_mapping(value: Any, field_name: str = "data") -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    return value


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _json_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    return dict(value)


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be a positive integer")
    if value < 1:
        raise ValueError(f"{field_name} must be a positive integer")
    return value
