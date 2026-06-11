# Implementation Plan

## Phase 1 — Model and Storage Validation

- Add speakability enum values.
- Add trusted/internal query flags.
- Normalize provenance JSON shape.
- Reject secret-like provenance keys.

## Phase 2 — Meta-Memory Writes

- Write optional meta-memory records during raw trace storage.
- Write optional meta-memory records during episode storage.
- Write optional meta-memory records during fact upsert.
- Add summary storage with optional meta-memory writes.

## Phase 3 — Retrieval Integration

- Filter `never_say` and `internal_only` items from ordinary retrieval.
- Allow those records only when trusted internal queries explicitly request them.
- Update retrieval count and last-retrieved timestamp for returned facts and episodes.

## Phase 4 — Tests and Docs

- Test provenance preservation.
- Test retrieval count updates.
- Test speakability filtering.
- Update provenance and retrieval docs.
- Update backlog, roadmap/status docs, and durable project memory.

## Validation

- `python -m pytest tests/test_models.py tests/test_storage_migrations.py tests/test_storage_retrieval.py`
- `python -m pytest`
- `python scripts/dev_check.py`

## Rollback

Revert model, storage, retrieval, tests, docs, implementation notes, backlog, and memory changes. No schema rollback is required because the existing `meta_memory` schema already had the needed columns.

## Definition of Done

- Stored raw traces, episodes, facts, and summaries can write meta-memory.
- Provenance JSON has normalized source, derivation, support, and notes fields.
- Retrieval updates meta-memory history for returned records.
- Ordinary retrieval excludes `never_say` and `internal_only`.
- Tests and docs cover the behavior.
