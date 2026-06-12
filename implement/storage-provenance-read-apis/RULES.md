# Rules

## Architectural Boundaries

- Storage owns these reads; retrieval ranking, consolidation, and CLI must not be modified in this change.
- Provenance traversal is read-only. It must not create, repair, or normalize stored provenance rows.
- No ROS, asyncio, threading, or new dependencies.

## Safety Constraints

- No hardware or actuator behavior.
- Never expose secret-bearing provenance keys; rely on existing write-time rejection and do not add bypasses.

## Testing Expectations

- Tests written before implementation (red first).
- Cover: ID round-trips, missing-ID `None` returns, list ordering, source-type filter, window overlap semantics, invalid window `ValueError`, full fact→episode→trace chain, missing-reference reporting.
- Use temporary SQLite databases via `tmp_path`, mirroring existing storage tests.

## Performance Constraints

- Single-process SQLite queries with LIMIT clauses; no full-graph walks beyond the visited set of one chain.

## Persistence / Migration Rules

- No schema changes. No new migrations. Existing rows must remain readable.

## Anti-Patterns

- Do not return raw `sqlite3.Row` objects from public APIs.
- Do not guess at missing provenance; report it under `missing`.
- Do not introduce nondeterministic ordering (unordered dict iteration over query results, random IDs in outputs).

## What Must Not Change

- Existing write APIs' behavior and signatures (additive optional `created_ts` only).
- The migration checksum of applied migration files.
- Conflict/supersession behavior in `upsert_fact`.
