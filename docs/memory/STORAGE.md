# Memory Storage

Status: V1 local SQLite prototype

Mneme's V1 storage layer is intentionally small and local. It uses Python's standard-library `sqlite3` module and the migration files in `storage/migrations/`. No external persistence service, vector database, ORM, or schema framework is required.

## Boundary

The storage layer owns:

- SQLite connection setup.
- Applying tracked SQL migrations.
- Writing raw traces, episodes, facts, fact support links, meta-memory records, and working context snapshots.
- Reading facts and episodes by ID.
- Basic text search over facts and episodes.
- Structured fact search over subject, predicate, object text, source type, status, and tags.
- Recent working context snapshot reads.

The storage layer does not own:

- Salience scoring.
- Retrieval reranking.
- Consolidation or semantic extraction.
- Conflict resolution policy.
- ROS 2 transport.
- Hardware or actuator behavior.

## Migration Tracking

Migrations are tracked in `schema_migration`.

Each row records:

- `migration_id`
- `filename`
- `checksum_sha256`
- `applied_ts`

`MemoryStore.run_migrations(path)` applies `*.sql` files in sorted order. `MemoryStore.apply_migration(path)` applies one migration.

Migration behavior:

- If a migration has not been seen before, the SQL is executed and a tracking row is written.
- If the migration was already applied with the same checksum, it is skipped.
- If the migration was already applied with a different checksum, the store raises an error instead of silently reapplying changed SQL.

`scripts/init_db.py` uses the migration runner and reports whether any migrations were applied.

## Typed Storage Records

The storage module exposes lightweight dataclasses for storage-specific rows:

- `MigrationRecord`
- `MetaMemoryRecord`
- `WorkingContextSnapshot`

These are storage transfer objects, not separate cognition layers. Core memory domain models still live in `src/android_brain_memory/models.py`.

## Meta-Memory

Meta-memory records preserve audit metadata about stored memories.

Supported methods:

- `write_meta_memory(record)`
- `get_meta_memory(memory_id, memory_kind)`
- `update_meta_memory(memory_id, memory_kind, ...)`

Fields preserved:

- memory ID and kind,
- source type,
- provenance JSON,
- last retrieval timestamp,
- retrieval count,
- contradiction score,
- speakability.

The provenance field is stored as JSON and returned as a dictionary. Source type is normalized back to `SourceType`.

## Working Context Snapshots

Working context snapshots capture a small JSON-friendly view of active context.

Supported methods:

- `store_working_context_snapshot(context, snapshot_id=None, created_ts=None)`
- `get_recent_working_context_snapshots(limit=5)`

Snapshots are returned newest first by `created_ts`.

## Episodes and Facts

Supported ID lookups:

- `get_episode(episode_id)`
- `get_fact(fact_id)`

Fact lookups preserve:

- source type,
- status,
- confidence,
- object value,
- tags,
- supporting episode IDs.

Episode lookups preserve:

- timestamps,
- summary,
- context,
- salience,
- confidence,
- participant entity IDs,
- object entity IDs.

The current schema does not yet persist `Episode.provenance_refs` as a first-class column or table. Episode provenance should continue to travel through raw traces, context, fact support links, and meta-memory until a dedicated migration adds first-class episode provenance.

## Structured Fact Search

Supported method:

- `search_facts_structured(...)`

Filters:

- query text across subject, predicate, and object JSON,
- subject partial match,
- predicate partial match,
- object text partial match,
- source type exact match,
- status exact match,
- all requested tags.

Ordinary fact search defaults to active facts. Explicit non-active status searches are available for review/debug flows.

Fact tags are stored in `fact_tag`, added by migration `002_fact_tags.sql`. The storage layer tolerates older `001`-only databases by returning empty tag lists and no tag-filtered matches if `fact_tag` does not exist.

## Local Verification

Run:

```bash
python scripts/dev_check.py
```

Storage-specific tests use temporary databases and do not depend on `.local/android_brain_memory.sqlite3`.

Useful targeted command:

```bash
python -m pytest tests/test_storage_migrations.py tests/test_storage_retrieval.py
```

## Safety Notes

The storage layer is bench-only. It must not assume connected hardware, issue actuator commands, or bypass the future executive/safety layers.

Schema changes should be added as migrations rather than by manually editing local database files.
