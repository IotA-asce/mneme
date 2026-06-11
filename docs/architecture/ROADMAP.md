# Roadmap

Date: 2026-06-11
Status: V1 memory prototype roadmap

This roadmap orders the next work by safety and dependency. Mneme should remain bench-only and memory-first until the storage, retrieval, provenance, and consolidation contracts are testable.

## Phase 0 — Verified Starter Baseline

Status: mostly complete.

Already present:

- Package skeleton, SQLite migration, scripts, tests, docs, config, and interface drafts.
- Salience scoring with explicit remember override.
- Raw trace, episode, and fact writes.
- Basic text retrieval over facts and episodes.
- Conservative non-mutating consolidation placeholder.

Remaining baseline cleanup:

- Keep status documents and backlog aligned with implemented behavior.
- Add storage contract tests before adding more storage behavior.
- Avoid treating interface drafts as runtime ROS integration.

## Phase 1 — Storage and Provenance Baseline

Goal: make stored memories inspectable and provenance-preserving without changing the schema.

Deliverables:

- Read APIs for raw traces, episodes, facts, and fact support links.
- Tests for migration table creation and foreign-key-backed support links.
- Episode persistence for participant/object roles or a documented V1 limitation if object persistence is deferred.
- Provenance summary generation from stored trace, episode, and fact support data.

Exit criteria:

- A stored candidate can be traced from raw trace to episode to fact support.
- Tests prove support links survive writes and reads.
- No new dependencies are introduced.

## Phase 2 — Structured Fact Retrieval

Goal: move beyond simple free-text lookup while preserving the current simple API.

Deliverables:

- Fact lookup by subject, predicate, and optional object/topic text.
- Tests for user-confirmed and inferred fact retrieval.
- Clear behavior for active versus superseded/conflicted/suppressed statuses.
- Backward-compatible `retrieve_memory()` behavior over the new structured storage methods.

Exit criteria:

- A topic/person query can return relevant facts without relying only on JSON substring matching.
- Retrieval results preserve source type and confidence.

## Phase 3 — Conflict and Meta-Memory

Goal: implement the truth/provenance rules documented in the design.

Deliverables:

- Meta-memory writes for stored episodes and facts.
- Basic conflict detection for facts with the same subject/predicate and incompatible object values.
- User-confirmed fact precedence over inferred facts.
- Supersession/conflict status tests.

Exit criteria:

- Conflicts are marked rather than silently overwritten.
- User-confirmed facts outrank weaker inferred facts in tested retrieval scenarios.

## Phase 4 — Retrieval Ranking

Goal: make retrieval cue-based while staying local and deterministic.

Deliverables:

- Reranking based on context match, entity match, recency, salience, confidence, source type, and retrieval history where available.
- Use of `MemoryQuery.entities` and `MemoryQuery.tags`.
- Retrieval warnings for empty, suppressed, or conflicting memory results.
- Tests for rank order and provenance summary.

Exit criteria:

- Retrieval order is explainable and tested.
- Queries for the same topic/person return stable, relevant bundles.

## Phase 5 — Minimal Consolidation

Goal: create useful summaries without pretending to have a full daemon.

Deliverables:

- `memory_summary` writes for repeated or high-salience episodes.
- A deterministic repeated-event grouping placeholder.
- Decay/downranking fields or documented schema changes if current tables are insufficient.
- Consolidation report tests.

Exit criteria:

- Repeated events can produce one summary artifact.
- The consolidation pass remains safe, local, and deterministic.

## Deferred Until V1 Memory Is Stable

Do not start these until the memory core is demonstrably stable:

- ROS 2 runtime packages and launch files.
- Real camera, microphone, touch, or body-state integrations.
- Hardware actuation, GPIO, serial, servo control, or firmware flashing.
- LLM-backed summarization or autonomous procedural memory.
- Vector databases or cloud storage.

## Current Safest Next Task

Start with Phase 1 storage and provenance tests. This gives the next implementation a narrow blast radius and creates confidence before retrieval ranking, conflict handling, or consolidation changes.
