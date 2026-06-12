# Implementation Plan

## Phase 1 — Storage Summary Search

- `search_memory_summaries(text, limit=5)` over `memory_summary.summary` and `scope_key` (case-insensitive partial match), ordered `created_ts DESC, summary_id ASC`.

## Phase 2 — Bundle Model

- Add `MemoryBundle.summaries: list[dict]` (JSON-friendly summary records), default empty, validated like `ranking_explanations`, included in `to_dict`/`from_dict`.

## Phase 3 — Retrieval Integration

- Build summary retrieval candidates (kind `summary`) when `include_summaries` is set and `query_text` is non-empty.
- Rank with the existing weights (timestamp = `end_ts` or `created_ts`; no salience; source type from meta-memory).
- Cap by `max_results`, include ranking explanations, update retrieval counters, apply existing speakability filtering.
- Add `found N summary(ies)` to the bundle summary line.

## Phase 4 — Warnings

- Empty bundle → `no matching memory found for this query`.
- Speakability filtering withheld candidates → `N candidate(s) withheld by speakability policy`.
- Returned facts whose subject/predicate group has conflicted records → one warning per group, deterministic order.
- Keep the existing non-active status warning.

## Phase 5 — Derived Provenance Summary

- Replace the hardcoded `provenance_summary` with text generated from `get_provenance_chain()` for returned facts, episodes, and summaries.
- Deduplicate edge lines, deterministic order, fall back to a clear sentence when no links exist.

## Phase 6 — Tests and Docs

- New `tests/test_retrieval_warnings_summaries.py` written first (TDD).
- Update `docs/memory/RETRIEVAL.md`, `docs/memory/PROVENANCE.md`, roadmap Phase 4, repo status.

## Files Likely To Change

- `src/android_brain_memory/models.py`, `storage.py`, `retrieval.py`
- `tests/test_retrieval_warnings_summaries.py` (new)
- `docs/memory/RETRIEVAL.md`, `docs/memory/PROVENANCE.md`
- `docs/architecture/ROADMAP.md`, `docs/architecture/REPO_STATUS.md`

## Validation

- `python -m pytest tests/test_retrieval_warnings_summaries.py`
- `python -m pytest`
- `python scripts/dev_check.py`

## Dependency Order

Storage search → bundle model → retrieval candidates → warnings → provenance summary → docs.

## Rollback

Revert model, storage, retrieval, test, and doc changes. No migrations involved.

## Definition of Done

- Text queries return ranked summaries respecting `include_summaries`, speakability, and `max_results`.
- Empty/withheld/conflicting conditions produce deterministic warnings.
- `provenance_summary` reflects stored support links and is covered by tests.
- Full suite passes with no behavioral regressions for facts/episodes.
