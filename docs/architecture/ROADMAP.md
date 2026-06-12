# Roadmap

Date: 2026-06-12
Status: V1 memory prototype roadmap

This roadmap orders the next work by safety and dependency. Mneme should remain bench-only and memory-first until the storage, retrieval, provenance, and consolidation contracts are testable.

## Phase 0 — Verified Starter Baseline

Status: mostly complete.

Already present:

- Package skeleton, SQLite migration, scripts, tests, docs, config, and interface drafts.
- Tracked migration runner with checksum audit.
- Salience scoring with explicit remember override.
- Raw trace, episode, and fact writes.
- Meta-memory and working context snapshot storage methods.
- Fact and episode ID lookups.
- Basic text retrieval over facts and episodes.
- Conservative non-mutating consolidation placeholder.
- High-level memory facade and JSON CLI for local debug/replay workflows.
- Local runtime event model and deterministic in-process event bus for ROS-like tests and demos.
- Bounded sensory echo and working memory components integrated with local runtime events.
- Deterministic simulated perception workers and scenario replay fixtures.

Remaining baseline cleanup:

- Keep status documents and backlog aligned with implemented behavior.
- Add raw trace read/list and fact support read APIs before expanding retrieval behavior.
- Avoid treating interface drafts as runtime ROS integration.
- Consider a package console-script entry point after CLI command shape settles.
- Keep local runtime events adapter-free until the event boundaries stabilize.
- Add durable promotion flows only after replay, echo, and working-memory behavior remains stable under tests.

## Phase 1 — Storage and Provenance Baseline

Goal: make stored memories inspectable and provenance-preserving without changing the schema.

Deliverables:

- Read APIs for raw traces and fact support links.
- Episode time-window retrieval.
- [x] Meta-memory writes for raw traces, episodes, facts, and summaries.
- [x] Speakability filtering for ordinary retrieval.
- [x] Retrieval count updates for returned records.
- Provenance summary generation from stored trace, episode, and fact support data.

Exit criteria:

- A stored candidate can be traced from raw trace to episode to fact support.
- Tests prove support links can be read directly.
- No new dependencies are introduced.

## Phase 2 — Structured Fact Retrieval

Goal: move beyond simple free-text lookup while preserving the current simple API.

Status: Implemented for facts. Episode time-window/topic retrieval remains future work.

Deliverables:

- [x] Fact lookup by subject, predicate, and optional object/topic text.
- [x] Tests for user-confirmed and inferred fact retrieval.
- [x] Clear behavior for active versus superseded/conflicted/suppressed statuses.
- [x] Backward-compatible `retrieve_memory()` behavior over the new structured storage methods.

Exit criteria:

- [x] A topic/person query can return relevant facts without relying only on JSON substring matching.
- [x] Retrieval results preserve source type and confidence.

## Phase 3 — Conflict and Meta-Memory

Goal: implement the truth/provenance rules documented in the design.

Deliverables:

- [x] Meta-memory writes for stored episodes and facts.
- [x] Basic conflict detection for facts with the same subject/predicate and incompatible object values.
- [x] User-confirmed fact precedence over inferred facts during conflict/supersession decisions.
- [x] Supersession/conflict status tests.

Exit criteria:

- [x] Conflicts are marked rather than silently overwritten.
- [x] User-confirmed facts are preferred during conflict/supersession decisions.

## Phase 4 — Retrieval Ranking

Goal: make retrieval cue-based while staying local and deterministic.

Status: Implemented for facts and episodes. Summaries remain future work because summary retrieval is not implemented yet.

Deliverables:

- [x] Reranking based on context match, entity match, recency, salience, confidence, source type, and retrieval history where available.
- [x] Use of `MemoryQuery.entities`; `MemoryQuery.tags` is already supported for fact retrieval.
- Retrieval warnings for empty, suppressed, or conflicting memory results.
- [x] Tests for rank order and ranking explanations.
- Tests for provenance summary derived from stored support links.

Exit criteria:

- [x] Retrieval order is explainable and tested.
- Queries for the same topic/person return stable, relevant bundles.

## Phase 5 — Minimal Consolidation

Goal: create useful summaries without pretending to have a full daemon.

Deliverables:

- [x] `memory_summary` writes for repeated or high-salience episodes.
- [x] A deterministic repeated-event grouping placeholder.
- [x] Decay/downranking fields or documented schema changes if current tables are insufficient.
- [x] Consolidation report tests.

Exit criteria:

- [x] Repeated events can produce one summary artifact.
- [x] The consolidation pass remains safe, local, and deterministic.

## Deferred Until V1 Memory Is Stable

Do not start these until the memory core is demonstrably stable:

- ROS 2 runtime packages and launch files.
- Real camera, microphone, touch, or body-state integrations.
- Hardware actuation, GPIO, serial, servo control, or firmware flashing.
- LLM-backed summarization or autonomous procedural memory.
- Vector databases or cloud storage.

## Current Safest Next Task

Start with the remaining Phase 1 storage/provenance read APIs: raw trace reads, fact support reads, and episode time-window retrieval. This keeps the next implementation narrow before retrieval ranking, conflict handling, or consolidation changes.
