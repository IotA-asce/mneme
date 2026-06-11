# Implementation Plan

## Phase 1 — Model and Schema

- Add optional `Fact.tags`.
- Add structured fact filters to `MemoryQuery`.
- Add `002_fact_tags.sql` with `fact_tag`.
- Keep `001_init.sql` unchanged.

## Phase 2 — Storage and Retrieval

- Add `MemoryStore.search_facts_structured()`.
- Preserve `search_facts(text)` by routing it through structured search.
- Default ordinary fact retrieval to active facts.
- Allow explicit status filtering for review/debug flows.
- Rank user-confirmed facts ahead of inferred facts when relevance is similar.
- Skip empty episode searches for structured fact-only queries.

## Phase 3 — Tests and Docs

- Add tests for subject, predicate, object text, source priority, source filtering, status filtering, and tags.
- Update retrieval, storage, model, and design docs.
- Update backlog and durable project memory.

## Validation

- `python -m pytest tests/test_models.py tests/test_storage_migrations.py tests/test_storage_retrieval.py`
- `python -m pytest`
- `python scripts/dev_check.py`

## Rollback

Revert the model, storage, retrieval, migration, tests, docs, backlog, implementation notes, and project memory changes. Existing databases that already applied `002_fact_tags.sql` can keep the unused table without affecting `001` behavior.

## Definition of Done

- Structured fact retrieval returns expected facts.
- Non-active facts are excluded from ordinary retrieval.
- Explicit non-active status queries return warnings.
- User-confirmed facts outrank inferred facts in tested similar-relevance cases.
- Query-text retrieval remains covered.
