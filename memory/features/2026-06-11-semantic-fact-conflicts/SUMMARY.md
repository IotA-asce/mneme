# Semantic Fact Conflict Detection

Type: Feature
Date: 2026-06-11
Status: Complete

## Summary

Added deterministic semantic conflict handling for facts:

- facts can carry `supersedes_fact_id`,
- `upsert_fact()` checks new active truth assertions against existing active facts with the same subject/predicate,
- user-confirmed facts supersede incompatible inferred facts,
- incompatible user-confirmed facts are preserved and marked `conflicted`,
- duplicate facts and different-context facts are not marked as conflicts,
- conflict/supersession groups can be queried through `get_fact_conflict_reports()`.

No old facts are deleted by conflict handling. No dependencies or migrations were added.
