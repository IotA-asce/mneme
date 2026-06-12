# Memory Storage

Status: V1 local SQLite prototype

Mneme's V1 storage layer is intentionally small and local. It uses Python's standard-library `sqlite3` module and the migration files in `storage/migrations/`. No external persistence service, vector database, ORM, or schema framework is required.

## Boundary

The storage layer owns:

- SQLite connection setup.
- Applying tracked SQL migrations.
- Writing raw traces, episodes, facts, fact support links, meta-memory records, and working context snapshots.
- Writing memory summaries.
- Writing corresponding meta-memory records during raw trace, episode, fact, and summary storage.
- Reading memory summaries.
- Writing decay/downranking metadata through meta-memory provenance.
- Conservative semantic fact conflict and supersession handling during fact upsert.
- Reading facts and episodes by ID.
- Reading recent active episodes.
- Reading raw traces by ID and listing recent raw traces.
- Reading fact support links directly, in both directions.
- Reading episodes by overlapping time window.
- Generating provenance chains from stored trace, episode, fact support, and meta-memory data.
- Basic text search over facts and episodes.
- Structured fact search over subject, predicate, object text, source type, status, and tags.
- Conflict/supersession report queries for facts.
- Recent working context snapshot reads.

The storage layer does not own:

- Salience scoring.
- Retrieval reranking.
- Consolidation or semantic extraction.
- Human review workflows for unresolved conflicts.
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
- `FactConflictReport`
- `WorkingContextSnapshot`
- `RawTraceRecord`
- `FactSupportRecord`

These are storage transfer objects, not separate cognition layers. Core memory domain models still live in `src/android_brain_memory/models.py`.

## Meta-Memory

Meta-memory records preserve audit metadata about stored memories.

Supported methods:

- `write_meta_memory(record)`
- `get_meta_memory(memory_id, memory_kind)`
- `update_meta_memory(memory_id, memory_kind, ...)`
- `record_retrieval(memory_id, memory_kind, ...)`
- `update_decay_metadata(memory_id, memory_kind, ...)`

Fields preserved:

- memory ID and kind,
- source type,
- provenance JSON,
- last retrieval timestamp,
- retrieval count,
- contradiction score,
- speakability.

The provenance field is stored as JSON and returned as a dictionary. Source type is normalized back to `SourceType`.

See `docs/memory/PROVENANCE.md` for normalized provenance fields and speakability policy.

Consolidation decay/downranking hints are stored in `provenance_json["decay"]`. This is metadata only; retrieval does not use it for ranking yet.

## Summaries

Supported method:

- `store_memory_summary(...)`
- `get_memory_summary(summary_id)`
- `get_memory_summaries(...)`
- `search_memory_summaries(text, limit=5)` — case-insensitive partial match over summary text and scope key, ordered `created_ts DESC, summary_id ASC`.

Summary storage writes to `memory_summary` and can write a corresponding `meta_memory` row. The retrieval manager searches summaries for text queries and returns them in `MemoryBundle.summaries`.

## Working Context Snapshots

Working context snapshots capture a small JSON-friendly view of active context.

Supported methods:

- `store_working_context_snapshot(context, snapshot_id=None, created_ts=None)`
- `get_recent_working_context_snapshots(limit=5)`

Snapshots are returned newest first by `created_ts`.

## Raw Traces

Supported methods:

- `get_raw_trace(trace_id)` returns a `RawTraceRecord` or `None`.
- `get_recent_raw_traces(limit=50, source_type=None)` returns records newest first (`created_ts DESC, trace_id DESC`), optionally filtered to one source type.
- `store_raw_trace(...)` accepts an optional `created_ts` keyword so replay and tests can write deterministic timestamps. The default remains the current time.

`RawTraceRecord` preserves the trace ID, created timestamp, source type, optional source ID, summary, decoded JSON payload, confidence, and salience.

## Fact Support Links

Supported methods:

- `get_fact_support(fact_id)` returns `FactSupportRecord` links ordered by `episode_id`.
- `get_facts_for_episode(episode_id)` returns the facts supported by an episode ordered by `fact_id`.

These reads expose the `fact_support` table directly so provenance and review tooling does not need to re-derive support from `Fact.supporting_episode_ids`.

## Provenance Chains

`get_provenance_chain(memory_id, memory_kind)` walks already-stored provenance for a `raw_trace`, `episode`, `fact`, or `summary`:

- facts link to supporting episodes through `fact_support` (`supported_by` edges),
- every node follows `meta_memory.provenance.supporting_memory_ids` (`derived_from` edges),
- referenced IDs are resolved against raw traces, episodes, facts, then summaries,
- IDs that cannot be resolved are reported under `missing` instead of failing,
- traversal is breadth-first, cycle-safe, and deterministic.

The result is a JSON-friendly dict with `nodes`, `edges`, `missing`, and a human-readable `summary` string. An unknown root raises `KeyError`; an unsupported kind raises `ValueError`. Traversal is read-only and never repairs or rewrites stored provenance.

## Episodes and Facts

Supported ID lookups:

- `get_episode(episode_id)`
- `get_recent_episodes(...)`
- `get_episodes_in_window(start_ts, end_ts, limit=100, status=active)` — returns episodes overlapping the window (`start_ts <= window_end AND end_ts >= window_start`) ordered by `start_ts ASC, episode_id ASC`; pass `status=None` to disable the status filter.
- `get_fact(fact_id)`

Status setters for lifecycle transitions (suppression, purge, review workflows):

- `set_episode_status(episode_id, status)` — also refreshes `updated_ts`; raises `KeyError` for unknown IDs.
- `set_fact_status(fact_id, status)` — raises `KeyError` for unknown IDs.

Fact lookups preserve:

- source type,
- status,
- confidence,
- object value,
- supersession link,
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

## Fact Conflicts

`upsert_fact()` performs conservative semantic conflict handling for active `user_confirmed` and `model_inferred` facts.

When an incompatible user-confirmed fact supersedes an inferred fact, the inferred fact is marked `superseded`, the new fact remains `active`, and `supersedes_fact_id` points at the older fact.

When incompatible user-confirmed facts disagree, both facts are preserved and marked `conflicted` for review.

Different context in `object_value` preserves both facts as active. Duplicate object values are not conflicts.

Supported helper:

- `get_fact_conflict_reports(subject="", predicate="", limit=50)`

See `docs/memory/CONFLICTS.md` for the full V1 rule set.

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
