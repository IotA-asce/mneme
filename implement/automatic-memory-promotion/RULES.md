# Rules

## Architectural Boundaries

- The promoter consumes `memory_candidate` events and publishes `memory_lifecycle` events only — never intent, skill, or safety events.
- Salience scoring remains the only decision authority; the promoter must not adjust scores or thresholds.
- Storage writes go through `MnemeMemory` so provenance/meta-memory behavior stays uniform.

## Safety Constraints

- No actuator or hardware behavior. Lifecycle events carry decision metadata, not raw perception payloads.

## Testing Expectations

- Tests first (red). Cover all four promotion decisions, bus integration, malformed payload tolerance, lifecycle event contents, and end-to-end scenario replay with provenance verification.

## Performance Constraints

- One synchronous storage call per candidate event; no buffering or batching in V1.

## Persistence / Migration Rules

- No schema changes.

## Anti-Patterns

- Do not bypass `remember_candidate` with direct store calls.
- Do not let a malformed event raise out of the bus callback.
- Do not store echo-only candidates "just in case".

## What Must Not Change

- Salience thresholds/decisions, existing `remember_candidate` behavior, event kind/topic boundary validation for existing kinds.
