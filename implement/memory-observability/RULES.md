# Rules

## Architectural Boundaries

- Engine eventing is opt-in and additive; `event_bus=None` must preserve existing behavior exactly.
- Observability events describe state changes; nothing may consume them as commands.

## Safety Constraints

- Retrieval events must never include memory content — IDs, counts, query metadata, and warnings only. Speakability-withheld items must not be identifiable from events.

## Testing Expectations

- Tests first (red). Assert event payload shapes, the no-bus path, and CLI output as parsed JSON.

## Performance Constraints

- Event payloads bounded by `max_results`; decay listing bounded by `limit`.

## Persistence / Migration Rules

- No schema changes.

## Anti-Patterns

- No print/log side channels — the event bus is the observability stream.
- No content leakage into events "for convenience".

## What Must Not Change

- Existing CLI command behavior and output shapes.
- Lifecycle event contract from M1.1–M1.4.
