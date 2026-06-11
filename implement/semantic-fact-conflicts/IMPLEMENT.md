# Implementation Plan

## Phase 1

- Extend `Fact` with optional `supersedes_fact_id`.
- Add `FactConflictReport`.
- Load and write `supersedes_fact_id` through storage.

## Phase 2

- Compare new active facts against existing active facts with the same subject/predicate.
- Treat matching context with different assertion values as incompatible.
- Supersede lower-trust inferred facts when a user-confirmed fact arrives.
- Mark incompatible user-confirmed facts as conflicted.

## Phase 3

- Add report/query helper for conflict and supersession groups.
- Add tests for inferred-vs-confirmed, confirmed-vs-confirmed, duplicates, and context-specific non-conflicts.
- Update docs, backlog, and project memory.

## Validation

- `git diff --check`
- `python -m pytest tests/test_models.py tests/test_storage_migrations.py tests/test_storage_retrieval.py`
- `python -m pytest`
- `python scripts/dev_check.py`

## Rollback

- Revert the storage conflict helper and `Fact.supersedes_fact_id` model extension.
- Existing databases do not need migration rollback because `supersedes_fact_id` already exists.

## Definition of Done

- Conflicts are marked rather than silently overwritten.
- User-confirmed facts supersede inferred facts.
- Incompatible user-confirmed facts are preserved and marked for review.
- Tests, docs, backlog, and project memory are updated.
