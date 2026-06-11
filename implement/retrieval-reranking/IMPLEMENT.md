# Implementation Plan

## Phase 1 — Candidate Layer

- Add retrieval candidate dataclasses for facts and episodes.
- Keep the candidate shape generic enough for future summaries.
- Continue reading candidates from existing storage methods.

## Phase 2 — Deterministic Ranking

- Apply the documented ranking weights:
  - context match,
  - entity match,
  - recency,
  - salience,
  - confidence,
  - source reliability,
  - retrieval history bonus.
- Read meta-memory when present for retrieval history.
- Use deterministic tie-breaks.

## Phase 3 — Bundle Explanations

- Add optional `MemoryBundle.ranking_explanations`.
- Include score, weights, factors, weighted components, matched terms, matched entities, source type, timestamp, and meta-memory summary.
- Preserve existing `facts`, `episodes`, `summary`, and `warnings` behavior.

## Phase 4 — Tests and Docs

- Add tests for deterministic order.
- Add tests for explanations and meta-memory history bonus.
- Update retrieval docs, backlog, roadmap/status docs, and memory.

## Validation

- `python -m pytest tests/test_models.py tests/test_storage_retrieval.py`
- `python -m pytest`
- `python scripts/dev_check.py`

## Rollback

Revert retrieval, model, test, documentation, implementation-plan, and memory changes. No migration rollback is needed because this change does not alter persistence schema.

## Definition of Done

- Existing retrieval behavior still works.
- Facts and episodes are reranked deterministically.
- Returned results include ranking explanations.
- Tests prove order and explanations.
