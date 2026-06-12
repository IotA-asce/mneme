# Core Idea: Consolidation Daemon (Stage 1 / M1.3)

## Problem Statement

Consolidation exists only as a manual one-shot pass (`consolidate_once`). Nothing schedules it, limits it, reports its progress on the runtime bus, or tracks totals across passes — so the `consolidate` lifecycle step never happens by itself.

## Desired Outcome

- A `ConsolidationDaemon` component that wraps the one-shot pass with a scheduling policy (minimum interval between passes), batch limits, cumulative statistics, and `memory_lifecycle` progress events (`lifecycle_stage="consolidation"`).
- Fully deterministic and replay-testable: time arrives through an injected clock and `tick()` calls — no threads, no sleeps, no background process in V1. A future runtime loop (or ROS timer) simply calls `tick()` periodically.

## User / Project Value

Consolidation becomes a schedulable subsystem with observable progress instead of a function someone must remember to call, while staying 100% deterministic for tests and CI.

## Affected Systems

- `src/android_brain_memory/consolidation_daemon.py` (new), `__init__.py` exports
- `tests/test_consolidation_daemon.py` (new)
- `docs/memory/CONSOLIDATION.md`, roadmap/status docs

## Assumptions

- `consolidate_once` is already idempotent for unchanged inputs (deterministic summary IDs, INSERT OR REPLACE) — repeated passes update rather than duplicate.
- Callers (tests today, a runtime loop later) drive `tick()`; the daemon never spawns threads itself.

## Constraints

- Deterministic, standard library only, no schema changes, no threads/asyncio.
- The daemon must not change consolidation semantics — it only schedules, bounds, observes, and aggregates.

## Non-Goals

- A real OS daemon/process or thread (the runtime loop arrives with the ROS bridge, Stage 3).
- Idle-detection triggers (needs the executive/world model integration from Stage 2).
- Fact extraction from summaries (future increment of M1.2).

## Risks

- A long gap between ticks delays consolidation; acceptable on the bench where ticks are driven by tests/replay.
- Misconfigured `min_interval_s=0` would consolidate every tick; allowed but documented (consolidation is idempotent and bounded by `max_episodes`).
