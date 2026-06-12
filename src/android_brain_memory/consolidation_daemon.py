from __future__ import annotations

import time
from collections.abc import Callable, Mapping
from typing import Any

from .consolidation import ConsolidationOptions, ConsolidationReport
from .engine import MnemeMemory
from .runtime import EventBus, memory_lifecycle_event


class ConsolidationDaemon:
    """Schedulable wrapper around the one-shot consolidation pass.

    Deterministic by construction: time arrives through an injected clock and
    callers drive tick() — no threads, timers, or sleeps. A future runtime
    loop or ROS timer simply calls tick() periodically.
    """

    def __init__(
        self,
        engine: MnemeMemory,
        *,
        min_interval_s: int = 300,
        consolidation_options: ConsolidationOptions | Mapping[str, Any] | None = None,
        bus: EventBus | None = None,
        source: str = "consolidation_daemon",
        clock: Callable[[], int] | None = None,
    ) -> None:
        if isinstance(min_interval_s, bool) or not isinstance(min_interval_s, int) or min_interval_s < 0:
            raise ValueError("min_interval_s must be a non-negative integer")
        self.engine = engine
        self.min_interval_s = min_interval_s
        self.consolidation_options = consolidation_options
        self.bus = bus
        self.source = source
        self._clock = clock or _now_ms
        self._last_run_ms: int | None = None
        self._passes = 0
        self._skipped_ticks = 0
        self._summaries_created = 0
        self._summaries_updated = 0
        self._decay_metadata_updates = 0

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "passes": self._passes,
            "skipped_ticks": self._skipped_ticks,
            "last_run_ms": self._last_run_ms,
            "summaries_created": self._summaries_created,
            "summaries_updated": self._summaries_updated,
            "decay_metadata_updates": self._decay_metadata_updates,
        }

    def tick(self, now_ms: int | None = None) -> ConsolidationReport | None:
        now = now_ms if now_ms is not None else self._clock()
        if (
            self._last_run_ms is not None
            and (now - self._last_run_ms) < self.min_interval_s * 1000
        ):
            self._skipped_ticks += 1
            return None
        return self._run(now)

    def run_once(self, now_ms: int | None = None) -> ConsolidationReport:
        now = now_ms if now_ms is not None else self._clock()
        return self._run(now)

    def _run(self, now_ms: int) -> ConsolidationReport:
        report = self.engine.consolidate_once(self.consolidation_options)
        self._passes += 1
        self._last_run_ms = now_ms
        self._summaries_created += report.summaries_created
        self._summaries_updated += report.summaries_updated
        self._decay_metadata_updates += report.decay_metadata_updates
        if self.bus is not None:
            self.bus.publish(
                memory_lifecycle_event(
                    source=self.source,
                    lifecycle_stage="consolidation",
                    timestamp=now_ms,
                    payload={
                        "episodes_examined": report.episodes_examined,
                        "groups_considered": report.groups_considered,
                        "groups_summarized": report.groups_summarized,
                        "summaries_created": report.summaries_created,
                        "summaries_updated": report.summaries_updated,
                        "decay_metadata_updates": report.decay_metadata_updates,
                        "summary_ids": list(report.summary_ids),
                        "notes": list(report.notes),
                    },
                )
            )
        return report


def _now_ms() -> int:
    return int(time.time() * 1000)
