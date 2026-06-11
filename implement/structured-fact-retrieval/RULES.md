# Rules

## Architectural Boundaries

- Retrieval may query memory storage but must not write facts, episodes, actuator goals, or safety state.
- Storage owns SQLite details; retrieval owns query orchestration and bundle warnings.
- Models remain standard-library dataclasses.

## Persistence Rules

- Add schema changes through new migrations only.
- Do not edit already-applied migration files.
- Fact tags must remain optional and backwards compatible with databases that do not yet have `fact_tag`.

## Status Rules

- Active facts are the default ordinary retrieval surface.
- `conflicted`, `superseded`, `suppressed`, and `purged` facts require an explicit status filter to retrieve.
- Returning non-active facts must surface a warning in the result bundle.

## Source Rules

- User-confirmed facts outrank inferred facts when relevance is otherwise similar.
- Source priority is retrieval ordering only; it does not confirm, overwrite, supersede, or delete facts.

## Testing Expectations

- Test structured subject, predicate, object text, source type, source priority, status, and tag behavior.
- Keep existing `query_text` retrieval tests passing.

## Anti-Patterns

- Do not add embeddings or vector search in this phase.
- Do not treat inferred facts as confirmed facts.
- Do not return suppressed or purged facts through ordinary active retrieval.
