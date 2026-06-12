# Implementation Plan

## Phase 1 — Daemon Component

- `consolidation_daemon.py`:
  - `ConsolidationDaemon(engine, *, min_interval_s=300, consolidation_options=None, bus=None, source="consolidation_daemon", clock=None)` (clock in ms, consistent with other runtime components).
  - `tick(now_ms=None) -> ConsolidationReport | None`: returns `None` (and counts a skip) when the minimum interval since the last pass has not elapsed; otherwise runs `consolidate_once` with the configured options, updates cumulative stats, publishes a `memory_lifecycle` event with the report payload, and records the pass time.
  - `run_once(now_ms=None) -> ConsolidationReport`: forced pass ignoring the interval (still updates stats/eventing/last-run time).
  - `stats` property: passes, skipped ticks, last-run timestamp, cumulative summaries created/updated and decay updates.

## Phase 2 — Tests (written first)

- `tests/test_consolidation_daemon.py`: first tick consolidates repeated episodes and publishes a lifecycle event; ticks inside the interval are skipped; ticks after the interval run again and update (not duplicate) summaries; `run_once` forces a pass; `max_episodes` batch limit is honored; stats accumulate.

## Phase 3 — Docs and Status

- `docs/memory/CONSOLIDATION.md` daemon section; `MASTER_ROADMAP.md` M1.3; `REPO_STATUS.md`; memory entry + index.

## Validation

- `python -m pytest tests/test_consolidation_daemon.py`
- `python -m pytest`
- `python scripts/dev_check.py`

## Dependency Order

Daemon → tests green → docs.

## Rollback

Revert the new module, tests, docs. No schema changes.

## Definition of Done

- Repeated invocations are idempotent; interval policy and batch limits proven; passes observable as lifecycle events; full suite passes; no threads anywhere.
