# Rules

## Architectural Boundaries

- Extraction consumes `memory_lifecycle` promotion events and episode data; it publishes `memory_lifecycle` extraction events only.
- All fact writes go through `engine.add_fact` (the conflict-aware path). Never call `upsert_fact` with conflict handling bypassed.
- Extraction never mutates episodes, traces, or existing facts directly.

## Safety Constraints

- Extracted facts are always `model_inferred` with capped confidence. Never emit `user_confirmed` facts from extraction.
- Never silently treat an inference as a confirmed fact (AGENTS.md §9).

## Testing Expectations

- Tests first (red). Cover validation, determinism/idempotency, conflict precedence, confidence capping, and the event-driven end-to-end path.

## Performance Constraints

- One pass per episode; statements list bounded by episode context size.

## Persistence / Migration Rules

- No schema changes.

## Anti-Patterns

- No NLP heuristics over free text in V1 — structured statements only.
- No retroactive "fixing" of conflicting facts; conflicts are flagged for review.
- No random or time-based fact IDs; IDs must be content-derived.

## What Must Not Change

- Fact conflict/supersession semantics in storage.
- Promotion behavior (M1.1) and its lifecycle event contract.
