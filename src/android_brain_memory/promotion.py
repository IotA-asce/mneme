from __future__ import annotations

import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from .engine import MnemeMemory
from .models import MemoryCandidate, SalienceResult
from .runtime import (
    EventBus,
    RuntimeEvent,
    RuntimeEventKind,
    Subscription,
    memory_lifecycle_event,
)
from .salience import SalienceScoringConfig, score_candidate

DECISIONS_WITH_TRACE = frozenset(
    {"working_memory_candidate", "episode", "episode_and_semantic_candidate"}
)
DECISIONS_WITH_EPISODE = frozenset({"episode", "episode_and_semantic_candidate"})
SEMANTIC_DECISION = "episode_and_semantic_candidate"


@dataclass(slots=True)
class PromotionOutcome:
    candidate_id: str
    decision: str
    score: float
    stored_trace: bool
    stored_episode: bool
    semantic_candidate: bool
    salience: SalienceResult
    trace_id: str | None = None
    episode_id: str | None = None
    lifecycle_event_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "decision": self.decision,
            "score": self.score,
            "stored_trace": self.stored_trace,
            "stored_episode": self.stored_episode,
            "semantic_candidate": self.semantic_candidate,
            "trace_id": self.trace_id,
            "episode_id": self.episode_id,
            "lifecycle_event_id": self.lifecycle_event_id,
            "salience": self.salience.to_dict(),
        }


@dataclass(slots=True)
class _PromoterStats:
    handled: int = 0
    skipped: int = 0
    by_decision: dict[str, int] = field(default_factory=dict)


class MemoryPromoter:
    """Drives the observe -> score -> promote segment of the memory lifecycle.

    Subscribes to memory_candidate events and maps the salience decision to
    storage actions through the memory engine. Publishes every decision as a
    memory_lifecycle event when a bus is available. Never adjusts scores and
    never publishes intent, goal, or safety events.
    """

    def __init__(
        self,
        engine: MnemeMemory,
        *,
        config: SalienceScoringConfig | None = None,
        bus: EventBus | None = None,
        source: str = "memory_promoter",
        clock: Callable[[], int] | None = None,
    ) -> None:
        self.engine = engine
        self.config = config
        self.bus = bus
        self.source = source
        self._clock = clock or _now_ms
        self._subscription: Subscription | None = None
        self._stats = _PromoterStats()

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "handled": self._stats.handled,
            "skipped": self._stats.skipped,
            "by_decision": dict(self._stats.by_decision),
        }

    def attach_to_bus(self, bus: EventBus) -> Subscription:
        self.detach_from_bus()
        self.bus = bus
        self._subscription = bus.subscribe(
            self.handle_event,
            kinds=[RuntimeEventKind.MEMORY_CANDIDATE],
            subscription_id=f"{self.source}_candidates",
        )
        return self._subscription

    def detach_from_bus(self) -> None:
        if self._subscription is not None and self.bus is not None:
            self.bus.unsubscribe(self._subscription.subscription_id)
        self._subscription = None

    def handle_event(self, event: RuntimeEvent) -> PromotionOutcome | None:
        payload = event.payload.get("candidate")
        if not isinstance(payload, Mapping):
            self._stats.skipped += 1
            return None
        try:
            candidate = MemoryCandidate.from_dict(payload)
        except ValueError:
            self._stats.skipped += 1
            return None
        return self.promote(candidate)

    def promote(self, candidate: MemoryCandidate | Mapping[str, Any]) -> PromotionOutcome:
        memory_candidate = (
            candidate
            if isinstance(candidate, MemoryCandidate)
            else MemoryCandidate.from_dict(candidate)
        )
        salience = score_candidate(memory_candidate, config=self.config)
        decision = salience.decision
        store_trace = decision in DECISIONS_WITH_TRACE
        create_episode = decision in DECISIONS_WITH_EPISODE

        trace_id = None
        episode_id = None
        if store_trace:
            result = self.engine.remember_candidate(
                memory_candidate,
                config=self.config,
                store_trace=True,
                create_episode=create_episode,
            )
            trace_id = result.trace_id
            episode_id = result.episode.episode_id if result.episode else None

        outcome = PromotionOutcome(
            candidate_id=memory_candidate.candidate_id,
            decision=decision,
            score=salience.score,
            stored_trace=trace_id is not None,
            stored_episode=episode_id is not None,
            semantic_candidate=decision == SEMANTIC_DECISION,
            salience=salience,
            trace_id=trace_id,
            episode_id=episode_id,
        )
        self._stats.handled += 1
        self._stats.by_decision[decision] = self._stats.by_decision.get(decision, 0) + 1
        self._publish_lifecycle(outcome)
        return outcome

    def _publish_lifecycle(self, outcome: PromotionOutcome) -> None:
        if self.bus is None:
            return
        event = self.bus.publish(
            memory_lifecycle_event(
                source=self.source,
                lifecycle_stage="promotion",
                timestamp=self._clock(),
                payload={
                    "candidate_id": outcome.candidate_id,
                    "decision": outcome.decision,
                    "score": outcome.score,
                    "trace_id": outcome.trace_id,
                    "episode_id": outcome.episode_id,
                    "semantic_candidate": outcome.semantic_candidate,
                },
            )
        )
        outcome.lifecycle_event_id = event.event_id


def _now_ms() -> int:
    return int(time.time() * 1000)
