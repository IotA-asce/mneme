# Implementation Plan

## Phase 1

- Add `ConsolidationOptions`.
- Expand `ConsolidationReport`.
- Fetch recent active episodes through storage.

## Phase 2

- Build deterministic candidate groups from context tags, participants plus topic text, topic tokens, and participant/time buckets.
- Create deterministic summary IDs and scope keys.
- Write `memory_summary` records for groups meeting the repetition threshold.

## Phase 3

- Preserve source episodes.
- Write decay/downranking hints to `meta_memory.provenance_json["decay"]`.
- Add a manual `scripts/consolidate_once.py` runner.

## Phase 4

- Add repeated-event tests.
- Update docs, backlog, implementation records, and project memory.

## Validation

- `git diff --check`
- `python -m pytest tests/test_consolidation.py tests/test_storage_migrations.py`
- `python -m pytest`
- `python scripts/dev_check.py`
- `python scripts/consolidate_once.py`

## Rollback

- Revert the consolidation module changes and script.
- Remove summary-read/decay metadata helper methods if no longer needed.
- No migration rollback is required because no schema migration is added.

## Definition of Done

- Repeated active episodes can create one deterministic summary.
- Source episodes remain active and readable.
- Non-representative episodes receive meta-memory decay/downranking metadata.
- Tests and docs describe the V1 deterministic boundary.
