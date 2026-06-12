# Rules

## Architectural Boundaries

- The daemon schedules and observes; consolidation semantics live in `consolidation.py` and must not be duplicated or altered.
- Publishes `memory_lifecycle` events only.
- No threads, asyncio, timers, or sleeps — time is injected; callers drive `tick()`.

## Safety Constraints

- No hardware behavior. Consolidation remains conservative: summaries are created, source episodes preserved.

## Testing Expectations

- Tests first (red). Cover interval policy, forced runs, idempotency across passes, batch limits, lifecycle events, and stat accumulation — all with a fixed injected clock.

## Performance Constraints

- Each pass bounded by `ConsolidationOptions.max_episodes`.

## Persistence / Migration Rules

- No schema changes.

## Anti-Patterns

- No wall-clock reads inside logic paths (clock injection only).
- No "catch-up" multi-pass loops inside a single tick.
- No swallowing of consolidation errors; SQLite failures propagate.

## What Must Not Change

- `consolidate_once` behavior and report shape.
- Lifecycle event contract established in M1.1.
