# Rules

## Architectural Boundaries

- Decay reads meta-memory and statuses; it never rewrites memory content, provenance history, or support links.
- Retrieval downranking is a transparent multiplier — visible in every ranking explanation, never hidden.
- Decay publishes `memory_lifecycle` events only.

## Safety Constraints

- `user_confirmed` facts: never auto-suppressed, never auto-purged; explicit purge requires `force=True` and a reason.
- No deletion in V1 — suppression is reversible; purge is a status + provenance tombstone.

## Testing Expectations

- Tests first (red). Each suppression criterion (policy, age, retrieval count) must be shown to gate independently. Purge force-gate and tombstone shape pinned. Deterministic `now_s` injection everywhere.

## Performance Constraints

- One bounded pass (`max_items`) per invocation; no full-table scans beyond the bounded recent sets.

## Persistence / Migration Rules

- No schema changes; `suppressed`/`purged` statuses already exist.

## Anti-Patterns

- No probabilistic forgetting.
- No silent decay: every action lands in the report and the lifecycle event.
- No coupling decay decisions to retrieval-time state (the pass is storage-driven, not query-driven).

## What Must Not Change

- Active-status retrieval defaults; conflict/supersession semantics; consolidation's decay-metadata writing.
