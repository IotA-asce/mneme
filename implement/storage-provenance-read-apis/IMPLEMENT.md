# Implementation Plan

## Phase 1 — Read Models

- Add `RawTraceRecord` dataclass (trace_id, created_ts, source_type, source_id, summary, payload, confidence, salience) with validation in `__post_init__`.
- Add `FactSupportRecord` dataclass (fact_id, episode_id, weight).

## Phase 2 — Raw Trace Reads

- `get_raw_trace(trace_id)` returns a `RawTraceRecord` or `None`.
- `get_recent_raw_traces(limit=50, source_type=None)` ordered by `created_ts DESC, trace_id DESC`.
- Add optional `created_ts` keyword to `store_raw_trace()` so replay/tests can write deterministic timestamps (defaults to now, preserving current behavior).

## Phase 3 — Fact Support and Episode Window Reads

- `get_fact_support(fact_id)` returns support links ordered by `episode_id`.
- `get_facts_for_episode(episode_id)` returns facts supported by an episode ordered by `fact_id`.
- `get_episodes_in_window(start_ts, end_ts, limit=100, status=active)` using overlap semantics, ordered by `start_ts ASC, episode_id ASC`; `status=None` disables the status filter.

## Phase 4 — Provenance Chain

- `get_provenance_chain(memory_id, memory_kind)` walks stored data:
  - fact → supporting episodes via `fact_support` (`supported_by` edges),
  - episode/trace → `meta_memory.provenance.supporting_memory_ids` (`derived_from` edges),
  - resolves each referenced ID against raw traces, episodes, then facts,
  - collects unresolvable IDs under `missing`,
  - cycle-safe via a visited set, deterministic ordering throughout.
- Output is a JSON-friendly dict: `memory_id`, `memory_kind`, `nodes`, `edges`, `missing`, and a human-readable `summary` string.

## Phase 5 — Tests and Docs

- New `tests/test_storage_provenance_reads.py` written first (TDD) covering round-trips, ordering, filters, window overlap, validation errors, full fact→episode→trace traversal, and missing-reference reporting.
- Update `docs/memory/STORAGE.md` and `docs/memory/PROVENANCE.md`.
- Tick roadmap Phase 1 deliverables; update repo status.

## Files Likely To Change

- `src/android_brain_memory/storage.py`
- `src/android_brain_memory/__init__.py` (exports)
- `tests/test_storage_provenance_reads.py` (new)
- `docs/memory/STORAGE.md`, `docs/memory/PROVENANCE.md`
- `docs/architecture/ROADMAP.md`, `docs/architecture/REPO_STATUS.md`

## Validation

- `python -m pytest tests/test_storage_provenance_reads.py`
- `python -m pytest`
- `python scripts/dev_check.py`

## Dependency Order

Read models → raw trace reads → support/window reads → provenance chain → docs/memory.

## Rollback

Revert the storage, test, and documentation changes. No migration rollback needed; no schema changes.

## Definition of Done

- A stored candidate can be traced from raw trace to episode to fact support through public read APIs.
- Support links can be read directly and tests prove it.
- All list reads are deterministic.
- No new dependencies; full test suite passes.
