# Rules

## Architecture

- Conflict handling belongs to memory storage for this V1 prototype.
- Retrieval must continue to treat only active facts as ordinary results by default.
- Conflict reports are review/debug data, not final user-facing policy.

## Persistence

- Do not delete old facts during conflict handling.
- Use existing `status` and `supersedes_fact_id` fields.
- Add a migration only if the schema lacks required columns.

## Conflict Policy

- Same subject/predicate alone is not enough; object assertions must be incompatible.
- Different context means preserve both active facts.
- User-confirmed facts outrank model-inferred facts.
- User-confirmed versus user-confirmed incompatibility must preserve both as conflicted.

## Non-Goals

- No purge behavior.
- No LLM contradiction checks.
- No vector search.
- No background consolidation changes.
