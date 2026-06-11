# Core Idea

## Problem

The storage layer directly executed SQL migrations without tracking which files had been applied. That made initialization idempotent only because the SQL used `IF NOT EXISTS`, not because the system had an auditable migration history.

The schema also included `meta_memory` and `working_context_snapshot` tables without typed store methods, and there were no ID lookup helpers for episodes or facts.

## Desired Outcome

Add a lightweight migration runner and typed storage methods while preserving the current SQLite-only, local V1 architecture.

## Value

This makes database initialization repeatable, auditable, and safer for future migrations. It also exposes the storage tables already present in the schema through typed methods that preserve source type, confidence, status, and provenance fields.

## Affected Systems

- SQLite migration schema.
- `MemoryStore`.
- `scripts/init_db.py`.
- Storage tests.
- Memory storage documentation.
- Backlog and project memory.

## Constraints

- Keep SQLite as the only persistence dependency.
- Do not add an ORM.
- Do not change retrieval architecture.
- Do not add hardware, ROS runtime, or actuator behavior.

## Non-Goals

- No conflict resolution.
- No consolidation summaries.
- No vector search.
- No first-class episode provenance migration in this phase.

## Risks

Existing local databases may not yet have migration history. The runner bootstraps the tracking table and can record `001_init` safely because the current migration remains idempotent.
