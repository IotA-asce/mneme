from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from .engine import MnemeMemory
from .models import Episode, Fact, SourceType
from .runtime import (
    EventBus,
    RuntimeEvent,
    RuntimeEventKind,
    Subscription,
    memory_lifecycle_event,
)

DEFAULT_CONFIDENCE_CAP = 0.75
EXTRACTION_DERIVATION_PATH = ["episode", "extraction", "fact"]


def statement_fact_id(subject: str, predicate: str, value: Any) -> str:
    canonical = json.dumps(
        [subject.strip().lower(), predicate.strip().lower(), value],
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
    return f"fact_{digest}"


@dataclass(slots=True)
class FactExtractionReport:
    episode_id: str
    statements_found: int = 0
    facts_upserted: int = 0
    conflicts_flagged: int = 0
    fact_ids: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "statements_found": self.statements_found,
            "facts_upserted": self.facts_upserted,
            "conflicts_flagged": self.conflicts_flagged,
            "fact_ids": list(self.fact_ids),
            "skipped": list(self.skipped),
        }


class FactExtractor:
    """Deterministic structured-context fact extraction (semanticization).

    Reads entity-predicate-value statements from episode context and upserts
    them as model_inferred facts through the conflict-aware engine path.
    Inference never masquerades as confirmation: source type is always
    model_inferred and confidence is capped.
    """

    def __init__(
        self,
        engine: MnemeMemory,
        *,
        bus: EventBus | None = None,
        source: str = "fact_extractor",
        confidence_cap: float = DEFAULT_CONFIDENCE_CAP,
        clock: Callable[[], int] | None = None,
    ) -> None:
        if (
            isinstance(confidence_cap, bool)
            or not isinstance(confidence_cap, (int, float))
            or not 0.0 < float(confidence_cap) <= 1.0
        ):
            raise ValueError("confidence_cap must be a number in (0.0, 1.0]")
        self.engine = engine
        self.bus = bus
        self.source = source
        self.confidence_cap = float(confidence_cap)
        self._clock = clock or _now_ms
        self._subscription: Subscription | None = None
        self._extractions = 0
        self._skipped_events = 0

    @property
    def stats(self) -> dict[str, int]:
        return {"extractions": self._extractions, "skipped_events": self._skipped_events}

    def attach_to_bus(self, bus: EventBus) -> Subscription:
        self.detach_from_bus()
        self.bus = bus
        self._subscription = bus.subscribe(
            self.handle_event,
            kinds=[RuntimeEventKind.MEMORY_LIFECYCLE],
            subscription_id=f"{self.source}_lifecycle",
        )
        return self._subscription

    def detach_from_bus(self) -> None:
        if self._subscription is not None and self.bus is not None:
            self.bus.unsubscribe(self._subscription.subscription_id)
        self._subscription = None

    def handle_event(self, event: RuntimeEvent) -> FactExtractionReport | None:
        payload = event.payload
        if payload.get("lifecycle_stage") != "promotion":
            return None
        if not payload.get("semantic_candidate"):
            return None
        episode_id = payload.get("episode_id")
        if not isinstance(episode_id, str) or not episode_id:
            self._skipped_events += 1
            return None
        return self.extract_from_episode(episode_id)

    def extract_from_episode(self, episode: Episode | str) -> FactExtractionReport:
        stored_episode = (
            episode
            if isinstance(episode, Episode)
            else self.engine.store.get_episode(episode)
        )
        if stored_episode is None:
            raise KeyError(f"episode not found: {episode}")

        report = FactExtractionReport(episode_id=stored_episode.episode_id)
        raw_statements = stored_episode.context.get("statements", [])
        if not isinstance(raw_statements, list):
            report.skipped.append("statements must be a list")
            return self._finish(report)

        report.statements_found = len(raw_statements)
        for index, raw in enumerate(raw_statements):
            reason = _statement_problem(raw)
            if reason is not None:
                report.skipped.append(f"statement[{index}]: {reason}")
                continue
            subject = raw["subject"].strip()
            predicate = raw["predicate"].strip()
            value = raw["value"]
            confidence = min(
                stored_episode.confidence,
                _statement_confidence(raw, stored_episode.confidence),
                self.confidence_cap,
            )
            fact = Fact(
                fact_id=statement_fact_id(subject, predicate, value),
                subject=subject,
                predicate=predicate,
                object_value={"value": value},
                confidence=confidence,
                source_type=SourceType.MODEL_INFERRED,
                supporting_episode_ids=[stored_episode.episode_id],
            )
            result = self.engine.add_fact(
                fact,
                source_id=stored_episode.episode_id,
                derivation_path=list(EXTRACTION_DERIVATION_PATH),
                notes="Extracted deterministically from structured episode statements.",
            )
            report.facts_upserted += 1
            report.fact_ids.append(fact.fact_id)
            if result.conflict_report is not None:
                report.conflicts_flagged += 1
        return self._finish(report)

    def extract_recent(self, *, limit: int = 50) -> list[FactExtractionReport]:
        reports = []
        for episode in self.engine.store.get_recent_episodes(limit=limit):
            if isinstance(episode.context.get("statements"), list):
                reports.append(self.extract_from_episode(episode))
        return reports

    def _finish(self, report: FactExtractionReport) -> FactExtractionReport:
        self._extractions += 1
        if self.bus is not None:
            self.bus.publish(
                memory_lifecycle_event(
                    source=self.source,
                    lifecycle_stage="extraction",
                    timestamp=self._clock(),
                    payload=report.to_dict(),
                )
            )
        return report


def _statement_problem(raw: Any) -> str | None:
    if not isinstance(raw, Mapping):
        return "must be a mapping"
    for key in ("subject", "predicate"):
        value = raw.get(key)
        if not isinstance(value, str) or not value.strip():
            return f"{key} must be a non-empty string"
    if "value" not in raw:
        return "value is required"
    return None


def _statement_confidence(raw: Mapping[str, Any], default: float) -> float:
    confidence = raw.get("confidence", default)
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        return default
    normalized = float(confidence)
    if not 0.0 <= normalized <= 1.0:
        return default
    return normalized


def _now_ms() -> int:
    return int(time.time() * 1000)
