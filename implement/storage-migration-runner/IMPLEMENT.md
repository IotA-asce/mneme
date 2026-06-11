# Implementation Plan

## Phase 1 — Migration Tracking

- Add `schema_migration`.
- Add `MigrationRecord`.
- Make `apply_migration()` skip already-applied migrations with matching checksums.
- Raise on checksum mismatch.
- Add `run_migrations()` for sorted migration directory application.
- Update `scripts/init_db.py` to call the runner.

## Phase 2 — Typed Storage Methods

- Add `MetaMemoryRecord` and methods to write, read, and update records.
- Add `WorkingContextSnapshot` and methods to write and read recent snapshots.
- Add `get_episode()` and `get_fact()`.
- Preserve source type, status, confidence, and support links in returned model objects.

## Phase 3 — Verification and Docs

- Add temporary database tests for migrations and storage methods.
- Add `docs/memory/STORAGE.md`.
- Update backlog and durable project memory.

## Rollback

Revert the storage module, migration SQL, script update, and storage tests. Existing data tables remain compatible because the only schema addition is an idempotent migration tracking table.

## Definition of Done

- Migrations are tracked and idempotent.
- Changed checksums are rejected.
- Typed storage methods are tested against temporary databases.
- Existing smoke scripts and tests still pass.
